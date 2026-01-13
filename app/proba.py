import os
import re
import requests
import fitz
import camelot

def pdf_letolto(url, nev):
    # --- 1. Elérési utak beállítása ---
    base_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(base_dir, ".."))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    pdf_path = os.path.join(data_dir, nev)

    # --- 2. PDF letöltése ---
    response = requests.get(url)
    with open(pdf_path, "wb") as f:
        f.write(response.content)

    print(f"✅ PDF letöltve ide: {pdf_path}")

    return pdf_path


def borovi(termek_neve):
    pdf_path = pdf_letolto("https://www.borovigerendahazkft.hu/tools/generate_pdf", "borovi_ar.pdf")

    # --- 3. PDF megnyitás ---
    doc = fitz.open(pdf_path)
    oldalak_szovege = [page.get_text("text") for page in doc]

    # --- 4. Címek felismerése ---
    cim_minta = r"^[A-ZÁÉÍÓÖŐÚÜŰ].+$"
    cim_poziciok = []

    for i, szoveg in enumerate(oldalak_szovege):
        for sor in szoveg.splitlines():
            if re.match(cim_minta, sor.strip()):
                cim_poziciok.append((i, sor.strip()))

    if not cim_poziciok:
        print("⚠️ Nem találtam címeket a PDF-ben.")
        return {}

    # --- 5. Címek és határok keresése ---
    start_index = None
    end_index = None

    for idx, (oldal_index, cim) in enumerate(cim_poziciok):
        if termek_neve.lower() in cim.lower():
            start_index = oldal_index
            if idx + 1 < len(cim_poziciok):
                end_index = cim_poziciok[idx + 1][0]  # következő cím oldalszáma
            else:
                end_index = len(oldalak_szovege) - 1  # ha az utolsó cím
            break

    if start_index is None:
        print(f"⚠️ Nem találtam '{termek_neve}' című szakaszt.")
        return {}

    # --- 6. Oldaltartomány meghatározása ---
    pages_to_read = list(range(start_index + 1, end_index + 1))
    print(f"📄 Táblázatkeresés az oldalakon: {pages_to_read}")

    # --- 7. Táblázatok beolvasása ---
    talalatok = []
    for oldal in pages_to_read:
        try:
            tables = camelot.read_pdf(
                pdf_path,
                pages=str(oldal + 1),
                flavor="stream",
                strip_text="\n"
            )
            for t in tables:
                if not t.df.empty:
                    talalatok.append(t.df)
        except Exception as e:
            print(f"⚠️ Hiba az {oldal+1}. oldal feldolgozásakor: {e}")

    if talalatok:
        print(f"✅ {len(talalatok)} táblázat beolvasva a(z) '{termek_neve}' szakasz után.")
        return {termek_neve: talalatok}
    else:
        print("⚠️ Nem talált táblázatot a megadott cím utáni szakaszban.")
        return {}
