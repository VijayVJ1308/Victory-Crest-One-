"""Victory Crest One - Unit Tests for CRM & Sales Calculations
"""

from decimal import Decimal
from shared.calculations import (
    get_default_stage_probability,
    calculate_weighted_pipeline,
    calculate_win_rate
)


def test_default_stage_probabilities():
    assert get_default_stage_probability("QUALIFICATION") == 10
    assert get_default_stage_probability("needs_analysis") == 30
    assert get_default_stage_probability("PROPOSAL") == 60
    assert get_default_stage_probability("NEGOTIATION") == 80
    assert get_default_stage_probability("CLOSED_WON") == 100
    assert get_default_stage_probability("CLOSED_LOST") == 0


def test_calculate_weighted_pipeline():
    deals = [
        {"stage": "PROPOSAL", "amount": Decimal("100000.00"), "probability_percent": 60},
        {"stage": "NEGOTIATION", "amount": Decimal("200000.00"), "probability_percent": 80},
        {"stage": "CLOSED_LOST", "amount": Decimal("50000.00"), "probability_percent": 0},  # Excluded from active pipeline
    ]
    total_val, weighted_val = calculate_weighted_pipeline(deals)
    assert total_val == Decimal("300000.00")
    # 100k*60% + 200k*80% = 60k + 160k = 220k
    assert weighted_val == Decimal("220000.00")


def test_calculate_win_rate_standard():
    rate = calculate_win_rate(won_count=3, lost_count=1)
    # 3 / 4 * 100 = 75.00%
    assert rate == Decimal("75.00")


def test_calculate_win_rate_zero():
    rate = calculate_win_rate(won_count=0, lost_count=0)
    assert rate == Decimal("0.00")
