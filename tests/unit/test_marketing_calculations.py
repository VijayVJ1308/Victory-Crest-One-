"""Victory Crest One - Unit Tests for Marketing Performance Calculations
Decimal-safe telemetry, open rates, CTR, CTOR, conversion rates, CPA, and ROAS.
"""

from decimal import Decimal
from shared.calculations import calculate_campaign_kpis


def test_calculate_campaign_kpis_standard():
    # Delivered: 1000, Opened: 400, Clicked: 150, Converted: 25, Spend: 50,000, Revenue: 250,000
    res = calculate_campaign_kpis(
        delivered=1000,
        opened=400,
        clicked=150,
        converted=25,
        spend=Decimal("50000.00"),
        revenue=Decimal("250000.00")
    )

    # Open Rate = (400 / 1000) * 100 = 40.00%
    assert res["open_rate_percent"] == Decimal("40.00")

    # CTR = (150 / 1000) * 100 = 15.00%
    assert res["ctr_percent"] == Decimal("15.00")

    # CTOR = (150 / 400) * 100 = 37.50%
    assert res["ctor_percent"] == Decimal("37.50")

    # Conversion Rate = (25 / 1000) * 100 = 2.50%
    assert res["conversion_rate_percent"] == Decimal("2.50")

    # CPA = 50,000 / 25 = ₹2,000.00
    assert res["cpa"] == Decimal("2000.00")

    # ROAS = 250,000 / 50,000 = 5.00x
    assert res["roas"] == Decimal("5.00")

    # ROMI % = ((250,000 - 50,000) / 50,000) * 100 = 400.00%
    assert res["romi_percent"] == Decimal("400.00")


def test_calculate_campaign_kpis_zero_delivered():
    # Zero delivered (scheduled campaign)
    res = calculate_campaign_kpis(
        delivered=0,
        opened=0,
        clicked=0,
        converted=0,
        spend=Decimal("0.00"),
        revenue=Decimal("0.00")
    )
    assert res["open_rate_percent"] == Decimal("0.00")
    assert res["ctr_percent"] == Decimal("0.00")
    assert res["conversion_rate_percent"] == Decimal("0.00")
    assert res["cpa"] == Decimal("0.00")
    assert res["roas"] == Decimal("0.00")


def test_calculate_campaign_kpis_zero_conversions_cpa():
    # Delivered 500, spend 10,000, but 0 conversions
    res = calculate_campaign_kpis(
        delivered=500,
        opened=100,
        clicked=20,
        converted=0,
        spend=Decimal("10000.00"),
        revenue=Decimal("0.00")
    )
    assert res["conversion_rate_percent"] == Decimal("0.00")
    assert res["cpa"] == Decimal("0.00")  # safe division
    assert res["roas"] == Decimal("0.00")


def test_calculate_campaign_kpis_zero_spend_roas():
    # Organic social post: spend is 0, generated 50,000 revenue
    res = calculate_campaign_kpis(
        delivered=1000,
        opened=300,
        clicked=80,
        converted=10,
        spend=Decimal("0.00"),
        revenue=Decimal("50000.00")
    )
    assert res["roas"] == Decimal("0.00")  # safe division
    assert res["cpa"] == Decimal("0.00")
