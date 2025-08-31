import app.adatgyujto as adatgyujto

class Arajanlat:
    def __init__(self, wb, vezetek_nev, kereszt_nev):
        self.wb = wb
        self.ws = wb['arajanlat']
        self.vezetek_nev = vezetek_nev
        self.kereszt_nev = kereszt_nev

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

