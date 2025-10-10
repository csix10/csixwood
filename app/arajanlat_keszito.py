import app.szabasjegyzek_szerkeszto as szabjegy
import app.adatgyujto as adatgyujto
import app.faj_beolvaso_kiirato as faj
from openpyxl.drawing.image import Image
import openpyxl.styles as stilus
import os
import pandas as pd

class Arajanlat:
    def __init__(self, df, vezetek_nev = "", kereszt_nev = ""):
        self.df = df
        self.vezetek_nev = vezetek_nev
        self.kereszt_nev = kereszt_nev
        self.wb, self.ws = faj.BeolvasKiirat().szerkesztett_excel_beolvaso("minta_arajanlat.xlsx")
        self.sor = 17
        self.kezdosor = self.sor

    def tablazat_tolto(self, anyagjegyzek):
        anyagjegyzek = anyagjegyzek.astype({
            "Mennyiseg": float,
            "Egysegar": float,
            "Osszar": float
        })

        for _, row in anyagjegyzek.iterrows():
            self.ws.insert_rows(self.sor)
            self.ws.row_dimensions[self.sor].height = 16

            center_align = stilus.Alignment(vertical="center")

            # --- Cellák kitöltése ---
            self.ws.cell(row=self.sor, column=1, value=str(self.sor - self.kezdosor + 1) + ".")
            self.ws.cell(row=self.sor, column=2, value=row.get("Anyag", ""))
            self.ws.cell(row=self.sor, column=4, value=row.get("Szin", ""))

            url = row.get("URL", "")

            if isinstance(url, float) or not url:
                url = ""

            if url:
                c5 = self.ws.cell(row=self.sor, column=5, value="Link")
                c5.hyperlink = str(url)
                c5.style = "Hyperlink"

            self.ws.cell(row=self.sor, column=6, value=round(row.get("Mennyiseg", ""),2))
            self.ws.cell(row=self.sor, column=7, value=row.get("Mertekegyseg", ""))
            c8 = self.ws.cell(row=self.sor, column=8, value=round(row.get("Egysegar", ""),0))
            c8.number_format = '#,##0 "Ft"'
            c9 = self.ws.cell(row=self.sor, column=9, value=round(row.get("Osszar", ""),0))
            c9.number_format = '#,##0 "Ft"'

            # --- Egyesítés ---
            self.ws.merge_cells(
                start_row=self.sor,
                start_column=2,
                end_row=self.sor,
                end_column=3
            )

            # --- Igazítás minden cellára ---
            for col in [1, 2, 4, 6, 7, 8, 9]:
                self.ws.cell(row=self.sor, column=col).alignment = center_align

            self.sor += 1

    def kep_illeszto(self, kep_nev, cella, meret = None):
        kep_ut = os.path.join("data", kep_nev)
        kep = Image(kep_ut)

        if not meret is None:
            kep.width = meret[0]
            kep.height = meret[1]

        self.ws.add_image(kep, cella)

    def szemelyes_adatok(self):
        if self.vezetek_nev == "" and self.kereszt_nev == "":
            print("Nincs név megadva, a személyes adatok nem lettek beírva!")
            return
        jotform = adatgyujto.Jotform().jotform_to_dataframe()
        adat = jotform[(jotform["name.first"] == self.vezetek_nev) & (jotform["name.last"] == self.kereszt_nev)]

        if not adat.empty:
            email = adat["email"].dropna().iloc[0] if adat["email"].notna().any() else ""
            tel = adat["phonenumber"].dropna().iloc[0] if adat["phonenumber"].notna().any() else ""
            city = adat["address.city"].dropna().iloc[0] if adat["address.city"].notna().any() else ""
            addr1 = adat["address.addr_line1"].dropna().iloc[0] if adat["address.addr_line1"].notna().any() else ""
            addr2 = adat["address.addr_line2"].dropna().iloc[0] if adat["address.addr_line2"].notna().any() else ""

            cim = f"{city}, {addr1} {addr2}".strip(", ").strip() # csak akkor rakjon vesszőt, ha van város

            center_align = stilus.Alignment(horizontal="left", vertical="center",  wrap_text=True)

            self.ws["G9"] = self.vezetek_nev + " " + self.kereszt_nev
            self.ws["G9"].alignment = center_align

            self.ws["G10"] = tel
            self.ws["G10"].alignment = center_align

            self.ws["G11"] = email
            self.ws["G11"].alignment = center_align

            self.ws["G12"] = cim
            self.ws["G12"].alignment = center_align

    def anyagok_beirasa(self):
        anyagjegyzek, nyomtathato_szabjegy = szabjegy.SzabasjegyzekSzerkeszto(self.df).anyagigeny_szamitasa()

        self.tablazat_tolto(anyagjegyzek)

        ws_2 = self.wb.create_sheet(title="szabasjegyzek")

        for i, col in enumerate(nyomtathato_szabjegy.columns, start=1):
            ws_2.cell(row=1, column=i, value=col)  # oszlopnevek

        for r in nyomtathato_szabjegy.itertuples(index=False):
            ws_2.append(r)

    def utdij_beirasa(self):
            # ha F7 üres vagy None, akkor kilépünk
        if not self.ws["G12"].value:
            print("Nincs cím megadva, ezért nem történt utdíj kalkulálás.")
            return
        utdij = adatgyujto.Utdij_kalkulator(self.ws["G12"].value)
        fogyasztas = utdij.utdij_kalkulacio()

        sorok = [
            {
                "Anyag": "Benzin",
                "Szin": "",
                "URL": utdij.nav_url,
                "Mennyiseg": fogyasztas.get("literek", 0) * 2,
                "Mertekegyseg": "l",
                "Egysegar": fogyasztas.get("literar_huf", 0),
                "Osszar": fogyasztas.get("uzemanyag_koltseg_huf", 0) * 2,
            },
            {
                "Anyag": "Autóamortizáció",
                "Szin": "",
                "URL": "",
                "Mennyiseg": fogyasztas.get("tavolsag_km", 0) * 2,
                "Mertekegyseg": "km",
                "Egysegar": fogyasztas.get("amortizacio_per_km", 0),
                "Osszar": fogyasztas.get("auto_amortizacio_huf", 0) * 2,
            }
        ]

        anyagjegyzek_df = pd.DataFrame(sorok,
                                       columns=["Anyag", "Szin", "URL", "Mennyiseg", "Mertekegyseg", "Egysegar", "Osszar"])

        self.tablazat_tolto(anyagjegyzek_df)

    def elkeszites(self):
        #self.kep_illeszto("fejlec.png","A1", [200, 100])
        self.szemelyes_adatok()
        self.anyagok_beirasa()
        self.utdij_beirasa()

        faj.BeolvasKiirat().exel_kiiratasa(self.wb, r"C:\Users\csiki\OneDrive\csixwood program\proba")