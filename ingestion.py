#ingestion.py 

import pandas as pd
from datetime import datetime, timedelta
import re
import os
from textblob import TextBlob  # for sentiment analysis

# ---------------- CONFIG ----------------
REVIEWS_FILE = "review.csv"   # cleaned review input
MOBILE_FILE = "mobile.csv"    # scraped mobile data input
OUTPUT_REVIEWS = "cleaned_reviews.csv"
OUTPUT_MOBILE = "cleaned_mobile.csv"
os.makedirs("data", exist_ok=True)

# ---------------- FUNCTIONS ----------------

def parse_relative_date(text):
    """Convert relative dates like '22 days ago' to absolute date safely"""
    text = str(text).strip().lower()
    now = datetime.now()

    try:
        if "day" in text:
            match = re.search(r"(\d+)", text)
            days = int(match.group(1)) if match else 0
            return (now - timedelta(days=days)).date()
        elif "month" in text:
            match = re.search(r"(\d+)", text)
            months = int(match.group(1)) if match else 0
            month = now.month - months
            year = now.year
            if month <= 0:
                month += 12
                year -= 1
            day = min(now.day, 28)
            return datetime(year, month, day).date()
        elif "year" in text:
            match = re.search(r"(\d+)", text)
            years = int(match.group(1)) if match else 0
            return datetime(now.year - years, now.month, now.day).date()
        else:
            dt = pd.to_datetime(text, errors='coerce')
            if pd.isna(dt):
                return None
            return dt.date()
    except Exception:
        return None

def remove_emojis(text):
    """Remove emojis, symbols, and non-text characters from review"""
    if not isinstance(text, str):
        return text
    return re.sub(r'[^A-Za-z0-9.,!?;:\'"()\-\s]', '', text)

# ---------------- CLEANING FUNCTIONS ----------------

def clean_reviews(df):
    """Clean review DataFrame"""
    df['mobilename'] = df['mobilename'].astype(str).str.strip()
    df['userid'] = df['userid'].astype(str).str.strip()
    df['review'] = df['review'].astype(str).str.strip()
    df['review'] = df['review'].apply(remove_emojis)
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    df['reviewdate'] = df['reviewdate'].apply(parse_relative_date)
    df = df[df['review'].str.len() > 0]
    df = df.drop_duplicates(subset=['productid', 'userid', 'review'])
    return df

def clean_mobile(df):
    """Clean mobile/product DataFrame"""
    df['mobilename'] = df['mobilename'].astype(str).str.strip()
    df['source'] = df['source'].astype(str).str.strip()
    df['sellingprice'] = pd.to_numeric(df['sellingprice'], errors='coerce')
    df['discountoffering'] = df['discountoffering'].astype(str).str.replace('% off','',regex=False).str.strip()
    df['discountoffering'] = pd.to_numeric(df['discountoffering'], errors='coerce')
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    # Ensure scraped_at is datetime
    df['scraped_at'] = pd.to_datetime(df['scraped_at'], errors='coerce')
    df = df.drop_duplicates(subset=['productid', 'scraped_at'], keep='last')
    return df

# ---------------- MAIN ----------------

def main():
    valid_product_ids = set()

    # -------- Load and Clean Mobile Data --------
    if os.path.exists(MOBILE_FILE):
        df_mobile = pd.read_csv(MOBILE_FILE)
        print(f"Raw mobile data: {len(df_mobile)} rows")
        df_mobile_clean = clean_mobile(df_mobile)
        valid_product_ids = set(df_mobile_clean['productid'].dropna().unique())
        print(f"Cleaned mobile data: {len(df_mobile_clean)} rows")
        df_mobile_clean.to_csv(os.path.join("data", OUTPUT_MOBILE), index=False, encoding="utf-8-sig")
        print(f"✅ Cleaned mobile data saved: data/{OUTPUT_MOBILE}")
    else:
        print(f"Mobile file not found: {MOBILE_FILE}")

    # -------- Load and Clean Reviews --------
    if os.path.exists(REVIEWS_FILE):
        df_reviews = pd.read_csv(REVIEWS_FILE)
        print(f"Raw reviews: {len(df_reviews)} rows")

        # ✅ Filter only reviews whose productid exists in mobiles.csv
        if valid_product_ids:
            before = len(df_reviews)
            df_reviews = df_reviews[df_reviews['productid'].isin(valid_product_ids)]
            print(f"Filtered reviews by productid: {len(df_reviews)} rows (kept {len(df_reviews)}/{before})")

        df_reviews_clean = clean_reviews(df_reviews)
        print(f"Cleaned reviews: {len(df_reviews_clean)} rows")
        df_reviews_clean.to_csv(os.path.join("data", OUTPUT_REVIEWS), index=False, encoding="utf-8-sig")
        print(f"✅ Cleaned reviews saved: data/{OUTPUT_REVIEWS}")
    else:
        print(f"Reviews file not found: {REVIEWS_FILE}")

if __name__ == "__main__":
    main()