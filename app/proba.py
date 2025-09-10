from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# 1. Keresett termék
search_term = "Blum+Aventos+HK-S+felny%C3%ADl%C3%B3+vasalat"

# 2. Kereső URL
search_url = f"https://butorkellek.eu/kereses?description=0&utm_source=iai_ads&utm_medium=google_shopping&gad_source=1&gad_campaignid=22402103487&gclid=Cj0KCQjww4TGBhCKARIsAFLXndQ-h0gI5LLAt5S8GS5YgmguS7Fq36fURGc7etdspSxbUuXa3B6zSGsaAg3SEALw_wcB&keyword={search_term}"

# 3. Böngésző indítása
options = webdriver.ChromeOptions()
#options.add_argument("--headless")   # háttérben fusson, ne nyisson ablakot
#options.add_argument("--no-sandbox")
#options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 4. Oldal megnyitása
driver.get(search_url)

# 5. Várunk, hogy a JS betöltse a találatokat
time.sleep(5)

# 6. Termékek kigyűjtése
products = []
items = driver.find_elements(By.CSS_SELECTOR, ".product-name a")

for item in items:
    products.append({
        "name": item.text.strip(),
        "url": item.get_attribute("href")
    })

driver.quit()

# 7. Eredmények kiírása
if products:
    print("✅ Találatok:")
    for p in products:
        print(p)
else:
    print("❌ Nem találtam terméket!")
