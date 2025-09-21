import app.szabasjegyzek_szerkeszto as szabszerk
import app.faj_beolvaso_kiirato as faj
import app.arajanlat_keszito as araj
import app.adatgyujto as adat

def szabasjegyzek():
    #df = faj.BeolvasKiirat().csv_beolvasasa_databol("galeria.csv")
    df = faj.BeolvasKiirat().csv_beolvas_df()

    araj.Arajanlat(df, "Gárdián", "Lajos").elkeszites()

def proba_utdij():
    hup = adat.Utdij_kalkulator("Balatonfenyves, Vörösmarty utca 135.").utdij_kalkulacio()
    print(hup)

if __name__ == "__main__":
    proba_utdij()

