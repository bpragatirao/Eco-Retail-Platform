"""
Waste Risk Scoring System.
Computes a 0-100 risk score for each product/batch based on multiple factors.
"""

import logging
from datetime import date

logger = logging.getLogger(__name__)


def compute_waste_risk(
    days_to_expiry: int,
    remaining_quantity: int,
    total_quantity: int,
    predicted_demand: float,
    category: str = "general",
) -> dict:
    """
    Compute a waste risk score (0-100) based on multiple factors.

    Factors:
        - Expiry urgency (40% weight): How close is the expiry date?
        - Stock surplus (30% weight): Remaining vs predicted demand ratio
        - Category perishability (15% weight): Some categories spoil faster
        - Inventory utilization (15% weight): How much of the batch is still unsold?

    Args:
        days_to_expiry: Days until the batch expires
        remaining_quantity: Units still in stock
        total_quantity: Total units in the original batch
        predicted_demand: ML-predicted demand for this product
        category: Product category

    Returns:
        Dictionary with overall score, individual factor scores, and risk level.
    """
    # ── Factor 1: Expiry Urgency (0-100) ─────────────────────────────────
    if days_to_expiry <= 0:
        expiry_score = 100.0
    elif days_to_expiry <= 1:
        expiry_score = 95.0
    elif days_to_expiry <= 3:
        expiry_score = 75.0
    elif days_to_expiry <= 7:
        expiry_score = 40.0
    elif days_to_expiry <= 14:
        expiry_score = 15.0
    else:
        expiry_score = 5.0

    # ── Factor 2: Stock Surplus (0-100) ──────────────────────────────────
    if predicted_demand <= 0:
        surplus_score = 90.0
    else:
        surplus_ratio = remaining_quantity / predicted_demand
        if surplus_ratio > 3.0:
            surplus_score = 90.0
        elif surplus_ratio > 2.0:
            surplus_score = 70.0
        elif surplus_ratio > 1.5:
            surplus_score = 50.0
        elif surplus_ratio > 1.0:
            surplus_score = 30.0
        else:
            surplus_score = 10.0

    # ── Factor 3: Category Perishability (0-100) ─────────────────────────
    perishability = {
        "dairy": 75.0,
        "produce": 80.0,
        "bakery": 85.0,
        "meat": 90.0,
        "beverages": 30.0,
    }
    category_score = perishability.get(category.lower(), 50.0)

    # ── Factor 4: Inventory Utilization (0-100) ──────────────────────────
    if total_quantity <= 0:
        utilization_score = 50.0
    else:
        unsold_ratio = remaining_quantity / total_quantity
        utilization_score = min(100, unsold_ratio * 100)

    # ── Weighted Composite Score ─────────────────────────────────────────
    overall = (
        expiry_score * 0.40 +
        surplus_score * 0.30 +
        category_score * 0.15 +
        utilization_score * 0.15
    )
    overall = round(min(100, max(0, overall)), 1)

    # ── Risk Level ───────────────────────────────────────────────────────
    if overall >= 70:
        risk_level = "critical"
    elif overall >= 40:
        risk_level = "warning"
    else:
        risk_level = "safe"

    result = {
        "overall_score": overall,
        "risk_level": risk_level,
        "factors": {
            "expiry_urgency": round(expiry_score, 1),
            "stock_surplus": round(surplus_score, 1),
            "category_perishability": round(category_score, 1),
            "inventory_utilization": round(utilization_score, 1),
        },
        "recommendation": _get_recommendation(risk_level, overall),
    }

    logger.debug(f"Waste risk computed: {result}")
    return result


def _get_recommendation(risk_level: str, score: float) -> str:
    """Generate a human-readable recommendation based on risk."""
    if risk_level == "critical":
        if score >= 85:
            return "URGENT: Apply maximum discount (40-50%) or consider donation/composting"
        return "Apply significant discount (25-40%) immediately"
    elif risk_level == "warning":
        if score >= 55:
            return "Apply moderate discount (15-25%) to accelerate sales"
        return "Monitor closely and apply small discount (5-15%)"
    else:
        return "No action needed — product is moving well"
