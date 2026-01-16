import pandas as pd

df = pd.read_parquet("eco-retail-platform/data/processed/features_transformed.parquet")
df.to_parquet("eco-retail-platform/data/processed/final_features.parquet", index=False)

print("Features ready for ML.")
