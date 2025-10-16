# Import necessary libraries
import pandas as pd  # For data loading and manipulation
from sklearn.model_selection import train_test_split  # For splitting data into training and testing sets
from sklearn.ensemble import RandomForestRegressor  # The machine learning model used for price prediction
import joblib  # For saving the trained model to disk
import os  # For checking if the input file exists

# Define the function to train the price prediction model
def train_price_model(df, target_col='Price (₹)'):
    print(f"📊 Initial rows in dataset: {len(df)}")  # Show how many rows were loaded

    # Drop rows where the target column (Price) is missing
    df = df.dropna(subset=[target_col])
    print(f"✅ Rows after dropping missing target values: {len(df)}")

    # Fill missing values in other columns with 0 to avoid errors during training
    df = df.fillna(0)

    # Prepare a list of columns to drop: the target column and optionally 'date' if it exists
    drop_cols = [target_col]
    if 'date' in df.columns:
        drop_cols.append('date')

    # Create feature matrix X by dropping target and date columns
    X = df.drop(columns=drop_cols)

    # Create target vector y using the specified target column
    y = df[target_col]

    # Convert categorical features to numeric using one-hot encoding
    X = pd.get_dummies(X)

    # Ensure only numeric columns are used for training
    X = X.select_dtypes(include=['number'])

    # Check if there's any data left to train on
    if len(X) == 0 or len(y) == 0:
        raise ValueError("❌ No data available for training after preprocessing.")

    print(f"🧠 Training on {len(X)} samples with {X.shape[1]} features...")

    # Split the data into training and testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Initialize the Random Forest Regressor model
    model = RandomForestRegressor()

    # Train the model using the training data
    model.fit(X_train, y_train)

    # Save the trained model to a file for future use
    joblib.dump(model, "price_predictor.joblib")
    print("✅ Model trained and saved successfully.")

    # Return the trained model object
    return model

# Main block: runs only when the script is executed directly
if __name__ == "__main__":
    file_path = "flipkart_product_details.csv"  # Path to your dataset file

    # Check if the file exists before proceeding
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
    else:
        try:
            # Load the dataset into a DataFrame
            df = pd.read_csv(file_path)

            # Call the training function with the loaded data
            train_price_model(df, target_col='Price (₹)')
        except Exception as e:
            # Catch and print any errors that occur during training
            print(f"⚠️ Error during training: {e}")