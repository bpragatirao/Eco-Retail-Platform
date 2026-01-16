import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
import os

os.makedirs("eco-retail-platform/ml", exist_ok=True)

df = pd.read_parquet("eco-retail-platform/data/processed/final_features.parquet")

print(df.head())
print("Shape:", df.shape)

# ---- SAFETY CHECK ----
if df.empty:
    raise ValueError("Training data is empty. Check ETL pipeline and database.")

X = df[["day_of_week"]]
y = df["quantity_sold"]

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)

joblib.dump(model, "eco-retail-platform/ml/demand_model.pkl")
print("Model trained and saved")
