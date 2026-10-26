"""Victory Crest One - Unit Tests for Data Lakehouse & Predictive ML Calculations
"""

from decimal import Decimal
import pytest

from shared.calculations import (
    calculate_lake_storage_efficiency,
    evaluate_demand_forecast,
    calculate_guest_churn_risk,
    calculate_lakehouse_metrics
)


def test_calculate_lake_storage_efficiency_standard():
    # 100 MB uncompressed vs 25 MB Parquet -> 4x compression, 75 MB saved (75%)
    res = calculate_lake_storage_efficiency(104857600, 26214400)
    assert res["compression_ratio"] == Decimal("4.00")
    assert res["bytes_saved"] == Decimal("78643200.00")
    assert res["space_reduction_percent"] == Decimal("75.00")


def test_calculate_lake_storage_efficiency_zero_guard():
    res = calculate_lake_storage_efficiency(0, 0)
    assert res["compression_ratio"] == Decimal("1.00")
    assert res["bytes_saved"] == Decimal("0.00")
    assert res["space_reduction_percent"] == Decimal("0.00")


def test_evaluate_demand_forecast_nominal():
    res = evaluate_demand_forecast(base_demand=65.0, seasonality_factor=1.0, event_multiplier=1.0, base_rate=5000.0)
    assert res["predicted_demand"] == Decimal("65.00")
    assert res["confidence_lower"] == Decimal("59.80")
    assert res["confidence_upper"] == Decimal("70.20")
    assert res["recommended_rate"] == Decimal("5000.00")
    assert res["pricing_tier"] == "NOMINAL"


def test_evaluate_demand_forecast_surge_and_discount():
    # High demand (surge > 90%)
    res_surge = evaluate_demand_forecast(base_demand=80.0, seasonality_factor=1.2, event_multiplier=1.0, base_rate=5000.0)
    assert res_surge["predicted_demand"] == Decimal("96.00")
    assert res_surge["recommended_rate"] == Decimal("6250.00")  # 5000 * 1.25
    assert res_surge["pricing_tier"] == "SURGE"

    # Low demand (< 50%) -> discount
    res_disc = evaluate_demand_forecast(base_demand=40.0, seasonality_factor=1.0, event_multiplier=1.0, base_rate=5000.0)
    assert res_disc["predicted_demand"] == Decimal("40.00")
    assert res_disc["recommended_rate"] == Decimal("4250.00")  # 5000 * 0.85
    assert res_disc["pricing_tier"] == "DISCOUNT"


def test_calculate_guest_churn_risk_active_and_dormant():
    # Frequent active guest: 30 days inactive, 6 bookings -> LOW risk
    prob, tier = calculate_guest_churn_risk(days_since_last_stay=30, total_bookings=6, nps_rating=10)
    assert prob < Decimal("40.00")
    assert tier == "LOW"

    # Long inactive detractor: 300 days inactive, 1 booking, NPS 4 -> CRITICAL risk
    prob_crit, tier_crit = calculate_guest_churn_risk(days_since_last_stay=300, total_bookings=1, nps_rating=4)
    assert prob_crit >= Decimal("70.00")
    assert tier_crit == "CRITICAL"


def test_calculate_lakehouse_metrics():
    datasets = [
        {"dataset_code": "DS-GL", "size_bytes": 10485760, "raw_size_bytes": 41943040},  # 10 MB parq vs 40 MB raw
        {"dataset_code": "DS-FOL", "size_bytes": 5242880, "raw_size_bytes": 15728640},  # 5 MB parq vs 15 MB raw
    ]
    pipelines = [
        {"status": "COMPLETED", "records_processed": 50000},
        {"status": "COMPLETED", "records_processed": 30000},
    ]
    models = [
        {"accuracy_score": 0.945},
        {"accuracy_score": 0.885},
    ]

    metrics = calculate_lakehouse_metrics(pipelines, datasets, models)
    assert metrics["total_datasets"] == 2
    assert metrics["total_parquet_size_mb"] == Decimal("15.00")
    assert metrics["total_raw_size_mb"] == Decimal("55.00")
    assert metrics["overall_compression_ratio"] == Decimal("3.67")
    assert metrics["daily_records_ingested"] == 80000
    assert metrics["pipeline_success_rate_percent"] == Decimal("100.00")
    assert metrics["deployed_ml_models_count"] == 2
    assert metrics["avg_model_accuracy_percent"] == Decimal("91.50")
