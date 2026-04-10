"""
Tests for the AI Waste Risk Scoring system.
"""

import pytest
from ai.waste_risk import compute_waste_risk


class TestWasteRiskScoring:
    """Test waste risk score computation."""

    def test_expired_product_is_critical(self):
        """Products past expiry should always be critical risk."""
        result = compute_waste_risk(
            days_to_expiry=0,
            remaining_quantity=50,
            total_quantity=100,
            predicted_demand=10,
            category="dairy"
        )
        assert result["risk_level"] == "critical"
        assert result["overall_score"] >= 70

    def test_fresh_product_is_safe(self):
        """Products with plenty of shelf life and low stock should be safe."""
        result = compute_waste_risk(
            days_to_expiry=20,
            remaining_quantity=5,
            total_quantity=100,
            predicted_demand=10,
            category="beverages"
        )
        assert result["risk_level"] == "safe"
        assert result["overall_score"] < 40

    def test_near_expiry_high_stock_is_critical(self):
        """Near expiry with high remaining stock should be critical."""
        result = compute_waste_risk(
            days_to_expiry=1,
            remaining_quantity=80,
            total_quantity=100,
            predicted_demand=5,
            category="bakery"
        )
        assert result["risk_level"] == "critical"
        assert result["overall_score"] >= 75

    def test_warning_zone(self):
        """Mid-range risk should be warning."""
        result = compute_waste_risk(
            days_to_expiry=5,
            remaining_quantity=30,
            total_quantity=50,
            predicted_demand=15,
            category="produce"
        )
        assert result["risk_level"] in ("warning", "critical")
        assert result["overall_score"] >= 30

    def test_score_range(self):
        """Score should always be between 0 and 100."""
        for days in [0, 1, 3, 7, 14, 30]:
            for stock in [1, 10, 50, 100]:
                result = compute_waste_risk(
                    days_to_expiry=days,
                    remaining_quantity=stock,
                    total_quantity=100,
                    predicted_demand=20,
                    category="dairy"
                )
                assert 0 <= result["overall_score"] <= 100

    def test_zero_demand_high_risk(self):
        """Zero predicted demand should result in high surplus score."""
        result = compute_waste_risk(
            days_to_expiry=3,
            remaining_quantity=50,
            total_quantity=50,
            predicted_demand=0,
            category="meat"
        )
        assert result["overall_score"] >= 60

    def test_result_structure(self):
        """Result should contain all expected keys."""
        result = compute_waste_risk(
            days_to_expiry=5,
            remaining_quantity=20,
            total_quantity=50,
            predicted_demand=10,
            category="dairy"
        )
        assert "overall_score" in result
        assert "risk_level" in result
        assert "factors" in result
        assert "recommendation" in result
        assert "expiry_urgency" in result["factors"]
        assert "stock_surplus" in result["factors"]
        assert "category_perishability" in result["factors"]
        assert "inventory_utilization" in result["factors"]

    def test_category_affects_score(self):
        """Different categories should produce different perishability scores."""
        meat_result = compute_waste_risk(5, 20, 50, 10, "meat")
        bev_result = compute_waste_risk(5, 20, 50, 10, "beverages")

        assert meat_result["factors"]["category_perishability"] > bev_result["factors"]["category_perishability"]

    def test_recommendation_exists(self):
        """Every risk level should have a recommendation."""
        for days in [0, 5, 20]:
            result = compute_waste_risk(days, 30, 50, 10, "dairy")
            assert len(result["recommendation"]) > 0
