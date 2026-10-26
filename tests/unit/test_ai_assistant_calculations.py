"""Victory Crest One - Unit Tests for AI Assistant Intent Classification & Permissions Masking
"""

from decimal import Decimal
import pytest

from shared.calculations import (
    classify_natural_language_intent,
    filter_data_by_role_permissions,
    calculate_ai_assistant_metrics
)


def test_classify_natural_language_intent():
    assert classify_natural_language_intent("What is our current hotel room occupancy and ADR?") == "OCCUPANCY_STATUS"
    assert classify_natural_language_intent("Show me the resort guest check-ins and folios") == "OCCUPANCY_STATUS"
    assert classify_natural_language_intent("What is our operating EBITDA and cash balance?") == "FINANCIAL_HEALTH"
    assert classify_natural_language_intent("Summarize this quarter's sales revenue and CRM pipeline deals") == "REVENUE_ANALYSIS"
    assert classify_natural_language_intent("Are there any low warehouse stock alerts or reorder purchase orders?") == "INVENTORY_AUDIT"
    assert classify_natural_language_intent("How are the PSA project milestones and timesheets progressing?") == "PROJECT_DELIVERY"
    assert classify_natural_language_intent("Check open customer service support tickets and SLA breaches") == "SERVICE_SLA"
    assert classify_natural_language_intent("What is our current staff headcount and monthly payroll?") == "STAFFING_OVERVIEW"
    assert classify_natural_language_intent("Give me an executive dashboard overview of all business KPIs") == "EXECUTIVE_KPI"
    assert classify_natural_language_intent("How is the weather today?") == "GENERAL_INQUIRY"


def test_filter_data_by_role_permissions_executive():
    test_data = {
        "total_revenue": "₹28,750,000",
        "ebitda": "₹8,450,000",
        "net_income": "₹6,120,000",
        "cash_balance": "₹14,500,000",
        "occupancy_percent": "78.5%"
    }

    # Executive General Manager
    filtered, rating = filter_data_by_role_permissions("General Manager", test_data)
    assert rating == "SAFE"
    assert filtered["ebitda"] == "₹8,450,000"
    assert filtered["net_income"] == "₹6,120,000"
    assert filtered["cash_balance"] == "₹14,500,000"


def test_filter_data_by_role_permissions_operational():
    test_data = {
        "total_revenue": "₹28,750,000",
        "ebitda": "₹8,450,000",
        "net_income": "₹6,120,000",
        "cash_balance": "₹14,500,000",
        "occupancy_percent": "78.5%"
    }

    # POS Cashier / Receptionist
    filtered, rating = filter_data_by_role_permissions("POS Cashier", test_data)
    assert rating == "CONFIDENTIAL_RESTRICTED"
    assert filtered["occupancy_percent"] == "78.5%"
    assert "[CONFIDENTIAL" in filtered["ebitda"]
    assert "[CONFIDENTIAL" in filtered["net_income"]
    assert "[CONFIDENTIAL" in filtered["cash_balance"]


def test_calculate_ai_assistant_metrics():
    history = [
        {"intent": "REVENUE_ANALYSIS", "latency_ms": 150.0, "safety_rating": "SAFE"},
        {"intent": "OCCUPANCY_STATUS", "latency_ms": 120.0, "safety_rating": "SAFE"},
        {"intent": "FINANCIAL_HEALTH", "latency_ms": 180.0, "safety_rating": "CONFIDENTIAL_RESTRICTED"}
    ]

    metrics = calculate_ai_assistant_metrics(history)
    assert metrics["total_queries"] == 3
    # 150 + 120 + 180 = 450 / 3 = 150.00
    assert metrics["avg_latency_ms"] == Decimal("150.00")
    assert metrics["intent_counts"]["REVENUE_ANALYSIS"] == 1
    assert metrics["intent_counts"]["OCCUPANCY_STATUS"] == 1
    # safe: 2 / 3 * 100 = 66.67%
    assert metrics["safe_queries_percent"] == Decimal("66.67")


def test_calculate_ai_assistant_metrics_empty():
    metrics = calculate_ai_assistant_metrics([])
    assert metrics["total_queries"] == 0
    assert metrics["avg_latency_ms"] == Decimal("0.00")
    assert metrics["safe_queries_percent"] == Decimal("100.00")
