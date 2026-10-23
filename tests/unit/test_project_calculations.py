"""Victory Crest One - Unit Tests for Project Management & PSA Calculations
Validates decimal safety, budget variance, burn rates, timesheets, and milestone invoicing.
"""

from decimal import Decimal
import pytest
from shared.calculations import (
    calculate_project_budget_variance,
    calculate_project_burn_rate,
    calculate_timesheet_totals,
    calculate_milestone_invoice,
    calculate_project_kpis
)


def test_calculate_project_budget_variance_under_and_over():
    # Budget ₹500,000, Actual ₹420,000 -> Variance ₹80,000 (16.00%), not over budget
    res = calculate_project_budget_variance(budget_amount="500000.00", actual_cost="420000.00")
    assert res["budget_amount"] == Decimal("500000.00")
    assert res["actual_cost"] == Decimal("420000.00")
    assert res["variance"] == Decimal("80000.00")
    assert res["variance_percent"] == Decimal("16.00")
    assert not res["is_over_budget"]

    # Budget ₹200,000, Actual ₹250,000 -> Variance -₹50,000 (-25.00%), is over budget
    res_over = calculate_project_budget_variance(budget_amount="200000.00", actual_cost="250000.00")
    assert res_over["variance"] == Decimal("-50000.00")
    assert res_over["variance_percent"] == Decimal("-25.00")
    assert res_over["is_over_budget"]


def test_calculate_project_budget_variance_zero_budget():
    res = calculate_project_budget_variance(budget_amount=0, actual_cost="15000.00")
    assert res["variance_percent"] == Decimal("0.00")
    assert res["is_over_budget"]


def test_calculate_project_burn_rate():
    # Spent ₹150,000 over 15 elapsed days -> daily burn = ₹10,000/day
    # Total project planned = 45 days -> projected total = ₹450,000
    res = calculate_project_burn_rate(total_cost="150000.00", elapsed_days=15, total_project_days=45)
    assert res["daily_burn_rate"] == Decimal("10000.00")
    assert res["projected_total_cost"] == Decimal("450000.00")


def test_calculate_timesheet_totals_billable_and_cost():
    timesheets = [
        {"hours": 40, "is_billable": True, "hourly_billing_rate": 2500, "hourly_cost_rate": 800},
        {"hours": 20, "is_billable": True, "hourly_billing_rate": 2000, "hourly_cost_rate": 600},
        {"hours": 20, "is_billable": False, "hourly_billing_rate": 0, "hourly_cost_rate": 600},
    ]
    # Total hours = 80
    # Billable hours = 60 (75.00% utilization)
    # Non-billable = 20
    # Billable amount = 40*2500 (100,000) + 20*2000 (40,000) = 140,000
    # Cost = 40*800 (32,000) + 20*600 (12,000) + 20*600 (12,000) = 56,000
    res = calculate_timesheet_totals(timesheets)
    assert res["total_hours"] == Decimal("80.00")
    assert res["billable_hours"] == Decimal("60.00")
    assert res["non_billable_hours"] == Decimal("20.00")
    assert res["billable_amount"] == Decimal("140000.00")
    assert res["labor_cost"] == Decimal("56000.00")
    assert res["utilization_rate"] == Decimal("75.00")


def test_calculate_milestone_invoice_with_gst():
    # Milestone ₹250,000 + 18% GST = ₹295,000
    res = calculate_milestone_invoice(milestone_amount="250000.00", tax_percent=18)
    assert res["subtotal"] == Decimal("250000.00")
    assert res["tax_amount"] == Decimal("45000.00")
    assert res["grand_total"] == Decimal("295000.00")


def test_calculate_project_kpis_and_margin():
    projects = [
        {"status": "ACTIVE", "budget_amount": "500000.00", "billed_amount": "200000.00"},
        {"status": "COMPLETED", "budget_amount": "300000.00", "billed_amount": "300000.00"},
    ]
    timesheets = [
        {"hours": 100, "is_billable": True, "hourly_billing_rate": 2000, "hourly_cost_rate": 800},  # cost 80,000
    ]
    expenses = [
        {"amount": 20000.00},
    ]
    # Total billed = 500,000
    # Total actual cost = 80,000 + 20,000 = 100,000
    # Profit margin = (500,000 - 100,000) / 500,000 * 100 = 80.00%
    res = calculate_project_kpis(projects, timesheets, expenses)
    assert res["total_projects"] == 2
    assert res["active_projects"] == 1
    assert res["completed_projects"] == 1
    assert res["total_budget"] == Decimal("800000.00")
    assert res["total_billed"] == Decimal("500000.00")
    assert res["total_actual_cost"] == Decimal("100000.00")
    assert res["profit_margin_percent"] == Decimal("80.00")
