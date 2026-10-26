"""Victory Crest One - System Calculations
Decimal-safe and zero-division-protected calculation functions for KPIs, hospitality, finance, and CRM.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional
from datetime import datetime, timezone

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


def calculate_campaign_kpis(
    delivered: Number,
    opened: Number,
    clicked: Number,
    converted: Number,
    spend: Number,
    revenue: Number
) -> dict:
    """
    Calculate comprehensive marketing campaign telemetry KPIs:
    - Open Rate (%) = (Opened / Delivered) * 100
    - Click-Through Rate (CTR %) = (Clicked / Delivered) * 100
    - Click-to-Open Rate (CTOR %) = (Clicked / Opened) * 100
    - Conversion Rate (%) = (Converted / Delivered) * 100
    - Cost Per Acquisition (CPA) = Spend / Converted
    - Return on Ad Spend (ROAS) = Revenue / Spend
    - Return on Marketing Investment (ROMI %) = ((Revenue - Spend) / Spend) * 100
    Safely handles all zero denominators with Decimal precision.
    """
    deliv = to_decimal(delivered)
    open_cnt = to_decimal(opened)
    clk_cnt = to_decimal(clicked)
    conv_cnt = to_decimal(converted)
    spd = to_decimal(spend)
    rev = to_decimal(revenue)

    open_rate = (
        ((open_cnt / deliv) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if deliv > Decimal("0") else Decimal("0.00")
    )

    ctr = (
        ((clk_cnt / deliv) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if deliv > Decimal("0") else Decimal("0.00")
    )

    ctor = (
        ((clk_cnt / open_cnt) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if open_cnt > Decimal("0") else Decimal("0.00")
    )

    conversion_rate = (
        ((conv_cnt / deliv) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if deliv > Decimal("0") else Decimal("0.00")
    )

    cpa = (
        (spd / conv_cnt).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if conv_cnt > Decimal("0") else Decimal("0.00")
    )

    roas = (
        (rev / spd).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if spd > Decimal("0") else Decimal("0.00")
    )

    romi_pct = (
        (((rev - spd) / spd) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if spd > Decimal("0") else Decimal("0.00")
    )

    return {
        "delivered": deliv,
        "opened": open_cnt,
        "clicked": clk_cnt,
        "converted": conv_cnt,
        "spend": spd,
        "revenue": rev,
        "open_rate_percent": open_rate,
        "ctr_percent": ctr,
        "ctor_percent": ctor,
        "conversion_rate_percent": conversion_rate,
        "cpa": cpa,
        "roas": roas,
        "romi_percent": romi_pct
    }


def calculate_reorder_point(
    lead_time_days: Number,
    daily_usage: Number,
    safety_stock: Number = Decimal("0.00")
) -> Decimal:
    """
    Calculate inventory Reorder Point (ROP) = (Lead Time Days * Daily Usage) + Safety Stock.
    """
    lt = to_decimal(lead_time_days)
    usage = to_decimal(daily_usage)
    safety = to_decimal(safety_stock)
    rop = (lt * usage) + safety
    return rop.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_inventory_valuation(items: list) -> dict:
    """
    Calculate aggregate inventory valuation across stock items:
    Total Value = Sum(quantity_on_hand * unit_cost)
    """
    total_units = Decimal("0.00")
    total_val = Decimal("0.00")

    for item in items:
        if isinstance(item, dict):
            qty = to_decimal(item.get("quantity_on_hand", item.get("quantity", 0)))
            cost = to_decimal(item.get("unit_cost", item.get("cost_price", 0)))
        else:
            qty = to_decimal(getattr(item, "quantity_on_hand", getattr(item, "quantity", 0)))
            cost = to_decimal(getattr(item, "unit_cost", getattr(item, "cost_price", 0)))
        total_units += qty
        total_val += (qty * cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "total_skus": len(items),
        "total_units": total_units.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_valuation": total_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    }


def calculate_stock_variance(
    book_quantity: Number,
    counted_quantity: Number,
    unit_cost: Number
) -> dict:
    """
    Calculate stocktaking cycle count discrepancy:
    Variance Qty = Counted - Book (positive = surplus, negative = shrinkage/loss)
    Variance Value = Variance Qty * Unit Cost
    """
    book = to_decimal(book_quantity)
    counted = to_decimal(counted_quantity)
    cost = to_decimal(unit_cost)

    var_qty = (counted - book).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    var_val = (var_qty * cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "book_quantity": book,
        "counted_quantity": counted,
        "unit_cost": cost,
        "variance_quantity": var_qty,
        "variance_value": var_val,
        "is_discrepant": var_qty != Decimal("0.00")
    }


def calculate_weighted_average_cost(
    old_qty: Number,
    old_cost: Number,
    new_qty: Number,
    new_price: Number
) -> Decimal:
    """
    Calculate Weighted Average Cost (AVCO) when new stock is received:
    New Avg Cost = (Old Value + New Purchase Value) / Total Quantity.
    """
    o_qty = to_decimal(old_qty)
    o_cost = to_decimal(old_cost)
    n_qty = to_decimal(new_qty)
    n_price = to_decimal(new_price)

    tot_qty = o_qty + n_qty
    if tot_qty <= Decimal("0.00"):
        return n_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    tot_value = (o_qty * o_cost) + (n_qty * n_price)
    avg_cost = tot_value / tot_qty
    return avg_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_po_totals(lines: list, tax_rate_percent: Number = Decimal("0.00")) -> dict:
    """
    Calculate itemized Purchase Order totals: Subtotal, Tax Amount, and Grand Total.
    """
    subtotal = Decimal("0.00")
    for line in lines:
        if isinstance(line, dict):
            qty = to_decimal(line.get("quantity_ordered", line.get("quantity", 1)))
            price = to_decimal(line.get("unit_price", 0))
            raw_amt = line.get("total_amount") or line.get("amount")
            line_amt = to_decimal(raw_amt) if raw_amt is not None else (qty * price)
        else:
            qty = to_decimal(getattr(line, "quantity_ordered", getattr(line, "quantity", 1)))
            price = to_decimal(getattr(line, "unit_price", 0))
            raw_amt = getattr(line, "total_amount", None) or getattr(line, "amount", None)
            line_amt = to_decimal(raw_amt) if raw_amt is not None else (qty * price)
        subtotal += line_amt

    subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax_pct = to_decimal(tax_rate_percent)
    tax_amt = (subtotal * (tax_pct / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    grand_total = subtotal + tax_amt

    return {
        "subtotal": subtotal,
        "tax_rate_percent": tax_pct,
        "tax_amount": tax_amt,
        "total_amount": grand_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    }


def calculate_salary_breakdown(
    monthly_gross: Number,
    basic_ratio: Number = Decimal("0.50"),
    hra_ratio: Number = Decimal("0.20"),
    pf_rate: Number = Decimal("0.12"),
    tds_rate: Number = Decimal("0.05")
) -> dict:
    """
    Calculate statutory salary structure breakdown:
    Earnings: Basic, HRA, Special Allowance
    Deductions: Provident Fund (12% of basic), Professional Tax, TDS
    """
    gross = to_decimal(monthly_gross)
    b_ratio = to_decimal(basic_ratio)
    h_ratio = to_decimal(hra_ratio)
    pf_pct = to_decimal(pf_rate)
    tds_pct = to_decimal(tds_rate)

    basic = (gross * b_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    hra = (gross * h_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    conveyance = Decimal("1600.00") if gross >= Decimal("20000.00") else Decimal("800.00")
    special_allowance = gross - (basic + hra + conveyance)
    if special_allowance < Decimal("0.00"):
        special_allowance = Decimal("0.00")

    # Deductions
    pf_deduction = (basic * pf_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    pt_deduction = Decimal("200.00") if gross >= Decimal("15000.00") else Decimal("0.00")
    tds_deduction = (gross * tds_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_deductions = pf_deduction + pt_deduction + tds_deduction
    net_salary = gross - total_deductions

    return {
        "gross_salary": gross,
        "basic": basic,
        "hra": hra,
        "conveyance": conveyance,
        "special_allowance": special_allowance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "pf_deduction": pf_deduction,
        "professional_tax": pt_deduction,
        "tds_deduction": tds_deduction,
        "total_deductions": total_deductions.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "net_salary": net_salary.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    }


def calculate_leave_deduction(
    monthly_gross: Number,
    working_days: int = 30,
    unpaid_leave_days: Number = 0
) -> dict:
    """
    Calculate salary deduction for unpaid leaves (LWP - Leave Without Pay).
    """
    gross = to_decimal(monthly_gross)
    unpaid = to_decimal(unpaid_leave_days)
    if working_days <= 0 or unpaid <= Decimal("0.00"):
        return {
            "daily_rate": Decimal("0.00"),
            "unpaid_days": Decimal("0.00"),
            "deduction_amount": Decimal("0.00"),
            "adjusted_gross": gross
        }

    daily_rate = (gross / Decimal(str(working_days))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    deduction = (daily_rate * unpaid).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    adj_gross = (gross - deduction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if adj_gross < Decimal("0.00"):
        adj_gross = Decimal("0.00")

    return {
        "daily_rate": daily_rate,
        "unpaid_days": unpaid,
        "deduction_amount": deduction,
        "adjusted_gross": adj_gross
    }


def calculate_overtime_pay(
    monthly_gross: Number,
    standard_monthly_hours: int = 240,
    overtime_hours: Number = 0,
    ot_multiplier: Number = Decimal("1.50")
) -> Decimal:
    """
    Calculate overtime compensation based on hourly wage and multiplier.
    """
    gross = to_decimal(monthly_gross)
    ot_hrs = to_decimal(overtime_hours)
    mult = to_decimal(ot_multiplier)

    if standard_monthly_hours <= 0 or ot_hrs <= Decimal("0.00"):
        return Decimal("0.00")

    hourly_rate = gross / Decimal(str(standard_monthly_hours))
    ot_pay = hourly_rate * ot_hrs * mult
    return ot_pay.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_payroll_run_totals(payslips: list) -> dict:
    """
    Aggregate total gross earnings, statutory liabilities, and net pay for a monthly payroll batch.
    """
    tot_gross = Decimal("0.00")
    tot_pf = Decimal("0.00")
    tot_tds = Decimal("0.00")
    tot_pt = Decimal("0.00")
    tot_deductions = Decimal("0.00")
    tot_net = Decimal("0.00")

    for p in payslips:
        if isinstance(p, dict):
            gross = to_decimal(p.get("gross_earnings", p.get("gross_salary", 0)))
            pf = to_decimal(p.get("pf_deduction", 0))
            tds = to_decimal(p.get("tds_deduction", 0))
            pt = to_decimal(p.get("professional_tax", 0))
            ded = to_decimal(p.get("total_deductions", pf + tds + pt))
            net = to_decimal(p.get("net_pay", p.get("net_salary", gross - ded)))
        else:
            gross = to_decimal(getattr(p, "gross_earnings", getattr(p, "gross_salary", 0)))
            pf = to_decimal(getattr(p, "pf_deduction", 0))
            tds = to_decimal(getattr(p, "tds_deduction", 0))
            pt = to_decimal(getattr(p, "professional_tax", 0))
            ded = to_decimal(getattr(p, "total_deductions", pf + tds + pt))
            net = to_decimal(getattr(p, "net_pay", getattr(p, "net_salary", gross - ded)))

        tot_gross += gross
        tot_pf += pf
        tot_tds += tds
        tot_pt += pt
        tot_deductions += ded
        tot_net += net

    return {
        "total_employees": len(payslips),
        "total_gross_earnings": tot_gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_pf_liability": tot_pf.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_tds_liability": tot_tds.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_pt_liability": tot_pt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_statutory_deductions": tot_deductions.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_net_disbursement": tot_net.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    }


def calculate_attendance_rate(total_rostered_shifts: int, present_shifts: int) -> Decimal:
    """
    Calculate attendance percentage: (Present / Rostered) * 100
    """
    if total_rostered_shifts <= 0:
        return Decimal("100.00")
    rate = (Decimal(str(present_shifts)) / Decimal(str(total_rostered_shifts))) * Decimal("100.00")
    return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_service_labor_cost(
    labor_hours: Number,
    hourly_rate: Number,
    overtime_hours: Number = 0,
    overtime_multiplier: Number = 1.5
) -> Decimal:
    """
    Calculate total labor cost for service technicians:
    Regular Labor = hours * hourly_rate
    Overtime Labor = overtime_hours * hourly_rate * overtime_multiplier
    """
    hours = to_decimal(labor_hours)
    rate = to_decimal(hourly_rate)
    ot_hrs = to_decimal(overtime_hours)
    ot_mult = to_decimal(overtime_multiplier)

    if hours < Decimal("0"):
        hours = Decimal("0")
    if rate < Decimal("0"):
        rate = Decimal("0")
    if ot_hrs < Decimal("0"):
        ot_hrs = Decimal("0")

    regular_cost = hours * rate
    ot_cost = ot_hrs * rate * ot_mult
    total = regular_cost + ot_cost
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_work_order_totals(
    labor_total: Number,
    parts_total: Number,
    tax_rate_percent: Number = 18.0
) -> dict:
    """
    Calculate subtotal, tax, and grand total for a field work order or service job.
    """
    labor = to_decimal(labor_total)
    parts = to_decimal(parts_total)
    tax_rate = to_decimal(tax_rate_percent)

    if labor < Decimal("0"):
        labor = Decimal("0.00")
    if parts < Decimal("0"):
        parts = Decimal("0.00")
    if tax_rate < Decimal("0"):
        tax_rate = Decimal("0.00")

    subtotal = (labor + parts).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax_amount = (subtotal * (tax_rate / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    grand_total = (subtotal + tax_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "labor_total": labor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "parts_total": parts.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "subtotal": subtotal,
        "tax_rate_percent": tax_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "tax_amount": tax_amount,
        "grand_total": grand_total
    }


def calculate_sla_remaining_hours(
    created_at: datetime,
    sla_target_hours: Number,
    current_time: Optional[datetime] = None
) -> tuple[Decimal, bool]:
    """
    Calculate remaining hours until SLA breach.
    Returns: (remaining_hours, is_breached)
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    
    # Handle timezone differences if any
    if created_at.tzinfo is None and current_time.tzinfo is not None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    elif created_at.tzinfo is not None and current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    target_hours = to_decimal(sla_target_hours)
    elapsed_seconds = (current_time - created_at).total_seconds()
    if elapsed_seconds < 0:
        elapsed_seconds = 0
    elapsed_hours = Decimal(str(elapsed_seconds)) / Decimal("3600")

    remaining = target_hours - elapsed_hours
    is_breached = remaining <= Decimal("0.00")
    return (remaining.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), is_breached)


def calculate_sla_compliance_rate(total_resolved: int, breached_count: int) -> Decimal:
    """
    Calculate percentage of tickets resolved within SLA:
    Compliance % = ((Total Resolved - Breached) / Total Resolved) * 100
    """
    if total_resolved <= 0:
        return Decimal("100.00")
    if breached_count >= total_resolved:
        return Decimal("0.00")
    if breached_count < 0:
        breached_count = 0

    met = Decimal(str(total_resolved - breached_count))
    rate = (met / Decimal(str(total_resolved))) * Decimal("100.00")
    return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_first_contact_resolution_rate(total_tickets: int, fcr_count: int) -> Decimal:
    """
    Calculate First Contact Resolution (FCR) rate:
    FCR % = (FCR Count / Total Tickets) * 100
    """
    if total_tickets <= 0:
        return Decimal("0.00")
    if fcr_count < 0:
        fcr_count = 0
    if fcr_count > total_tickets:
        fcr_count = total_tickets

    rate = (Decimal(str(fcr_count)) / Decimal(str(total_tickets))) * Decimal("100.00")
    return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_reservation_totals(
    room_rate_per_night: Number,
    nights: int,
    meal_plan_rate: Number = 0,
    tax_rate_percent: Number = 12.0
) -> dict:
    """
    Calculate reservation room charges, meal plan charges, tax, and grand total.
    """
    rate = to_decimal(room_rate_per_night)
    n = max(1, int(nights))
    meal_rate = to_decimal(meal_plan_rate)
    tax_pct = to_decimal(tax_rate_percent)

    room_charges = (rate * Decimal(str(n))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    meal_charges = (meal_rate * Decimal(str(n))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    subtotal = room_charges + meal_charges
    tax_amount = (subtotal * (tax_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    grand_total = subtotal + tax_amount

    return {
        "room_charges": room_charges,
        "meal_charges": meal_charges,
        "subtotal": subtotal,
        "tax_rate_percent": tax_pct.quantize(Decimal("0.01")),
        "tax_amount": tax_amount,
        "grand_total": grand_total
    }


def calculate_folio_balance(lines: list) -> dict:
    """
    Calculate Guest Folio total charges, total payments, and remaining balance due.
    """
    tot_charges = Decimal("0.00")
    tot_payments = Decimal("0.00")

    for line in lines:
        if isinstance(line, dict):
            ltype = str(line.get("line_type", "")).upper()
            amt = to_decimal(line.get("amount", 0))
        else:
            ltype = str(getattr(line, "line_type", "")).upper()
            amt = to_decimal(getattr(line, "amount", 0))

        if ltype == "PAYMENT":
            tot_payments += amt
        else:
            tot_charges += amt

    balance_due = (tot_charges - tot_payments).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "total_charges": tot_charges.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_payments": tot_payments.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "balance_due": balance_due,
        "is_settled": balance_due <= Decimal("0.00")
    }


def calculate_dining_bill_totals(
    subtotal: Number,
    service_charge_percent: Number = 5.0,
    gst_percent: Number = 5.0,
    discount_amount: Number = 0
) -> dict:
    """
    Calculate restaurant food bill breakdown:
    Subtotal - Discount + Service Charge (5%) + Restaurant GST (5%) = Grand Total
    """
    sub = to_decimal(subtotal)
    disc = to_decimal(discount_amount)
    sc_pct = to_decimal(service_charge_percent)
    gst_pct = to_decimal(gst_percent)

    net_sub = max(Decimal("0.00"), sub - disc)
    sc_amt = (net_sub * (sc_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    gst_amt = (net_sub * (gst_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    grand_total = (net_sub + sc_amt + gst_amt).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "subtotal": sub.quantize(Decimal("0.01")),
        "discount_amount": disc.quantize(Decimal("0.01")),
        "net_subtotal": net_sub.quantize(Decimal("0.01")),
        "service_charge": sc_amt,
        "gst_amount": gst_amt,
        "grand_total": grand_total
    }


# ============================================================================
# Phase 12: Manufacturing & Production Orders / Bill of Materials (BOM)
# ============================================================================

def calculate_bom_line_cost(
    quantity_required: Number,
    unit_cost: Number,
    scrap_percent: Number = 0
) -> dict:
    """
    Calculate BOM component cost including scrap / shrinkage allowance:
    base_cost = quantity_required * unit_cost
    scrap_cost = base_cost * (scrap_percent / 100)
    total_line_cost = base_cost + scrap_cost
    """
    qty = max(Decimal("0.00"), to_decimal(quantity_required))
    cost = max(Decimal("0.00"), to_decimal(unit_cost))
    scrap_pct = max(Decimal("0.00"), to_decimal(scrap_percent))

    base_cost = (qty * cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    scrap_cost = (base_cost * (scrap_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_line_cost = (base_cost + scrap_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "quantity_required": qty,
        "unit_cost": cost,
        "scrap_percent": scrap_pct,
        "base_cost": base_cost,
        "scrap_cost": scrap_cost,
        "total_line_cost": total_line_cost
    }


def calculate_bom_totals(
    components: list,
    operations: list,
    batch_quantity: Number = 1
) -> dict:
    """
    Calculate full Bill of Materials totals:
    - Sum of component material costs with scrap
    - Sum of routing operations labor and machine costs: (setup_hours + run_hours_per_unit * batch_qty) * hourly_rate
    - Total BOM cost and Unit Cost per finished product.
    """
    batch_qty = max(Decimal("1.00"), to_decimal(batch_quantity))
    tot_materials = Decimal("0.00")
    tot_scrap = Decimal("0.00")

    for c in components:
        if isinstance(c, dict):
            qty = to_decimal(c.get("quantity", 0))
            cost = to_decimal(c.get("unit_cost", 0))
            scrap = to_decimal(c.get("scrap_percent", 0))
        else:
            qty = to_decimal(getattr(c, "quantity", 0))
            cost = to_decimal(getattr(c, "unit_cost", 0))
            scrap = to_decimal(getattr(c, "scrap_percent", 0))

        line_res = calculate_bom_line_cost(qty, cost, scrap)
        tot_materials += line_res["base_cost"]
        tot_scrap += line_res["scrap_cost"]

    tot_material_with_scrap = tot_materials + tot_scrap

    tot_operations = Decimal("0.00")
    for op in operations:
        if isinstance(op, dict):
            setup = to_decimal(op.get("setup_time_hours", 0))
            run_unit = to_decimal(op.get("run_time_per_unit_hours", 0))
            rate = to_decimal(op.get("hourly_rate", 0))
        else:
            setup = to_decimal(getattr(op, "setup_time_hours", 0))
            run_unit = to_decimal(getattr(op, "run_time_per_unit_hours", 0))
            rate = to_decimal(getattr(op, "hourly_rate", 0))

        total_op_hours = setup + (run_unit * batch_qty)
        op_cost = (total_op_hours * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tot_operations += op_cost

    tot_bom_cost = (tot_material_with_scrap + tot_operations).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    unit_cost = (tot_bom_cost / batch_qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "batch_quantity": batch_qty,
        "base_material_cost": tot_materials.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "scrap_material_cost": tot_scrap.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_material_cost": tot_material_with_scrap.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_operations_cost": tot_operations.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_bom_cost": tot_bom_cost,
        "unit_cost": unit_cost
    }


def calculate_production_order_cost(
    actual_materials: list,
    actual_labor_hours: Number,
    labor_hourly_rate: Number,
    overhead_cost: Number = 0,
    produced_quantity: Number = 1
) -> dict:
    """
    Calculate actual manufacturing work order cost upon completion:
    Total Cost = Materials Consumed + (Labor Hours * Rate) + Allocated Overhead
    Unit Finished Goods Cost = Total Cost / Max(1, Produced Quantity)
    """
    produced_qty = max(Decimal("1.00"), to_decimal(produced_quantity))
    tot_mat = Decimal("0.00")

    for m in actual_materials:
        if isinstance(m, dict):
            cost = to_decimal(m.get("total_cost", 0))
            if cost == Decimal("0.00") and "quantity" in m and "unit_cost" in m:
                cost = to_decimal(m["quantity"]) * to_decimal(m["unit_cost"])
        else:
            cost = to_decimal(getattr(m, "total_cost", 0))
            if cost == Decimal("0.00") and hasattr(m, "quantity") and hasattr(m, "unit_cost"):
                cost = to_decimal(getattr(m, "quantity", 0)) * to_decimal(getattr(m, "unit_cost", 0))
        tot_mat += cost

    hours = max(Decimal("0.00"), to_decimal(actual_labor_hours))
    rate = max(Decimal("0.00"), to_decimal(labor_hourly_rate))
    labor = (hours * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    overhead = max(Decimal("0.00"), to_decimal(overhead_cost)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    total_actual = (tot_mat + labor + overhead).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    unit_cost = (total_actual / produced_qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "material_cost": tot_mat.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "labor_cost": labor,
        "overhead_cost": overhead,
        "total_actual_cost": total_actual,
        "unit_actual_cost": unit_cost,
        "produced_quantity": produced_qty
    }


def calculate_manufacturing_kpis(
    orders: list,
    total_capacity_hours: Number = 0,
    actual_hours_used: Number = 0
) -> dict:
    """
    Calculate manufacturing executive KPIs:
    - Total Orders, Completed Orders, In-Progress Orders
    - Total Units Produced & Rejected
    - Scrap Rate % = Rejected / (Produced + Rejected) * 100
    - Capacity Utilization % = (Actual Hours / Total Capacity) * 100
    """
    tot_orders = len(orders)
    completed_orders = 0
    in_progress_orders = 0
    tot_produced = Decimal("0.00")
    tot_rejected = Decimal("0.00")
    tot_wip_value = Decimal("0.00")

    for o in orders:
        st = str(o.get("status", "") if isinstance(o, dict) else getattr(o, "status", "")).upper()
        p_qty = to_decimal(o.get("produced_quantity", 0) if isinstance(o, dict) else getattr(o, "produced_quantity", 0))
        r_qty = to_decimal(o.get("rejected_quantity", 0) if isinstance(o, dict) else getattr(o, "rejected_quantity", 0))
        cost = to_decimal(o.get("total_actual_cost", 0) if isinstance(o, dict) else getattr(o, "total_actual_cost", 0))

        if st == "COMPLETED":
            completed_orders += 1
            tot_produced += p_qty
            tot_rejected += r_qty
        elif st in ("IN_PROGRESS", "QUALITY_CHECK"):
            in_progress_orders += 1
            tot_wip_value += cost

    total_units = tot_produced + tot_rejected
    if total_units > Decimal("0.00"):
        scrap_rate = ((tot_rejected / total_units) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        scrap_rate = Decimal("0.00")

    cap_hrs = to_decimal(total_capacity_hours)
    used_hrs = to_decimal(actual_hours_used)
    if cap_hrs > Decimal("0.00"):
        capacity_util = ((used_hrs / cap_hrs) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        capacity_util = Decimal("0.00")

    return {
        "total_orders": tot_orders,
        "completed_orders": completed_orders,
        "in_progress_orders": in_progress_orders,
        "total_produced_units": tot_produced,
        "total_rejected_units": tot_rejected,
        "scrap_rate_percent": scrap_rate,
        "total_wip_value": tot_wip_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "capacity_utilization_percent": capacity_util
    }


# ============================================================================
# Phase 13: Project Management & Professional Services (PSA)
# ============================================================================

def calculate_project_budget_variance(
    budget_amount: Number,
    actual_cost: Number
) -> dict:
    """
    Calculate project budget variance:
    variance = budget_amount - actual_cost
    variance_pct = (variance / budget_amount) * 100
    is_over_budget = actual_cost > budget_amount
    """
    budget = max(Decimal("0.00"), to_decimal(budget_amount))
    actual = max(Decimal("0.00"), to_decimal(actual_cost))
    variance = (budget - actual).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if budget > Decimal("0.00"):
        var_pct = ((variance / budget) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        var_pct = Decimal("0.00")

    return {
        "budget_amount": budget.quantize(Decimal("0.01")),
        "actual_cost": actual.quantize(Decimal("0.01")),
        "variance": variance,
        "variance_percent": var_pct,
        "is_over_budget": actual > budget
    }


def calculate_project_burn_rate(
    total_cost: Number,
    elapsed_days: Number,
    total_project_days: Number = 0
) -> dict:
    """
    Calculate project burn rate:
    daily_burn_rate = total_cost / max(1, elapsed_days)
    projected_total = daily_burn_rate * total_project_days
    """
    cost = max(Decimal("0.00"), to_decimal(total_cost))
    elapsed = max(Decimal("1.00"), to_decimal(elapsed_days))
    total_days = max(Decimal("0.00"), to_decimal(total_project_days))

    daily_burn = (cost / elapsed).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if total_days > Decimal("0.00"):
        projected = (daily_burn * total_days).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        projected = cost

    return {
        "total_cost": cost.quantize(Decimal("0.01")),
        "elapsed_days": elapsed,
        "daily_burn_rate": daily_burn,
        "total_project_days": total_days,
        "projected_total_cost": projected
    }


def calculate_timesheet_totals(timesheets: list) -> dict:
    """
    Calculate timesheet metrics:
    - total_hours, billable_hours, non_billable_hours
    - billable_amount (hours * hourly_billing_rate)
    - labor_cost (hours * hourly_cost_rate)
    - utilization_rate = (billable_hours / total_hours) * 100
    """
    tot_hours = Decimal("0.00")
    bill_hours = Decimal("0.00")
    tot_billable_amt = Decimal("0.00")
    tot_cost_amt = Decimal("0.00")

    for t in timesheets:
        if isinstance(t, dict):
            hrs = to_decimal(t.get("hours", 0))
            is_bill = bool(t.get("is_billable", True))
            bill_rate = to_decimal(t.get("hourly_billing_rate", 0))
            cost_rate = to_decimal(t.get("hourly_cost_rate", 0))
        else:
            hrs = to_decimal(getattr(t, "hours", 0))
            is_bill = bool(getattr(t, "is_billable", True))
            bill_rate = to_decimal(getattr(t, "hourly_billing_rate", 0))
            cost_rate = to_decimal(getattr(t, "hourly_cost_rate", 0))

        tot_hours += hrs
        tot_cost_amt += hrs * cost_rate
        if is_bill:
            bill_hours += hrs
            tot_billable_amt += hrs * bill_rate

    non_bill_hours = tot_hours - bill_hours
    if tot_hours > Decimal("0.00"):
        util_rate = ((bill_hours / tot_hours) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        util_rate = Decimal("0.00")

    return {
        "total_hours": tot_hours.quantize(Decimal("0.01")),
        "billable_hours": bill_hours.quantize(Decimal("0.01")),
        "non_billable_hours": non_bill_hours.quantize(Decimal("0.01")),
        "billable_amount": tot_billable_amt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "labor_cost": tot_cost_amt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "utilization_rate": util_rate
    }


def calculate_milestone_invoice(
    milestone_amount: Number,
    tax_percent: Number = 18.0
) -> dict:
    """
    Calculate customer invoice amounts for achieved project milestone:
    subtotal = milestone_amount
    tax_amount = subtotal * (tax_percent / 100)
    grand_total = subtotal + tax_amount
    """
    sub = max(Decimal("0.00"), to_decimal(milestone_amount))
    t_pct = max(Decimal("0.00"), to_decimal(tax_percent))

    tax_amt = (sub * (t_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    grand_total = (sub + tax_amt).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "subtotal": sub.quantize(Decimal("0.01")),
        "tax_percent": t_pct.quantize(Decimal("0.01")),
        "tax_amount": tax_amt,
        "grand_total": grand_total
    }


def calculate_project_kpis(
    projects: list,
    timesheets: list,
    expenses: list
) -> dict:
    """
    Calculate executive PSA telemetry:
    - total_projects, active_projects, completed_projects
    - total_budget, total_billed, total_actual_cost, profit_margin_percent
    """
    tot_proj = len(projects)
    active_proj = 0
    completed_proj = 0
    tot_budget = Decimal("0.00")
    tot_billed = Decimal("0.00")

    for p in projects:
        st = str(p.get("status", "") if isinstance(p, dict) else getattr(p, "status", "")).upper()
        b_amt = to_decimal(p.get("budget_amount", 0) if isinstance(p, dict) else getattr(p, "budget_amount", 0))
        billed = to_decimal(p.get("billed_amount", 0) if isinstance(p, dict) else getattr(p, "billed_amount", 0))

        tot_budget += b_amt
        tot_billed += billed
        if st == "ACTIVE":
            active_proj += 1
        elif st == "COMPLETED":
            completed_proj += 1

    ts_res = calculate_timesheet_totals(timesheets)
    labor_cost = ts_res["labor_cost"]

    exp_cost = Decimal("0.00")
    for e in expenses:
        amt = to_decimal(e.get("amount", 0) if isinstance(e, dict) else getattr(e, "amount", 0))
        exp_cost += amt

    total_actual_cost = labor_cost + exp_cost
    if tot_billed > Decimal("0.00"):
        margin = (((tot_billed - total_actual_cost) / tot_billed) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        margin = Decimal("0.00")

    return {
        "total_projects": tot_proj,
        "active_projects": active_proj,
        "completed_projects": completed_proj,
        "total_budget": tot_budget.quantize(Decimal("0.01")),
        "total_billed": tot_billed.quantize(Decimal("0.01")),
        "total_labor_cost": labor_cost.quantize(Decimal("0.01")),
        "total_expense_cost": exp_cost.quantize(Decimal("0.01")),
        "total_actual_cost": total_actual_cost.quantize(Decimal("0.01")),
        "profit_margin_percent": margin,
        "overall_utilization_rate": ts_res["utilization_rate"]
    }


# ============================================================================
# Phase 14: Business Intelligence & Executive Analytics
# ============================================================================

def calculate_financial_ratios(
    revenue: Number,
    cogs: Number = 0,
    opex: Number = 0,
    depreciation: Number = 0,
    interest: Number = 0,
    tax: Number = 0,
    current_assets: Number = 0,
    current_liabilities: Number = 0,
    total_assets: Number = 0,
    total_equity: Number = 0
) -> dict:
    """
    Compute executive financial health ratios:
    - Gross Profit & Gross Margin %
    - Gross Operating Profit (GOP) & GOP Margin %
    - EBIT / Operating Income & Operating Margin %
    - EBITDA & EBITDA Margin %
    - Net Income & Net Profit Margin %
    - Current Ratio (Liquidity)
    - Return on Assets (ROA %) & Return on Equity (ROE %)
    """
    rev = max(Decimal("0.00"), to_decimal(revenue))
    c = max(Decimal("0.00"), to_decimal(cogs))
    op = max(Decimal("0.00"), to_decimal(opex))
    dep = max(Decimal("0.00"), to_decimal(depreciation))
    intr = max(Decimal("0.00"), to_decimal(interest))
    tx = max(Decimal("0.00"), to_decimal(tax))
    ca = max(Decimal("0.00"), to_decimal(current_assets))
    cl = max(Decimal("0.00"), to_decimal(current_liabilities))
    ta = max(Decimal("0.00"), to_decimal(total_assets))
    te = max(Decimal("0.00"), to_decimal(total_equity))

    gross_profit = rev - c
    gross_margin_pct = ((gross_profit / rev) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if rev > Decimal("0.00") else Decimal("0.00")

    # GOP (Gross Operating Profit) standard: Revenue minus direct operational delivery costs
    gop = gross_profit - (op * Decimal("0.40"))  # direct operational opex
    gop_margin_pct = ((gop / rev) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if rev > Decimal("0.00") else Decimal("0.00")

    # EBIT (Operating Income) = Gross Profit - Total OPEX
    ebit = gross_profit - op
    operating_margin_pct = ((ebit / rev) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if rev > Decimal("0.00") else Decimal("0.00")

    # EBITDA = EBIT + Depreciation & Amortization
    ebitda = ebit + dep
    ebitda_margin_pct = ((ebitda / rev) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if rev > Decimal("0.00") else Decimal("0.00")

    # Net Income = EBIT - Interest - Tax
    net_income = ebit - intr - tx
    net_margin_pct = ((net_income / rev) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if rev > Decimal("0.00") else Decimal("0.00")

    # Liquidity: Current Ratio = Current Assets / Current Liabilities
    if cl > Decimal("0.00"):
        current_ratio = (ca / cl).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        current_ratio = Decimal("0.00")

    # Profitability Ratios: ROA & ROE
    roa_pct = ((net_income / ta) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if ta > Decimal("0.00") else Decimal("0.00")
    roe_pct = ((net_income / te) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if te > Decimal("0.00") else Decimal("0.00")

    return {
        "revenue": rev.quantize(Decimal("0.01")),
        "gross_profit": gross_profit.quantize(Decimal("0.01")),
        "gross_margin_percent": gross_margin_pct,
        "gop": gop.quantize(Decimal("0.01")),
        "gop_margin_percent": gop_margin_pct,
        "ebit": ebit.quantize(Decimal("0.01")),
        "operating_margin_percent": operating_margin_pct,
        "ebitda": ebitda.quantize(Decimal("0.01")),
        "ebitda_margin_percent": ebitda_margin_pct,
        "net_income": net_income.quantize(Decimal("0.01")),
        "net_margin_percent": net_margin_pct,
        "current_ratio": current_ratio,
        "roa_percent": roa_pct,
        "roe_percent": roe_pct
    }


def calculate_portfolio_kpis(properties_data: list) -> dict:
    """
    Consolidate multi-property enterprise performance:
    - Total consolidated revenue & GOP
    - Blended occupancy %, Average ADR, RevPAR
    - Breakdown of room, dining, retail, and service revenues
    """
    tot_rev = Decimal("0.00")
    tot_gop = Decimal("0.00")
    tot_rooms_rev = Decimal("0.00")
    tot_dining_rev = Decimal("0.00")
    tot_retail_rev = Decimal("0.00")
    tot_service_rev = Decimal("0.00")

    occ_weighted_sum = Decimal("0.00")
    adr_weighted_sum = Decimal("0.00")
    total_available_rooms = Decimal("0.00")

    for p in properties_data:
        r = to_decimal(p.get("revenue", p.get("total_revenue", 0)))
        g = to_decimal(p.get("gop", 0))
        rr = to_decimal(p.get("rooms_revenue", p.get("room_revenue", 0)))
        dr = to_decimal(p.get("dining_revenue", 0))
        rt = to_decimal(p.get("retail_revenue", 0))
        sr = to_decimal(p.get("service_revenue", 0))

        tot_rev += r
        tot_gop += g
        tot_rooms_rev += rr
        tot_dining_rev += dr
        tot_retail_rev += rt
        tot_service_rev += sr

        rooms = to_decimal(p.get("available_rooms", p.get("rooms_count", 50)))
        total_available_rooms += rooms

        occ = to_decimal(p.get("occupancy_percent", 0))
        adr = to_decimal(p.get("adr", 0))
        occ_weighted_sum += (occ * rooms)
        adr_weighted_sum += (adr * rooms)

    if total_available_rooms > Decimal("0.00"):
        blended_occ = (occ_weighted_sum / total_available_rooms).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        avg_adr = (adr_weighted_sum / total_available_rooms).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        blended_occ = Decimal("0.00")
        avg_adr = Decimal("0.00")

    blended_revpar = ((blended_occ / Decimal("100.00")) * avg_adr).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    gop_margin = ((tot_gop / tot_rev) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if tot_rev > Decimal("0.00") else Decimal("0.00")

    return {
        "total_properties": len(properties_data),
        "total_revenue": tot_rev.quantize(Decimal("0.01")),
        "total_gop": tot_gop.quantize(Decimal("0.01")),
        "gop_margin_percent": gop_margin,
        "total_rooms_revenue": tot_rooms_rev.quantize(Decimal("0.01")),
        "total_dining_revenue": tot_dining_rev.quantize(Decimal("0.01")),
        "total_retail_revenue": tot_retail_rev.quantize(Decimal("0.01")),
        "total_service_revenue": tot_service_rev.quantize(Decimal("0.01")),
        "blended_occupancy_percent": blended_occ,
        "average_adr": avg_adr,
        "blended_revpar": blended_revpar
    }


def calculate_department_contributions(departments_data: list) -> list:
    """
    Calculate department revenue share and profit margins for executive P&L ranking.
    """
    total_rev = Decimal("0.00")
    for d in departments_data:
        total_rev += to_decimal(d.get("revenue", 0))

    results = []
    for d in departments_data:
        rev = to_decimal(d.get("revenue", 0))
        exp = to_decimal(d.get("expenses", 0))
        net = rev - exp

        share = ((rev / total_rev) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if total_rev > Decimal("0.00") else Decimal("0.00")
        margin = ((net / rev) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if rev > Decimal("0.00") else Decimal("0.00")

        results.append({
            "department": d.get("department", "General"),
            "revenue": rev.quantize(Decimal("0.01")),
            "expenses": exp.quantize(Decimal("0.01")),
            "net_profit": net.quantize(Decimal("0.01")),
            "profit_margin_percent": margin,
            "revenue_share_percent": share
        })

    # Sort descending by revenue
    results.sort(key=lambda x: x["revenue"], reverse=True)
    return results


def calculate_linear_forecast(historical_points: list, periods_ahead: int = 1) -> dict:
    """
    Simple linear trend regression for revenue trajectory forecasting:
    y = mx + b
    Returns forecast values, average growth rate, and predicted next period.
    """
    if not historical_points:
        return {
            "forecast_values": [Decimal("0.00")] * periods_ahead,
            "next_period_prediction": Decimal("0.00"),
            "growth_rate_percent": Decimal("0.00"),
            "historical_mean": Decimal("0.00")
        }

    points = [to_decimal(p) for p in historical_points]
    n = len(points)
    if n == 1:
        return {
            "forecast_values": [points[0]] * periods_ahead,
            "next_period_prediction": points[0],
            "growth_rate_percent": Decimal("0.00"),
            "historical_mean": points[0]
        }

    x_vals = [Decimal(i) for i in range(n)]
    sum_x = sum(x_vals)
    sum_y = sum(points)
    sum_xx = sum(x * x for x in x_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, points))

    denom = (Decimal(n) * sum_xx) - (sum_x * sum_x)
    if denom == Decimal("0.00"):
        slope = Decimal("0.00")
        intercept = sum_y / Decimal(n)
    else:
        slope = ((Decimal(n) * sum_xy) - (sum_x * sum_y)) / denom
        intercept = (sum_y - (slope * sum_x)) / Decimal(n)

    forecast_vals = []
    for k in range(1, periods_ahead + 1):
        pred = max(Decimal("0.00"), (slope * Decimal(n - 1 + k)) + intercept)
        forecast_vals.append(pred.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    # Growth rate from first to last point
    first_pt = points[0]
    last_pt = points[-1]
    if first_pt > Decimal("0.00"):
        growth = (((last_pt - first_pt) / first_pt) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        growth = Decimal("0.00")

    mean_val = (sum_y / Decimal(n)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "forecast_values": forecast_vals,
        "next_period_prediction": forecast_vals[0],
        "growth_rate_percent": growth,
        "historical_mean": mean_val
    }








