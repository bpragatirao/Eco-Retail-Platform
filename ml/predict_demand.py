"""
Demand prediction module.
Loads the trained model and predicts demand for given features.
"""

import joblib
import pandas as pd
import logging
from pathlib import Path

from config import MODEL_PATH

logger = logging.getLogger(__name__)

# Feature columns the model was trained on (must match train_model.py)
DEFAULT_FEATURES = ["day_of_week", "month", "is_weekend", "week_of_year", "category_encoded", "base_price"]

# Cache the model in memory after first load
_model_cache = None


def _load_model():
    """Load model with caching to avoid repeated disk reads."""
    global _model_cache
    if _model_cache is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Run `python -m ml.train_model` to train first."
            )
        _model_cache = joblib.load(MODEL_PATH)
        logger.info(f"Model loaded from {MODEL_PATH}")
    return _model_cache


def predict_demand(
    day_of_week: int,
    month: int = 1,
    is_weekend: int = 0,
    week_of_year: int = 1,
    category_encoded: int = 0,
    base_price: float = 50.0,
) -> float:
    """
    Predict demand using the trained model.

    Args:
        day_of_week: 0=Monday ... 6=Sunday
        month: 1-12
        is_weekend: 0 or 1
        week_of_year: 1-52
        category_encoded: integer category code
        base_price: product base price

    Returns:
        Predicted demand quantity (float).
    """
    model = _load_model()

    features = {
        "day_of_week": day_of_week,
        "month": month,
        "is_weekend": is_weekend,
        "week_of_year": week_of_year,
        "category_encoded": category_encoded,
        "base_price": base_price,
    }

    # Use only features the model knows (handle models trained with fewer features)
    try:
        expected_features = model.feature_names_in_.tolist()
    except AttributeError:
        # Older models may not have feature_names_in_
        expected_features = DEFAULT_FEATURES

    X = pd.DataFrame([{k: features.get(k, 0) for k in expected_features}])
    prediction = model.predict(X)[0]

    logger.info(f"Predicted demand: {prediction:.2f} (features: {features})")
    return float(max(0, prediction))


def predict_demand_simple(day_of_week: int) -> float:
    """
    Backward-compatible simple prediction using only day_of_week.
    Kept for legacy compatibility.
    """
    return predict_demand(
        day_of_week=day_of_week,
        is_weekend=1 if day_of_week >= 5 else 0,
    )
