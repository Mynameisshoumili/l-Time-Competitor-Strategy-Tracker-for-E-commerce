# trend_detection.py
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

def detect_trends(review_file):
    df = pd.read_csv(review_file)
    vectorizer = CountVectorizer(stop_words='english', max_features=20)
    X = vectorizer.fit_transform(df['review_text'])
    keywords = vectorizer.get_feature_names_out()
    print("Top keywords in reviews:", keywords)

if __name__ == "__main__":
    detect_trends("flipkart_reviews_unique.csv")