import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv


# LOAD ENV
load_dotenv(dotenv_path=".env")


# CONFIG

CSV_TODAY_MOBILE = "data/flipkart_product_details.csv"
CSV_YESTERDAY_MOBILE = "data/previous_prices.csv"

CSV_TODAY_REVIEW = "data/flipkart_reviews_unique.csv"
CSV_YESTERDAY_REVIEW = "data/previous_reviews.csv"

PRICE_DROP_THRESHOLD = 10  # % drop
NEGATIVE_REVIEW_THRESHOLD = 2  # alerts if new negatives > this

EMAIL_SENDER = "chevvakulakartheeka@gmail.com"
EMAIL_RECEIVER = "adisheshu1913@gmail.com"
EMAIL_PASSWORD = "Lucky$2369"  # Use an app password for Gmail

# EMAIL HELPER

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        print(f"📧 Email sent → {subject}")
    except Exception as e:
        print(f"⚠ Email send failed: {e}")

# PRICE DROP CHECK

def check_price_drops():
    if not (os.path.exists(CSV_TODAY_MOBILE) and os.path.exists(CSV_YESTERDAY_MOBILE)):
        print("⚠ Missing mobile CSV files, skipping price check.")
        return

    today = pd.read_csv(CSV_TODAY_MOBILE)
    yesterday = pd.read_csv(CSV_YESTERDAY_MOBILE)

    merged = pd.merge(today, yesterday, on="Product", suffixes=("_today", "_yesterday"))

    for _, row in merged.iterrows():
        try:
            old_price = float(row["Price (₹)_yesterday"])
            new_price = float(row["Price (₹)_today"])

            if old_price > 0:
                drop_percent = ((old_price - new_price) / old_price) * 100
                if drop_percent >= PRICE_DROP_THRESHOLD:
                    body = f"""
                    Price Drop Alert 🚨

                    Product: {row['Product']}
                    Old Price: ₹{old_price}
                    New Price: ₹{new_price}
                    Drop: {drop_percent:.2f}%

                    Check competitor site immediately.
                    """
                    send_email(f"⚠ Price Drop: {row['Product']}", body)
        except Exception as e:
            print(f"⚠ Error checking price for {row.get('Product')}: {e}")

# NEGATIVE REVIEW CHECK
def check_negative_reviews():
    if not (os.path.exists(CSV_TODAY_REVIEW) and os.path.exists(CSV_YESTERDAY_REVIEW)):
        print("⚠ Missing review CSV files, skipping review check.")
        return

    today = pd.read_csv(CSV_TODAY_REVIEW)
    yesterday = pd.read_csv(CSV_YESTERDAY_REVIEW)

    # Find new reviews by comparing today and yesterday
    merged = pd.concat([yesterday, today]).drop_duplicates(
        subset=["ProductName", "ReviewerName", "ReviewText"], keep=False
    )

    negatives = merged[merged["Rating"].astype(str).isin(["1", "2"])]

    if len(negatives) >= NEGATIVE_REVIEW_THRESHOLD:
        body = f"""
        Negative Review Alert 🚨

        Found {len(negatives)} new negative reviews today.

        Example:
        Product: {negatives.iloc[0]['ProductName']}
        Review: {negatives.iloc[0]['ReviewText']}
        Rating: {negatives.iloc[0]['Rating']}

        Check full review report for details.
        """
        send_email("⚠ Negative Reviews Detected", body)

# MAIN

if __name__ == "__main__":
    print("🔍 Running notification checks...")
    check_price_drops()
    check_negative_reviews()
    print("✅ Notification run complete.")

    import shutil
    shutil.copyfile(CSV_TODAY_REVIEW, CSV_YESTERDAY_REVIEW)