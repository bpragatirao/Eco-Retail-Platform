import pandas as pd

df = pd.read_parquet("eco-retail-platform/data/processed/features.parquet")

df["sale_date"] = pd.to_datetime(df["sale_date"])
df["day_of_week"] = df["sale_date"].dt.dayofweek
df = df.fillna(0)

df.to_parquet("eco-retail-platform/data/processed/features_transformed.parquet", index=False)
print("Transformation complete")
