from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import fitz
import camelot
import os

class Arukereso:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")  # háttérben fusson, ne nyisson ablakot
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")

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
            print("Nem találtam meg a " + termek_neve + "nevű terméket!")

        return products[0] #Majd ez is valtoztatni kell ha tobb termeket akarok visszaadni!

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

            products.append({
                "nev": adatok[7],
                "url": webshop_link,
                "ar": adatok[4][:-3]
            })
        driver.quit()
        if not products:
            print("Nem találtam meg a " + termek_neve + "nevű terméket!")

        return products[0] #Majd ez is valtoztatni kell ha tobb termeket akarok visszaadni!

    def borovi(self, termek_neve):
        # --- 1. data mappa az app-on kívül ---
        base_dir = os.path.dirname(__file__)  # ez: csixwood/app/
        project_root = os.path.abspath(os.path.join(base_dir, ".."))  # -> csixwood/
        data_dir = os.path.join(project_root, "data")  # -> csixwood/data
        os.makedirs(data_dir, exist_ok=True)

        pdf_path = os.path.join(data_dir, "borovi_ar.pdf")

        # --- 2. PDF letöltése ---
        response = requests.get("https://www.borovigerendahazkft.hu/tools/generate_pdf")
        with open(pdf_path, "wb") as f:
            f.write(response.content)

        print(f"✅ PDF letöltve ide: {pdf_path}")

        # --- 3. PDF megnyitás és feldolgozás ---
        doc = fitz.open(pdf_path)
        eredmenyek = {}

        for i, page in enumerate(doc):
            text = page.get_text("text")

            if termek_neve.lower() in text.lower():
                print(f"🔎 Találat az {i + 1}. oldalon")

                tables = camelot.read_pdf(
                    pdf_path,
                    pages=str(i + 1),
                    flavor="stream",  # ez kell, mert a PDF nem rácsos
                    strip_text="\n"
                )
                print(tables[0].df)

                if tables and len(tables) > 0:
                    eredmenyek[termek_neve] = tables[0].df
                    print("✅ Táblázat beolvasva!")
                else:
                    print("⚠️ Nem talált táblázatot ezen az oldalon.")

        return eredmenyek

'''
eredmenyek = Arukereso().borovi("Táblásított fenyő")
print(eredmenyek)
'''