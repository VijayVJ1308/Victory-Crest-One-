"""Victory Crest One - Customer & Field Service Unit Calculations Test Suite
Validates decimal-safe calculations for labor costs, work order totals, SLA countdowns,
compliance percentages, and first-contact resolution rates.
"""

from decimal import Decimal
from datetime import datetime, timedelta, timezone
from shared.calculations import (
    calculate_service_labor_cost,
    calculate_work_order_totals,
    calculate_sla_remaining_hours,
    calculate_sla_compliance_rate,
    calculate_first_contact_resolution_rate
)


def test_calculate_service_labor_cost_standard_and_overtime():
    # 4 regular hours @ 850/hr = 3400.00
    # 2 overtime hours @ 850/hr * 1.5 = 2550.00
    # Total = 5950.00
    res = calculate_service_labor_cost(
        labor_hours=4.0,
        hourly_rate=850.0,
        overtime_hours=2.0,
        overtime_multiplier=1.5
    )
    assert res == Decimal("5950.00")


def test_calculate_service_labor_cost_negative_guards():
    res = calculate_service_labor_cost(
        labor_hours=-5,
        hourly_rate=-100,
        overtime_hours=-2
    )
    assert res == Decimal("0.00")


def test_calculate_work_order_totals_with_18_percent_tax():
    # Labor: 3825.00, Parts: 9000.00 -> Subtotal: 12825.00
    # Tax 18%: 2308.50
    # Grand Total: 15133.50
    totals = calculate_work_order_totals(
        labor_total="3825.00",
        parts_total="9000.00",
        tax_rate_percent=18.0
    )
    assert totals["subtotal"] == Decimal("12825.00")
    assert totals["tax_amount"] == Decimal("2308.50")
    assert totals["grand_total"] == Decimal("15133.50")


def test_calculate_work_order_totals_zero_parts():
    totals = calculate_work_order_totals(
        labor_total="2000.00",
        parts_total="0.00",
        tax_rate_percent=0.0
    )
    assert totals["subtotal"] == Decimal("2000.00")
    assert totals["tax_amount"] == Decimal("0.00")
    assert totals["grand_total"] == Decimal("2000.00")


def test_calculate_sla_remaining_hours_not_breached():
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(hours=2)
    # Target 4.0 hours, elapsed 2.0 -> remaining 2.0 hours
    remaining, is_breached = calculate_sla_remaining_hours(
        created_at=created_at,
        sla_target_hours=Decimal("4.00"),
        current_time=now
    )
    assert remaining == Decimal("2.00")
    assert is_breached is False


def test_calculate_sla_remaining_hours_breached():
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(hours=5)
    # Target 4.0 hours, elapsed 5.0 -> remaining -1.0 hours
    remaining, is_breached = calculate_sla_remaining_hours(
        created_at=created_at,
        sla_target_hours=Decimal("4.00"),
        current_time=now
    )
    assert remaining == Decimal("-1.00")
    assert is_breached is True


def test_calculate_sla_compliance_rate():
    # 20 resolved, 2 breached -> 18/20 = 90.00%
    rate = calculate_sla_compliance_rate(total_resolved=20, breached_count=2)
    assert rate == Decimal("90.00")

    # Zero resolved -> 100.00%
    assert calculate_sla_compliance_rate(0, 0) == Decimal("100.00")

    # All breached -> 0.00%
    assert calculate_sla_compliance_rate(10, 10) == Decimal("0.00")


def test_calculate_first_contact_resolution_rate():
    # 50 total tickets, 35 resolved on first contact -> 70.00%
    rate = calculate_first_contact_resolution_rate(total_tickets=50, fcr_count=35)
    assert rate == Decimal("70.00")

    # Zero tickets -> 0.00%
    assert calculate_first_contact_resolution_rate(0, 0) == Decimal("0.00")
