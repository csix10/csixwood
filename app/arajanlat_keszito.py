import app.szabasjegyzek_szerkeszto as szabjegy
import app.adatgyujto as adatgyujto
import app.faj_beolvaso_kiirato as faj
import pandas as pd

class Arajanlat:
    def __init__(self, df, vezetek_nev = "", kereszt_nev = ""):
        self.df = df
        self.vezetek_nev = vezetek_nev
        self.kereszt_nev = kereszt_nev
        self.wb, self.ws = faj.BeolvasKiirat().szerkesztett_excel_beolvaso("minta_arajanlat.xlsx")
        self.sor = 12

    def tablazat_tolto(self, anyagjegyzek):
        anyagjegyzek = anyagjegyzek.astype({
            "Mennyiseg": float,
            "Egysegar": float,
            "Osszar": float
        })
        for _, row in anyagjegyzek.iterrows():
            self.ws.insert_rows(self.sor)
            self.ws.cell(row=self.sor, column=1, value=str(self.sor - 11) + ".")
            self.ws.cell(row=self.sor, column=2, value=row.get("Anyag", ""))
            self.ws.cell(row=self.sor, column=4, value=row.get("Szin", ""))
            self.ws.cell(row=self.sor, column=5, value=row.get("Mennyiseg", ""))
            self.ws.cell(row=self.sor, column=6, value=row.get("Mertekegyseg", ""))
            self.ws.cell(row=self.sor, column=7, value=row.get("Egysegar", ""))
            self.ws.cell(row=self.sor, column=8, value=row.get("Osszar", ""))
            self.sor += 1

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

            self.ws["F4"] = self.vezetek_nev + " " + self.kereszt_nev
            self.ws["F5"] = tel
            self.ws["F6"] = email
            self.ws["F7"] = cim

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
        if not self.ws["F7"].value:
            print("Nincs cím megadva, ezért nem történt utdíj kalkulálás.")
            return
        fogyasztas = adatgyujto.Utdij_kalkulator(self.ws["F7"].value).utdij_kalkulacio()

        sorok = [
            {
                "Anyag": "Benzin",
                "Szin": "",
                "Mennyiseg": fogyasztas.get("literek", 0) * 2,
                "Mertekegyseg": "l",
                "Egysegar": fogyasztas.get("literar_huf", 0),
                "Osszar": fogyasztas.get("uzemanyag_koltseg_huf", 0) * 2,
            },
            {
                "Anyag": "Autóamortizáció",
                "Szin": "",
                "Mennyiseg": fogyasztas.get("tavolsag_km", 0) * 2,
                "Mertekegyseg": "km",
                "Egysegar": fogyasztas.get("amortizacio_per_km", 0),
                "Osszar": fogyasztas.get("auto_amortizacio_huf", 0) * 2,
            }
        ]

        anyagjegyzek_df = pd.DataFrame(sorok,
                                       columns=["Anyag", "Szin", "Mennyiseg", "Mertekegyseg", "Egysegar", "Osszar"])

        self.tablazat_tolto(anyagjegyzek_df)

    def elkeszites(self):
        self.szemelyes_adatok()
        self.anyagok_beirasa()
        self.utdij_beirasa()

        faj.BeolvasKiirat().exel_kiiratasa(self.wb, r"C:\Users\balin\OneDrive\csixwood program\proba")