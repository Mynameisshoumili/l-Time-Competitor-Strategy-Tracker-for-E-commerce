import pandas as pd

# Load your dataset
df = pd.read_csv("flipkart_product_details.csv")
df = df.fillna("N/A")

# Confirm the product name column
name_column = 'Product'

# Show sample product names to guide your search
print(f"\n🧾 Sample product names from '{name_column}':\n")
sample_names = df[name_column].dropna().unique()[:20]  # Show first 20 unique names
for i, name in enumerate(sample_names, 1):
    print(f"{i}. {name}")

# Ask for product name to search
product_name = input(f"\n🔍 Enter product name to search from above list or partial keyword: ").strip().lower()


# Filter rows where product name contains the search term (disable regex)
filtered_df = df[df[name_column].str.lower().str.contains(product_name, regex=False)]


# Display results
if filtered_df.empty:
    print("❌ No matching product found.")
else:
    display_cols = [name_column, 'Category', 'Price (₹)', 'Discount (%)', 'Rating', 'URL']
    available_cols = [col for col in display_cols if col in df.columns]

    print("\n📦 Matching Product Details:\n")
    print(filtered_df[available_cols].to_string(index=False))