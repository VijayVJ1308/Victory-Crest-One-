"""Victory Crest One - Unit Tests for Manufacturing & BOM Calculations
Validates decimal safety, scrap allowance math, routing costs, and executive KPIs.
"""

from decimal import Decimal
import pytest
from shared.calculations import (
    calculate_bom_line_cost,
    calculate_bom_totals,
    calculate_production_order_cost,
    calculate_manufacturing_kpis
)


def test_calculate_bom_line_cost_with_scrap():
    # 50 units @ 120.00 each with 5% scrap
    # base = 6,000.00, scrap = 300.00, total = 6,300.00
    res = calculate_bom_line_cost(quantity_required=50, unit_cost="120.00", scrap_percent=5)
    assert res["base_cost"] == Decimal("6000.00")
    assert res["scrap_cost"] == Decimal("300.00")
    assert res["total_line_cost"] == Decimal("6300.00")


def test_calculate_bom_line_cost_zero_scrap():
    res = calculate_bom_line_cost(quantity_required=10, unit_cost="45.50", scrap_percent=0)
    assert res["base_cost"] == Decimal("455.00")
    assert res["scrap_cost"] == Decimal("0.00")
    assert res["total_line_cost"] == Decimal("455.00")


def test_calculate_bom_totals_multi_component_and_routing():
    components = [
        {"quantity": 10, "unit_cost": 50, "scrap_percent": 0},      # 500.00
        {"quantity": 5, "unit_cost": 200, "scrap_percent": 10},     # 1000 + 100 = 1100.00
    ]
    # Total materials = 1600.00
    # Operations for batch_quantity = 10:
    # Op 1: setup = 1 hr, run = 0.2 hr/unit * 10 = 2 hr -> total 3 hr @ 400 = 1200.00
    # Op 2: setup = 0 hr, run = 0.1 hr/unit * 10 = 1 hr -> total 1 hr @ 600 = 600.00
    # Total operations = 1800.00
    # Total BOM = 3400.00, Unit cost = 340.00
    operations = [
        {"setup_time_hours": 1.0, "run_time_per_unit_hours": 0.2, "hourly_rate": 400.00},
        {"setup_time_hours": 0.0, "run_time_per_unit_hours": 0.1, "hourly_rate": 600.00},
    ]

    res = calculate_bom_totals(components=components, operations=operations, batch_quantity=10)
    assert res["batch_quantity"] == Decimal("10.00")
    assert res["base_material_cost"] == Decimal("1500.00")
    assert res["scrap_material_cost"] == Decimal("100.00")
    assert res["total_material_cost"] == Decimal("1600.00")
    assert res["total_operations_cost"] == Decimal("1800.00")
    assert res["total_bom_cost"] == Decimal("3400.00")
    assert res["unit_cost"] == Decimal("340.00")


def test_calculate_production_order_cost_standard():
    actual_materials = [
        {"quantity": 20, "unit_cost": 100, "total_cost": 2000.00},
        {"quantity": 10, "unit_cost": 50, "total_cost": 500.00},
    ]
    # Labor: 8 hours @ 500/hr = 4000.00
    # Overhead: 1500.00
    # Total: 2500 + 4000 + 1500 = 8000.00
    # Produced: 50 units -> unit cost = 160.00
    res = calculate_production_order_cost(
        actual_materials=actual_materials,
        actual_labor_hours=8,
        labor_hourly_rate=500,
        overhead_cost=1500,
        produced_quantity=50
    )
    assert res["material_cost"] == Decimal("2500.00")
    assert res["labor_cost"] == Decimal("4000.00")
    assert res["overhead_cost"] == Decimal("1500.00")
    assert res["total_actual_cost"] == Decimal("8000.00")
    assert res["unit_actual_cost"] == Decimal("160.00")


def test_calculate_manufacturing_kpis_scrap_and_utilization():
    orders = [
        {"status": "COMPLETED", "produced_quantity": 95, "rejected_quantity": 5, "total_actual_cost": 19000},
        {"status": "COMPLETED", "produced_quantity": 190, "rejected_quantity": 10, "total_actual_cost": 38000},
        {"status": "IN_PROGRESS", "produced_quantity": 0, "rejected_quantity": 0, "total_actual_cost": 12500},
    ]
    # Total units = (95 + 190) + (5 + 10) = 285 + 15 = 300
    # Scrap rate = 15 / 300 * 100 = 5.00%
    # WIP Value = 12500.00
    # Capacity: 160 hrs, used 120 hrs -> 120/160 * 100 = 75.00%
    res = calculate_manufacturing_kpis(orders=orders, total_capacity_hours=160, actual_hours_used=120)
    assert res["total_orders"] == 3
    assert res["completed_orders"] == 2
    assert res["in_progress_orders"] == 1
    assert res["total_produced_units"] == Decimal("285.00")
    assert res["total_rejected_units"] == Decimal("15.00")
    assert res["scrap_rate_percent"] == Decimal("5.00")
    assert res["total_wip_value"] == Decimal("12500.00")
    assert res["capacity_utilization_percent"] == Decimal("75.00")


def test_calculate_manufacturing_kpis_zero_divisions():
    res = calculate_manufacturing_kpis(orders=[], total_capacity_hours=0, actual_hours_used=0)
    assert res["total_orders"] == 0
    assert res["scrap_rate_percent"] == Decimal("0.00")
    assert res["capacity_utilization_percent"] == Decimal("0.00")
    assert res["total_wip_value"] == Decimal("0.00")
