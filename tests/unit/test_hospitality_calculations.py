"""Victory Crest One - Hospitality & Dining Unit Calculations Test Suite
Validates decimal-safe calculations for room reservations, guest folios,
restaurant dining bills, occupancy rates, ADR, and RevPAR.
"""

from decimal import Decimal
from shared.calculations import (
    calculate_reservation_totals,
    calculate_folio_balance,
    calculate_dining_bill_totals,
    calculate_occupancy_rate,
    calculate_adr,
    calculate_revpar
)


def test_calculate_reservation_totals_standard():
    # 3 nights @ 9500.00/night = 28500.00
    # Meal plan (CP): 500.00 * 3 = 1500.00
    # Subtotal: 30000.00
    # Tax 12%: 3600.00
    # Grand Total: 33600.00
    totals = calculate_reservation_totals(
        room_rate_per_night=9500.0,
        nights=3,
        meal_plan_rate=500.0,
        tax_rate_percent=12.0
    )
    assert totals["room_charges"] == Decimal("28500.00")
    assert totals["meal_charges"] == Decimal("1500.00")
    assert totals["subtotal"] == Decimal("30000.00")
    assert totals["tax_amount"] == Decimal("3600.00")
    assert totals["grand_total"] == Decimal("33600.00")


def test_calculate_reservation_totals_zero_nights_guard():
    # Nights clamped to min 1
    totals = calculate_reservation_totals(
        room_rate_per_night=5000.0,
        nights=0,
        meal_plan_rate=0.0,
        tax_rate_percent=0.0
    )
    assert totals["subtotal"] == Decimal("5000.00")
    assert totals["grand_total"] == Decimal("5000.00")


def test_calculate_folio_balance():
    lines = [
        {"line_type": "ROOM_CHARGE", "amount": Decimal("9500.00")},
        {"line_type": "ROOM_CHARGE", "amount": Decimal("9500.00")},
        {"line_type": "FOOD_BEVERAGE", "amount": Decimal("3200.00")},
        {"line_type": "SPA", "amount": Decimal("1800.00")},
        {"line_type": "PAYMENT", "amount": Decimal("15000.00")}
    ]
    # Total charges: 9500 + 9500 + 3200 + 1800 = 24000.00
    # Payments: 15000.00
    # Balance: 9000.00
    res = calculate_folio_balance(lines)
    assert res["total_charges"] == Decimal("24000.00")
    assert res["total_payments"] == Decimal("15000.00")
    assert res["balance_due"] == Decimal("9000.00")
    assert res["is_settled"] is False


def test_calculate_folio_balance_fully_settled():
    lines = [
        {"line_type": "ROOM_CHARGE", "amount": Decimal("5000.00")},
        {"line_type": "PAYMENT", "amount": Decimal("5000.00")}
    ]
    res = calculate_folio_balance(lines)
    assert res["balance_due"] == Decimal("0.00")
    assert res["is_settled"] is True


def test_calculate_dining_bill_totals():
    # Subtotal: 2000.00, Discount: 200.00 -> Net: 1800.00
    # Service Charge 5%: 90.00
    # Restaurant GST 5%: 90.00
    # Grand Total: 1980.00
    bill = calculate_dining_bill_totals(
        subtotal=2000.0,
        service_charge_percent=5.0,
        gst_percent=5.0,
        discount_amount=200.0
    )
    assert bill["net_subtotal"] == Decimal("1800.00")
    assert bill["service_charge"] == Decimal("90.00")
    assert bill["gst_amount"] == Decimal("90.00")
    assert bill["grand_total"] == Decimal("1980.00")


def test_hospitality_kpis_occupancy_adr_revpar():
    # 75 occupied rooms out of 100 available -> 75.00%
    occ = calculate_occupancy_rate(75, 100)
    assert occ == Decimal("75.00")

    # ₹600,000 revenue across 75 occupied rooms -> ADR = ₹8,000.00
    adr = calculate_adr(600000, 75)
    assert adr == Decimal("8000.00")

    # RevPAR = ₹600,000 / 100 available rooms = ₹6,000.00
    revpar = calculate_revpar(600000, 100)
    assert revpar == Decimal("6000.00")
