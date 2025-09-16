import app.szabasjegyzek_szerkeszto as szabszerk
import app.faj_beolvaso_kiirato as faj
import app.arajanlat_keszito as araj

def szabasjegyzek():
    df = faj.BeolvasKiirat().csv_beolvasasa_databol("galeria.csv")
    #df = faj.BeolvasKiirat().csv_beolvas_df()

    araj.Arajanlat(df, "Gárdián", "Lajos").elkeszites()

if __name__ == "__main__":
    szabasjegyzek()

