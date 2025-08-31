import app.szabasjegyzek_szerkeszto as szabszerk
import app.faj_beolvaso_kiirato as faj
import app.arajanlat_keszito as araj

def szabasjegyzek():
    df = faj.BeolvasKiirat().csv_beolvasasa_databol("szabasjegyzek.csv")
    #df = faj.BeolvasKiirat().csv_beolvas_df()
    mod_df=szabszerk.SzabasjegyzekSzerkeszto(df).szabasjegyzek_szerkeszto()
    faj.BeolvasKiirat().df_kiiratasa_exelbe(mod_df,"szabasjegyzek.xlsx", r"C:\Users\csiki\OneDrive\csixwood program\proba")

def arajanlat():
    wb, ws = faj.BeolvasKiirat().szerkesztett_excel_beolvaso("minta_arajanlat.xlsx")
    araj.Arajanlat(wb, "Horváth", "Zsombor").szemelyes_adatok()
    faj.BeolvasKiirat().exel_kiiratasa(wb, r"C:\Users\csiki\OneDrive\csixwood program\proba")

if __name__ == "__main__":
    arajanlat()

