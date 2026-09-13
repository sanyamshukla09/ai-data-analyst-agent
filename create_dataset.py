import pandas as pd
import numpy as np

np.random.seed(42)

n = 1000

products = [
    "Laptop",
    "Smartphone",
    "Headphones",
    "Keyboard",
    "Monitor",
    "Mouse",
    "Tablet",
    "Smartwatch"
]

regions = [
    "North",
    "South",
    "East",
    "West"
]

payment_methods = [
    "Credit Card",
    "Debit Card",
    "UPI",
    "Cash"
]

df = pd.DataFrame({
    "Order_ID": range(10001, 10001 + n),

    "Order_Date": pd.date_range(
        start="2025-01-01",
        periods=n,
        freq="D"
    ).strftime("%Y-%m-%d"),

    "Customer_ID": np.random.randint(
        1001,
        1201,
        n
    ),

    "Product": np.random.choice(
        products,
        n
    ),

    "Region": np.random.choice(
        regions,
        n
    ),

    "Quantity": np.random.randint(
        1,
        6,
        n
    ),

    "Unit_Price": np.random.randint(
        500,
        100000,
        n
    ),

    "Payment_Method": np.random.choice(
        payment_methods,
        n
    )
})

df["Revenue"] = (
    df["Quantity"] * df["Unit_Price"]
)

df["Profit"] = (
    df["Revenue"] * np.random.uniform(
        0.05,
        0.30,
        n
    )
).round(2)

df["Customer_Satisfaction"] = np.random.randint(
    1,
    6,
    n
)

df.to_csv(
    "data/sales_data.csv",
    index=False
)

print("Dataset created successfully!")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")
print("\nSaved to: data/sales_data.csv")