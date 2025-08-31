import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
from openpyxl import load_workbook

class BeolvasKiirat:
    def __init__(self):
        pass

    def csv_beolvasasa_databol(self, nev):
        input_file = "data/" + nev
        df = pd.read_csv(input_file, encoding="utf-8", sep=";")
        return df

    def csv_beolvas_df(self):
        root = tk.Tk()
        root.withdraw()  # főablak elrejtése
        file_path = filedialog.askopenfilename(
            title="Válassz CSV fájlt",
            filetypes=[("CSV fájlok", "*.csv"), ("Minden fájl", "*.*")]
        )
        if not file_path:
            print("Nem választottál fájlt.")
            return None

        df = pd.read_csv(file_path, sep=";")
        print(f"Beolvasva: {file_path} ({len(df)} sor)")
        return df

    def szerkesztett_excel_beolvaso(self, fajlnev, data_mappa="data"):
        """
        Beolvassa a sablon Excel fájlt a data mappából, megtartva a formázást.
        - fajlnev: a fájl neve pl. "arajanlat.xlsx"
        - data_mappa: a mappa ahol a fájl van (alapértelmezett: 'data')
        """
        # Teljes útvonal összeállítása
        fajl_ut = os.path.join(data_mappa, fajlnev)

        if not os.path.exists(fajl_ut):
            print(f"Hiba: a fájl nem található: {fajl_ut}")
            return None, None

        print(f"Beolvasás: {fajl_ut}")

        # openpyxl-lel beolvassuk a sablont úgy, hogy a stílusok megmaradjanak
        wb = load_workbook(fajl_ut, data_only=False)  # data_only=False -> stílusok megmaradnak

        # első lap kiválasztása
        ws = wb[wb.sheetnames[0]]  # vagy konkrét név: wb['Árajánlat']

        return wb, ws

    def df_kiiratasa_exelbe(self, df, nev, mappa):
        # Ha a mappa nem létezik, létrehozzuk
        os.makedirs(mappa, exist_ok=True)
        # Teljes fájlútvonal összeállítása
        fajl_ut = os.path.join(mappa, nev)
        # Mentés Excelbe
        df.to_excel(fajl_ut, index=False)

        print(f"✅ Fájl sikeresen mentve ide: {fajl_ut}")

    def exel_kiiratasa(self, wb, mappa, nev="arajanlat.xlsx"):
        """
        Excel fájl mentése a megadott mappába.
        - wb: Workbook objektum
        - mappa: célmappa
        - nev: fájlnév (alapértelmezett: "arajanlat.xlsx")
        """
        os.makedirs(mappa, exist_ok=True)
        fajl_ut = os.path.join(mappa, nev)
        wb.save(fajl_ut)
        print(f"✅ Fájl sikeresen mentve ide: {fajl_ut}")


