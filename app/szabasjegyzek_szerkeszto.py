import pandas as pd
import app.faj_beolvaso_kiirato as faj

class SzabasjegyzekSzerkeszto:
    def __init__(self, df):
        self.df = df

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
                         "Edge Length 2", "Edge Width 1", "Edge Width 2", "Frontside", "Backside", "Tags"],
                inplace=True)

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

        return self.df

    def anyagigeny_szamitasa(self):
        # Beolvasás
        anyagtip = faj.BeolvasKiirat().csv_beolvasasa_databol("anyagtipusok.csv")

        # Feldolgozott szabásjegyzék
        self.df = self.szabasjegyzek_szerkeszto()
        self.hosz_terulet_terfogat_szamitas()
        self.elzaras_szamitas()

        # Osszegzés anyag és szín szerint
        osszegzes = self.df.groupby(["Anyag", "Szin"], as_index=False, dropna=False)[
            ["Osz_Hosz", "Terulet", "Terfogat", "Vekonyelzaro", "Vastagelzaro"]
        ].sum()
        print(osszegzes)

        # Csak az adott anyaghoz tartozó elszámolási alapot hagyjuk meg
        eredmeny_list = []

        for _, row in osszegzes.iterrows():
            anyag = row["Anyag"]
            szin = row["Szin"]
            alap = anyagtip.loc[anyagtip["Anyag"] == anyag, "Szamitasialap"].values
            if len(alap) == 0:
                continue  # ha nincs meghatározva, kihagyjuk
            alap = alap[0]  # pl. "Terulet" vagy "Terfogat"

            # Kiválasztjuk az adott alaphoz tartozó oszlopot
            ertek = row.get(alap, 0)

            mertekegyseg_dict = {
                "Hosz": "m",
                "Terulet": "m²",
                "Terfogat": "m³",
                "Vekonyelzaro": "m",
                "Vastagelzaro": "m"
            }
            mertekegyseg = mertekegyseg_dict.get(alap, "")
            # Hozzáadjuk az eredmény listához, opcionálisan mértékegységgel
            eredmeny_list.append({
                "Anyag": anyag,
                "Szin": szin,
                "Menyiseg": ertek,
                "Mértékegység": mertekegyseg
            })

        # Új DataFrame az anyagonkénti elszámolásra
        df_eredmeny = pd.DataFrame(eredmeny_list)
        print(df_eredmeny)

        return df_eredmeny


