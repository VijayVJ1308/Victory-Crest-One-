"""Victory Crest One - Unit Tests for Calculations
Validates arithmetic precision, zero denominator safety, and metric calculations.
"""

from decimal import Decimal
from shared.calculations import (
    calculate_occupancy_rate,
    calculate_adr,
    calculate_revpar,
    calculate_gross_profit,
    calculate_budget_variance,
    calculate_lead_conversion_rate,
    to_decimal
)


def test_calculate_occupancy_rate_standard():
    rate = calculate_occupancy_rate(occupied_sellable_rooms=80, available_sellable_rooms=100)
    assert rate == Decimal("80.00")


def test_calculate_occupancy_rate_zero_denominator():
    rate = calculate_occupancy_rate(occupied_sellable_rooms=10, available_sellable_rooms=0)
    assert rate == Decimal("0.00")


def test_calculate_adr():
    adr = calculate_adr(room_revenue=50000, rooms_sold=10)
    assert adr == Decimal("5000.00")


def test_calculate_adr_zero_rooms():
    adr = calculate_adr(room_revenue=50000, rooms_sold=0)
    assert adr == Decimal("0.00")


def test_calculate_revpar():
    revpar = calculate_revpar(room_revenue=100000, available_sellable_rooms=25)
    assert revpar == Decimal("4000.00")


def test_calculate_revpar_zero_rooms():
    revpar = calculate_revpar(room_revenue=100000, available_sellable_rooms=0)
    assert revpar == Decimal("0.00")


def test_calculate_gross_profit():
    profit = calculate_gross_profit(revenue="150000.50", direct_costs="50000.25")
    assert profit == Decimal("100000.25")


def test_calculate_budget_variance():
    var = calculate_budget_variance(actual=12000, budget=10000)
    assert var == Decimal("2000.00")
    
    neg_var = calculate_budget_variance(actual=8000, budget=10000)
    assert neg_var == Decimal("-2000.00")


def test_calculate_lead_conversion_rate():
    rate = calculate_lead_conversion_rate(converted_leads=25, eligible_leads=100)
    assert rate == Decimal("25.00")

    zero_rate = calculate_lead_conversion_rate(converted_leads=25, eligible_leads=0)
    assert zero_rate == Decimal("0.00")
