"""
ETL Pipeline — Extract, Transform, Load features for ML training.
Refactored to use config-based paths and ORM.
"""

import pandas as pd
import logging
from datetime import date, timedelta
from pathlib import Path

from config import PROCESSED_DIR
from db.models import get_session, Transaction, InventoryBatch, Product

logger = logging.getLogger(__name__)


def extract(session=None) -> pd.DataFrame:
    """
    Extract transaction data from the database.

    Returns:
        DataFrame with transaction records joined with product info.
    """
    if session is None:
        session = get_session()

    try:
        query = (
            session.query(
                Transaction.transaction_id,
                Transaction.product_id,
                Transaction.quantity_sold,
                Transaction.sale_price,
                Transaction.original_price,
                Transaction.discount_pct,
                Transaction.sale_date,
                Product.name.label("product_name"),
                Product.category,
                Product.base_price,
            )
            .join(Product, Transaction.product_id == Product.product_id)
        )

        df = pd.read_sql(query.statement, session.bind)
        output_path = PROCESSED_DIR / "features.parquet"
        df.to_parquet(output_path, index=False)
        logger.info(f"Extraction complete — {len(df)} records → {output_path}")
        return df

    finally:
        session.close()


def transform(df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Transform extracted data: add time features, clean nulls.

    Args:
        df: Optional DataFrame. If None, reads from extracted parquet.

    Returns:
        Transformed DataFrame with ML-ready features.
    """
    if df is None:
        df = pd.read_parquet(PROCESSED_DIR / "features.parquet")

    # Parse dates
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    # Time-based features
    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["week_of_year"] = df["sale_date"].dt.isocalendar().week.astype(int)

    # Category encoding
    df["category_encoded"] = df["category"].astype("category").cat.codes

    # Fill nulls
    df = df.fillna(0)

    output_path = PROCESSED_DIR / "features_transformed.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Transformation complete — {len(df)} records → {output_path}")
    return df


def load_features(df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Load final features ready for ML model training.

    Args:
        df: Optional DataFrame. If None, reads from transformed parquet.

    Returns:
        Final feature DataFrame.
    """
    if df is None:
        df = pd.read_parquet(PROCESSED_DIR / "features_transformed.parquet")

    # Select ML features
    feature_columns = [
        "product_id", "quantity_sold", "sale_price", "original_price",
        "discount_pct", "day_of_week", "month", "is_weekend",
        "week_of_year", "category_encoded", "base_price"
    ]

    # Only keep columns that exist
    available = [c for c in feature_columns if c in df.columns]
    df_features = df[available].copy()

    output_path = PROCESSED_DIR / "final_features.parquet"
    df_features.to_parquet(output_path, index=False)
    logger.info(f"Feature loading complete — {len(df_features)} records → {output_path}")
    return df_features


def run_pipeline():
    """Execute the full ETL pipeline."""
    logger.info("Starting ETL pipeline...")
    df = extract()
    df = transform(df)
    df = load_features(df)
    logger.info("ETL pipeline complete!")
    return df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    run_pipeline()
