import requests
import fitz
import camelot
import os

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
    """
    def butorkellek(self, termek_neve):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        butorkellek_url = f"https://butorkellek.eu/kereses?description=0&utm_source=iai_ads&utm_medium=google_shopping&gad_source=1&gad_campaignid=22402103487&gclid=Cj0KCQjww4TGBhCKARIsAFLXndQ-h0gI5LLAt5S8GS5YgmguS7Fq36fURGc7etdspSxbUuXa3B6zSGsaAg3SEALw_wcB&keyword={termek_neve}"
        driver.get(butorkellek_url)
        time.sleep(5)

        products = []
        items = driver.find_elements(By.CSS_SELECTOR, ".product-card-body")  # minden termék doboza
        items = [items[0]] #Egyenlore csak a legelso termekkel probalom meg, ha tul nagy a talati hiba akkor ezen valtoztatok

        for item in items:
            try:
                name = item.find_element(By.CSS_SELECTOR, ".product-card-title a").text.strip()
            except:
                name = ""

            try:
                url = item.find_element(By.CSS_SELECTOR, ".product-card-title a").get_attribute("href")
            except:
                url = ""

            price_elements = item.find_elements(By.CSS_SELECTOR, ".product-price")

            if price_elements:
                price = price_elements[0].text.strip()
            else:
                # ha nincs normál ár, próbáljuk az akciósat
                special_price_elements = item.find_elements(By.CSS_SELECTOR, ".product-price-special")
                if special_price_elements:
                    price = special_price_elements[0].text.strip()
                else:
                    # ha egyik sincs, akkor 0
                    price = "0 ft"

            products.append({
                "nev": name,
                "url": url,
                "ar": price
            })
        driver.quit()

        if not products:
            print("Nem találtam meg a " + termek_neve + " nevű terméket!")

        return products[0] #Majd ez is valtoztatni kell ha tobb termeket akarok visszaadni!
    """
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
    '''
    def karnis(self, termek_neve):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        driver.get("https://butorszeged.hu/karnisbutor.hu/szakaruhaz/szabaszati-arlista/")

        search_box = driver.find_element(By.CSS_SELECTOR, 'input[type="search"]')
        search_box.send_keys(termek_neve)
        time.sleep(3)

        # Táblázat sorainak beolvasása
        rows = driver.find_elements(By.CSS_SELECTOR, "#tablepress-2 tbody tr")
        products = []

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            adatok = [c.text.strip() for c in cells]

            # Webshop link keresése a sorban (ha van)
            try:
                link_elem = row.find_element(By.CSS_SELECTOR, "a[href*='product']")
                webshop_link = link_elem.get_attribute("href")
            except:
                webshop_link = None

            print(adatok)
            if adatok != ['Nincs a keresésnek megfelelő találat']:
                products.append({
                    "nev": termek_neve,
                    "url": webshop_link,
                    "ar": adatok[4][:-3]
                })
        driver.quit()
        if not products:
            print("Nem találtam meg a " + termek_neve + " nevű terméket!")
            return ""
        else:
            return products[0] #Majd ez is valtoztatni kell ha tobb termeket akarok visszaadni!

    def borovi(self, termek_neve):
        # --- 1. data mappa az app-on kívül ---
        base_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(base_dir, ".."))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)

        pdf_path = os.path.join(data_dir, "borovi_ar.pdf")

        # --- 2. PDF letöltése ---
        response = requests.get("https://www.borovigerendahazkft.hu/tools/generate_pdf")
        with open(pdf_path, "wb") as f:
            f.write(response.content)

        print(f"✅ PDF letöltve ide: {pdf_path}")

        # --- 3. PDF megnyitás ---
        doc = fitz.open(pdf_path)
        oldalak_szovege = [page.get_text("text") for page in doc]

        # --- 4. Megkeressük, melyik oldalon és hol van a kulcsszó ---
        start_page = None
        heading_rect = None

        for i, page in enumerate(doc):
            if termek_neve.lower() in oldalak_szovege[i].lower():
                rects = page.search_for(termek_neve)
                if rects:
                    start_page = i  # 0-indexelt oldal
                    heading_rect = rects[0]  # a cím téglalapja
                    break

        if start_page is None:
            print(f"⚠️ Nem találtam '{termek_neve}' szöveget a PDF-ben.")
            return {}

        print(f"🔎 '{termek_neve}' megtalálva a(z) {start_page + 1}. oldalon")

        talalatok = []
        volt_mar_tabla = False
        ures_oldal_ok = False  # ha már találtunk táblát, és utána jön 1 üres oldal → ott megállunk

        # --- 5. Végigmegyünk a fejezet oldalain a címtől a PDF végéig ---
        for page_idx in range(start_page, len(doc)):
            page = doc[page_idx]
            page_height = page.rect.height
            page_width = page.rect.width

            # Paraméterek Camelot-nak
            kwargs = {
                "pages": str(page_idx + 1),  # Camelot 1-indexelt
                "flavor": "stream",  # ha nem jó, érdemes "lattice"-t is kipróbálni
                "strip_text": "\n"
            }

            if page_idx == start_page:
                # csak a CÍM ALATTI területet nézzük ezen az oldalon
                y_top = heading_rect.y1  # fitz: felülről mért
                # Camelot: (0,0) az oldal ALJÁN van → át kell fordítani
                y1_camelot = 0
                y2_camelot = page_height - y_top
                area = f"0,{y1_camelot},{page_width},{y2_camelot}"
                kwargs["table_areas"] = [area]

            try:
                tables = camelot.read_pdf(pdf_path, **kwargs)
            except Exception as e:
                print(f"⚠️ Hiba a(z) {page_idx + 1}. oldal feldolgozásakor: {e}")
                break

            page_dfk = [t.df for t in tables if not t.df.empty] if tables else []

            if page_dfk:
                # találtunk ezen az oldalon táblázatot
                talalatok.extend(page_dfk)
                volt_mar_tabla = True
                ures_oldal_ok = False
                print(f"✅ {len(page_dfk)} táblázat a(z) {page_idx + 1}. oldalon")
            else:
                # ezen az oldalon nincs táblázat
                if volt_mar_tabla:
                    # előtte már volt táblázat, most nincs → tekintsük a fejezet végét
                    print(f"⛔ Nincs táblázat a(z) {page_idx + 1}. oldalon, megállunk itt.")
                    break
                else:
                    # még nem volt egyetlen táblázat sem (pl. a címes oldal alja teljesen üres)
                    print(f"ℹ️ Nincs táblázat a(z) {page_idx + 1}. oldalon, lépünk tovább.")
                    continue

        eredmenyek = {}
        if talalatok:
            print(f"✅ Összesen {len(talalatok)} táblázat beolvasva a(z) '{termek_neve}' fejezetből.")
            eredmenyek[termek_neve] = talalatok
        else:
            print("⚠️ Nem talált táblázatot a fejezetben.")

        return eredmenyek
    '''

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

    def borovi(self, fejezet_cim: str, frissit: bool = False) -> dict | None:
        """
        Borovi PDF:
          - megkeresi a fejezet címét (fejezet_cim)
          - a cím ALATT indul
          - beolvassa az összes táblázatot a KÖVETKEZŐ FEJEZETCÍMIG
        Stabilabb fejezetcím-detekció: a fejezetcímeket a szöveg mérete/pozíciója alapján próbálja megfogni.
        """
        if not fejezet_cim or not fejezet_cim.strip():
            print("⚠️ Üres fejezet cím.")
            return None

        # --- data mappa az app-on kívül ---
        base_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(base_dir, ".."))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)

        pdf_path = os.path.join(data_dir, "borovi_ar.pdf")
        url = "https://www.borovigerendahazkft.hu/tools/generate_pdf"

        # --- letöltés (cache) ---
        if frissit or (not os.path.exists(pdf_path)):
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(r.content)
            print(f"✅ PDF letöltve ide: {pdf_path}")
        else:
            print(f"ℹ️ PDF már létezik: {pdf_path}")

        # --- PDF megnyitás ---
        doc = fitz.open(pdf_path)

        # 1) Keressük meg a fejezet címet és a y-pozícióját
        start_page = None
        start_rect = None

        for i in range(len(doc)):
            page = doc[i]
            rects = page.search_for(fejezet_cim)
            if rects:
                start_page = i
                start_rect = rects[0]
                break

        if start_page is None:
            print(f"⚠️ Nem találtam ilyen fejezetcímet a PDF-ben: '{fejezet_cim}'")
            return None

        # 2) Következő fejezetcím keresése:
        #    Ehhez kigyűjtjük a "nagyobb" szöveg spaneket (jellemzően címsorok),
        #    és megkeressük az első olyat, ami a start_page után jön.
        next_page = None
        next_y = None

        def heading_candidates(page: fitz.Page):
            """Cím jelöltek: nagyobb betűméretű szöveg spane-k (heurisztika)."""
            out = []
            data = page.get_text("dict")
            for block in data.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        txt = (span.get("text") or "").strip()
                        size = span.get("size", 0)
                        bbox = span.get("bbox", None)  # (x0,y0,x1,y1)
                        if not txt or not bbox:
                            continue
                        # heur: nagyobb betűméret + nem tipikus táblafejléc szavak
                        low = txt.lower()
                        taboo = ["fafaj", "minőség", "vastagság", "szélesség", "hossz", "ár", "ft", "mm"]
                        if size >= 12 and not any(t in low for t in taboo):
                            out.append((txt, size, bbox))
            return out

        # végig a start_page+1-től, keressük az első valós "cím-jelöltet"
        for p in range(start_page + 1, len(doc)):
            cands = heading_candidates(doc[p])
            if cands:
                # az első (legfelül levő) jelölt legyen a következő fejezet címe
                cands.sort(key=lambda x: x[2][1])  # bbox y0 szerint
                next_page = p
                next_y = cands[0][2][1]
                break

        # end_page: ha van next_page, akkor az előző oldal a vége, különben a PDF vége
        end_page = (next_page - 1) if next_page is not None else (len(doc) - 1)

        print(f"🔎 Fejezet kezdete: {start_page+1}. oldal")
        if next_page is not None:
            print(f"⛔ Következő fejezet: {next_page+1}. oldal (y≈{next_y:.1f}) → itt megállunk")
        else:
            print("ℹ️ Nincs következő fejezetcím → PDF végéig olvasok")

        # 3) Táblázat beolvasás: start oldalon csak a cím alatti rész, többi oldalon teljes oldal
        talalatok = []

        for page_idx in range(start_page, end_page + 1):
            page = doc[page_idx]
            w = page.rect.width
            h = page.rect.height

            # először stream, ha 0 táblázat, próbál lattice
            def read_tables(flavor: str, table_areas=None):
                kwargs = {
                    "pages": str(page_idx + 1),
                    "flavor": flavor,
                    "strip_text": "\n"
                }
                if table_areas:
                    kwargs["table_areas"] = table_areas
                return camelot.read_pdf(pdf_path, **kwargs)

            table_areas = None
            if page_idx == start_page and start_rect is not None:
                y_top = start_rect.y1
                # camelot koordináta: alulról számol, ezért: y2 = h - y_top
                area = f"0,0,{w},{h - y_top}"
                table_areas = [area]

            tables = None
            try:
                tables = read_tables("stream", table_areas=table_areas)
                if not tables or tables.n == 0:
                    tables = read_tables("lattice", table_areas=table_areas)
            except Exception as e:
                print(f"⚠️ Hiba a(z) {page_idx+1}. oldalon: {e}")
                continue

            if tables and tables.n > 0:
                for t in tables:
                    if t.df is not None and not t.df.empty:
                        talalatok.append(t.df)
                print(f"✅ {tables.n} tábla a(z) {page_idx+1}. oldalon")

        if not talalatok:
            print("⚠️ Nem találtam táblázatot ebben a fejezetben.")
            return {"fejezet": fejezet_cim, "tablazatok": []}

        return {"fejezet": fejezet_cim, "tablazatok": talalatok}
