from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# 1. Keresett termék
search_term = "Blum+173H7100"#"Blum+Aventos+HK-S+felny%C3%ADl%C3%B3+vasalat"

# 2. Kereső URL
search_url = f"https://butorkellek.eu/kereses?description=0&utm_source=iai_ads&utm_medium=google_shopping&gad_source=1&gad_campaignid=22402103487&gclid=Cj0KCQjww4TGBhCKARIsAFLXndQ-h0gI5LLAt5S8GS5YgmguS7Fq36fURGc7etdspSxbUuXa3B6zSGsaAg3SEALw_wcB&keyword={search_term}"

# 3. Böngésző indítása
options = webdriver.ChromeOptions()
options.add_argument("--headless")   # háttérben fusson, ne nyisson ablakot
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 4. Oldal megnyitása
driver.get(search_url)

# 5. Várunk, hogy a JS betöltse a találatokat
time.sleep(5)

# 6. Termékek kigyűjtése
products = []
"""
items = driver.find_elements(By.CSS_SELECTOR, ".product-card-title a")
#<h2 class="product-card-item product-card-title rps-product-title h4"><a href="https://butorkellek.eu/blum-felnyilo-vasalat-aventos-hk-s-6369?keyword=Blum%20Aventos%20HK-S%20felny%C3%ADl%C3%B3%20vasalat&amp;_gl=1*1arl0y5*_up*MQ..*_gs*MQ..&amp;gclid=Cj0KCQjww4TGBhCKARIsAFLXndQ-h0gI5LLAt5S8GS5YgmguS7Fq36fURGc7etdspSxbUuXa3B6zSGsaAg3SEALw_wcB" title="Blum Felnyíló vasalat AVENTOS HK-S" class="">Blum Felnyíló vasalat AVENTOS HK-S</a></h2>

for item in items:
    products.append({
        "name": item.text.strip(),
        "url": item.get_attribute("href")
    })

driver.quit()
"""
products = []
items = driver.find_elements(By.CSS_SELECTOR, ".product-card-body")  # minden termék doboza
#<div class="card-body product-card-body"><h2 class="product-card-item product-card-title rps-product-title h4"><a href="https://butorkellek.eu/blum-felnyilo-vasalat-aventos-hk-s-6369?keyword=Blum%20Aventos%20HK-S%20felny%C3%ADl%C3%B3%20vasalat&amp;_gl=1*1arl0y5*_up*MQ..*_gs*MQ..&amp;gclid=Cj0KCQjww4TGBhCKARIsAFLXndQ-h0gI5LLAt5S8GS5YgmguS7Fq36fURGc7etdspSxbUuXa3B6zSGsaAg3SEALw_wcB" title="Blum Felnyíló vasalat AVENTOS HK-S" class="">Blum Felnyíló vasalat AVENTOS HK-S</a></h2><div class="product-card-item product-card-sku product-card__item product-card__sku"><span class="product-card__label">Cikkszám:</span> <a>D027252</a></div><div class="snapshot-list-item list_stock product-card-item product-card-stock product-card__item product-card__stock  stock_status_id-9" style="color: rgb(123, 166, 23);"><span class="mr-1"><svg class="" viewBox="0 0 13 10" height="11px" fill="var(--rps-instant-search-resource-hover)"><path d="M11.0353 0L4.86064 6.28947L1.69674 3.11283L0 4.80963L4.9882 9.78508L13 2.01572L11.0353 0Z" fill="currentColor"></path></svg></span>Raktáron</div><div class="product-card-item product-card-price d-flex flex-row flex-wrap"><span class="product-price rps-product-final-price">9.654 Ft</span></div></div>

for item in items:
    try:
        name = item.find_element(By.CSS_SELECTOR, ".product-card-title a").text.strip()
        #<span class="product-price rps-product-final-price">9.654 Ft</span>
    except:
        name = ""

    try:
        url = item.find_element(By.CSS_SELECTOR, ".product-card-title a").get_attribute("href")
    except:
        url = ""

    try:
        price = item.find_element(By.CSS_SELECTOR, ".product-price").text.strip()
    except:
        price = "Nincs ár"

    products.append({
        "name": name,
        "url": url,
        "price": price
    })
driver.quit()

# 7. Eredmények kiírása
if products:
    for p in products:
        print(p)
else:
    print("❌ Nem találtam terméket!")
