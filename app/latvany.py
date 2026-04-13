from pathlib import Path
from PIL import Image
import faj_beolvaso_kiirato as faj

class Latvanyterv:
    def __init__(self):
        self.faj = faj.BeolvasKiirat()
        self.kepekhelye = [Path(p) for p in self.faj.kep_tallozo()]

    def logo_bal_also_sarok(
        self,
        alap_kep: Image.Image,
        logo_szazalek: float = 0.2,
        also_margin: int = 20,
        bal_margin: int = 0,
    ) -> Image.Image:
        """
        Ráteszi a logót a kép bal alsó sarkára.

        logo_szazalek: a logó szélessége az alap kép szélességének hányada (pl 0.2 = 20%)
        also_margin, bal_margin: belső margó pixelben
        """
        logo_ut = Path(__file__).resolve().parent.parent / "data" / "fejlec.png"
        logo = Image.open(logo_ut).convert("RGBA")

        # alap kép RGBA (hogy az alpha mask biztosan működjön)
        alap_kep = alap_kep.convert("RGBA")

        # ---- Logó átméretezése aránytartóan ----
        uj_logo_szelesseg = max(1, int(alap_kep.width * logo_szazalek))
        arany = uj_logo_szelesseg / logo.width
        uj_logo_magassag = max(1, int(logo.height * arany))

        logo = logo.resize((uj_logo_szelesseg, uj_logo_magassag), Image.LANCZOS)

        # ---- Pozíció számítása (bal alsó) ----
        x = bal_margin
        y = alap_kep.height - uj_logo_magassag - also_margin
        if y < 0:
            y = 0  # ha túl nagy a logo/margin

        # ---- Logó ráillesztése ----
        alap_kep.paste(logo, (x, y), logo)

        # a logót bezárjuk, az alapképet NEM (mert visszaadjuk)
        logo.close()

        return alap_kep

    def kepekbol_pdf(self) -> Path:
        """
        Képekből PDF-et készít úgy, hogy minden kép egy külön oldal legyen.
        """

        if not self.kepekhelye:
            raise ValueError("A kep_utak lista üres.")

        kepek = []
        try:
            for p in self.kepekhelye:
                p = Path(p)
                if not p.exists():
                    raise FileNotFoundError(f"Nem találom: {p}")

                with Image.open(p) as img:
                    img2 = self.logo_bal_also_sarok(img).convert("RGB")
                    kepek.append(img2)

            # kimeneti út az első kép alapján (pont ahogy kéred)
            vegleges_ut = self.faj.png_utbol_latvany_ut(self.kepekhelye[0])
            if not vegleges_ut:
                raise RuntimeError("A mentési útvonal nem lett kiválasztva (Cancel).")

            kimeneti_pdf = Path(vegleges_ut)
            kimeneti_pdf.parent.mkdir(parents=True, exist_ok=True)

            elso, tobbi = kepek[0], kepek[1:]

            elso.save(
                kimeneti_pdf,
                "PDF",
                save_all=True,
                append_images=tobbi
            )

            return kimeneti_pdf

        finally:
            # Zárás (Windows-on fontos)
            for im in kepek:
                try:
                    im.close()
                except Exception:
                    pass


# --- példa használat ---
if __name__ == "__main__":
    latvany = Latvanyterv()
    pdf = latvany.kepekbol_pdf()
    print("Kész:", pdf)