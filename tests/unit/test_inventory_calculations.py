"""Victory Crest One - Unit Tests for Inventory & Supply Chain Calculations
Decimal-safe Reorder Point (ROP), AVCO Weighted Average Costing, Stock Valuation,
Cycle Count Stocktaking Variances, and Purchase Order Totals.
"""

from decimal import Decimal
from shared.calculations import (
    calculate_reorder_point,
    calculate_inventory_valuation,
    calculate_stock_variance,
    calculate_weighted_average_cost,
    calculate_po_totals
)


def test_calculate_reorder_point():
    # Lead time = 7 days, daily usage = 5 units, safety stock = 10 units
    # ROP = (7 * 5) + 10 = 45.00
    rop = calculate_reorder_point(lead_time_days=7, daily_usage=5, safety_stock=10)
    assert rop == Decimal("45.00")

    # Zero safety stock
    rop_zero_safety = calculate_reorder_point(lead_time_days=5, daily_usage=2)
    assert rop_zero_safety == Decimal("10.00")


def test_calculate_inventory_valuation():
    items = [
        {"quantity_on_hand": 100, "unit_cost": Decimal("50.00")},
        {"quantity_on_hand": 20, "unit_cost": Decimal("250.00")},
        {"quantity_on_hand": 5, "unit_cost": Decimal("1000.00")},
    ]
    val = calculate_inventory_valuation(items)

    assert val["total_skus"] == 3
    # 100 + 20 + 5 = 125 units
    assert val["total_units"] == Decimal("125.00")
    # (100*50) + (20*250) + (5*1000) = 5000 + 5000 + 5000 = 15000.00
    assert val["total_valuation"] == Decimal("15000.00")


def test_calculate_stock_variance_balanced():
    res = calculate_stock_variance(book_quantity=50, counted_quantity=50, unit_cost=100)
    assert res["variance_quantity"] == Decimal("0.00")
    assert res["variance_value"] == Decimal("0.00")
    assert res["is_discrepant"] is False


def test_calculate_stock_variance_shrinkage_and_surplus():
    # Shrinkage (loss of 5 units)
    shrinkage = calculate_stock_variance(book_quantity=50, counted_quantity=45, unit_cost=120)
    assert shrinkage["variance_quantity"] == Decimal("-5.00")
    assert shrinkage["variance_value"] == Decimal("-600.00")
    assert shrinkage["is_discrepant"] is True

    # Surplus (found 4 extra units)
    surplus = calculate_stock_variance(book_quantity=50, counted_quantity=54, unit_cost=120)
    assert surplus["variance_quantity"] == Decimal("4.00")
    assert surplus["variance_value"] == Decimal("480.00")
    assert surplus["is_discrepant"] is True


def test_calculate_weighted_average_cost():
    # Existing: 100 units @ ₹50.00 (Total value: ₹5,000.00)
    # New Purchase: 50 units @ ₹80.00 (Total value: ₹4,000.00)
    # Total units: 150, Total value: ₹9,000.00 => New AVCO: ₹60.00
    new_avco = calculate_weighted_average_cost(
        old_qty=100,
        old_cost=Decimal("50.00"),
        new_qty=50,
        new_price=Decimal("80.00")
    )
    assert new_avco == Decimal("60.00")

    # Initial stock arrival from zero
    init_cost = calculate_weighted_average_cost(
        old_qty=0,
        old_cost=0,
        new_qty=20,
        new_price=Decimal("150.00")
    )
    assert init_cost == Decimal("150.00")


def test_calculate_po_totals_with_tax():
    lines = [
        {"quantity_ordered": 10, "unit_price": Decimal("100.00")},  # 1000.00
        {"quantity_ordered": 5, "unit_price": Decimal("200.00")},   # 1000.00
    ]
    totals = calculate_po_totals(lines, tax_rate_percent=Decimal("18.00"))

    assert totals["subtotal"] == Decimal("2000.00")
    assert totals["tax_rate_percent"] == Decimal("18.00")
    assert totals["tax_amount"] == Decimal("360.00")
    assert totals["total_amount"] == Decimal("2360.00")


def test_calculate_po_totals_zero_tax():
    lines = [
        {"quantity_ordered": 2, "unit_price": Decimal("450.00")},
    ]
    totals = calculate_po_totals(lines, tax_rate_percent=Decimal("0.00"))
    assert totals["subtotal"] == Decimal("900.00")
    assert totals["tax_amount"] == Decimal("0.00")
    assert totals["total_amount"] == Decimal("900.00")
