"""
Unit and API integration tests for the Salary Insights and Career Growth service.
Verifies currency support (USD & INR), experience tier multipliers, and API responses.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.salary_service import (
    compute_salary_insights,
    match_role_key,
)

client = TestClient(app)

def test_match_role_key():
    """Verifies that titles map correctly to benchmark role keys."""
    assert match_role_key("Senior Backend Python Developer") == "backend_engineer"
    assert match_role_key("Frontend React Engineer") == "frontend_engineer"
    assert match_role_key("Data Scientist / ML") == "data_scientist"
    assert match_role_key("Full Stack Developer") == "software_engineer"
    assert match_role_key("Electrical & Electronics Engineer") == "electrical_engineer"
    assert match_role_key("Embedded Firmware Engineer (ARM/STM32)") == "embedded_systems_engineer"
    assert match_role_key("VLSI ASIC Design Engineer") == "vlsi_design_engineer"
    assert match_role_key("Hardware PCB Design Engineer") == "hardware_engineer"
    assert match_role_key("Robotics & Automation Engineer") == "robotics_automation_engineer"

def test_ece_and_hardware_salary():
    """Verifies that ECE roles produce valid salary benchmarks and all_available_roles."""
    res = compute_salary_insights(role="electrical_engineer", currency="INR")
    assert res.role_key == "electrical_engineer"
    assert res.category == "Electronics & Hardware"
    assert res.range.min < res.range.median < res.range.max
    assert res.all_available_roles is not None
    assert len(res.all_available_roles) >= 10
    assert any(r["id"] == "embedded_systems_engineer" for r in res.all_available_roles)

def test_salary_currencies():
    """Tests USD and INR currency calculations and ranges."""
    usd_data = compute_salary_insights(role="backend_engineer", currency="USD", years_exp=3.0)
    assert usd_data.currency == "USD"
    assert usd_data.range.min < usd_data.range.median < usd_data.range.max
    assert usd_data.range.min >= 50000

    inr_data = compute_salary_insights(role="backend_engineer", currency="INR", years_exp=3.0)
    assert inr_data.currency == "INR"
    assert inr_data.range.min < inr_data.range.median < inr_data.range.max
    assert inr_data.range.min >= 500000  # In INR (e.g. 7.5 LPA)

def test_experience_multipliers():
    """Tests that senior experience increases benchmark compensation."""
    entry = compute_salary_insights(role="software_engineer", currency="USD", years_exp=1.0)
    senior = compute_salary_insights(role="software_engineer", currency="USD", years_exp=6.0)

    assert senior.range.median > entry.range.median

def test_growth_projections_and_disclaimer():
    """Verifies presence of 1, 3, 5 year projections and required disclaimer."""
    res = compute_salary_insights(role="software_engineer", currency="USD")
    assert len(res.growth_projection) >= 4
    assert len(res.high_impact_skills) > 0
    # Must explicitly state it is an indicative estimate
    assert "indicative" in res.disclaimer.lower()

def test_salary_endpoint_api():
    """Tests the GET /api/salary endpoint."""
    response = client.get("/api/salary?role=backend_engineer&currency=INR&years_exp=4.0")
    assert response.status_code == 200
    data = response.json()

    assert data["currency"] == "INR"
    assert data["role_key"] == "backend_engineer"
    assert data["range"]["median"] > 0
    assert len(data["growth_projection"]) > 0
