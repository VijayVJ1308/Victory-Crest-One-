"""Victory Crest One - Unit Tests for Accounting Calculations
Tests double-entry balance validation, invoice calculation with taxes, and account balance normal rules.
"""

from decimal import Decimal
from shared.calculations import (
    validate_journal_balance,
    calculate_invoice_totals,
    calculate_account_net_balance
)


def test_validate_journal_balance_balanced():
    lines = [
        {"account_code": "1010", "debit": Decimal("150000.00"), "credit": Decimal("0.00")},
        {"account_code": "3010", "debit": Decimal("0.00"), "credit": Decimal("150000.00")},
    ]
    is_balanced, debits, credits, diff = validate_journal_balance(lines)
    assert is_balanced is True
    assert debits == Decimal("150000.00")
    assert credits == Decimal("150000.00")
    assert diff == Decimal("0.00")


def test_validate_journal_balance_unbalanced():
    lines = [
        {"account_code": "1010", "debit": Decimal("150000.00"), "credit": Decimal("0.00")},
        {"account_code": "3010", "debit": Decimal("0.00"), "credit": Decimal("140000.00")},
    ]
    is_balanced, debits, credits, diff = validate_journal_balance(lines)
    assert is_balanced is False
    assert debits == Decimal("150000.00")
    assert credits == Decimal("140000.00")
    assert diff == Decimal("10000.00")


def test_calculate_invoice_totals_with_tax():
    lines = [
        {"quantity": 2, "unit_price": 5000, "amount": 10000},
        {"quantity": 1, "unit_price": 2500, "amount": 2500},
    ]
    totals = calculate_invoice_totals(lines, tax_rate_percent=18)
    assert totals["subtotal"] == Decimal("12500.00")
    assert totals["tax_amount"] == Decimal("2250.00")
    assert totals["total_amount"] == Decimal("14750.00")


def test_calculate_invoice_totals_zero_tax():
    lines = [
        {"quantity": 3, "unit_price": 1000, "amount": 3000},
    ]
    totals = calculate_invoice_totals(lines, tax_rate_percent=0)
    assert totals["subtotal"] == Decimal("3000.00")
    assert totals["tax_amount"] == Decimal("0.00")
    assert totals["total_amount"] == Decimal("3000.00")


def test_calculate_account_net_balance_rules():
    # Asset: normal balance is Debit (Debits - Credits)
    asset_bal = calculate_account_net_balance("ASSET", total_debits=1000, total_credits=300)
    assert asset_bal == Decimal("700.00")

    # Liability: normal balance is Credit (Credits - Debits)
    liab_bal = calculate_account_net_balance("LIABILITY", total_debits=200, total_credits=1000)
    assert liab_bal == Decimal("800.00")

    # Revenue: normal balance is Credit
    rev_bal = calculate_account_net_balance("REVENUE", total_debits=50, total_credits=5000)
    assert rev_bal == Decimal("4950.00")

    # Expense: normal balance is Debit
    exp_bal = calculate_account_net_balance("EXPENSE", total_debits=1200, total_credits=100)
    assert exp_bal == Decimal("1100.00")
