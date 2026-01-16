import joblib
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def predict_demand(day_of_week: int) -> float:
    model = joblib.load("eco-retail-platform/ml/demand_model.pkl")

    X = pd.DataFrame([[day_of_week]], columns=["day_of_week"])
    prediction = model.predict(X)[0]
    logger.info(f"Predicted demand: {prediction}")

    return float(prediction)

