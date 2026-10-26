"""Victory Crest One - Unit Tests for Workflow Automation Calculations & Rule Evaluator
"""

from decimal import Decimal
import pytest

from shared.calculations import (
    evaluate_rule_condition,
    evaluate_workflow_conditions,
    calculate_workflow_kpis
)


def test_evaluate_rule_condition_numeric():
    # Greater Than
    assert evaluate_rule_condition(15, "GREATER_THAN", 10) is True
    assert evaluate_rule_condition(10, ">", 10) is False
    assert evaluate_rule_condition(5, "GT", 10) is False

    # Greater Than or Equal
    assert evaluate_rule_condition(10, "GREATER_THAN_OR_EQUAL", 10) is True
    assert evaluate_rule_condition(11, ">=", 10) is True
    assert evaluate_rule_condition(9, "GTE", 10) is False

    # Less Than
    assert evaluate_rule_condition(5, "LESS_THAN", 10) is True
    assert evaluate_rule_condition(10, "<", 10) is False
    assert evaluate_rule_condition(15, "LT", 10) is False

    # Less Than or Equal
    assert evaluate_rule_condition(10, "LESS_THAN_OR_EQUAL", 10) is True
    assert evaluate_rule_condition(9, "<=", 10) is True
    assert evaluate_rule_condition(11, "LTE", 10) is False

    # Numeric Equality with Decimal conversion
    assert evaluate_rule_condition("100.50", "EQUALS", 100.5) is True
    assert evaluate_rule_condition(Decimal("50.00"), "==", 50) is True
    assert evaluate_rule_condition(50, "!=", 51) is True


def test_evaluate_rule_condition_string_and_contains():
    # String equality
    assert evaluate_rule_condition("ACTIVE", "EQUALS", "active") is True
    assert evaluate_rule_condition("P1", "==", "p1") is True
    assert evaluate_rule_condition("VIP", "NOT_EQUALS", "REGULAR") is True

    # String contains
    assert evaluate_rule_condition("Grand Ballroom AV Setup", "CONTAINS", "ballroom") is True
    assert evaluate_rule_condition("Inventory stock deficit", "CONTAINS", "surplus") is False

    # List contains
    assert evaluate_rule_condition(["VIP", "PLATINUM", "GOLD"], "CONTAINS", "VIP") is True

    # IN operator
    assert evaluate_rule_condition("VIP", "IN", ["VIP", "VVIP", "PRESIDENTIAL"]) is True
    assert evaluate_rule_condition("STANDARD", "IN", ["VIP", "VVIP"]) is False
    assert evaluate_rule_condition("P1", "IN", "P1, P2, P3") is True


def test_evaluate_workflow_conditions_all_and_any():
    context = {
        "event": "inventory.stock_level_low",
        "current_stock": 5,
        "reorder_point": 20,
        "item": {
            "category": "RAW_MATERIAL",
            "criticality": "HIGH"
        }
    }

    # Match mode ALL - all satisfied
    conds_all_pass = [
        {"field": "current_stock", "operator": "LESS_THAN_OR_EQUAL", "value": 10},
        {"field": "item.criticality", "operator": "EQUALS", "value": "HIGH"}
    ]
    assert evaluate_workflow_conditions(conds_all_pass, context, match_mode="ALL") is True

    # Match mode ALL - one fails
    conds_one_fail = [
        {"field": "current_stock", "operator": "LESS_THAN_OR_EQUAL", "value": 10},
        {"field": "item.criticality", "operator": "EQUALS", "value": "LOW"}
    ]
    assert evaluate_workflow_conditions(conds_one_fail, context, match_mode="ALL") is False

    # Match mode ANY - one passes
    assert evaluate_workflow_conditions(conds_one_fail, context, match_mode="ANY") is True

    # Empty conditions default to True
    assert evaluate_workflow_conditions([], context) is True


def test_calculate_workflow_kpis_standard():
    executions = [
        {
            "id": "ex-1",
            "status": "SUCCESS",
            "duration_ms": 12.5,
            "actions_executed": [{"action": "SEND_NOTIFICATION"}, {"action": "CREATE_TASK"}]
        },
        {
            "id": "ex-2",
            "status": "SUCCESS",
            "duration_ms": 15.0,
            "actions_executed": [{"action": "WEBHOOK_CALL"}]
        },
        {
            "id": "ex-3",
            "status": "FAILED",
            "duration_ms": 8.0,
            "actions_executed": []
        },
        {
            "id": "ex-4",
            "status": "SKIPPED",
            "duration_ms": 2.5,
            "actions_executed": []
        }
    ]

    kpis = calculate_workflow_kpis(executions)
    assert kpis["total_executions"] == 4
    assert kpis["success_count"] == 2
    assert kpis["failed_count"] == 1
    assert kpis["skipped_count"] == 1
    assert kpis["total_actions_triggered"] == 3
    # evaluated = 2 success + 1 failed = 3. 2 / 3 * 100 = 66.67%
    assert kpis["success_rate_percent"] == Decimal("66.67")
    # total duration: 12.5 + 15.0 + 8.0 + 2.5 = 38.0 / 4 = 9.50 ms
    assert kpis["avg_duration_ms"] == Decimal("9.50")


def test_calculate_workflow_kpis_empty_and_zero_division():
    kpis = calculate_workflow_kpis([])
    assert kpis["total_executions"] == 0
    assert kpis["success_count"] == 0
    assert kpis["failed_count"] == 0
    assert kpis["success_rate_percent"] == Decimal("0.00")
    assert kpis["avg_duration_ms"] == Decimal("0.00")
