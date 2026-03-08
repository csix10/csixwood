import pandas as pd
import app.faj_beolvaso_kiirato as faj
import app.arukereso as arukereso

class SzabasjegyzekSzerkeszto:
    def __init__(self, df):
        self.df = df
        self.kereso = arukereso.Arukereso()
        self.boltok =[]
        self.anyagigeny = pd.DataFrame()
        self.nyomtathato_szabjegy = pd.DataFrame()
        self.anyagtip = faj.BeolvasKiirat().csv_beolvasasa_databol("anyagtipusok.csv")
        self.mertekegyseg_dict = {
                "Osz_Hosz": "m",
                "Terulet": "m²",
                "Teljes_Felulet": "m²",
                "Terfogat": "m³",
                "DB": "db",
                "Vekonyelzaro": "m",
                "Vastagelzaro": "m",
                "Ora": "óra"
            }

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
            kulcsok = ["Nev", "Hosz", "Szel", "Vas", "Anyag", "Szin", "Elzaras"]
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

    '''def atforfato(self):
        valogatot = pd.DataFrame()
        lehetseges_melyseg = []
        for sor in self.df:
            if sor["Hosz"]>600:
                valogatot.append(sor)
                if sor["DB"]>=2:
                    lehetseges_melyseg.append(sor["Szel"])
        melyseg = []
        for m in lehetseges_melyseg:
            i=0
            for n in lehetseges_melyseg:
                if m<n and m<=m+34:
                    i=1
            if i==0:
                melyseg.append(m)
        modostott_df = pd.DataFrame()
        for sor in self.df:
            if sor in valogatot:
                modostott_df.append(sor)
            else:
                for m in melyseg:
                    if m-34<=sor["Hosz"] and sor["Hosz"]<= m:
                        i=0
                        for n in melyseg:
                            if n - 34 <= sor["Szel"] and sor["Szel"] <= n:
                                modostott_df.append(sor)
                                i=1
                                break
                        if i==0:
                            hosz=sor["Hosz"]
                            sor["Hosz"]=sor["Szel"]
                            sor["Szel"]=hosz
                            modostott_df.append(sor)

        self.df = modostott_df'''

    def atforgato(self, df):
        """
        A self.df alapján kiválasztja azokat a sorokat, amelyek:
        - vagy eleve megfelelnek a feltételnek,
        - vagy átforgatva (Hossz <-> Szél) lesznek megfelelőek.
        """

        # 1) Kiválogatott sorok: Hosz > 600
        valogatott_mask = df["Hosz"] > 600
        valogatott_df = df[valogatott_mask].copy()

        # 2) Lehetséges mélységek: a kiválogatott sorok közül, ahol DB >= 2
        lehetseges_melyseg = (
            df.loc[valogatott_mask & (df["DB"] >= 2), "Szel"]
            .dropna()
            .astype(float)
            .tolist()
        )

        # 3) Mélységek szűrése:
        #    csak azokat tartjuk meg, amelyekhez nincs nagyobb érték 34-en belül
        #    tehát egy közeli csoportból a legnagyobb marad meg
        lehetseges_melyseg = sorted(set(lehetseges_melyseg))
        melysegek = []

        for m in lehetseges_melyseg:
            van_nagyobb_kozelben = any(m < n <= m + 34 for n in lehetseges_melyseg)
            if not van_nagyobb_kozelben:
                melysegek.append(m)
        print(melysegek)

        def illeszkedik_melyseghez(ertek: float) -> bool:
            """Igaz, ha az érték beleesik valamelyik [m-34, m] intervallumba."""
            return any(m - 34 <= ertek <= m for m in melysegek)

        # 4) Új DataFrame sorainak összeállítása
        uj_sorok = []

        for idx, sor in df.iterrows():
            sor_dict = sor.to_dict()

            # Ha eleve a kiválogatottak között van, változtatás nélkül marad
            if valogatott_mask.loc[idx]:
                uj_sorok.append(sor_dict)
                continue

            hosz = float(sor["Hosz"])
            szel = float(sor["Szel"])

            # Csak akkor foglalkozunk vele, ha a hossz beleesik valamely mélység-intervallumba
            if illeszkedik_melyseghez(hosz):
                # Ha a szélesség is beleesik valamely mélység-intervallumba, marad
                if illeszkedik_melyseghez(szel):
                    uj_sorok.append(sor_dict)
                else:
                    # különben átforgatjuk
                    sor_dict["Hosz"], sor_dict["Szel"] = szel, hosz
                    uj_sorok.append(sor_dict)
            else:
                uj_sorok.append(sor_dict)

        return pd.DataFrame(uj_sorok, columns=df.columns)

    def atforgato_anyag_szin_szerint(self):
        """
        Az atforgató algoritmust külön futtatja
        minden (Anyag, Szin) csoportra.
        """

        df = self.df.copy()
        eredmeny = []

        for (anyag, szin), csoport in df.groupby(["Anyag", "Szin"], dropna=False):
            talalat = self.anyagtip.loc[
                self.anyagtip["Anyag"] == anyag, "Szamitasialap"
            ]

            if talalat.empty:
                uj_df = csoport
            else:
                alap = talalat.iloc[0]
                if alap == "Terulet":
                    uj_df = self.atforgato(csoport.copy())
                else:
                    uj_df = csoport

            eredmeny.append(uj_df)

        self.df = pd.concat(eredmeny, ignore_index=True)

    def hosz_terulet_terfogat_szamitas(self):
        self.df["Osz_Hosz"] = self.df["DB"] * self.df["Hosz"] / 1000
        self.df["Terulet"] = self.df["DB"] * self.df["Hosz"] * self.df["Szel"] / 1000000
        self.df["Teljes_Felulet"] = 2 * self.df["DB"] * (self.df["Hosz"] * self.df["Szel"] + self.df["Hosz"] * self.df["Vas"] + self.df["Szel"] * self.df["Vas"]) / 1000000
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

        self.atforgato_anyag_szin_szerint()

        nyomtathato_szabjegy = self.df.copy()

        self.hosz_terulet_terfogat_szamitas()
        self.elzaras_szamitas()

        return self.df, nyomtathato_szabjegy

    def bongeszo(self, nev, hely):
        if hely == "Butorkellek":
            if "Butorkellek" not in self.boltok:
                self.boltok.append("Butorkellek")

            adatok = self.kereso.butorkellek(nev)
            if not adatok:
                return { "nev": "",
                "url": "",
                "ar": "0 ft"}
            else:
                return adatok
        elif hely == "Karnis":
            if "Karnis" not in self.boltok:
                self.boltok.append("Karnis")

            adatok = self.kereso.karnis(nev)
            if not adatok:
                return { "nev": "",
                "url": "",
                "ar": "0 ft"}
            else:
                return adatok
        elif hely == "Borovi":
            if "Borovi" not in self.boltok:
                self.boltok.append("Borovi")
            return {"nev": "",
                    "url": "",
                    "ar": "0 ft"}

        else:
            return { "nev": "",
                "url": "",
                "ar": "0 ft"}


    def anyagigeny_szamitasa(self):
        # Osszegzés anyag és szín szerint
        self.df, self.nyomtathato_szabjegy = self.szabasjegyzek_szerkeszto()
        osszegzes = self.df.groupby(["Anyag", "Szin"], as_index=False, dropna=False)[
            ["DB", "Osz_Hosz", "Terulet", "Teljes_Felulet", "Terfogat", "Vekonyelzaro", "Vastagelzaro"]
        ].sum()

        self.anyagigeny = osszegzes

    def anyagjegyzek_szamitasa(self):
        if self.anyagigeny.empty:
            self.anyagigeny_szamitasa()

        # Csak az adott anyaghoz tartozó elszámolási alapot hagyjuk meg
        eredmeny_list = []

        for _, row in self.anyagigeny.iterrows():
            anyag = row["Anyag"]
            szin = row["Szin"]
            alap = self.anyagtip.loc[self.anyagtip["Anyag"] == anyag, "Szamitasialap"].squeeze()
            if len(alap) == 0:
                continue  # ha nincs meghatározva, kihagyjuk
            hulladek_arany = float(self.anyagtip.loc[self.anyagtip["Anyag"] == anyag, "Hulladekaranya"].iloc[0])
            kereses_helye = self.anyagtip.loc[self.anyagtip["Anyag"] == anyag, "Beszerzeshelyes"].values
            szep_anyagnev = self.anyagtip.loc[self.anyagtip["Anyag"] == anyag, "Anyag_szep"].squeeze()


            url_ar = self.bongeszo(szin, kereses_helye)
            print(url_ar["ar"])
            egysegar = int(url_ar["ar"][:-3].replace(".", ""))

            # Kiválasztjuk az adott alaphoz tartozó oszlopot
            ertek = row.get(alap, 0)

            mertekegyseg = self.mertekegyseg_dict.get(alap, "")
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

        return df_eredmeny, self.nyomtathato_szabjegy