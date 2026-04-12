"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


# ── Request Schemas ──────────────────────────────────────────────────────────

class PriceCalculateRequest(BaseModel):
    """Request body for dynamic price calculation."""
    stock: int = Field(..., ge=0, description="Current stock quantity")
    days_to_expiry: int = Field(..., ge=0, description="Days until batch expires")
    base_price: float = Field(..., gt=0, description="Original product price")
    category: str = Field(default="general", description="Product category")
    total_quantity: Optional[int] = Field(None, ge=0, description="Total batch quantity")
    min_margin: Optional[float] = Field(None, ge=0, le=1, description="Minimum margin (0-1)")


# ── Response Schemas ─────────────────────────────────────────────────────────

class WasteRiskFactors(BaseModel):
    expiry_urgency: float
    stock_surplus: float
    category_perishability: float
    inventory_utilization: float


class WasteRiskResponse(BaseModel):
    overall_score: float
    risk_level: str
    factors: WasteRiskFactors
    recommendation: str


class PriceCalculateResponse(BaseModel):
    final_price: float
    base_price: float
    discount_pct: float
    predicted_demand: float
    waste_risk: WasteRiskResponse
    potential_revenue_at_risk: float
    estimated_clearance_value: float
    reasoning: str


class ProductResponse(BaseModel):
    product_id: int
    name: str
    category: str
    base_price: float
    unit: str
    min_margin: float


class InventoryBatchResponse(BaseModel):
    batch_id: int
    product_id: int
    product_name: str
    category: str
    quantity: int
    remaining_quantity: int
    expiry_date: str
    days_to_expiry: int
    status: str
    arrival_date: str
    waste_risk_score: Optional[float] = None
    risk_level: Optional[str] = None


class TransactionResponse(BaseModel):
    transaction_id: int
    product_name: str
    category: str
    quantity_sold: int
    sale_price: float
    original_price: Optional[float]
    discount_pct: float
    sale_date: str


class AlertResponse(BaseModel):
    batch_id: int
    product_name: str
    category: str
    remaining_quantity: int
    days_to_expiry: int
    risk_level: str
    risk_score: float
    recommendation: str
    current_price: float
    suggested_price: float


class WasteAnalytics(BaseModel):
    total_waste_quantity: int
    total_value_lost: float
    waste_by_category: dict
    waste_by_reason: dict
    recent_waste: List[dict]


class RevenueAnalytics(BaseModel):
    total_revenue: float
    total_savings: float
    avg_discount: float
    transactions_with_discount: int
    total_transactions: int
    daily_revenue: List[dict]
    category_revenue: dict


class DashboardOverview(BaseModel):
    total_products: int
    active_batches: int
    near_expiry_count: int
    total_revenue: float
    total_waste_value: float
    revenue_recovered: float
    avg_waste_risk: float
    critical_alerts: int
    total_transactions: int = 0
    avg_risk_score: float = 0.0
