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





