import requests
import re
import pdfplumber
import os
import unicodedata
import difflib

import time
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def _first_text(el, selectors: list[str]) -> str:
    """Első olyan selector textje, ami létezik és nem üres."""
    for sel in selectors:
        try:
            found = el.find_elements(By.CSS_SELECTOR, sel)
            if found:
                txt = found[0].text.strip()
                if txt:
                    return txt
        except Exception:
            pass
    return ""


def _first_attr(el, selector: str, attr: str) -> str:
    try:
        found = el.find_elements(By.CSS_SELECTOR, selector)
        if found:
            val = found[0].get_attribute(attr)
            return val.strip() if val else ""
    except Exception:
        pass
    return ""


def _parse_price_text(price_text: str) -> str:
    """
    Itt csak normalizáljuk a szöveget (üres -> '0 Ft').
    Ha később számként akarod: itt tudod kivágni a pontokat/szóközöket és int-té alakítani.
    """
    if not price_text:
        return "0 Ft"
    return price_text

class Arukereso:
    def __init__(self, options: webdriver.ChromeOptions | None = None, timeout: int = 12):
        self.options = options or webdriver.ChromeOptions()
        self.options.add_argument("--headless")  # háttérben fusson, ne nyisson ablakot
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.timeout = timeout

    def butorkellek(self, termek_neve: str, max_results: int = 1) -> dict | None:
        """
        Visszaadja a találatokból az elsőt (vagy max_results-ig listát könnyen bővíthető).
        Ha nincs találat, None.
        """
        if not termek_neve or not termek_neve.strip():
            print("⚠️ Üres terméknév.")
            return None

        # URL-encode: ékezetek/szóközök rendesen menjenek a query-be
        q = quote_plus(termek_neve.strip())

        butorkellek_url = (
            "https://butorkellek.eu/kereses?"
            "description=0"
            "&utm_source=iai_ads&utm_medium=google_shopping"
            "&gad_source=1&gad_campaignid=22402103487"
            "&gclid=Cj0KCQjww4TGBhCKARIsAFLXndQ-h0gI5LLAt5S8GS5YgmguS7Fq36fURGc7etdspSxbUuXa3B6zSGsaAg3SEALw_wcB"
            f"&keyword={q}"
        )

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

        try:
            driver.get(butorkellek_url)

            wait = WebDriverWait(driver, self.timeout)

            # Várjuk, hogy vagy találatok legyenek, vagy valami "nincs találat" jellegű elem.
            # Ha az oldal lassú, ez sokkal stabilabb mint sleep.
            try:
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card-body")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".alert, .no-results, .search-empty"))
                    )
                )
            except TimeoutException:
                # Sem találat, sem "no results" jellegű elem – akkor is kezeljük
                pass

            items = driver.find_elements(By.CSS_SELECTOR, ".product-card-body")

            if not items:
                print(f"❌ Nem találtam meg a(z) '{termek_neve}' nevű terméket!")
                return None

            products = []
            # max_results terméket dolgozunk fel (alapból 1)
            for item in items[:max_results]:
                try:
                    # név + url
                    name = _first_text(item, [".product-card-title a", "a.product-card-title", ".product-card-title"])
                    url = _first_attr(item, ".product-card-title a", "href") or _first_attr(item, "a", "href")

                    # ár: több lehetséges selector, mert webshopoknál gyakran változik
                    price_text = _first_text(item, [
                        ".product-price-special",
                        ".product-price",
                        ".price",                 # fallback
                        ".product-card-price",    # fallback
                    ])
                    price = _parse_price_text(price_text)

                    products.append({"nev": name, "url": url, "ar": price})

                except StaleElementReferenceException:
                    # DOM frissült (ritka), ilyenkor kihagyjuk ezt az itemet
                    continue
                except Exception:
                    # bármilyen váratlan hiba esetén is legyen stabil
                    products.append({"nev": "", "url": "", "ar": "0 Ft"})

            # ha max_results=1, az elsőt adja vissza
            return products[0] if products else None

        finally:
            # mindig bezár
            try:
                driver.quit()
            except Exception:
                pass

    def karnis(self, termek_neve: str) -> dict | None:
        """
        Karnis szabaszati árlista: DataTables keresővel szűkít, majd az első releváns sort visszaadja.
        Kezeli:
          - nincs találat
          - lassú betöltés
          - link nincs / más formátumú
          - oszlopok hiányoznak / ár üres
        """
        if not termek_neve or not termek_neve.strip():
            print("⚠️ Üres terméknév.")
            return None

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        try:
            driver.get("https://butorszeged.hu/karnisbutor.hu/szakaruhaz/szabaszati-arlista/")
            wait = WebDriverWait(driver, self.timeout)

            # Várjuk, hogy a kereső megjelenjen
            try:
                search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"]')))
            except TimeoutException:
                print("⚠️ Nem találom a keresőmezőt (lehet megváltozott az oldal).")
                return None

            search_box.clear()
            search_box.send_keys(termek_neve)

            # Várjuk, hogy a táblázat sorai frissüljenek
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tablepress-2 tbody tr")))
            except TimeoutException:
                print("⚠️ Nem töltött be a táblázat.")
                return None

            # Adjunk egy pici időt DataTables szűrésre (nem kötelező, de segít)
            time.sleep(0.7)

            rows = driver.find_elements(By.CSS_SELECTOR, "#tablepress-2 tbody tr")
            if not rows:
                print(f"❌ Nem találtam meg a(z) '{termek_neve}' nevű terméket!")
                return None

            products = []

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                adatok = [c.text.strip() for c in cells]

                # DataTables "nincs találat" sor
                if adatok and "Nincs a keresésnek megfelelő találat" in adatok[0]:
                    continue

                # web link: először product-os, ha nincs akkor bármilyen link
                webshop_link = ""
                try:
                    link_elem = row.find_element(By.CSS_SELECTOR, "a[href]")
                    webshop_link = link_elem.get_attribute("href") or ""
                except Exception:
                    webshop_link = ""

                # Ár: nálad eddig adatok[4][:-3] volt.
                # Itt biztonságosan: ha nincs elég oszlop, ár = "0"
                ar = "0"
                try:
                    if len(adatok) >= 5 and adatok[4]:
                        # levágjuk a " Ft" / "ft" végét, és tisztítjuk
                        ar = adatok[4].replace("Ft", "").replace("ft", "").strip()
                except Exception:
                    ar = "0"

                products.append({
                    "nev": termek_neve,
                    "url": webshop_link,
                    "ar": ar
                })

            if not products:
                print(f"❌ Nem találtam meg a(z) '{termek_neve}' nevű terméket!")
                return None

            return products[0]

        finally:
            try:
                driver.quit()
            except Exception:
                pass

    # Az Arukereso osztályban, a borovi() metódus ELEJÉN definiáld:



    def borovi(self, termek_neve: str, frissit: bool = False) -> dict | None:
        BOROVI_KATEGORIA_MAP = {
            # PDF kategória neve (kisbetű, ékezet nélkül) → weboldal URL
            "borovi fureszaru": "epitoipari-faaru",
            "fureszaru": "epitoipari-faaru",
            "epitoipari faaru": "epitoipari-faaru",
            "asztalosipari faaru": "asztalosipari-faaru",
            "ablakfriz": "friz",
            "ajtofriz": "friz",
            "friz": "friz",
            "hajopadlo": "hajopadlo",
            "lamberia": "lamberia",
            "szegolec": "szegolec",
            "borovi ajtoszegely": "szegolec",
            "retegelt lemez": "retegelt-lemez",
            "tablasitott falap": "tablasitott-falap-es-polc",
            "tablasitott polc": "tablasitott-falap-es-polc",
            "osb lap": "osb-lap",
            "lepcso": "lepcso-es-kiegeszitoi",
            "polc": "polc-es-vazszerkezet",
            "vazszerkezet": "polc-es-vazszerkezet",
            "szauna": "szauna-epites",
            "gyalult faaru": "gyalult-faaru",
            "terasz": "terasz-es-pergola",
            "pergola": "terasz-es-pergola",
            "zsindely": "zsindely-es-kiegeszitoi",
            "fahaz burkolasa": "fahaz-burkolasa",
            "kerites": "kerites",
            "akac karo": "epitoipari-faaru/akac-karo-es-oszlop",
            "feluletkezeles": "feluletkezeles",
        }

        BOROVI_BASE = "https://www.borovigerendahazkft.hu/termekek/"
        try:
            import pdfplumber
        except ImportError:
            print("⚠️  pdfplumber nincs telepítve")
            return None

        BOROVI_URL = "https://www.borovigerendahazkft.hu/"
        PDF_URL = "https://www.borovigerendahazkft.hu/tools/generate_pdf"

        base_dir = os.path.dirname(__file__)
        pdf_path = os.path.join(os.path.abspath(os.path.join(base_dir, "..")), "data", "borovi_ar.pdf")
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        if frissit or not os.path.exists(pdf_path):
            try:
                r = requests.get(PDF_URL, timeout=30)
                r.raise_for_status()
                with open(pdf_path, "wb") as f:
                    f.write(r.content)
                for attr in ("_borovi_tabla", "_borovi_url_terkep"):
                    if hasattr(self, attr):
                        delattr(self, attr)
            except Exception as e:
                print(f"⚠️  PDF letöltési hiba: {e}")
                return None

        if not hasattr(self, "_borovi_tabla"):
            self._borovi_tabla = self._borovi_pdf_parse(pdf_path, pdfplumber)
            print(f"ℹ️  Borovi cache: {len(self._borovi_tabla)} tétel")

        if not hasattr(self, "_borovi_url_terkep"):
            self._borovi_url_terkep = self._borovi_url_terkep_epites()

        if not termek_neve or not termek_neve.strip():
            return None

        ar_ft, kategoria = self._borovi_keres(termek_neve.strip(), self._borovi_tabla)

        if ar_ft is None:
            print(f"❌ Borovi: nem találtam árat erre: '{termek_neve}'")
            return {"nev": "", "url": BOROVI_URL, "ar": "0 Ft"}

        def norm(s: str) -> str:
            return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()

        url = BOROVI_URL
        if kategoria:
            kat_norm = norm(kategoria)

            # 1) Statikus térkép – pontos
            if kat_norm in BOROVI_KATEGORIA_MAP:
                url = BOROVI_BASE + BOROVI_KATEGORIA_MAP[kat_norm]

            # 2) Statikus térkép – részleges szóegyezés
            else:
                for kulcs, utvonal in BOROVI_KATEGORIA_MAP.items():
                    kulcs_szavak = set(kulcs.split())
                    kat_szavak = set(kat_norm.split())
                    if kulcs_szavak & kat_szavak:  # van közös szó
                        url = BOROVI_BASE + utvonal
                        break

            # 3) Weboldal nav térkép fallback
            if url == BOROVI_URL and hasattr(self, "_borovi_url_terkep"):
                for link_szoveg, link_url in self._borovi_url_terkep.items():
                    if norm(link_szoveg) in kat_norm or kat_norm in norm(link_szoveg):
                        url = link_url
                        break

            print(f"ℹ️  Borovi URL: '{kategoria}' → {url}")

        return {"nev": termek_neve, "url": url, "ar": ar_ft}

    def _borovi_keres(self, keresett: str, tabla: dict) -> tuple[str | None, str]:
        """Visszaad: (formázott_ár vagy None, kategória_név)"""
        import difflib, unicodedata

        def norm(s):
            return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()

        STOP = {"a", "az", "es", "vagy", "cm", "mm", "db", "m", "ft"}

        def szavak(s):
            return {w for w in re.split(r'[\s/,;]+', norm(s)) if len(w) > 1 and w not in STOP}

        k = keresett.lower().strip()
        kn = norm(k)

        def eredmeny(adat):
            return self._borovi_format(adat["ar"]), adat.get("kategoria", "")

        if k in tabla:                          return eredmeny(tabla[k])
        for ku, ad in tabla.items():
            if norm(ku) == kn:                  return eredmeny(ad)
        for ku, ad in tabla.items():
            kun = norm(ku)
            if kun in kn or kn in kun:          return eredmeny(ad)

        k_szavak = szavak(k)
        legjobb, legjobb_pont = None, 0
        for ku, ad in tabla.items():
            kozos = k_szavak & szavak(ku)
            if len(kozos) > legjobb_pont:
                legjobb_pont, legjobb = len(kozos), ad
        if legjobb_pont >= 1 and legjobb:       return eredmeny(legjobb)

        kulcsok = list(tabla.keys())
        t = difflib.get_close_matches(kn, [norm(kk) for kk in kulcsok], n=1, cutoff=0.45)
        if t:
            idx = [norm(kk) for kk in kulcsok].index(t[0])
            return eredmeny(tabla[kulcsok[idx]])

        return None, ""

    # ── Segédfüggvények (a class belsejébe kerülnek) ─────────────────────

    def _borovi_pdf_parse(self, pdf_path: str, pdfplumber) -> dict:
        # {kulcs: {"ar": int, "kategoria": str}}
        tabla: dict[str, dict] = {}

        AR_RE = re.compile(
            r'(\d{1,3}(?:[.\s]\d{3})*)'
            r'\s*,\s*-?\s*ft'
            r'(?:/\S*)?',
            re.IGNORECASE,
        )
        SKIP = re.compile(
            r'borovigerendahazkft\.hu|^\s*»|^\s*\('
            r'|Méret\s+Bruttó|Fafaj\s+Megnevezés|Árlista\s+\d{4}'
            r'|feltüntetett|Bruttó\s+ár\s*/|^\s*Megnevezés\b'
            r'|A feltüntetett|^\s*$',
            re.IGNORECASE,
        )

        aktualis_kategoria = ""

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for oldal in pdf.pages:
                    text = oldal.extract_text() or ""
                    for sor in text.splitlines():
                        if SKIP.search(sor):
                            continue

                        m = AR_RE.search(sor)
                        if m:
                            ar_tiszta = re.sub(r'[^\d]', '', m.group(1))
                            if not ar_tiszta:
                                continue
                            ar = int(ar_tiszta)
                            if ar < 50:
                                continue

                            termek = sor[:m.start()].strip().lower()
                            if not termek:
                                utana = re.sub(r'^[/\s]+', '', sor[m.end():].strip().lower())
                                termek = utana if utana else aktualis_kategoria.lower()

                            kat = aktualis_kategoria.lower()
                            adat = {"ar": ar, "kategoria": aktualis_kategoria}

                            tabla[f"{kat} {termek}".strip()] = adat
                            if termek:
                                tabla[termek] = adat
                            if kat and kat not in tabla:
                                tabla[kat] = adat
                        else:
                            s = sor.strip()
                            if (s and 2 < len(s) < 80
                                    and not re.search(r'\d{3,}', s)
                                    and not s[0].islower()
                                    and not s.startswith(("Csak ", "Mér", "Vas", "Szé",
                                                          "Hos", "Rög", "Fek", "Pol"))):
                                aktualis_kategoria = s
        except Exception as e:
            print(f"⚠️  Borovi PDF parse hiba: {e}")

        return tabla

    def _borovi_url_terkep_epites(self) -> dict[str, str]:
        """
        Lescrapeli a Borovi weboldal navigációját,
        visszaad {kategória_név_kisbetű: url} szótárt.
        """
        from bs4 import BeautifulSoup
        import unicodedata

        def norm(s: str) -> str:
            return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()

        terkep: dict[str, str] = {}
        try:
            r = requests.get("https://www.borovigerendahazkft.hu/", timeout=15,
                             headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Minden <a> linket begyűjtünk ami a saját domainen van
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                szoveg = a.get_text(strip=True)
                if not szoveg or len(szoveg) < 3:
                    continue

                # Abszolút URL
                if href.startswith("/"):
                    href = "https://www.borovigerendahazkft.hu" + href
                if "borovigerendahazkft.hu" not in href:
                    continue

                terkep[norm(szoveg)] = href

            print(f"ℹ️  Borovi URL térkép: {len(terkep)} link")
        except Exception as e:
            print(f"⚠️  Borovi URL térkép hiba: {e}")

        return terkep

    def _borovi_ar_kinyeres(self, szoveg: str) -> int | None:
        """'1 234,-Ft' → 1234  |  '12.345' → 12345  |  '0' → None"""
        try:
            csak_szam = re.sub(r'[^\d]', '', szoveg.split(",")[0].split("-")[0])
            ertek = int(csak_szam)
            return ertek if ertek > 0 else None
        except Exception:
            return None

    def _norm(self, s: str) -> str:
        return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()

    def _borovi_format(self, ar_int: int) -> str:
        """1234 → '1.234 Ft'  (a meglévő egysegar = int(ar[:-3].replace('.','')) logikához)"""
        return f"{ar_int:,} Ft".replace(",", ".")

