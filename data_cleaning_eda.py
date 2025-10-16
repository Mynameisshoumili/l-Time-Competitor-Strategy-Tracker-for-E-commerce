import pandas as pd
import matplotlib.pyplot as plt

def basic_cleaning_eda(df_comp, df_rev, show_plots=True, save_plots=False):
    # --- 1. Ensure date columns are datetime ---
    df_comp['date'] = pd.to_datetime(df_comp['date'], errors='coerce')
    df_rev['date'] = pd.to_datetime(df_rev['date'], errors='coerce')

    # --- 2. Sort competitor data by product, competitor, and date ---
    df_comp.sort_values(by=['product_id', 'competitor_id', 'date'], inplace=True)

    # --- 3. Check for missing values ---
    print("Missing values in competitor data:")
    print(df_comp.isnull().sum(), "\n")
    print("Missing values in review data:")
    print(df_rev.isnull().sum(), "\n")

    # --- 4. Basic statistics ---
    print("Competitor price stats:")
    print(df_comp['price'].describe(), "\n")

    # --- 5. Plot price trends per product ---
    for product in df_comp['product_id'].unique():
        product_data = df_comp[df_comp['product_id'] == product]
        plt.figure(figsize=(8,4))
        for comp in product_data['competitor_id'].unique():
            comp_data = product_data[product_data['competitor_id'] == comp]
            plt.plot(comp_data['date'], comp_data['price'], marker='o', label=comp)
        plt.title(f'Price Trend for {product}')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.tight_layout()
        if save_plots:
            plt.savefig(f"price_trend_{product}.png")
            plt.close()
        elif show_plots:
            plt.show()
        else:
            plt.close()

    return df_comp, df_rev

if __name__ == "__main__":
    from data_loader import load_csv_files

    # Load data
    comp_df, rev_df = load_csv_files("flipkart_product_details.csv", "flipkart_reviews_unique.csv")

    # Run cleaning and EDA
    # Option 1: Show plots one by one (default)
    comp_df, rev_df = basic_cleaning_eda(comp_df, rev_df)

    # Option 2: Save plots as images and do not show windows
    # comp_df, rev_df = basic_cleaning_eda(comp_df, rev_df, show_plots=False, save_plots=