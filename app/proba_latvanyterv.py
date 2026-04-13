import faj_beolvaso_kiirato as faj
from pathlib import Path
import requests
import io
from PIL import Image

class AIKepJavito:
    def __init__(self, api_kulcs: str):
        self.api_kulcs = api_kulcs

    def kep_b64_bytes(self, kep: Image.Image) -> bytes:
        buffer = io.BytesIO()
        kep.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()

    def fotorealisztikus(self, kep: Image.Image) -> Image.Image:
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={
                "authorization": f"Bearer {self.api_kulcs}",
                "accept": "image/*"
            },
            files={
                "image": ("image.png", self.kep_b64_bytes(kep), "image/png"),
            },
            data={
                "prompt": (
                    "same furniture, same layout, same colors, same structure, "
                    "slightly improved lighting, subtle ambient occlusion, "
                    "minor texture enhancement, keep everything identical"
                ),
                "negative_prompt": (
                    "different furniture, different layout, different colors, "
                    "new objects, changed structure, photorealistic, painting style"
                ),
                "control_strength": 1.0,  # ← maximális struktúra megőrzés
                "output_format": "png",
            },
        )

        if response.status_code != 200:
            raise RuntimeError(f"Stability AI hiba {response.status_code}: {response.text}")

        return Image.open(io.BytesIO(response.content))


class Latvanyterv:
    def __init__(self):
        self.faj = faj.BeolvasKiirat()
        self.kepekhelye = [Path(p) for p in self.faj.kep_tallozo()]
        self.ai_javito = AIKepJavito("sk-EDj3NnNjq8kXRDHpxMMGskfUXNtSz2zRTam55Gj93yyKPsWf")

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
        kepek = []
        try:
            for p in self.kepekhelye:
                p = Path(p)
                with Image.open(p) as img:
                    if self.ai_javito:
                        print(f"AI javítás: {p.name}...")
                        try:
                            img = self.ai_javito.fotorealisztikus(img)
                        except RuntimeError as e:
                            print(f"  ⚠ AI hiba, eredeti kép marad: {e}")

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