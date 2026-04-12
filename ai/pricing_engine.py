"""
AI Dynamic Pricing Engine — Multi-tier discount strategy.
Uses waste risk scoring, demand predictions, and product margins
to compute optimal dynamic prices.
"""

from ml.predict_demand import predict_demand
from ai.waste_risk import compute_waste_risk
from config import MAX_DISCOUNT, CRITICAL_EXPIRY_DAYS, WARNING_EXPIRY_DAYS, MIN_MARGIN
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def dynamic_price(
    stock: int,
    days_to_expiry: int,
    base_price: float,
    total_quantity: int = None,
    category: str = "general",
    min_margin: float = None,
    day_of_week: int = None,
    month: int = None,
    predicted_demand_override: float = None,
) -> dict:
    """
    Compute the optimal dynamic price using multi-tier strategy.

    Strategy tiers:
        1. Critical (risk >= 70): Aggressive discount to clear stock before waste
        2. Warning (risk 40-70): Moderate discount to accelerate sales
        3. Safe (risk < 40): Maintain base price or minimal adjustment

    Args:
        stock: Current remaining stock quantity
        days_to_expiry: Days until batch expires
        base_price: Original price
        total_quantity: Total batch quantity (defaults to stock if not provided)
        category: Product category for perishability weighting
        min_margin: Minimum margin to maintain (overrides config if set)
        day_of_week: Day of week (0=Mon, 6=Sun). Auto-detected if None.
        month: Month number (1-12). Auto-detected if None.
        predicted_demand_override: Pre-computed demand to skip ML call. 

    Returns:
        Dictionary with price, discount, risk info, and reasoning.
    """
    if total_quantity is None:
        total_quantity = stock
    if min_margin is None:
        min_margin = MIN_MARGIN
    if day_of_week is None:
        day_of_week = datetime.today().weekday()
    if month is None:
        month = datetime.today().month

    # ── Step 1: Predict demand ───────────────────────────────────────────
    if predicted_demand_override is not None:
        predicted_demand = predicted_demand_override
    else:
        predicted_demand = predict_demand(
            day_of_week=day_of_week,
            month=month,
            is_weekend=1 if day_of_week >= 5 else 0,
        )

    # ── Step 2: Compute waste risk ───────────────────────────────────────
    risk = compute_waste_risk(
        days_to_expiry=days_to_expiry,
        remaining_quantity=stock,
        total_quantity=total_quantity,
        predicted_demand=predicted_demand,
        category=category,
    )

    # ── Step 3: Determine discount tier ──────────────────────────────────
    risk_score = risk["overall_score"]
    risk_level = risk["risk_level"]

    if risk_level == "critical":
        # Aggressive — scale discount with risk severity
        if risk_score >= 85:
            discount = min(MAX_DISCOUNT, 0.40 + (risk_score - 85) * 0.007)
        else:
            discount = 0.25 + (risk_score - 70) * 0.01
    elif risk_level == "warning":
        # Moderate — proportional to risk
        discount = 0.05 + (risk_score - 40) * 0.006
    else:
        # Safe — no or minimal discount
        if days_to_expiry <= WARNING_EXPIRY_DAYS and stock > predicted_demand * 1.5:
            discount = 0.03  # Nudge pricing
        else:
            discount = 0.0

    # ── Step 4: Apply margin floor ───────────────────────────────────────
    max_allowed_discount = 1.0 - min_margin
    discount = min(discount, max_allowed_discount)
    discount = round(discount, 4)

    # ── Step 5: Compute final price ──────────────────────────────────────
    final_price = round(base_price * (1 - discount), 2)

    # ── Step 6: Determine revenue impact ─────────────────────────────────
    potential_revenue_saved = round(stock * (base_price - final_price), 2)

    result = {
        "final_price": final_price,
        "base_price": base_price,
        "discount_pct": round(discount * 100, 1),
        "predicted_demand": round(predicted_demand, 1),
        "waste_risk": risk,
        "potential_revenue_at_risk": round(stock * base_price, 2),
        "estimated_clearance_value": round(stock * final_price, 2),
        "reasoning": _build_reasoning(risk_level, discount, days_to_expiry, stock, predicted_demand),
    }

    logger.info(
        f"Dynamic price: ₹{base_price} → ₹{final_price} "
        f"({discount*100:.1f}% off | risk={risk_score} [{risk_level}])"
    )
    return result


def dynamic_price_simple(stock: int, days_to_expiry: int, base_price: float) -> float:
    """
    Backward-compatible simple pricing.
    Returns only the final price as a float.
    """
    result = dynamic_price(stock=stock, days_to_expiry=days_to_expiry, base_price=base_price)
    return result["final_price"]


def _build_reasoning(risk_level: str, discount: float, days_to_expiry: int, stock: int, demand: float) -> str:
    """Generate human-readable pricing reasoning."""
    parts = []

    if risk_level == "critical":
        parts.append(f"⚠️ CRITICAL: Only {days_to_expiry} day(s) to expiry with {stock} units remaining.")
        parts.append(f"Predicted demand is only {demand:.0f} units — aggressive pricing applied.")
    elif risk_level == "warning":
        parts.append(f"⚡ WARNING: {days_to_expiry} days to expiry, {stock} units in stock.")
        parts.append(f"Demand forecast ({demand:.0f}) suggests moderate discount needed.")
    else:
        if discount > 0:
            parts.append(f"✅ Product is moving well but slight stock surplus detected.")
        else:
            parts.append(f"✅ No pricing action needed — demand ({demand:.0f}) aligns with stock ({stock}).")

    if discount > 0:
        parts.append(f"Applied {discount*100:.1f}% discount to optimize sell-through.")

    return " ".join(parts)
