import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from textblob import TextBlob
from sklearn.linear_model import LinearRegression

# ---------------- Streamlit Page Config ----------------
st.set_page_config(
    page_title="E-Commerce Competitor Strategy Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main-header {font-size:2.3rem;color:#1f77b4;text-align:center;margin-bottom:1rem;}
.section-header {font-size:1.6rem;color:#2e86ab;margin-top:2rem;margin-bottom:1rem;}
.positive-sentiment { color:#28a745; }
.negative-sentiment { color:#dc3545; }
.neutral-sentiment  { color:#ffc107; }
</style>
""", unsafe_allow_html=True)

# ---------------- Competitor Analyzer ----------------
class CompetitorAnalyzer:
    def _init_(self):
        self.products_df = None
        self.reviews_df = None

    def load_data(self,
                  products_file="data/cleaned_mobile.csv",
                  reviews_file="data/cleaned_reviews.csv") -> bool:
        """Load cleaned product & review data"""
        try:
            if os.path.exists(products_file):
                self.products_df = pd.read_csv(products_file)
                # Rename columns to internal standard
                self.products_df.rename(columns={
                    "mobilename": "product_name",
                    "sellingprice": "price",
                    "discountoffering": "discount",
                    "rating": "rating",
                    "productid": "product_id",
                    "source": "source"
                }, inplace=True)
            else:
                st.error(f"Missing {products_file}")
                return False

            if os.path.exists(reviews_file):
                self.reviews_df = pd.read_csv(reviews_file)
                self.reviews_df.rename(columns={
                    "mobilename": "product_name",
                    "review": "review_text",
                    "rating": "rating",
                    "reviewdate": "date",
                    "productid": "product_id",
                    "source": "source"
                }, inplace=True)
            else:
                st.error(f"Missing {reviews_file}")
                return False

            # Clean/convert data
            self.products_df["price"] = pd.to_numeric(
                self.products_df["price"], errors="coerce")
            self.products_df["discount"] = pd.to_numeric(
                self.products_df["discount"], errors="coerce").fillna(0)
            self.products_df["rating"] = pd.to_numeric(
                self.products_df["rating"], errors="coerce").fillna(0)
            self.reviews_df["date"] = pd.to_datetime(
                self.reviews_df["date"], errors="coerce")

            return True
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return False

    # ---------- Analysis Helpers ----------
    def analyze_sentiment(self, text):
        a = TextBlob(str(text))
        p = a.sentiment.polarity
        if p > 0.1:
            return "positive", p
        elif p < -0.1:
            return "negative", p
        else:
            return "neutral", p

    def get_sentiment_analysis(self, product_name):
        df = self.reviews_df[
            self.reviews_df["product_name"] == product_name].copy()
        if df.empty:
            return None
        sentiments = []
        for r in df["review_text"]:
            s, sc = self.analyze_sentiment(r)
            sentiments.append({"sentiment": s, "score": sc})
        s_df = pd.DataFrame(sentiments)
        return {
            "total_reviews": len(df),
            "sentiment_distribution": s_df["sentiment"].value_counts().to_dict(),
            "average_sentiment_score": s_df["score"].mean(),
            "reviews_data": df
        }
    
# ---------------- Dashboard Sections ----------------
def product_analysis(analyzer, product_name):
    st.markdown('<div class="section-header">Product Analysis</div>',
                unsafe_allow_html=True)
    prod = analyzer.products_df.query("product_name == @product_name").iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"₹{int(prod['price'])}")
    c2.metric("Discount", f"{prod['discount']}%")
    c3.metric("Rating", f"{prod['rating']}/5")
    c4.metric("Source", prod["source"])

    # ---- Sentiment ----
    st.subheader("Customer Sentiment")
    sdata = analyzer.get_sentiment_analysis(product_name)
    if sdata:
        col1, col2 = st.columns([2, 1])
        with col1:
            fig = px.pie(values=list(sdata["sentiment_distribution"].values()),
                         names=list(sdata["sentiment_distribution"].keys()),
                         title="Sentiment Distribution")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Total Reviews", sdata["total_reviews"])
            st.metric("Avg Sentiment Score",
                      f"{sdata['average_sentiment_score']:.2f}")
        st.markdown("### Recent Reviews")
        for _, r in sdata["reviews_data"].head(5).iterrows():
            sent, sc = analyzer.analyze_sentiment(r["review_text"])
            with st.expander(f"{r['userid']} - Rating: {r['rating']}"):
                st.write(r["review_text"])
                st.write(f"Sentiment: *{sent}* (score {sc:.2f})")
    else:
        st.info("No reviews available.")

# def competitor_comparison(analyzer, product_name):
#     st.markdown('<div class="section-header">Competitor Comparison</div>',
#                 unsafe_allow_html=True)

#     # --- Competitor data: same source, different product ---
#     source = analyzer.products_df.query(
#         "product_name==@product_name")["source"].iloc[0]
#     comp = analyzer.products_df.query("source==@source and product_name!=@product_name")
#     if comp.empty:
#         st.info("No competitor data available.")
#         return

#     # --- Plot competitor price bar chart ---
#     fig = px.bar(comp, x="product_name", y="price", color="price",
#                  title=f"Competitor Price Comparison ({source})")
#     st.plotly_chart(fig, use_container_width=True)

#     # --- Show competitor table ---
#     st.dataframe(comp[["product_name", "price", "discount", "rating", "url"]])

#     # --- Interactive selection by product ---
#     st.markdown("### Explore Competitors Under Selected Price")
#     selected_product = st.selectbox("Select competitor product", comp["product_name"].unique())

#     if selected_product:
#         selected_price = comp.query("product_name==@selected_product")["price"].values[0]
#         st.markdown(f"*Showing products under ₹{selected_price}*")

#         # 1️⃣ All mobiles under selected price
#         under_price = analyzer.products_df.query("price <= @selected_price").sort_values("price")
#         st.markdown("*All Mobiles Under Selected Price:*")
#         st.dataframe(under_price[["product_name", "source", "price", "discount", "rating", "url"]])

#         # 2️⃣ Different sources for the selected product
#         same_product_sources = analyzer.products_df.query("product_name==@selected_product")
#         st.markdown(f"'{selected_product}' Price & Discount Across Sources:")
#         st.dataframe(same_product_sources[["source", "price", "discount", "rating", "url"]])
def competitor_comparison(analyzer, product_name):
    st.markdown('<div class="section-header">Competitor Comparison</div>',
                unsafe_allow_html=True)

    # --- Competitor data: same source, different product ---
    source = analyzer.products_df.query(
        "product_name==@product_name")["source"].iloc[0]
    comp = analyzer.products_df.query("source==@source and product_name!=@product_name")
    if comp.empty:
        st.info("No competitor data available.")
        return

    # --- Plot competitor price bar chart ---
    fig = px.bar(comp, x="product_name", y="price", color="price",
                 title=f"Competitor Price Comparison ({source})")
    st.plotly_chart(fig, use_container_width=True)

    # --- Show competitor table ---
    st.dataframe(comp[["product_name", "price", "discount", "rating", "url"]])

    # --- Interactive selection by product ---
    st.markdown("### Explore Competitors Near Selected Product Price")
    selected_product = st.selectbox("Select competitor product", comp["product_name"].unique())

    if selected_product:
        selected_price = comp.query("product_name==@selected_product")["price"].values[0]
        st.markdown(f"*Showing products around ₹{selected_price}*")

        # 1️⃣ Define price range ±20% of selected product
        lower_bound = selected_price * 0.8
        upper_bound = selected_price * 1.2

        # 2️⃣ Products within price range
        nearby_products = analyzer.products_df.query(
            "price >= @lower_bound and price <= @upper_bound"
        ).copy()

        # 3️⃣ Add average sentiment score for each product
        sentiment_scores = []
        for prod in nearby_products["product_name"]:
            sentiment_info = analyzer.get_sentiment_analysis(prod)
            if sentiment_info:
                sentiment_scores.append(sentiment_info["average_sentiment_score"])
            else:
                sentiment_scores.append(np.nan)
        nearby_products["avg_sentiment"] = sentiment_scores

        # 4️⃣ Sort by high sentiment first
        nearby_products.sort_values(by="avg_sentiment", ascending=False, inplace=True)

        # 5️⃣ Show table with avg_sentiment before URL
        cols = ["product_name", "source", "price", "discount", "rating", "avg_sentiment", "url"]
        st.dataframe(nearby_products[cols])

        # 6️⃣ Different sources for the selected product
        same_product_sources = analyzer.products_df.query("product_name==@selected_product")
        st.markdown(f"'{selected_product}' Price & Discount Across Sources:")
        st.dataframe(same_product_sources[["source", "price", "discount", "rating", "url"]])

def strategic_recommendations(analyzer, product_name):
    st.markdown('<div class="section-header">Strategic Recommendations</div>',
                unsafe_allow_html=True)

    # Get product info
    prod = analyzer.products_df.query("product_name==@product_name").iloc[0]
    sdata = analyzer.get_sentiment_analysis(product_name)

    # Default sentiment info
    avg_score = sdata["average_sentiment_score"] if sdata else 0
    sentiment_counts = sdata["sentiment_distribution"] if sdata else {}

    # --- Generate Strategy dynamically ---
    strategy_lines = []

    # 1. Pricing strategy
    if prod["price"] > 50000:
        strategy_lines.append(f"- High price detected (₹{prod['price']}). Consider limited-time discounts or EMI options.")
    elif prod["price"] < 20000:
        strategy_lines.append(f"- Competitive price (₹{prod['price']}) can be leveraged with marketing campaigns.")
    
    # 2. Discount analysis
    if prod["discount"] < 5:
        strategy_lines.append(f"- Current discount is low ({prod['discount']}%). Increase discount to attract price-sensitive customers.")
    elif prod["discount"] > 20:
        strategy_lines.append(f"- Generous discount ({prod['discount']}%) observed. Maintain for high conversion or flash sales.")

    # 3. Sentiment-based recommendations
    if avg_score < 0:
        strategy_lines.append("- Customer sentiment is negative. Investigate recurring complaints and improve product/service quality.")
    elif avg_score < 0.2:
        strategy_lines.append("- Customer sentiment is neutral. Consider improving features or adding promotional offers.")
    else:
        strategy_lines.append("- Positive sentiment! Promote product strengths in marketing campaigns.")

    # 4. Review volume insight
    total_reviews = sdata["total_reviews"] if sdata else 0
    if total_reviews < 10:
        strategy_lines.append("- Low review volume. Encourage satisfied customers to leave reviews for social proof.")
    elif total_reviews > 100:
        strategy_lines.append("- High review volume. Analyze reviews for specific improvement areas and feature requests.")

    # 5. Combine all insights
    strategy_text = "\n".join(strategy_lines)

    # --- Display ---
    sentiment_status = "Needs Improvement" if avg_score < 0.2 else "Good" if avg_score < 0.5 else "Excellent"
    sentiment_class = "negative-sentiment" if avg_score < 0.2 else "neutral-sentiment" if avg_score < 0.5 else "positive-sentiment"

    st.markdown(
        f"*Sentiment Status:* <span class='{sentiment_class}'>{sentiment_status}</span>",
        unsafe_allow_html=True
    )

    st.markdown("### Recommended Strategy")
    st.markdown(strategy_text)


# ---------------- Main App ----------------
def main():
    st.markdown('<div class="main-header">E-Commerce Competitor Strategy Dashboard</div>',
                unsafe_allow_html=True)
    analyzer = CompetitorAnalyzer()
    if not analyzer.load_data():
        st.stop()

    # Sidebar navigation
    section = st.sidebar.radio("Navigate",
                               ["Product Analysis",
                                "Competitor Comparison",
                                "Strategic Recommendations"])
    product = st.sidebar.selectbox(
        "Select Product", analyzer.products_df["product_name"].unique())

    if section == "Product Analysis":
        product_analysis(analyzer, product)
    elif section == "Competitor Comparison":
        competitor_comparison(analyzer, product)
    else:
        strategic_recommendations(analyzer, product)


if __name__ == "__main__":
    main()