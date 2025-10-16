from transformers import pipeline
import pandas as pd
import os

# Define label mapping for the CardiffNLP sentiment model
label_map = {
    'LABEL_0': 'Negative',
    'LABEL_1': 'Neutral',
    'LABEL_2': 'Positive'
}

def analyze_sentiment(review_file="data/flipkart_reviews_unique.csv", output_file="data/reviews_with_sentiment.csv"):
    # Check if the input file exists
    if not os.path.exists(review_file):
        raise FileNotFoundError(f"❌ File not found: {review_file}")

    # Load the review data
    df = pd.read_csv(review_file)

    # Check if required column exists
    if "ReviewText" not in df.columns:
        raise ValueError("❌ 'ReviewText' column not found in input file.")

    # Load the sentiment analysis model
    sentiment_model = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

    # Apply sentiment analysis in batch
    results = sentiment_model(df["ReviewText"].tolist(), batch_size=32)

    # Extract sentiment label and score
    df["sentiment"] = [label_map[r["label"]] for r in results]
    df["sentiment_score"] = [r["score"] for r in results]

    # Save the full DataFrame with readable sentiment labels and scores
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ Sentiment analysis saved to '{output_file}' with labels and scores")

    return df

if __name__ == "__main__":
    result_df = analyze_sentiment()
    print(result_df[["ReviewText", "sentiment", "sentiment_score"]].head())