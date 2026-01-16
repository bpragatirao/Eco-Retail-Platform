import os
import pandas as pd
from sqlalchemy import create_engine

# Create directory if it doesn't exist
os.makedirs("eco-retail-platform/data/processed", exist_ok=True)

# SQLAlchemy engine
engine = create_engine("postgresql://priyarao:Priya%4015@localhost:5432/retail")

df = pd.read_sql("SELECT * FROM transactions", engine)
df.to_parquet("eco-retail-platform/data/processed/features.parquet", index=False)

print("Extraction complete")
