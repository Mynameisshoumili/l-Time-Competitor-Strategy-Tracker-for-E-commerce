import pandas as pd
import joblib
import os

# Load the trained model
model = joblib.load("price_predictor.joblib")

# Define the input file for prediction
file_path = "flipkart_product_details.csv"

# Check if the file exists
if not os.path.exists(file_path):
    print(f" File not found: {file_path}")
else:
    # Load the full data
    full_df = pd.read_csv(file_path)

    # Drop the target column if it exists
    if 'Price (₹)' in full_df.columns:
        full_df = full_df.drop(columns=['Price (₹)'])

    # Keep a copy of original columns for reference (e.g., Category, Brand)
    reference_cols = ['Category', 'Brand', 'Product Name']  # Update based on your actual column names
    reference_df = full_df[reference_cols] if all(col in full_df.columns for col in reference_cols) else full_df.copy()

    # Preprocess the data for prediction
    df = pd.get_dummies(full_df)
    df = df.select_dtypes(include=['number'])

    # Make predictions
    predictions = model.predict(df)

    # Add predictions to the reference DataFrame
    reference_df['Predicted Price'] = predictions

    # Show the first few predictions with categories
    print(reference_df.head())

    # Save predictions to a new file
    reference_df.to_csv("predicted_prices.csv", index=False)
    print(" Predictions saved to 'predicted_prices.csv'")