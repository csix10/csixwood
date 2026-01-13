import pandas as pd
import app.faj_beolvaso_kiirato as faj
import app.arukereso as arukereso

class SzabasjegyzekSzerkeszto:
    def __init__(self, df):
        self.df = df
        self.kereso = arukereso.Arukereso()

    def oszlop_atnevezes_torles(self):
        self.df.rename(columns={"Designation": "Nev"}, inplace=True)
        self.df.rename(columns={"Quantity": "DB"}, inplace=True)
        self.df.rename(columns={"Length": "Hosz"}, inplace=True)
        self.df.rename(columns={"Width": "Szel"}, inplace=True)
        self.df.rename(columns={"Thickness": "Vas"}, inplace=True)
        self.df.rename(columns={"Material": "Szin"}, inplace=True)
        self.df.rename(columns={"Description": "Elzaras"}, inplace=True)
        self.df.rename(columns={"Badges": "Anyag"}, inplace=True)
        self.df.drop(columns=["No.", "Length - raw", "Width - raw", "Thickness - raw", "Area - final", "Type",
                         "Material description", "URL of the material", "Instance names", "URL", "Edge Length 1",
                         "Edge Length 2", "Edge Width 1", "Edge Width 2", "Frontside", "Backside", "Tags"], inplace=True)

    def azonos_sorok_szurese(self, kulcsok=None, db_col="DB"):
        if kulcsok is None:
            kulcsok = ["Nev", "Hosz", "Szel", "Vas", "Anyag", "Szin", "Elzaras", "Anyag"]
        self.df.columns = self.df.columns.str.strip()
        self.df[db_col] = pd.to_numeric(self.df[db_col], errors="coerce").fillna(0)

        # DB sum, minden más oszlopbol az első erteket tartjuk meg
        agg_dict = {col: ("sum" if col == db_col else "first") for col in self.df.columns}
        self.df = self.df.groupby(kulcsok, as_index=False, dropna=False).agg(agg_dict)

    def sorszam_hozzaadasa(self):
        # Rendezés anyagfajta es szin szerint
        self.df.sort_values(by=["Anyag", "Szin"], inplace=True)

        # Sorszámozás anyagfajtánként
        self.df["Sz."] = self.df.groupby(["Anyag", "Szin"], dropna=False).cumcount() + 1

        cols = ["Sz."] + [c for c in self.df.columns if c != "Sz."]
        self.df = self.df[cols]

    def mm_eltavolitasa(self):
        for col in ["Hosz", "Szel", "Vas"]:
            self.df[col] = self.df[col].str.replace("mm", "", regex=False).str.strip().astype(int)

    def hosz_terulet_terfogat_szamitas(self):
        self.df["Osz_Hosz"] = self.df["DB"] * self.df["Hosz"] / 1000
        self.df["Terulet"] = self.df["DB"] * self.df["Hosz"] * self.df["Szel"] / 1000000
        self.df["Terfogat"] = self.df["DB"] * self.df["Hosz"] * self.df["Szel"] * self.df["Vas"] / 1000000000

    def elzaras_szamitas(self):
        # Győződjünk meg róla, hogy stringként kezeljük az Elzaras oszlopot
        self.df["Elzaras"] = self.df["Elzaras"].fillna("").astype(str)

        self.df["Vekonyelzaro"] = self.df.apply(lambda row: row["DB"] * row["Hosz"] * row["Elzaras"].count("a"),
                                      axis=1) + self.df.apply(
            lambda row: row["DB"] * row["Szel"] * row["Elzaras"].count("b"), axis=1)
        self.df["Vastagelzaro"] = self.df.apply(lambda row: row["DB"] * row["Hosz"] * row["Elzaras"].count("A"),
                                      axis=1) + self.df.apply(
            lambda row: row["DB"] * row["Szel"] * row["Elzaras"].count("B"), axis=1)

    def szabasjegyzek_szerkeszto(self):
        self.oszlop_atnevezes_torles()
        self.azonos_sorok_szurese()
        self.sorszam_hozzaadasa()
        self.mm_eltavolitasa()

        #faj.BeolvasKiirat().df_kiiratasa_exelbe(self.df, "szabasjegyzek.xlsx", r"C:\Users\csiki\OneDrive\csixwood program\proba")
        nyomtathato_szabjegy = self.df.copy()

        self.hosz_terulet_terfogat_szamitas()
        self.elzaras_szamitas()

        return self.df, nyomtathato_szabjegy

    def bongeszo(self, nev, hely):
        if hely == "Butorkellek":
            adatok = self.kereso.butorkellek(nev)
            if not adatok:
                return { "nev": "",
                "url": "",
                "ar": "0 ft"}
            else:
                return adatok
        elif hely == "Karnis":
            adatok = self.kereso.karnis(nev)
            if not adatok:
                return { "nev": "",
                "url": "",
                "ar": "0 ft"}
            else:
                return adatok
        else:
            return { "nev": "",
                "url": "",
                "ar": "0 ft"}


    def anyagigeny_szamitasa(self):
        # Beolvasás
        anyagtip = faj.BeolvasKiirat().csv_beolvasasa_databol("anyagtipusok.csv")

        self.df, nyomtathato_szabjegy = self.szabasjegyzek_szerkeszto()

        # Osszegzés anyag és szín szerint
        osszegzes = self.df.groupby(["Anyag", "Szin"], as_index=False, dropna=False)[
            ["DB", "Osz_Hosz", "Terulet", "Terfogat", "Vekonyelzaro", "Vastagelzaro"]
        ].sum()

        # Csak az adott anyaghoz tartozó elszámolási alapot hagyjuk meg
        eredmeny_list = []

        for _, row in osszegzes.iterrows():
            anyag = row["Anyag"]
            szin = row["Szin"]
            alap = anyagtip.loc[anyagtip["Anyag"] == anyag, "Szamitasialap"].squeeze()
            if len(alap) == 0:
                continue  # ha nincs meghatározva, kihagyjuk
            hulladek_arany = float(anyagtip.loc[anyagtip["Anyag"] == anyag, "Hulladekaranya"].iloc[0])
            kereses_helye = anyagtip.loc[anyagtip["Anyag"] == anyag, "Beszerzeshelyes"].values
            szep_anyagnev = anyagtip.loc[anyagtip["Anyag"] == anyag, "Anyag_szep"].squeeze()


            url_ar = self.bongeszo(szin, kereses_helye)
            print(url_ar["ar"])
            egysegar = int(url_ar["ar"][:-3].replace(".", ""))

            # Kiválasztjuk az adott alaphoz tartozó oszlopot
            ertek = row.get(alap, 0)

            mertekegyseg_dict = {
                "Osz_Hosz": "m",
                "Terulet": "m²",
                "Terfogat": "m³",
                "DB": "db",
                "Vekonyelzaro": "m",
                "Vastagelzaro": "m"
            }

            mertekegyseg = mertekegyseg_dict.get(alap, "")
            # Hozzáadjuk az eredmény listához, opcionálisan mértékegységgel
            eredmeny_list.append({
                "Anyag": szep_anyagnev,
                "Szin": szin,
                "URL": url_ar["url"],
                "Mennyiseg": ertek * hulladek_arany,
                "Mertekegyseg": mertekegyseg,
                "Egysegar": egysegar,
                "Osszar": ertek * hulladek_arany * egysegar,
            })

            #Vekonyelzaro
            if row.get("Vekonyelzaro", 0) > 0:
                meterar_vekony = 393 #Ezt kesobb modosítani kell!
                menyiseg_vekony = row["Vekonyelzaro"]/1000
                eredmeny_list.append({
                    "Anyag": "Vékony élzáró",
                    "Szin": szin,
                    "URL": "",
                    "Mennyiseg": menyiseg_vekony,
                    "Mertekegyseg": "m",
                    "Egysegar": meterar_vekony,
                    "Osszar": meterar_vekony * menyiseg_vekony
                })

            # Vastagelzáró
            if row.get("Vastagelzaro", 0) > 0:
                meterar_vastag = 727  # Ezt kesobb modosítani kell!
                menyiseg_vastag = row["Vastagelzaro"]/1000
                eredmeny_list.append({
                    "Anyag": "Vastag élzaró",
                    "Szin": szin,
                    "URL": "",
                    "Mennyiseg": menyiseg_vastag,
                    "Mertekegyseg": "m",
                    "Egysegar": meterar_vastag, #Ezt kesobb modosítani kell!
                    "Osszar": meterar_vastag * menyiseg_vastag
                })

        # Új DataFrame az anyagonkénti elszámolásra
        df_eredmeny = pd.DataFrame(eredmeny_list)

        return df_eredmeny, nyomtathato_szabjegy


