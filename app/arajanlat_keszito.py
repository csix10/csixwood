import app.szabasjegyzek_szerkeszto as szabjegy
import app.adatgyujto as adatgyujto
import app.faj_beolvaso_kiirato as faj

class Arajanlat:
    def __init__(self, df, vezetek_nev, kereszt_nev):
        self.df = df
        self.vezetek_nev = vezetek_nev
        self.kereszt_nev = kereszt_nev
        self.wb, self.ws = faj.BeolvasKiirat().szerkesztett_excel_beolvaso("minta_arajanlat.xlsx")

    def szemelyes_adatok(self):
        jotform = adatgyujto.AdatokGyujtese().jotform_to_dataframe()
        adat = jotform[(jotform["name.first"] == self.vezetek_nev) & (jotform["name.last"] == self.kereszt_nev)]

        if not adat.empty:
            email = adat["email"].dropna().iloc[0] if adat["email"].notna().any() else ""
            tel = adat["phonenumber"].dropna().iloc[0] if adat["phonenumber"].notna().any() else ""
            cim = adat["address.city"].dropna().iloc[0] + ", " + adat["address.addr_line1"].dropna().iloc[0] + " " + \
                  adat["address.addr_line2"].dropna().iloc[0] if adat["email"].notna().any() else ""

            self.ws["F4"] = self.vezetek_nev + " " + self.kereszt_nev
            self.ws["F5"] = tel
            self.ws["F6"] = email
            self.ws["F7"] = cim

    def anyagok_beirasa(self):
        anyagjegyzek, nyomtathato_szabjegy = szabjegy.SzabasjegyzekSzerkeszto(self.df).anyagigeny_szamitasa()
        sor = 12
        for _, row in anyagjegyzek.iterrows():
            self.ws.insert_rows(sor)
            self.ws.cell(row=sor, column=1, value=sor - 11)
            self.ws.cell(row=sor, column=2, value=row.get("Anyag", ""))
            self.ws.cell(row=sor, column=4, value=row.get("Szin", ""))
            self.ws.cell(row=sor, column=5, value=row.get("Menyiseg", ""))
            self.ws.cell(row=sor, column=6, value=row.get("Mértékegység", ""))
            self.ws.cell(row=sor, column=7, value=0)
            self.ws.cell(row=sor, column=8, value=0)
            sor += 1

        ws_2 = self.wb.create_sheet(title="szabasjegyzek")

        for i, col in enumerate(nyomtathato_szabjegy.columns, start=1):
            ws_2.cell(row=1, column=i, value=col)  # oszlopnevek

        for r in nyomtathato_szabjegy.itertuples(index=False):
            ws_2.append(r)

    def elkeszites(self):
        self.szemelyes_adatok()
        self.anyagok_beirasa()

        faj.BeolvasKiirat().exel_kiiratasa(self.wb, r"C:\Users\balin\OneDrive\csixwood program\proba")