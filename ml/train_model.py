"""
Multi-feature demand prediction model training with evaluation metrics.
Upgrades the single-feature RandomForest to use time, product, and pricing features.
"""

import pandas as pd
import joblib
import json
import logging
from datetime import datetime
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, root_mean_squared_error

from config import PROCESSED_DIR, MODEL_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ── Feature Configuration ────────────────────────────────────────────────────
FEATURE_COLUMNS = [
    "day_of_week",
    "month",
    "is_weekend",
    "week_of_year",
    "category_encoded",
    "base_price",
]
TARGET_COLUMN = "quantity_sold"


def load_training_data() -> pd.DataFrame:
    """Load the final features from the ETL pipeline."""
    data_path = PROCESSED_DIR / "final_features.parquet"
    df = pd.read_parquet(data_path)

    if df.empty:
        raise ValueError("Training data is empty. Run the ETL pipeline and seed the database first.")

    logger.info(f"Loaded training data: {df.shape[0]} rows, {df.shape[1]} columns")
    logger.info(f"Columns available: {list(df.columns)}")
    return df


def train_model(df: pd.DataFrame) -> dict:
    """
    Train a RandomForest model with evaluation metrics.

    Returns:
        Dictionary with model, metrics, and feature importances.
    """
    # Select available features
    available_features = [c for c in FEATURE_COLUMNS if c in df.columns]
    if not available_features:
        # Fallback to basic feature
        available_features = ["day_of_week"]

    logger.info(f"Training with features: {available_features}")

    X = df[available_features]
    y = df[TARGET_COLUMN]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    metrics = {
        "mae": round(mean_absolute_error(y_test, y_pred), 4),
        "rmse": round(root_mean_squared_error(y_test, y_pred), 4),
        "r2": round(r2_score(y_test, y_pred), 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "features_used": available_features,
    }

    # Feature importance
    importance = dict(zip(available_features, model.feature_importances_.round(4).tolist()))

    logger.info(f"Model evaluation — MAE: {metrics['mae']}, RMSE: {metrics['rmse']}, R²: {metrics['r2']}")
    logger.info(f"Feature importance: {importance}")

    return {
        "model": model,
        "metrics": metrics,
        "feature_importance": importance,
        "features": available_features,
    }


def save_model(result: dict):
    """Save model with versioned filename and metadata."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save the main model (always overwrite the standard path)
    model_path = MODEL_DIR / "demand_model.pkl"
    joblib.dump(result["model"], model_path)
    logger.info(f"Model saved to {model_path}")

    # Save versioned copy
    versioned_path = MODEL_DIR / f"demand_model_{timestamp}.pkl"
    joblib.dump(result["model"], versioned_path)

    # Save metadata alongside the model
    metadata = {
        "version": timestamp,
        "metrics": result["metrics"],
        "feature_importance": result["feature_importance"],
        "features": result["features"],
        "trained_at": datetime.now().isoformat(),
    }
    meta_path = MODEL_DIR / "model_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Model metadata saved to {meta_path}")

    return model_path


def run_training():
    """Execute the full training pipeline."""
    df = load_training_data()
    result = train_model(df)
    save_model(result)
    logger.info("Training pipeline complete!")
    return result


if __name__ == "__main__":
    run_training()
