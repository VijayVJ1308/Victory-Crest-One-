"""Victory Crest One - Unit Tests for POS Calculations
Decimal-safe currency arithmetic, change calculations, drawer reconciliation, and split tenders.
"""

from decimal import Decimal
from shared.calculations import (
    calculate_pos_change,
    calculate_drawer_variance,
    calculate_pos_order_totals,
    calculate_split_tenders
)


def test_calculate_pos_change_exact_and_over():
    # Exact payment: change is 0.00
    change = calculate_pos_change(Decimal("840.00"), Decimal("840.00"))
    assert change == Decimal("0.00")

    # Overpayment: tendered 1000, total 840 -> change 160.00
    change = calculate_pos_change(Decimal("1000.00"), Decimal("840.00"))
    assert change == Decimal("160.00")

    # Float inputs safely converted to Decimal
    change = calculate_pos_change(2000.0, 1850.50)
    assert change == Decimal("149.50")


def test_calculate_pos_change_underpaid_returns_zero():
    # Tendered less than total returns 0.00
    change = calculate_pos_change(Decimal("500.00"), Decimal("840.00"))
    assert change == Decimal("0.00")

    # Zero or negative tendered returns 0.00
    assert calculate_pos_change(Decimal("0.00"), Decimal("100.00")) == Decimal("0.00")
    assert calculate_pos_change(Decimal("-50.00"), Decimal("100.00")) == Decimal("0.00")


def test_calculate_drawer_variance_balanced_over_short():
    # Balanced drawer
    var = calculate_drawer_variance(Decimal("5840.00"), Decimal("5840.00"))
    assert var == Decimal("0.00")

    # Overage: counted 6000, expected 5840 -> +160.00
    var = calculate_drawer_variance(Decimal("6000.00"), Decimal("5840.00"))
    assert var == Decimal("160.00")

    # Shortage: counted 5700, expected 5840 -> -140.00
    var = calculate_drawer_variance(Decimal("5700.00"), Decimal("5840.00"))
    assert var == Decimal("-140.00")


def test_calculate_pos_order_totals_with_discount_and_tax():
    lines = [
        {"quantity": Decimal("2"), "unit_price": Decimal("180.00")},  # 360.00
        {"quantity": Decimal("1"), "unit_price": Decimal("240.00")},  # 240.00
    ]
    # Subtotal = 600.00, 10% discount = 60.00, Taxable = 540.00, 12% GST = 64.80, Total = 604.80
    totals = calculate_pos_order_totals(lines, discount_percent=Decimal("10.00"), tax_rate_percent=Decimal("12.00"))
    assert totals["subtotal"] == Decimal("600.00")
    assert totals["discount_amount"] == Decimal("60.00")
    assert totals["taxable_amount"] == Decimal("540.00")
    assert totals["tax_amount"] == Decimal("64.80")
    assert totals["total_amount"] == Decimal("604.80")


def test_calculate_split_tenders():
    tenders = [
        {"tender_type": "CASH", "amount": Decimal("500.00")},
        {"tender_type": "CREDIT_CARD", "amount": Decimal("500.00")}
    ]
    # Total due 1000.00 -> exactly paid
    tendered, remaining, is_paid = calculate_split_tenders(tenders, Decimal("1000.00"))
    assert tendered == Decimal("1000.00")
    assert remaining == Decimal("0.00")
    assert is_paid is True

    # Total due 1200.00 -> remaining 200.00, not fully paid
    tendered, remaining, is_paid = calculate_split_tenders(tenders, Decimal("1200.00"))
    assert tendered == Decimal("1000.00")
    assert remaining == Decimal("200.00")
    assert is_paid is False
