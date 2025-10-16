import pandas as pd

def load_csv_files(competitor_file: str, review_file: str):
    """
    Reads competitor and review CSV files into Pandas DataFrames.

    Args:
        competitor_file (str): Path to competitor CSV
        review_file (str): Path to review CSV

    Returns:
        tuple: (competitor_df, review_df)
    """
    # Read competitor history
    competitor_df = pd.read_csv(competitor_file)
    if 'date' in competitor_df.columns:
        competitor_df['date'] = pd.to_datetime(competitor_df['date'], errors='coerce')

    # Read reviews
    review_df = pd.read_csv(review_file)
    if 'date' in review_df.columns:
        review_df['date'] = pd.to_datetime(review_df['date'], errors='coerce')

    return competitor_df, review_df

if __name__ == "__main__":
    comp_df, rev_df = load_csv_files("flipkart_product_details.csv", "flipkart_reviews_unique.csv")

    print("Competitor Data:")
    print(comp_df.to_string(index=False), "\n")  # Show all rows

    print("Review Data:")
    print(rev_df.to_string(index=False))         # Show all rows