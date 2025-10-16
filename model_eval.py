# model_eval.py

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import os

# Define the path to your dataset and model
data_path = "flipkart_product_details.csv"
model_path = "price_predictor.joblib"

# Check if both files exist
if not os.path.exists(data_path):
    print(f"❌ Dataset not found: {data_path}")
elif not os.path.exists(model_path):
    print(f"❌ Model file not found: {model_path}")
else:
    # Load the dataset
    df = pd.read_csv(data_path)

    # Drop rows with missing target values
    df = df.dropna(subset=['Price (₹)'])

    # Fill missing feature values
    df = df.fillna(0)

    # Drop target and optional 'date' column
    drop_cols = ['Price (₹)']
    if 'date' in df.columns:
        drop_cols.append('date')

    # Prepare features and target
    X = df.drop(columns=drop_cols)
    y = df['Price (₹)']

    # Encode categorical features
    X = pd.get_dummies(X)
    X = X.select_dtypes(include=['number'])

    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Load the trained model
    model = joblib.load(model_path)

    # Make predictions on the test set
    y_pred = model.predict(X_test)

    # Evaluate the model
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    # Print evaluation results
    print(f"📊 R² Score: {r2:.4f}")
    print(f"📉 Mean Absolute Error: ₹{mae:.2f}")