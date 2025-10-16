import os
import time, re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime

import ingestion
# ------------------------------
# CONFIG
# ------------------------------
SEARCH_URL = "https://www.flipkart.com/search?q=mobiles&page={}"
LISTING_PAGES = 3      # how many search pages
REVIEW_PAGES  = 2     # review pages per product
WAIT = 3                # seconds to wait for JS to load


# Selenium setup
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(options=options)

mobile_rows = []
review_rows = []

def clean_price(txt):
    return re.sub(r"[^\d]", "", txt) if txt else None

# ------------------------------
# Step 1: Collect Product Listing Data
# ------------------------------
product_links = set()
scraped_at = datetime.now().isoformat()

for page in range(1, LISTING_PAGES + 1):
    print(f"📄 Listing Page {page}")
    driver.get(SEARCH_URL.format(page))
    time.sleep(WAIT)

    soup = BeautifulSoup(driver.page_source, "lxml")
    products = soup.find_all("div", {"class": "tUxRFH"})

    for p in products:
        title_tag = p.find("div", {"class": "KzDlHZ"})
        mobilename = title_tag.get_text(strip=True) if title_tag else "Unknown"

        price_tag = p.find("div", {"class": "Nx9bqj _4b5DiR"})
        sellingprice = clean_price(price_tag.get_text()) if price_tag else None

        mrp_tag = p.find("div", {"class": "yRaY8j"})
        mrp = mrp_tag.get_text(strip=True).replace("₹","").replace(",","") if mrp_tag else None

        discount_tag = p.find("div", {"class": "UkUFwK"})
        discountoffering = discount_tag.get_text(strip=True) if discount_tag else None
        
        # Discount
        # discount_tag = p.find("div", {"class": "UkUFwK"})
        # discount = discount_tag.get_text(strip=True).replace("% off","") if discount_tag else None

        rating_tag = p.find("div", {"class": "XQDdHH"})
        rating = rating_tag.get_text(strip=True) if rating_tag else None

        link_tag = p.find("a", {"class": "CGtC98"})
        url = "https://www.flipkart.com" + link_tag["href"] if link_tag else None

        pid_match = re.search(r"/p/itm([0-9a-z]+)", url) if url else None
        productid = pid_match.group(1) if pid_match else None

        if url:
            product_links.add((productid, mobilename, url))

        mobile_rows.append({
            "source": "flipkart",
            "productid": productid,
            "mobilename": mobilename,
            "sellingprice": sellingprice,
            "mrp": mrp,
            "discountoffering": discountoffering,
            "rating": rating,
            "url": url,
            "scraped_at": scraped_at
        })

# Save mobile.csv (append if exists)
mobile_df_new = pd.DataFrame(mobile_rows)
try:
    mobile_df_existing = pd.read_csv("mobile.csv")
    mobile_df = pd.concat([mobile_df_existing, mobile_df_new], ignore_index=True)
    mobile_df = mobile_df.drop_duplicates(subset=["productid", "scraped_at"], keep="last")
except FileNotFoundError:
    mobile_df = mobile_df_new



os.makedirs("data", exist_ok=True)
mobile_df.to_csv("mobile.csv", index=False, encoding="utf-8-sig")
print(f"✅ Saved {len(mobile_df_new)} new products (total {len(mobile_df)}) to mobile.csv")

# ------------------------------
# Step 2: Collect Reviews
# ------------------------------
for productid, mobilename, url in product_links:
    if not url:
        continue
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "VU-ZEz"))
        )
        soup = BeautifulSoup(driver.page_source, "lxml")
        all_reviews_tag = soup.find("a", href=re.compile("/product-reviews/"))
        if not all_reviews_tag:
            continue
        reviews_base = "https://www.flipkart.com" + all_reviews_tag["href"]

        print(f"💬 Reviews for: {mobilename}")

        for rpage in range(1, REVIEW_PAGES + 1):
            review_url = f"{reviews_base}&page={rpage}"
            driver.get(review_url)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "cPHDOP"))
                )
            except TimeoutException:
                break

            rsoup = BeautifulSoup(driver.page_source, "lxml")
            containers = rsoup.find_all("div", {"class": "cPHDOP"})

            for c in containers:
                user_tag = c.find("p", {"class": "_2NsDsF AwS1CA"})
                userid = user_tag.get_text(strip=True) if user_tag else "Anonymous"

                rating_tag = c.find("div", {"class": "_3LWZlK"})
                rrating = rating_tag.get_text(strip=True) if rating_tag else None

                text_tag = c.find("div", {"class": "ZmyHeo"})
                review_text = text_tag.get_text(strip=True).replace("READ MORE", "") if text_tag else ""

                date_tag = c.find("p", {"class": "_2NsDsF", "style": False})
                reviewdate = ""
                if date_tag:
                    all_p = c.find_all("p", {"class": "_2NsDsF"})
                    if len(all_p) > 1:
                        reviewdate = all_p[-1].get_text(strip=True)

                if review_text:
                    review_rows.append({
                        "source": "flipkart",
                        "productid": productid,
                        "mobilename": mobilename,
                        "userid": userid,
                        "review": review_text,
                        "rating": rrating,
                        "reviewdate": reviewdate
                    })
            time.sleep(2)

    except Exception as e:
        print(f"⚠ Error scraping reviews for {mobilename}: {e}")

driver.quit()

# Save review.csv
review_df = pd.DataFrame(review_rows)
review_df.to_csv("review.csv", index=False, encoding="utf-8-sig")
print(f"✅ Saved {len(review_df)} reviews to review.csv")
ingestion.main()