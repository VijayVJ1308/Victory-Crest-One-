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
