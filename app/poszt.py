from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps
from pathlib import Path


class PosztKeszito:

    def __init__(self, kerekitesi_sugar=40):
        self.kerekitesi_sugar = kerekitesi_sugar

    # -------------------------------------------------
    # Sarok lekerekítés
    # -------------------------------------------------

    def sarkok_lekerekitese(self, kep):

        maszk = Image.new("L", kep.size, 0)
        rajz = ImageDraw.Draw(maszk)

        rajz.rounded_rectangle(
            (0, 0) + kep.size,
            radius=self.kerekitesi_sugar,
            fill=255
        )

        uj_kep = Image.new("RGBA", kep.size)
        uj_kep.paste(kep, (0, 0), maszk)

        return uj_kep

    # -------------------------------------------------
    # Panel készítés (lekerekített háttér objektum)
    # -------------------------------------------------

    def panel_keszites(self, szelesseg, magassag, sugar, szin,
                       szegely=None, szegely_szelesseg=2,
                       arnyek=True):

        # panel
        panel = Image.new("RGBA", (szelesseg, magassag), (0, 0, 0, 0))
        rajz = ImageDraw.Draw(panel)

        rajz.rounded_rectangle(
            (0, 0, szelesseg, magassag),
            radius=sugar,
            fill=szin
        )

        if szegely:
            rajz.rounded_rectangle(
                (0, 0, szelesseg, magassag),
                radius=sugar,
                outline=szegely,
                width=szegely_szelesseg
            )

        if not arnyek:
            return panel

        # árnyék készítése
        shadow = Image.new("RGBA", (szelesseg, magassag), (0, 0, 0, 0))
        rajz = ImageDraw.Draw(shadow)

        rajz.rounded_rectangle(
            (0, 0, szelesseg, magassag),
            radius=sugar,
            fill=(0, 0, 0, 180)
        )

        shadow = shadow.filter(ImageFilter.GaussianBlur(10))

        # végső kép
        final = Image.new(
            "RGBA",
            (szelesseg + 20, magassag + 20),
            (0, 0, 0, 0)
        )

        final.paste(shadow, (10, 10), shadow)
        final.paste(panel, (0, 0), panel)

        return final
    # -------------------------------------------------
    # Poszt alap elkészítése (NEM módosított)
    # -------------------------------------------------

    def poszt_alap_keszitese(self, bemeneti_kep, kimeneti_kep):

        bemeneti_kep = Path(__file__).resolve().parent.parent / "data" / "probakep.jpg"
        kep = Image.open(bemeneti_kep)
        kep = ImageOps.exif_transpose(kep)
        kep = kep.convert("RGB")

        vegso_szelesseg = 1080
        vegso_magassag = 1350

        hatter_ut = Path(__file__).resolve().parent.parent / "data" / "hatter.jpg"
        hatter = Image.open(hatter_ut)
        hatter = ImageOps.exif_transpose(hatter)
        hatter = hatter.convert("RGB")
        hatter = hatter.resize((vegso_szelesseg, vegso_magassag))
        hatter = hatter.filter(ImageFilter.GaussianBlur(5))

        fo_kep_szelesseg = 900
        arany = fo_kep_szelesseg / kep.width
        fo_kep_magassag = int(kep.height * arany)

        fo_kep = kep.resize((fo_kep_szelesseg, fo_kep_magassag))

        fo_kep = self.sarkok_lekerekitese(fo_kep)

        x = (vegso_szelesseg - fo_kep_szelesseg) // 2
        y = (vegso_magassag - fo_kep_magassag) // 2

        hatter = hatter.convert("RGBA")

        hatter.paste(fo_kep, (x, y), fo_kep)

        hatter.save(kimeneti_kep)

        return hatter

    # -------------------------------------------------
    # Logó hozzáadása (panel háttérrel)
    # -------------------------------------------------

    def logo_hozzaadasa(self, kep, logo_utvonal):

        logo_ut = Path(__file__).resolve().parent.parent / "data" / "fejlec.png"
        logo = Image.open(logo_ut).convert("RGBA")

        logo = logo.resize((90, 90))

        panel = self.panel_keszites(
            260,
            120,
            30,
            (120, 70, 30, 220)
        )

        panel.paste(logo, (20, 15), logo)

        rajz = ImageDraw.Draw(panel)
        font = ImageFont.truetype("arial.ttf", 40)

        rajz.text((120, 40), "CsixWood", fill="white", font=font)

        kep.paste(panel, (40, 40), panel)

        return kep

    # -------------------------------------------------
    # Szövegdoboz hozzáadása (panellel)
    # -------------------------------------------------

    def szoveg_hozzaadasa(self, kep, nev, telefonszam):

        w = 520
        h = 160

        panel = self.panel_keszites(
            w,
            h,
            20,
            (0, 0, 0, 220),
            szegely=(255, 255, 255)
        )

        rajz = ImageDraw.Draw(panel)

        nagy_betu = ImageFont.truetype("arial.ttf", 46)
        kis_betu = ImageFont.truetype("arial.ttf", 34)

        rajz.text((30, 20), nev, fill="white", font=nagy_betu)

        rajz.line((30, 80, w - 30, 80), fill="white", width=2)

        rajz.text((30, 95), telefonszam, fill="white", font=kis_betu)

        x = kep.width - w - 40
        y = kep.height - h - 40

        kep.paste(panel, (x, y), panel)

        return kep
    # -------------------------------------------------
    # Teljes poszt generálása
    # -------------------------------------------------

    def futtat(self, bemeneti_kep, kimeneti_kep, nev, telefonszam):

        # alap kép elkészítése
        kep = self.poszt_alap_keszitese(bemeneti_kep, kimeneti_kep)

        # logó hozzáadása
        kep = self.logo_hozzaadasa(kep, None)

        # szöveg hozzáadása
        kep = self.szoveg_hozzaadasa(kep, nev, telefonszam)

        # végső mentés
        kep.save(kimeneti_kep)

        return kep

PosztKeszito().futtat("probakep.jpg", "kesz_poszt.png", "én", "5346")