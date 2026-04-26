import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Generate realistic date range (18 months of historical data)
end_date = datetime.now() - timedelta(days=1)  # Yesterday
start_date = end_date - timedelta(days=540)  # 18 months ago

# Generate 1000 transactions
num_records = 1000

data = {
    "order_id": range(1, num_records + 1),
    "customer_id": np.random.randint(1, 200, num_records),
    "product_id": np.random.randint(1, 100, num_records),
    "order_date": pd.date_range(start=start_date, end=end_date, periods=num_records),
    "product_category": np.random.choice(["Electronics", "Clothing", "Home", "Books", "Sports"], num_records),
    "product_name": np.random.choice([
        "Laptop", "Smartphone", "Headphones", "T-Shirt", "Jeans", 
        "Sofa", "Table Lamp", "Novel", "Football", "Yoga Mat"
    ], num_records),
    "quantity": np.random.randint(1, 5, num_records),
    "unit_price": np.random.randint(100, 1000, num_records)
}

df = pd.DataFrame(data)
df["total_price"] = df["quantity"] * df["unit_price"]

# Sort by date
df = df.sort_values('order_date').reset_index(drop=True)

# Save to CSV
df.to_csv("ecommerce_data.csv", index=False)

print(f"✅ Dataset created successfully!")
print(f"📊 Records: {len(df)}")
print(f"📅 Date Range: {df['order_date'].min().date()} to {df['order_date'].max().date()}")
print(f"💰 Total Sales: ₹{df['total_price'].sum():,.2f}")