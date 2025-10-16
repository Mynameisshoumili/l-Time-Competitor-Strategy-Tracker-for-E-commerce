import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_SENDER, EMAIL_RECEIVER, EMAIL_PASSWORD  # ✅ Import from config.py

def clean_product_column(df):
    df["Product"] = (
        df["Product"]
        .astype(str)
        .str.strip()
        .str.replace("\u00a0", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
    )
    return df

def load_and_merge():
    #  Updated paths to use 'data' folder
    actual_path = "data/flipkart_product_details.csv"
    predicted_path = "data/predicted_prices.csv"

    actual_df = pd.read_csv(actual_path)
    predicted_df = pd.read_csv(predicted_path)

    actual_df = clean_product_column(actual_df)
    predicted_df = clean_product_column(predicted_df)

    actual_df["Price (₹)"] = pd.to_numeric(actual_df["Price (₹)"], errors="coerce")
    predicted_df["Predicted Price"] = pd.to_numeric(predicted_df["Predicted Price"], errors="coerce")

    merged = pd.merge(actual_df, predicted_df[["Product", "Predicted Price"]], on="Product", how="inner")
    return merged

def send_email(product, actual, predicted, url):
    subject = f"⚠ Price Drop Alert: {product}"
    body = f"""
 Price Drop Detected!

Product: {product}
Actual Price: ₹{actual:,.0f}
Predicted Price: ₹{predicted:,.0f}
Drop: ₹{predicted - actual:,.0f}

 View Product: {url}
"""

    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

def run_alerts():
    df = load_and_merge()

    #  Debug Print: Show first few rows of merged data
    print(" Checking for price drops...")
    print(df[["Product", "Price (₹)", "Predicted Price"]].head())

    alerts = df[df["Price (₹)"] < df["Predicted Price"]]

    if alerts.empty:
        print(" No price drops detected.")
    else:
        for _, row in alerts.iterrows():
            send_email(row["Product"], row["Price (₹)"], row["Predicted Price"], row["URL"])
        print(f" Sent {len(alerts)} price drop alerts.")

#  Trigger the alert system when script is run directly
if __name__== "__main__":
    run_alerts()