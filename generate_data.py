import pandas as pd
import numpy as np

data = {
    "order_id": range(1, 1001),
    "customer_id": np.random.randint(1, 200, 1000),
    "product_id": np.random.randint(1, 100, 1000),
    "order_date": pd.date_range(start="2023-01-01", periods=1000, freq="D"),
    "product_category": np.random.choice(["Electronics", "Clothing", "Home"], 1000),
    "quantity": np.random.randint(1, 5, 1000),
    "unit_price": np.random.randint(100, 1000, 1000)
}

df = pd.DataFrame(data)
df["total_price"] = df["quantity"] * df["unit_price"]

df.to_csv("ecommerce_data.csv", index=False)

print("Dataset created successfully!")