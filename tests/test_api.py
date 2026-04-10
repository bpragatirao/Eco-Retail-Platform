"""
Tests for the FastAPI endpoints.
Uses TestClient for integration testing.
"""

import pytest
from fastapi.testclient import TestClient
from api.app import app
from db.models import init_db


@pytest.fixture(scope="module")
def client():
    """Create a test client and initialize the database."""
    init_db()
    with TestClient(app) as c:
        yield c


class TestDashboardAPI:
    """Test the dashboard serving endpoint."""

    def test_root_returns_200(self, client):
        """Root endpoint should return 200."""
        response = client.get("/")
        assert response.status_code == 200


class TestProductsAPI:
    """Test the products endpoint."""

    def test_get_products(self, client):
        """GET /api/products should return a list."""
        response = client.get("/api/products")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestInventoryAPI:
    """Test the inventory endpoint."""

    def test_get_inventory(self, client):
        """GET /api/inventory should return a list."""
        response = client.get("/api/inventory")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPricingAPI:
    """Test the pricing calculation endpoint."""

    def test_calculate_price_valid(self, client):
        """POST /api/price/calculate with valid input should return price data."""
        response = client.post("/api/price/calculate", json={
            "stock": 50,
            "days_to_expiry": 2,
            "base_price": 60.0,
            "category": "dairy"
        })
        assert response.status_code == 200
        data = response.json()
        assert "final_price" in data
        assert "discount_pct" in data
        assert "waste_risk" in data
        assert data["final_price"] > 0
        assert data["final_price"] <= 60.0

    def test_calculate_price_no_discount_needed(self, client):
        """Products with plenty of shelf life should get minimal/no discount."""
        response = client.post("/api/price/calculate", json={
            "stock": 5,
            "days_to_expiry": 30,
            "base_price": 100.0,
            "category": "beverages"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["discount_pct"] < 15  # Should be low or zero

    def test_calculate_price_critical(self, client):
        """Near-expiry with high stock should trigger discount."""
        response = client.post("/api/price/calculate", json={
            "stock": 100,
            "days_to_expiry": 1,
            "base_price": 60.0,
            "category": "bakery"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["discount_pct"] > 0
        assert data["waste_risk"]["risk_level"] in ("critical", "warning")

    def test_calculate_price_invalid_input(self, client):
        """Invalid input should return 422."""
        response = client.post("/api/price/calculate", json={
            "stock": -1,
            "days_to_expiry": 2,
            "base_price": 60.0,
        })
        assert response.status_code == 422

    def test_calculate_price_missing_fields(self, client):
        """Missing required fields should return 422."""
        response = client.post("/api/price/calculate", json={
            "stock": 50,
        })
        assert response.status_code == 422


class TestAlertsAPI:
    """Test the alerts endpoint."""

    def test_get_alerts(self, client):
        """GET /api/alerts should return a list."""
        response = client.get("/api/alerts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAnalyticsAPI:
    """Test the analytics endpoints."""

    def test_get_waste_analytics(self, client):
        """GET /api/analytics/waste should return waste data."""
        response = client.get("/api/analytics/waste")
        assert response.status_code == 200
        data = response.json()
        assert "total_waste_quantity" in data
        assert "waste_by_category" in data

    def test_get_revenue_analytics(self, client):
        """GET /api/analytics/revenue should return revenue data."""
        response = client.get("/api/analytics/revenue")
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "daily_revenue" in data

    def test_get_dashboard_overview(self, client):
        """GET /api/dashboard/overview should return overview metrics."""
        response = client.get("/api/dashboard/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data
        assert "active_batches" in data
        assert "total_revenue" in data
        assert "critical_alerts" in data
