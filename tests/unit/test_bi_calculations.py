"""Victory Crest One - Unit Tests for Business Intelligence & Financial Analytics
Tests financial ratios, GOP, EBITDA, portfolio rollups, department rankings,
and trend forecasting regressions.
"""

from decimal import Decimal
import pytest
from shared.calculations import (
    calculate_financial_ratios,
    calculate_portfolio_kpis,
    calculate_department_contributions,
    calculate_linear_forecast
)


def test_calculate_financial_ratios_standard():
    # Revenue: 1,000,000, COGS: 400,000, OPEX: 300,000, Deprec: 50,000, Interest: 20,000, Tax: 30,000
    res = calculate_financial_ratios(
        revenue=1000000,
        cogs=400000,
        opex=300000,
        depreciation=50000,
        interest=20000,
        tax=30000,
        current_assets=500000,
        current_liabilities=250000,
        total_assets=2000000,
        total_equity=1200000
    )

    # Gross Profit = 1,000,000 - 400,000 = 600,000 (60.00%)
    assert res["gross_profit"] == Decimal("600000.00")
    assert res["gross_margin_percent"] == Decimal("60.00")

    # EBIT = 600,000 - 300,000 = 300,000 (30.00%)
    assert res["ebit"] == Decimal("300000.00")
    assert res["operating_margin_percent"] == Decimal("30.00")

    # EBITDA = 300,000 + 50,000 = 350,000 (35.00%)
    assert res["ebitda"] == Decimal("350000.00")
    assert res["ebitda_margin_percent"] == Decimal("35.00")

    # Net Income = 300,000 - 20,000 - 30,000 = 250,000 (25.00%)
    assert res["net_income"] == Decimal("250000.00")
    assert res["net_margin_percent"] == Decimal("25.00")

    # Current Ratio = 500,000 / 250,000 = 2.00
    assert res["current_ratio"] == Decimal("2.00")

    # ROA = 250,000 / 2,000,000 = 12.50%
    assert res["roa_percent"] == Decimal("12.50")

    # ROE = 250,000 / 1,200,000 = 20.83%
    assert res["roe_percent"] == Decimal("20.83")


def test_calculate_financial_ratios_zero_revenue_guard():
    res = calculate_financial_ratios(revenue=0, cogs=0, opex=0)
    assert res["revenue"] == Decimal("0.00")
    assert res["gross_margin_percent"] == Decimal("0.00")
    assert res["net_margin_percent"] == Decimal("0.00")
    assert res["current_ratio"] == Decimal("0.00")


def test_calculate_portfolio_kpis():
    properties = [
        {
            "name": "Madurai Heritage Hotel",
            "available_rooms": 85,
            "occupancy_percent": 80.0,
            "adr": 4500.0,
            "revenue": 5000000.0,
            "gop": 2200000.0,
            "rooms_revenue": 3000000.0,
            "dining_revenue": 1500000.0,
            "retail_revenue": 300000.0,
            "service_revenue": 200000.0
        },
        {
            "name": "Kodaikanal Mountain Resort",
            "available_rooms": 65,
            "occupancy_percent": 70.0,
            "adr": 6000.0,
            "revenue": 4500000.0,
            "gop": 1900000.0,
            "rooms_revenue": 2800000.0,
            "dining_revenue": 1200000.0,
            "retail_revenue": 200000.0,
            "service_revenue": 300000.0
        }
    ]

    res = calculate_portfolio_kpis(properties)
    assert res["total_properties"] == 2
    assert res["total_revenue"] == Decimal("9500000.00")
    assert res["total_gop"] == Decimal("4100000.00")
    assert res["total_rooms_revenue"] == Decimal("5800000.00")
    assert res["total_dining_revenue"] == Decimal("2700000.00")

    # Blended occupancy: (80*85 + 70*65) / 150 = (6800 + 4550) / 150 = 11350 / 150 = 75.67%
    assert res["blended_occupancy_percent"] == Decimal("75.67")
    assert res["gop_margin_percent"] > Decimal("40.00")


def test_calculate_department_contributions():
    departments = [
        {"department": "Rooms & Hospitality", "revenue": 6000000, "expenses": 2500000},
        {"department": "Restaurants & Banquets", "revenue": 3000000, "expenses": 1800000},
        {"department": "Professional Services", "revenue": 1000000, "expenses": 400000}
    ]

    res = calculate_department_contributions(departments)
    assert len(res) == 3
    # Sorted descending by revenue
    assert res[0]["department"] == "Rooms & Hospitality"
    assert res[0]["revenue_share_percent"] == Decimal("60.00")
    assert res[0]["net_profit"] == Decimal("3500000.00")

    assert res[1]["department"] == "Restaurants & Banquets"
    assert res[1]["revenue_share_percent"] == Decimal("30.00")

    assert res[2]["department"] == "Professional Services"
    assert res[2]["revenue_share_percent"] == Decimal("10.00")


def test_calculate_linear_forecast():
    # Points with steady positive slope: 100, 110, 120, 130, 140
    history = [100, 110, 120, 130, 140]
    res = calculate_linear_forecast(history, periods_ahead=2)

    assert res["historical_mean"] == Decimal("120.00")
    assert res["growth_rate_percent"] == Decimal("40.00")
    # Next predicted should be 150.00 and period 2 should be 160.00
    assert res["forecast_values"][0] == Decimal("150.00")
    assert res["forecast_values"][1] == Decimal("160.00")
    assert res["next_period_prediction"] == Decimal("150.00")


def test_calculate_linear_forecast_empty_and_single():
    empty_res = calculate_linear_forecast([])
    assert empty_res["next_period_prediction"] == Decimal("0.00")

    single_res = calculate_linear_forecast([250])
    assert single_res["next_period_prediction"] == Decimal("250.00")
