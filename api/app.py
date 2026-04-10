"""
Eco-Retail Platform — FastAPI Application
Full RESTful API for dynamic pricing, inventory management, and analytics.
"""

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import func

from config import API_HOST, API_PORT, LOG_LEVEL, DASHBOARD_DIR
from db.models import (
    init_db, get_session,
    Product, InventoryBatch, Transaction, PricingHistory, WasteLog
)
from ai.pricing_engine import dynamic_price
from ai.waste_risk import compute_waste_risk
from ml.predict_demand import predict_demand
from api.schemas import (
    PriceCalculateRequest, PriceCalculateResponse,
    ProductResponse, InventoryBatchResponse, TransactionResponse,
    AlertResponse, WasteAnalytics, RevenueAnalytics, DashboardOverview,
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Initialize ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Eco-Retail API",
    description="AI-driven dynamic pricing engine for perishable food waste reduction",
    version="2.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static dashboard files
STATIC_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def startup():
    """Initialize the database on startup."""
    init_db()
    logger.info("Database initialized")


# ── Dashboard Serving ────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serve the main dashboard HTML."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Eco-Retail API v2.0 — visit /docs for API documentation"}


# ── Products ─────────────────────────────────────────────────────────────────

@app.get("/api/products", response_model=List[ProductResponse])
def get_products():
    """Get all products in the catalog."""
    session = get_session()
    try:
        products = session.query(Product).all()
        return [
            ProductResponse(
                product_id=p.product_id,
                name=p.name,
                category=p.category,
                base_price=p.base_price,
                unit=p.unit,
                min_margin=p.min_margin,
            )
            for p in products
        ]
    finally:
        session.close()


# ── Inventory ────────────────────────────────────────────────────────────────

@app.get("/api/inventory", response_model=List[InventoryBatchResponse])
def get_inventory():
    """Get all inventory batches with expiry status and waste risk."""
    session = get_session()
    try:
        batches = (
            session.query(InventoryBatch, Product)
            .join(Product, InventoryBatch.product_id == Product.product_id)
            .filter(InventoryBatch.status == "active")
            .order_by(InventoryBatch.expiry_date.asc())
            .all()
        )

        results = []
        today = date.today()
        for batch, product in batches:
            days_left = (batch.expiry_date - today).days

            # Compute waste risk for each batch
            demand = predict_demand(
                day_of_week=today.weekday(),
                month=today.month,
                is_weekend=1 if today.weekday() >= 5 else 0,
            )
            risk = compute_waste_risk(
                days_to_expiry=days_left,
                remaining_quantity=batch.remaining_quantity,
                total_quantity=batch.quantity,
                predicted_demand=demand,
                category=product.category,
            )

            results.append(InventoryBatchResponse(
                batch_id=batch.batch_id,
                product_id=product.product_id,
                product_name=product.name,
                category=product.category,
                quantity=batch.quantity,
                remaining_quantity=batch.remaining_quantity,
                expiry_date=str(batch.expiry_date),
                days_to_expiry=days_left,
                status=batch.status,
                arrival_date=str(batch.arrival_date),
                waste_risk_score=risk["overall_score"],
                risk_level=risk["risk_level"],
            ))

        return results
    finally:
        session.close()


# ── Dynamic Pricing ──────────────────────────────────────────────────────────

@app.post("/api/price/calculate", response_model=PriceCalculateResponse)
def calculate_price(request: PriceCalculateRequest):
    """Calculate the optimal dynamic price for a product."""
    try:
        result = dynamic_price(
            stock=request.stock,
            days_to_expiry=request.days_to_expiry,
            base_price=request.base_price,
            category=request.category,
            total_quantity=request.total_quantity,
            min_margin=request.min_margin,
        )
        return PriceCalculateResponse(**result)
    except Exception as e:
        logger.error(f"Price calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Alerts ───────────────────────────────────────────────────────────────────

@app.get("/api/alerts", response_model=List[AlertResponse])
def get_alerts():
    """Get near-expiry alerts with risk scores and pricing suggestions."""
    session = get_session()
    try:
        today = date.today()
        threshold = today + timedelta(days=7)

        batches = (
            session.query(InventoryBatch, Product)
            .join(Product, InventoryBatch.product_id == Product.product_id)
            .filter(
                InventoryBatch.status == "active",
                InventoryBatch.expiry_date <= threshold,
                InventoryBatch.remaining_quantity > 0,
            )
            .order_by(InventoryBatch.expiry_date.asc())
            .all()
        )

        alerts = []
        for batch, product in batches:
            days_left = (batch.expiry_date - today).days
            demand = predict_demand(
                day_of_week=today.weekday(),
                month=today.month,
                is_weekend=1 if today.weekday() >= 5 else 0,
            )
            risk = compute_waste_risk(
                days_to_expiry=days_left,
                remaining_quantity=batch.remaining_quantity,
                total_quantity=batch.quantity,
                predicted_demand=demand,
                category=product.category,
            )

            pricing = dynamic_price(
                stock=batch.remaining_quantity,
                days_to_expiry=days_left,
                base_price=product.base_price,
                total_quantity=batch.quantity,
                category=product.category,
            )

            alerts.append(AlertResponse(
                batch_id=batch.batch_id,
                product_name=product.name,
                category=product.category,
                remaining_quantity=batch.remaining_quantity,
                days_to_expiry=days_left,
                risk_level=risk["risk_level"],
                risk_score=risk["overall_score"],
                recommendation=risk["recommendation"],
                current_price=product.base_price,
                suggested_price=pricing["final_price"],
            ))

        return alerts
    finally:
        session.close()


# ── Analytics: Waste ─────────────────────────────────────────────────────────

@app.get("/api/analytics/waste", response_model=WasteAnalytics)
def get_waste_analytics():
    """Get waste analytics — totals, by category, by reason."""
    session = get_session()
    try:
        waste_records = session.query(WasteLog).all()

        total_qty = sum(w.quantity_wasted for w in waste_records)
        total_value = sum(w.value_lost for w in waste_records)

        # By category
        waste_by_cat = {}
        for w in waste_records:
            product = session.query(Product).filter_by(product_id=w.product_id).first()
            cat = product.category if product else "unknown"
            waste_by_cat[cat] = waste_by_cat.get(cat, 0) + w.quantity_wasted

        # By reason
        waste_by_reason = {}
        for w in waste_records:
            waste_by_reason[w.reason] = waste_by_reason.get(w.reason, 0) + w.quantity_wasted

        # Recent waste (last 10)
        recent = sorted(waste_records, key=lambda w: w.waste_date or date.min, reverse=True)[:10]
        recent_data = []
        for w in recent:
            product = session.query(Product).filter_by(product_id=w.product_id).first()
            recent_data.append({
                "product_name": product.name if product else "Unknown",
                "quantity": w.quantity_wasted,
                "value_lost": w.value_lost,
                "date": str(w.waste_date),
                "reason": w.reason,
            })

        return WasteAnalytics(
            total_waste_quantity=total_qty,
            total_value_lost=round(total_value, 2),
            waste_by_category=waste_by_cat,
            waste_by_reason=waste_by_reason,
            recent_waste=recent_data,
        )
    finally:
        session.close()


# ── Analytics: Revenue ───────────────────────────────────────────────────────

@app.get("/api/analytics/revenue", response_model=RevenueAnalytics)
def get_revenue_analytics():
    """Get revenue analytics — totals, daily trends, by category."""
    session = get_session()
    try:
        transactions = session.query(Transaction).all()

        total_revenue = sum(t.sale_price * t.quantity_sold for t in transactions)
        total_savings = sum(
            (t.original_price - t.sale_price) * t.quantity_sold
            for t in transactions
            if t.original_price and t.discount_pct > 0
        )
        discounted_txns = [t for t in transactions if t.discount_pct > 0]
        avg_discount = (
            sum(t.discount_pct for t in discounted_txns) / len(discounted_txns)
            if discounted_txns else 0
        )

        # Daily revenue (last 30 days)
        daily = {}
        for t in transactions:
            day_key = str(t.sale_date)
            daily[day_key] = daily.get(day_key, 0) + (t.sale_price * t.quantity_sold)

        # Sort by date and take last 30
        daily_sorted = sorted(daily.items(), key=lambda x: x[0])[-30:]
        daily_revenue = [{"date": d, "revenue": round(r, 2)} for d, r in daily_sorted]

        # By category
        cat_revenue = {}
        for t in transactions:
            product = session.query(Product).filter_by(product_id=t.product_id).first()
            cat = product.category if product else "unknown"
            cat_revenue[cat] = cat_revenue.get(cat, 0) + (t.sale_price * t.quantity_sold)
        cat_revenue = {k: round(v, 2) for k, v in cat_revenue.items()}

        return RevenueAnalytics(
            total_revenue=round(total_revenue, 2),
            total_savings=round(total_savings, 2),
            avg_discount=round(avg_discount, 1),
            transactions_with_discount=len(discounted_txns),
            total_transactions=len(transactions),
            daily_revenue=daily_revenue,
            category_revenue=cat_revenue,
        )
    finally:
        session.close()


# ── Dashboard Overview ───────────────────────────────────────────────────────

@app.get("/api/dashboard/overview", response_model=DashboardOverview)
def get_dashboard_overview():
    """Get high-level dashboard metrics."""
    session = get_session()
    try:
        today = date.today()

        total_products = session.query(Product).count()
        active_batches = session.query(InventoryBatch).filter_by(status="active").count()

        # Near expiry (within 3 days)
        near_expiry = (
            session.query(InventoryBatch)
            .filter(
                InventoryBatch.status == "active",
                InventoryBatch.expiry_date <= today + timedelta(days=3),
            )
            .count()
        )

        # Revenue
        revenue_result = session.query(
            func.sum(Transaction.sale_price * Transaction.quantity_sold)
        ).scalar() or 0

        # Waste value
        waste_value = session.query(func.sum(WasteLog.value_lost)).scalar() or 0

        # Revenue recovered (savings from dynamic pricing)
        transactions = session.query(Transaction).filter(Transaction.discount_pct > 0).all()
        revenue_recovered = sum(
            (t.original_price - t.sale_price) * t.quantity_sold
            for t in transactions
            if t.original_price
        )

        # Average waste risk for active batches
        active = (
            session.query(InventoryBatch, Product)
            .join(Product)
            .filter(InventoryBatch.status == "active")
            .all()
        )
        risk_scores = []
        for batch, product in active:
            days_left = (batch.expiry_date - today).days
            risk = compute_waste_risk(
                days_to_expiry=days_left,
                remaining_quantity=batch.remaining_quantity,
                total_quantity=batch.quantity,
                predicted_demand=5,
                category=product.category,
            )
            risk_scores.append(risk["overall_score"])

        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        critical_count = sum(1 for s in risk_scores if s >= 70)

        return DashboardOverview(
            total_products=total_products,
            active_batches=active_batches,
            near_expiry_count=near_expiry,
            total_revenue=round(revenue_result, 2),
            total_waste_value=round(waste_value, 2),
            revenue_recovered=round(revenue_recovered, 2),
            avg_waste_risk=round(avg_risk, 1),
            critical_alerts=critical_count,
        )
    finally:
        session.close()


# ── Run Server ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
