from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pandas as pd

print("--- Starting Review Scraper ---")

# --- Setup Selenium Webdriver ---
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--log-level=3")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(options=options)

# --- Step 1: Get UNIQUE product links from the first 3 search pages ---
product_links = set() # Using a set to automatically avoid duplicate product links
for page_number in range(1, 4):
    search_url = f"https://www.flipkart.com/search?q=mobiles&page={page_number}"
    print(f" Getting product links from search page {page_number}...")
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
            product_links.add("https://www.flipkart.com" + link_tag['href'])

print(f"\nFound {len(product_links)} unique products to scrape reviews from.")

# --- Step 2: Iterate through each unique link and scrape reviews ---
all_reviews_data = []
for link in product_links:
    try:
        driver.get(link)
        wait = WebDriverWait(driver, 10)
        product_name_tag = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "VU-ZEz")))
        product_name = product_name_tag.text.strip()
        print(f"\nScraping reviews for: {product_name}")
        
        all_reviews_link_tag = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/product-reviews/']")))
        all_reviews_url = all_reviews_link_tag.get_attribute('href')
        
        # Scrape the first 3 pages of reviews for each product
        for page_num in range(1, 4):
            review_page_url = f"{all_reviews_url}&page={page_num}"
            driver.get(review_page_url)
            
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cPHDOP")))
            except TimeoutException:
                print(f"  -> No more reviews found on page {page_num}.")
                break 
            
            review_page_soup = BeautifulSoup(driver.page_source, "lxml")
            review_containers = review_page_soup.find_all("div", {"class": "cPHDOP"})
            
            for review in review_containers:
                name_tag = review.find("p", {"class": "_2sc7ZR"})
                reviewer_name = name_tag.get_text(strip=True) if name_tag else "Anonymous"
                rating_tag = review.find("div", {"class": "_3LWZlK"})
                rating = rating_tag.get_text(strip=True) if rating_tag else None
                title_tag = review.find("p", {"class": "_2-N8zT"})
                review_title = title_tag.get_text(strip=True) if title_tag else ""
                text_tag = review.find("div", {"class": "ZmyHeo"})
                review_text = text_tag.get_text(strip=True).replace("READ MORE", "").strip() if text_tag else ""
                
                if review_text:
                    all_reviews_data.append({
                        "ProductName": product_name, "ReviewerName": reviewer_name,
                        "Rating": rating, "Title": review_title, "ReviewText": review_text
                    })
    except TimeoutException:
        print(f"Could not find an 'All reviews' link for a product. Skipping.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

driver.quit()

# --- Step 3: Save the collected review data to a CSV file ---
if all_reviews_data:
    df = pd.DataFrame(all_reviews_data)
    df.drop_duplicates(subset=['ProductName', 'ReviewText'], inplace=True)
    save_path = "flipkart_reviews_unique.csv"
    df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ REVIEW SCRAPING COMPLETE. Scraped {len(df)} unique reviews. Saved to {save_path}")
else:
    print("\nNo reviews were scraped.")