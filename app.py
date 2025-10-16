import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import difflib
import price_alerts

st.set_page_config(page_title="📦 Flipkart Insights", layout="wide")

# Load data
products_df = pd.read_csv("data/flipkart_product_details.csv")
predicted_df = pd.read_csv("data/predicted_prices.csv")
reviews_df = pd.read_csv("data/reviews_with_sentiment.csv")

# Clean product names
def clean_names(df):
    df["Product"] = df["Product"].astype(str).str.strip().str.replace("\u00a0", " ", regex=True)
    return df

products_df = clean_names(products_df)
predicted_df = clean_names(predicted_df)

# Fix column names in reviews_df
if "ProductName" in reviews_df.columns and "Product" not in reviews_df.columns:
    reviews_df.rename(columns={"ProductName": "Product"}, inplace=True)
if "ReviewText" in reviews_df.columns and "review" not in reviews_df.columns:
    reviews_df.rename(columns={"ReviewText": "review"}, inplace=True)
if "Product" in reviews_df.columns:
    reviews_df["Product"] = reviews_df["Product"].astype(str).str.strip()
else:
    st.error("❌ 'Product' column not found in reviews_with_sentiment.csv")
    st.stop()

# Merge actual and predicted prices
merged_df = pd.merge(products_df, predicted_df[["Product", "Predicted Price"]], on="Product", how="left")
product_list = sorted(merged_df["Product"].dropna().unique())

# Sidebar
with st.sidebar:
    st.markdown("<h3 style='color:#2c3e50;'>🔍 Product Explorer</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:14px;color:#7f8c8d;'>Explore pricing, sentiment, and trends for Flipkart products.</p>", unsafe_allow_html=True)

    product_name = st.selectbox("Select a product to analyze", options=product_list)
    price_toggle = st.radio("Price View", ["Actual Price", "Predicted Price"])

    selected_row = merged_df[merged_df["Product"] == product_name].iloc[0]
    if "Image_URL" in selected_row and pd.notna(selected_row["Image_URL"]):
        st.image(selected_row["Image_URL"], caption=product_name, use_column_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    if st.button("📩 Send Price Drop Alert for Selected Product"):
        try:
            price_alerts.run_alerts(product_name)
            st.success(f"✅ Alert sent for: {product_name}")
        except Exception as e:
            st.error(f"❌ Failed to send alert: {e}")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Product Analysis", "📉 Competitor Comparison", "📈 Market Overview"])

# ---------------------- TAB 1 ----------------------
with tab1:
    st.markdown("<h3 style='color:#34495e;'>📊 Product Analysis</h3>", unsafe_allow_html=True)

    selected_row = merged_df[merged_df["Product"] == product_name].iloc[0]

    # Layout: Left for insights, right for image
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown(f"<h4 style='color:#2c3e50;'>📦 Insights for: {selected_row['Product']}</h4>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            price_label = "💰 Actual Price" if price_toggle == "Actual Price" else "🔮 Predicted Price"
            price_value = selected_row['Price (₹)'] if price_toggle == "Actual Price" else selected_row['Predicted Price']
            st.metric(price_label, f"₹{price_value:,.0f}")
        with col2:
            st.metric("📉 Discount", f"{selected_row['Discount (%)']}%")
        with col3:
            st.metric("⭐ Rating", f"{selected_row['Rating']}")

        st.markdown(f"<a href='{selected_row['URL']}' target='_blank'>🔗 View on Flipkart</a>", unsafe_allow_html=True)

    with col_right:
        if "Image_URL" in selected_row and pd.notna(selected_row["Image_URL"]):
            st.image(selected_row["Image_URL"], caption="Product Preview", use_column_width=True)
        else:
            st.markdown("📷 No image available")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 📈 Price Trend Chart
    st.markdown("<h4 style='color:#2c3e50;'>📈 Price Trend Forecast</h4>", unsafe_allow_html=True)
    years = [2015, 2016, 2017, 2018, 2019, 2020]
    historical_prices = [selected_row['Price (₹)'] * (1.1 - 0.03 * i) for i in range(len(years))]
    predicted_price = selected_row['Predicted Price']

    trend_df = pd.DataFrame({
        "Year": years,
        "Historical Price": historical_prices
    })

    fig = px.line(trend_df, x="Year", y="Historical Price", markers=True, title="Price Trend for Selected Product")
    fig.add_scatter(x=[2021], y=[predicted_price], mode="markers+text", name="Predicted Price",
                    marker=dict(color="red", size=12), text=["Predicted"], textposition="top center")
    fig.update_layout(height=400, margin=dict(t=30, b=20), title_font=dict(size=18))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # 🧠 Sentiment Analysis
    st.markdown("<h4 style='color:#2c3e50;'>🧠 Customer Sentiment</h4>", unsafe_allow_html=True)
    match = difflib.get_close_matches(product_name, reviews_df["Product"].unique(), n=1, cutoff=0.6)
    if match:
        matched_product = match[0]
        filtered_reviews = reviews_df[reviews_df["Product"] == matched_product]
        avg_score = filtered_reviews["sentiment_score"].mean()
        st.metric("🧠 Avg Sentiment Score", f"{avg_score:.2f}")
        st.caption(f"Matched review product: {matched_product}")

        col1, col2 = st.columns([1.2, 1])
        with col1:
            st.markdown("<h5 style='color:#2c3e50;'>📋 Sample Reviews by Sentiment</h5>", unsafe_allow_html=True)
            sentiment_table = (
                filtered_reviews.groupby("sentiment")
                .apply(lambda df: df[["review", "Rating", "sentiment_score"]].head(2))
                .reset_index(level=0)
                .rename(columns={"sentiment": "Sentiment", "review": "Review", "Rating": "Rating", "sentiment_score": "Score"})
            )
            st.dataframe(sentiment_table, use_container_width=True)

        with col2:
            st.markdown("<h5 style='color:#2c3e50;'>📊 Sentiment Distribution</h5>", unsafe_allow_html=True)
            sentiment_counts = filtered_reviews["sentiment"].value_counts().reset_index()
            sentiment_counts.columns = ["Sentiment", "Count"]
            color_map = {
                "Positive": "#a3c1ad",
                "Neutral": "#d5c9a3",
                "Negative": "#b0b0b0"
            }
            fig = px.pie(sentiment_counts, names="Sentiment", values="Count", color="Sentiment", color_discrete_map=color_map)
            fig.update_traces(textinfo='percent+label', pull=[0.05, 0.02, 0])
            fig.update_layout(margin=dict(t=20, b=20), height=300)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<h5 style='color:#2c3e50;'>📥 Export Filtered Reviews</h5>", unsafe_allow_html=True)
        csv = filtered_reviews.to_csv(index=False).encode("utf-8")
        st.download_button("Download Reviews", data=csv, file_name="filtered_reviews.csv", mime="text/csv")
    else:
        st.warning("No matching reviews found.")
# ---------------------- TAB 2 ----------------------
with tab2:
    st.markdown("<h3 style='color:#34495e;'>📉 Competitor Comparison</h3>", unsafe_allow_html=True)
    competitors = merged_df[merged_df["Product"].str.contains(product_name.split()[0], case=False, na=False)]
    if not competitors.empty:
        chart_df = competitors[["Product", "Price (₹)"]].dropna().sort_values(by="Price (₹)", ascending=True)
        fig = px.bar(chart_df, x="Price (₹)", y="Product", orientation="h", color="Price (₹)", color_continuous_scale="Blues")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<h5 style='color:#2c3e50;'>📋 Detailed Competitor Table</h5>", unsafe_allow_html=True)
        st.dataframe(competitors[["Product", "Discount (%)", "Rating", "Predicted Price", "URL"]])
    else:
        st.warning("🚫 No competitor data found.")
#---------------------- TAB 3 ----------------------
with tab3:
    st.markdown("<h3 style='color:#34495e;'>📈 Market Overview</h3>", unsafe_allow_html=True)

    # Filter valid data
    plot_df = merged_df[
        merged_df["Price (₹)"].notna() &
        merged_df["Rating"].notna() &
        (merged_df["Price (₹)"] > 0) &
        (merged_df["Rating"] > 0)
    ].copy()

    # Extract brand from product name
    plot_df["Brand"] = plot_df["Product"].str.extract(r'^(Apple|Samsung|MOTOROLA|Google|vivo|OPPO|realme)', expand=False)

    if not plot_df.empty:
        # Scatter Plot: Price vs Rating
        st.markdown("<h5 style='color:#2c3e50;'>📌 Price vs Rating (Scatter Plot)</h5>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.scatterplot(data=plot_df, x="Price (₹)", y="Rating", hue="Brand", ax=ax, palette="Set2", s=60)
        ax.set_title("Price vs Rating by Brand", fontsize=14)
        ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
        st.pyplot(fig)

        st.markdown("<hr>", unsafe_allow_html=True)

        # Box Plot: Price Distribution
        st.markdown("<h5 style='color:#2c3e50;'>📦 Price Distribution by Brand</h5>", unsafe_allow_html=True)
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        sns.boxplot(data=plot_df, x="Brand", y="Price (₹)", palette="pastel")
        ax2.set_title("Price Range Across Brands", fontsize=14)
        ax2.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
        st.pyplot(fig2)
    else:
        st.warning("🚫 No valid data available for market overview.")