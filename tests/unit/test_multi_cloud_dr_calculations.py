"""Victory Crest One - Unit Tests for Multi-Cloud Resiliency & Autonomous DR Calculations
"""

from decimal import Decimal
from datetime import datetime, timezone, timedelta
import pytest

from shared.calculations import (
    calculate_replication_lag,
    calculate_dr_rto_rpo_metrics,
    calculate_chaos_resiliency_score,
)


def test_calculate_replication_lag_tiers():
    now = datetime.now(timezone.utc)

    # 1. Zero-RPO synchronized (<1s lag)
    lag_0, tier_0 = calculate_replication_lag(last_sync_timestamp=now - timedelta(milliseconds=250), current_timestamp=now)
    assert lag_0 < Decimal("1.000")
    assert tier_0 == "SYNCHRONIZED_ZERO_RPO"

    # 2. Nominal standby (<5s lag)
    lag_nom, tier_nom = calculate_replication_lag(last_sync_timestamp=now - timedelta(seconds=3), current_timestamp=now)
    assert lag_nom == Decimal("3.000")
    assert tier_nom == "NOMINAL_STANDBY"

    # 3. Elevated lag (<30s)
    lag_elev, tier_elev = calculate_replication_lag(last_sync_timestamp=now - timedelta(seconds=15), current_timestamp=now)
    assert lag_elev == Decimal("15.000")
    assert tier_elev == "ELEVATED_LAG"

    # 4. Desynchronized alert (>=30s)
    lag_desync, tier_desync = calculate_replication_lag(last_sync_timestamp=now - timedelta(seconds=45), current_timestamp=now)
    assert lag_desync == Decimal("45.000")
    assert tier_desync == "DESYNCHRONIZED_ALERT"


def test_calculate_dr_rto_rpo_metrics():
    nodes = [
        {"provider": "AWS", "role": "PRIMARY", "health_status": "HEALTHY", "replication_lag_seconds": 0.000},
        {"provider": "AZURE", "role": "HOT_STANDBY", "health_status": "HEALTHY", "replication_lag_seconds": 0.120},
        {"provider": "GCP", "role": "HOT_STANDBY", "health_status": "STANDBY", "replication_lag_seconds": 0.450},
        {"provider": "ON_PREMISE", "role": "WITNESS", "health_status": "HEALTHY", "replication_lag_seconds": 0.050},
    ]
    drills = [
        {"drill_type": "ZONE_OUTAGE", "status": "SUCCEEDED", "actual_rto_seconds": 4.5, "actual_rpo_seconds": 0.0},
        {"drill_type": "DATABASE_SPLIT_BRAIN", "status": "SUCCEEDED", "actual_rto_seconds": 5.2, "actual_rpo_seconds": 0.1},
    ]

    metrics = calculate_dr_rto_rpo_metrics(nodes, drills, target_rto_seconds=30.0, target_rpo_seconds=1.0)
    assert metrics["total_nodes"] == 4
    assert metrics["healthy_nodes"] == 4
    assert metrics["active_primary_count"] == 1
    assert metrics["hot_standby_count"] == 2
    assert metrics["cluster_availability_percent"] == Decimal("100.00")
    assert metrics["max_replication_lag_seconds"] == Decimal("0.450")
    assert metrics["total_drills"] == 2
    assert metrics["drill_success_rate_percent"] == Decimal("100.00")
    assert metrics["avg_actual_rto_seconds"] == Decimal("4.85")
    assert metrics["rto_sla_met"] is True
    assert metrics["rpo_sla_met"] is True
    assert metrics["is_zero_rpo_compliant"] is True


def test_calculate_chaos_resiliency_score_tier_4():
    # 4 distinct cloud environments (AWS, Azure, GCP, On-Premise), healthy hot standby, 100% drill pass, low lag
    nodes = [
        {"provider": "AWS", "role": "PRIMARY", "health_status": "HEALTHY", "replication_lag_seconds": 0.000},
        {"provider": "AZURE", "role": "HOT_STANDBY", "health_status": "HEALTHY", "replication_lag_seconds": 0.120},
        {"provider": "GCP", "role": "HOT_STANDBY", "health_status": "STANDBY", "replication_lag_seconds": 0.250},
        {"provider": "ON_PREMISE", "role": "WITNESS", "health_status": "HEALTHY", "replication_lag_seconds": 0.080},
    ]
    drills = [
        {"status": "SUCCEEDED"},
        {"status": "SUCCEEDED"},
    ]

    score, tier = calculate_chaos_resiliency_score(nodes, drills)
    assert score == Decimal("100.00")
    assert tier == "TIER_4_FAULT_TOLERANT"


def test_calculate_chaos_resiliency_score_penalties():
    # Only 1 provider (AWS), no hot standby, degraded node, high lag
    nodes = [
        {"provider": "AWS", "role": "PRIMARY", "health_status": "DEGRADED", "replication_lag_seconds": 35.000},
    ]
    drills = [
        {"status": "FAILED"},
    ]

    score, tier = calculate_chaos_resiliency_score(nodes, drills)
    # Deductions: single provider (-25) + no hot standby (-25) + degraded node (-10) + lag > 30s (-20) + drill fail (-15) = -95
    assert score <= Decimal("10.00")
    assert tier == "TIER_1_VULNERABLE"
