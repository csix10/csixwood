from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, List, Dict, Any, Tuple
import re
import logging
import faj_beolvaso_kiirato

import pandas as pd


@dataclass(frozen=True)
class PDFTable:
    page: int
    table_index: int
    method: str
    df: pd.DataFrame


def _clean_cell(x: Any) -> str:
    """Normalize cell text."""
    if x is None:
        return ""
    s = str(x)
    s = s.replace("\u00a0", " ")  # nbsp
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s


def _drop_empty(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully empty rows/cols (after stripping)."""
    df2 = df.copy()
    df2 = df2.applymap(_clean_cell)
    df2 = df2.loc[~df2.apply(lambda r: all(v == "" for v in r), axis=1)]
    df2 = df2.loc[:, ~df2.apply(lambda c: all(v == "" for v in c), axis=0)]
    return df2.reset_index(drop=True)


def _promote_header_if_reasonable(df: pd.DataFrame) -> pd.DataFrame:
    """
    If first row looks like a header (few numbers, many text cells),
    promote it to columns.
    """
    if df.empty or df.shape[0] < 2:
        return df

    first = df.iloc[0].tolist()
    # Heuristic: header row has mostly non-numeric tokens
    def is_numericish(s: str) -> bool:
        s = _clean_cell(s)
        if s == "":
            return False
        # allow prices like "1.230,-ft" or "189.900,-ft"
        return bool(re.fullmatch(r"[0-9\.\, ]+(\-?\s*ft.*)?", s.lower()))

    numeric_ratio = sum(is_numericish(x) for x in first) / max(len(first), 1)
    # If it's mostly text, treat as header
    if numeric_ratio <= 0.35:
        cols = [(_clean_cell(c) or f"col_{i}") for i, c in enumerate(first)]
        out = df.iloc[1:].copy()
        out.columns = cols
        return out.reset_index(drop=True)

    return df


def _camelot_extract(
    pdf_path: str,
    pages: str,
    flavor: str,
    strip_text: str = "\n",
) -> List[PDFTable]:
    """
    Extract tables using camelot. Requires: pip install camelot-py[cv]
    For lattice: needs ghostscript; for stream: pure text-based.
    """
    import camelot  # type: ignore

    tables = camelot.read_pdf(
        pdf_path,
        pages=pages,
        flavor=flavor,
        strip_text=strip_text,
    )

    out: List[PDFTable] = []
    for i, t in enumerate(tables):
        df = t.df.copy()
        df = _drop_empty(df)
        df = _promote_header_if_reasonable(df)
        if df.empty:
            continue
        # camelot returns page number as string like "7"
        page_num = int(getattr(t, "page", "0") or 0)
        out.append(PDFTable(page=page_num, table_index=i, method=f"camelot:{flavor}", df=df))
    return out


def _pdfplumber_extract_simple(
    pdf_path: str,
    pages: Optional[Iterable[int]] = None,
) -> List[PDFTable]:
    """
    Fallback extraction using pdfplumber. It can do table extraction too, but
    here we keep it simple and robust: attempt extract_table(s) with defaults.
    """
    import pdfplumber  # type: ignore

    out: List[PDFTable] = []
    with pdfplumber.open(pdf_path) as pdf:
        page_indices = list(pages) if pages is not None else list(range(len(pdf.pages)))
        for pidx in page_indices:
            page = pdf.pages[pidx]
            # Try multiple tables
            tables = page.extract_tables() or []
            for tidx, tbl in enumerate(tables):
                if not tbl:
                    continue
                df = pd.DataFrame(tbl)
                df = _drop_empty(df)
                df = _promote_header_if_reasonable(df)
                if df.empty:
                    continue
                out.append(PDFTable(page=pidx + 1, table_index=tidx, method="pdfplumber", df=df))
    return out


def pdf_to_dataframe(
    pdf_path: str,
    pages: Optional[Iterable[int]] = None,
    *,
    prefer_camelot: bool = True,
    logger: Optional[logging.Logger] = None,
) -> pd.DataFrame:
    """
    Convert a PDF (multi-table) into a single pandas DataFrame.

    Output format (long, "tidy"):
      - page: int
      - table_index: int
      - method: str
      - row_index: int
      - data: dict (one row as a dict of columns -> values)

    Why long format?
      - The PDF contains many different table schemas; long format is robust.
      - You can later split/filter by 'page' and 'table_index', then normalize.

    Parameters
    ----------
    pdf_path:
        Path to PDF.
    pages:
        Iterable of 1-based page numbers to process (e.g., [1,2,3]).
        If None, process all pages.
    prefer_camelot:
        If True, try camelot first (lattice then stream), else go straight to pdfplumber.
    logger:
        Optional logger.

    Returns
    -------
    pd.DataFrame:
        Long-format dataframe aggregating all extracted tables/rows.
    """
    log = logger or logging.getLogger(__name__)

    # Normalize pages to camelot/pdfplumber expectations
    pages_1based: Optional[List[int]] = None
    if pages is not None:
        pages_1based = [int(p) for p in pages]
        if any(p <= 0 for p in pages_1based):
            raise ValueError("pages must be 1-based positive integers, e.g. [1,2,3].")

    extracted: List[PDFTable] = []

    if prefer_camelot:
        # camelot wants pages as "1,2,3" or "1-5"
        if pages_1based is None:
            pages_str = "all"
        else:
            # compress consecutive ranges for readability
            sorted_pages = sorted(set(pages_1based))
            ranges: List[Tuple[int, int]] = []
            start = prev = sorted_pages[0]
            for p in sorted_pages[1:]:
                if p == prev + 1:
                    prev = p
                else:
                    ranges.append((start, prev))
                    start = prev = p
            ranges.append((start, prev))
            parts = [f"{a}-{b}" if a != b else f"{a}" for a, b in ranges]
            pages_str = ",".join(parts)

        # Try lattice then stream
        for flavor in ("lattice", "stream"):
            try:
                got = _camelot_extract(pdf_path, pages=pages_str, flavor=flavor)
                if got:
                    log.info("camelot %s extracted %d tables", flavor, len(got))
                extracted.extend(got)
            except Exception as e:
                log.warning("camelot %s failed: %s", flavor, e)

    # Fallback if nothing found or camelot disabled
    if not extracted:
        try:
            # pdfplumber uses 0-based indices internally; we pass 0-based here
            pages_0based = None
            if pages_1based is not None:
                pages_0based = [p - 1 for p in pages_1based]
            got = _pdfplumber_extract_simple(pdf_path, pages=pages_0based)
            extracted.extend(got)
            log.info("pdfplumber extracted %d tables", len(got))
        except Exception as e:
            raise RuntimeError(f"pdfplumber extraction failed: {e}") from e

    # Build long-format dataframe
    records: List[Dict[str, Any]] = []
    for t in extracted:
        df = t.df.copy()
        df = df.applymap(_clean_cell)

        # Ensure unique column names
        cols = list(df.columns)
        seen = {}
        new_cols = []
        for c in cols:
            base = c if c else "col"
            k = seen.get(base, 0)
            seen[base] = k + 1
            new_cols.append(base if k == 0 else f"{base}_{k}")
        df.columns = new_cols

        for ridx, row in df.iterrows():
            row_dict = row.to_dict()
            # skip rows that are totally empty
            if all(v == "" for v in row_dict.values()):
                continue
            records.append(
                {
                    "page": t.page,
                    "table_index": t.table_index,
                    "method": t.method,
                    "row_index": int(ridx),
                    "data": row_dict,
                }
            )

    return pd.DataFrame.from_records(records)


# --- Example usage ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pdf_path = "../data/borovi_ar.pdf"

    df_long = pdf_to_dataframe(pdf_path)  # all pages
    #print(df_long.head())
    faj_beolvaso_kiirato.BeolvasKiirat().df_kiiratasa_exelbe(df_long, "futreszaru.xlsx", r"C:\Users\csiki\Downloads")
    print(df_long)

    # Example: get one table back into "wide" form:
    # pick page=2 table_index=0 for instance
    subset = df_long[(df_long["page"] == 3) & (df_long["table_index"] == 0)].copy()
    wide = pd.DataFrame(list(subset["data"]))
    print(wide.head())