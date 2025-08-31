import requests
import pandas as pd
import re

class AdatokGyujtese:
    def __init__(self):
        pass

    def _slugify(self, s: str) -> str:
        if s is None:
            return ""
        s = s.strip()
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"[^0-9a-zA-Z_]+", "", s)
        return s.lower()

    def jotform_to_dataframe(self, eu_mode: bool = True, limit: int = 1000) -> pd.DataFrame:
        api_key = "cb09ee37d76479f386088766221dfa6c"
        form_id = "252166213464049"
        """
        Jotform beküldések DataFrame-ként.
        - Hiányzó/üres answer -> None
        - Listák -> '; '-tel összefűzve
        - Dict válaszok -> több oszlopra bontva: <mezonev>.<kulcs>
        """
        base = "https://eu-api.jotform.com" if eu_mode else "https://api.jotform.com"
        url = f"{base}/form/{form_id}/submissions?apiKey={api_key}&limit={limit}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        # Ha EU Safe Mode átirányítást kapnánk, jelezzünk egyértelmű hibát
        if "content" not in payload:
            msg = payload.get("message", "Váratlan API válasz.")
            raise RuntimeError(f"Jotform API hiba: {msg}")

        rows = []
        for sub in payload["content"]:
            row = {
                "submission_id": sub.get("id"),
                "created_at": sub.get("created_at"),
                "status": sub.get("status"),
            }
            answers = sub.get("answers", {}) or {}
            for qid, ans in answers.items():
                field_base = ans.get("name") or ans.get("text") or f"field_{qid}"
                field_key = self._slugify(field_base) or f"field_{qid}"

                # Ha nincs 'answer' kulcs vagy üres az érték, tegyünk None-t
                if "answer" not in ans:
                    row[field_key] = None
                    continue

                a = ans.get("answer")
                if a in ("", None) or a == [] or a == {}:
                    row[field_key] = None
                    continue

                # Típusfüggő kezelés
                if isinstance(a, dict):
                    # pl. cím mező: {city: ..., street: ...}
                    for k, v in a.items():
                        subkey = self._slugify(str(k)) or str(k)
                        row[f"{field_key}.{subkey}"] = v
                elif isinstance(a, list):
                    # pl. több választás vagy több fájl -> egy cellába fűzzük
                    row[field_key] = "; ".join(map(str, a))
                else:
                    # skalár: string/number/bool
                    row[field_key] = a

            rows.append(row)

        df = pd.DataFrame(rows)
        return df