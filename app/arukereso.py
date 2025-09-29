from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

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
            ''' 
            try:
                price = item.find_element(By.CSS_SELECTOR, ".product-price").text.strip()
            except:
                price = "0 ft"
            '''
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
