"""Victory Crest One - System Calculations
Decimal-safe and zero-division-protected calculation functions for KPIs, hospitality, finance, and CRM.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional

Number = Union[int, float, Decimal]


def to_decimal(val: Optional[Number], default: str = "0.00") -> Decimal:
    """Safely convert any numeric value to Decimal."""
    if val is None:
        return Decimal(default)
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal(default)


def calculate_occupancy_rate(
    occupied_sellable_rooms: Number,
    available_sellable_rooms: Number
) -> Decimal:
    """
    Occupancy Rate = (Occupied sellable room nights / Available sellable room nights) * 100.
    Safely handles zero denominator.
    """
    available = to_decimal(available_sellable_rooms)
    if available <= Decimal("0"):
        return Decimal("0.00")
    occupied = to_decimal(occupied_sellable_rooms)
    rate = (occupied / available) * Decimal("100")
    return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_adr(
    room_revenue: Number,
    rooms_sold: Number
) -> Decimal:
    """
    Average Daily Rate (ADR) = Room revenue / Rooms sold.
    Safely handles zero rooms sold.
    """
    sold = to_decimal(rooms_sold)
    if sold <= Decimal("0"):
        return Decimal("0.00")
    revenue = to_decimal(room_revenue)
    adr = revenue / sold
    return adr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_revpar(
    room_revenue: Number,
    available_sellable_rooms: Number
) -> Decimal:
    """
    Revenue Per Available Room (RevPAR) = Room revenue / Available sellable room nights.
    """
    available = to_decimal(available_sellable_rooms)
    if available <= Decimal("0"):
        return Decimal("0.00")
    revenue = to_decimal(room_revenue)
    revpar = revenue / available
    return revpar.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_gross_profit(
    revenue: Number,
    direct_costs: Number
) -> Decimal:
    """
    Gross Profit = Revenue - Direct Costs.
    """
    rev = to_decimal(revenue)
    costs = to_decimal(direct_costs)
    return (rev - costs).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_budget_variance(
    actual: Number,
    budget: Number
) -> Decimal:
    """
    Budget Variance = Actual - Budget.
    """
    act = to_decimal(actual)
    bud = to_decimal(budget)
    return (act - bud).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_lead_conversion_rate(
    converted_leads: Number,
    eligible_leads: Number
) -> Decimal:
    """
    Lead Conversion Rate = (Converted Leads / Eligible Leads) * 100.
    """
    eligible = to_decimal(eligible_leads)
    if eligible <= Decimal("0"):
        return Decimal("0.00")
    converted = to_decimal(converted_leads)
    rate = (converted / eligible) * Decimal("100")
    return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validate_journal_balance(lines: list) -> tuple[bool, Decimal, Decimal, Decimal]:
    """
    Validate that total debits strictly equal total credits for a set of journal lines.
    Returns: (is_balanced, total_debits, total_credits, difference)
    """
    total_debits = Decimal("0.00")
    total_credits = Decimal("0.00")

    for line in lines:
        if isinstance(line, dict):
            deb = to_decimal(line.get("debit", 0))
            crd = to_decimal(line.get("credit", 0))
        else:
            deb = to_decimal(getattr(line, "debit", 0))
            crd = to_decimal(getattr(line, "credit", 0))
        total_debits += deb
        total_credits += crd

    diff = (total_debits - total_credits).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    is_balanced = (diff == Decimal("0.00"))
    return (
        is_balanced,
        total_debits.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        total_credits.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        diff
    )


def calculate_invoice_totals(lines: list, tax_rate_percent: Number = Decimal("0.00")) -> dict:
    """
    Calculate subtotal, tax amount, and total amount for invoice or bill lines.
    """
    subtotal = Decimal("0.00")
    for line in lines:
        if isinstance(line, dict):
            qty = to_decimal(line.get("quantity", 1))
            price = to_decimal(line.get("unit_price", 0))
            raw_amt = line.get("amount")
            line_amt = to_decimal(raw_amt) if raw_amt is not None else (qty * price)
        else:
            qty = to_decimal(getattr(line, "quantity", 1))
            price = to_decimal(getattr(line, "unit_price", 0))
            raw_amt = getattr(line, "amount", None)
            line_amt = to_decimal(raw_amt) if raw_amt is not None else (qty * price)
        subtotal += line_amt

    subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax_rate = to_decimal(tax_rate_percent)
    tax_amount = (subtotal * (tax_rate / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_amount = subtotal + tax_amount

    return {
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total_amount": total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    }


def calculate_account_net_balance(
    account_type: str,
    total_debits: Number,
    total_credits: Number
) -> Decimal:
    """
    Calculate net balance for an account based on standard normal balance rules:
    - ASSET, COGS, EXPENSE: Normal balance is DEBIT (Debits - Credits)
    - LIABILITY, EQUITY, REVENUE: Normal balance is CREDIT (Credits - Debits)
    """
    debits = to_decimal(total_debits)
    credits = to_decimal(total_credits)
    acc_type = account_type.lower()

    if acc_type in ("asset", "cogs", "expense"):
        return (debits - credits).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        return (credits - debits).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_default_stage_probability(stage: str) -> int:
    """Return standard sales pipeline probability percentage by stage."""
    probabilities = {
        "qualification": 10,
        "needs_analysis": 30,
        "proposal": 60,
        "negotiation": 80,
        "closed_won": 100,
        "closed_lost": 0,
    }
    return probabilities.get(stage.lower(), 10)


def calculate_weighted_pipeline(deals: list) -> tuple[Decimal, Decimal]:
    """
    Calculate Total Pipeline Value and Expected Weighted Revenue:
    Weighted Value = Sum(Amount * Probability / 100)
    Excludes CLOSED_LOST from active forecast.
    Returns: (total_active_pipeline, weighted_forecast_value)
    """
    total_val = Decimal("0.00")
    weighted_val = Decimal("0.00")

    for d in deals:
        if isinstance(d, dict):
            st = str(d.get("stage", "")).lower()
            amt = to_decimal(d.get("amount", 0))
            prob = int(d.get("probability_percent", get_default_stage_probability(st)))
        else:
            st = str(getattr(d, "stage", "")).lower()
            amt = to_decimal(getattr(d, "amount", 0))
            prob = int(getattr(d, "probability_percent", get_default_stage_probability(st)))

        if st == "closed_lost":
            continue

        total_val += amt
        weighted_val += (amt * Decimal(prob) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return (
        total_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        weighted_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )


def calculate_win_rate(won_count: int, lost_count: int) -> Decimal:
    """
    Win Rate = (Closed Won / (Closed Won + Closed Lost)) * 100.
    Handles zero denominator gracefully.
    """
    total_closed = won_count + lost_count
    if total_closed <= 0:
        return Decimal("0.00")
    rate = (Decimal(won_count) / Decimal(total_closed)) * Decimal("100")
    return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_pos_change(tendered_amount: Number, total_amount: Number) -> Decimal:
    """
    Calculate change to return to customer.
    Returns 0.00 if tendered is less than total or negative.
    """
    tendered = to_decimal(tendered_amount)
    total = to_decimal(total_amount)
    if tendered < total or tendered <= Decimal("0"):
        return Decimal("0.00")
    change = (tendered - total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return change


def calculate_drawer_variance(counted_cash: Number, expected_cash: Number) -> Decimal:
    """
    Calculate cash drawer variance = counted_cash - expected_cash.
    Positive value indicates overage; negative indicates shortage.
    """
    counted = to_decimal(counted_cash)
    expected = to_decimal(expected_cash)
    return (counted - expected).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_pos_order_totals(
    lines: list,
    discount_percent: Number = Decimal("0.00"),
    tax_rate_percent: Number = Decimal("0.00")
) -> dict:
    """
    Calculate itemized POS order totals:
    - Gross Subtotal
    - Discount Amount
    - Net Taxable Amount
    - Tax Amount
    - Grand Total
    """
    gross_subtotal = Decimal("0.00")
    for line in lines:
        if isinstance(line, dict):
            qty = to_decimal(line.get("quantity", 1))
            unit_price = to_decimal(line.get("unit_price", 0))
            raw_amt = line.get("total_amount") or line.get("amount")
            line_amt = to_decimal(raw_amt) if raw_amt is not None else (qty * unit_price)
        else:
            qty = to_decimal(getattr(line, "quantity", 1))
            unit_price = to_decimal(getattr(line, "unit_price", 0))
            raw_amt = getattr(line, "total_amount", None) or getattr(line, "amount", None)
            line_amt = to_decimal(raw_amt) if raw_amt is not None else (qty * unit_price)
        gross_subtotal += line_amt

    gross_subtotal = gross_subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    disc_pct = to_decimal(discount_percent)
    if disc_pct < Decimal("0"):
        disc_pct = Decimal("0.00")
    elif disc_pct > Decimal("100"):
        disc_pct = Decimal("100.00")

    discount_amount = (gross_subtotal * (disc_pct / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    taxable_amount = gross_subtotal - discount_amount

    tax_pct = to_decimal(tax_rate_percent)
    if tax_pct < Decimal("0"):
        tax_pct = Decimal("0.00")

    tax_amount = (taxable_amount * (tax_pct / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_amount = taxable_amount + tax_amount

    return {
        "subtotal": gross_subtotal,
        "discount_percent": disc_pct,
        "discount_amount": discount_amount,
        "taxable_amount": taxable_amount,
        "tax_rate_percent": tax_pct,
        "tax_amount": tax_amount,
        "total_amount": total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    }


def calculate_split_tenders(tender_list: list, total_amount: Number) -> tuple[Decimal, Decimal, bool]:
    """
    Calculate aggregate payments across multiple tenders.
    Returns: (total_tendered, remaining_balance, is_fully_paid)
    remaining_balance is 0.00 if fully paid (or overpaid).
    """
    total = to_decimal(total_amount)
    tendered = Decimal("0.00")
    for t in tender_list:
        if isinstance(t, dict):
            amt = to_decimal(t.get("amount", 0))
        else:
            amt = to_decimal(getattr(t, "amount", 0))
        tendered += amt

    tendered = tendered.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    diff = total - tendered
    if diff <= Decimal("0.00"):
        remaining = Decimal("0.00")
        is_paid = True
    else:
        remaining = diff.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        is_paid = False

    return tendered, remaining, is_paid



