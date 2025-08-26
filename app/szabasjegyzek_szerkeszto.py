import pandas as pd

class SzabasjegyzekSzerkeszto:
    def __init__(self, df):
        self.df = df

    def oszlop_atnevezes_torles(df):
        df.rename(columns={"Designation": "Nev"}, inplace=True)
        df.rename(columns={"Quantity": "DB"}, inplace=True)
        df.rename(columns={"Length": "Hosz"}, inplace=True)
        df.rename(columns={"Width": "Szel"}, inplace=True)
        df.rename(columns={"Thickness": "Vas"}, inplace=True)
        df.rename(columns={"Material": "Szin"}, inplace=True)
        df.rename(columns={"Description": "Elzaras"}, inplace=True)
        df.rename(columns={"Badges": "Anyag"}, inplace=True)
        df.drop(columns=["No.", "Length - raw", "Width - raw", "Thickness - raw", "Area - final", "Type",
                         "Material description", "URL of the material", "Instance names", "URL", "Edge Length 1",
                         "Edge Length 2", "Edge Width 1", "Edge Width 2", "Frontside", "Backside", "Tags"],
                inplace=True)
        return df
