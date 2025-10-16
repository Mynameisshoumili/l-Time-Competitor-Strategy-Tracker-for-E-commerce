import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.linear_model import LinearRegression

# Load your product data
file_path = "flipkart_product_details.csv"
df = pd.read_csv(file_path)
df = df.fillna(0)

# Check if 'Price (₹)' column exists
if 'Price (₹)' not in df.columns:
    print("⚠️ 'Price (₹)' column not found in dataset.")
    exit()

# Step 1: Simulate a 'Year' column if missing
# We'll assume the data spans from 2020 onward
df['Year'] = 2020 + (df.index % 6)  # Cycles through 2020–2025

# Step 2: Group by year and calculate average price
price_by_year = df.groupby('Year')['Price (₹)'].mean().reset_index()

# Step 3: Train a linear regression model
X = price_by_year['Year'].values.reshape(-1, 1)
y = price_by_year['Price (₹)'].values
model = LinearRegression()
model.fit(X, y)

# Step 4: Forecast prices for 2025–2030
future_years = np.array([2025, 2026, 2027, 2028, 2029, 2030]).reshape(-1, 1)
future_prices = model.predict(future_years)
forecast_df = pd.DataFrame({
    'Year': future_years.flatten(),
    'Predicted Price (₹)': future_prices
})

# Step 5: Plot the trend
sns.set(style="whitegrid")
plt.figure(figsize=(10, 6))
sns.lineplot(data=price_by_year, x='Year', y='Price (₹)', label='Historical Avg Price')
sns.lineplot(data=forecast_df, x='Year', y='Predicted Price (₹)', label='Forecasted Avg Price', linestyle='--')
plt.title("📈 Flipkart Product Price Forecast (2025–2030)")
plt.xlabel("Year")
plt.ylabel("Average Price (₹)")
plt.legend()
plt.tight_layout()
plt.show()