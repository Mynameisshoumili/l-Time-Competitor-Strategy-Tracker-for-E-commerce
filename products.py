from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

print("--- Starting Product Details Scraper (with Updated Selectors) ---")

# --- Setup Selenium Webdriver ---
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--log-level=3")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(options=options)

# --- Step 1: Get UNIQUE product links from the first 3 search pages ---
product_links = set() 
for page_number in range(1, 4):
    search_url = f"https://www.flipkart.com/search?q=mobiles&page={page_number}"
    print(f"📄 Getting product links from search page {page_number}...")
    driver.get(search_url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "CGtC98")))
    except TimeoutException:
        print(f"Could not find product links on page {page_number}. Moving on.")
        continue

    soup = BeautifulSoup(driver.page_source, "lxml")
    products = soup.find_all("div", {"class": "_75nlfW"}) 

    for product in products:
        link_tag = product.find("a", {"class": "CGtC98"})
        if link_tag and 'href' in link_tag.attrs:
            raw_url = "https://www.flipkart.com" + link_tag['href']
            clean_url = raw_url.split('?')[0]
            product_links.add(clean_url)

print(f"\nFound {len(product_links)} unique products to scrape details from.")

# --- Step 2: Iterate through each link and scrape its details ---
all_product_details = []
for url in product_links:
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "VU-ZEz")))
        
        soup = BeautifulSoup(driver.page_source, "lxml")
        
        # Product Name
        try:
            name = soup.find("span", class_="VU-ZEz").text.strip()
        except AttributeError:
            name = None
        
        print(f"Scraping: {name}")

        # Category
        try:
            # UPDATED SELECTOR for better reliability
            category_container = soup.find("div", class_="_1MR4o5")
            category_tags = category_container.find_all("a", class_="_2whKao")
            category = " > ".join([tag.text.strip() for tag in category_tags])
        except AttributeError:
            category = None

        # Price
        try:
            # UPDATED SELECTOR for the current price
            price_str = soup.find("div", class_="Nx9bqj CxhGGd").text.strip()
            price = float(re.sub(r'[^\d.]', '', price_str))
        except (AttributeError, ValueError):
            price = None

        # Discount
        try:
            # UPDATED SELECTOR for the discount percentage
            discount_str = soup.find("div", class_="UkUFwK").find("span").text.strip()
            discount = int(re.search(r'\d+', discount_str).group())
        except (AttributeError, ValueError):
            discount = None

        # Rating
        try:
            # UPDATED SELECTOR for the overall rating
            rating_str = soup.find("div", class_="XQDdHH").text.strip()
            rating = float(rating_str)
        except (AttributeError, ValueError):
            rating = None

        all_product_details.append({
            "Product": name, "Category": category, "Price (₹)": price,
            "Discount (%)": discount, "Rating": rating, "URL": url
        })
        time.sleep(1)

    except TimeoutException:
        print(f"Timeout while loading product page. Skipping URL: {url}")
    except Exception as e:
        print(f"An unexpected error occurred for URL {url}: {e}")

driver.quit()

# --- Step 3: Save the collected details to a new CSV file ---
if all_product_details:
    df = pd.DataFrame(all_product_details)
    df.drop_duplicates(subset=['Product'], inplace=True)
    
    save_path = "flipkart_product_details.csv"
    df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"\n Success! Scraped {len(df)} unique product details.")
    print(f"Data saved to {save_path}")
else:
    print("\nNo product details were scraped.")