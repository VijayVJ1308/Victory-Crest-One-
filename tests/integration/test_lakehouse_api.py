"""Victory Crest One - Integration Tests for Data Lakehouse & Predictive ML REST API
Verifies endpoints for Parquet datasets, ETL pipeline triggers,
ML model registry, real-time inferencing, and lakehouse KPIs.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_lake_datasets(client: TestClient):
    response = client.get("/api/v1/lakehouse/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4

    codes = [ds["dataset_code"] for ds in data]
    assert "DS-FIN-GL" in codes
    assert "DS-HOSP-FOLIOS" in codes
    assert "DS-IOT-TELEMETRY" in codes
    assert "DS-POS-COMMERCE" in codes


def test_get_lake_dataset_by_id_and_not_found(client: TestClient):
    response = client.get("/api/v1/lakehouse/datasets/ds_lake_1001")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_code"] == "DS-FIN-GL"
    assert data["format"] == "PARQUET"
    assert float(data["compression_ratio"]) > 1.0

    # 404 test
    bad = client.get("/api/v1/lakehouse/datasets/non_existent_dataset")
    assert bad.status_code == 404


def test_create_lake_dataset(client: TestClient):
    new_ds = {
        "dataset_code": "DS-CRM-LEADS",
        "name": "CRM Leads & Pipeline Deal Transitions Parquet Lake",
        "dataset_type": "FINANCIAL_LEDGER",
        "format": "PARQUET",
        "partition_key": "fiscal_year=YYYY",
        "compression_codec": "SNAPPY",
        "storage_uri": "s3://victory-lakehouse/gold/crm_leads/"
    }
    create_res = client.post("/api/v1/lakehouse/datasets", json=new_ds)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["dataset_code"] == "DS-CRM-LEADS"
    assert created["compression_codec"] == "SNAPPY"


def test_list_data_pipelines_and_run(client: TestClient):
    # 1. List pipelines
    list_res = client.get("/api/v1/lakehouse/pipelines")
    assert list_res.status_code == 200
    pipelines = list_res.json()
    assert isinstance(pipelines, list)
    assert len(pipelines) >= 4

    # 2. Trigger pipeline run
    pipe_id = pipelines[0]["id"]
    initial_records = pipelines[0]["records_processed"]
    run_res = client.post(f"/api/v1/lakehouse/pipelines/{pipe_id}/run")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["records_processed"] > initial_records
    assert float(run_data["duration_seconds"]) > 0


def test_list_ml_models(client: TestClient):
    response = client.get("/api/v1/lakehouse/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert len(models) >= 3

    codes = [m["model_code"] for m in models]
    assert "ML-DEMAND-PROP" in codes
    assert "ML-DYNAMIC-RATE" in codes
    assert "ML-GUEST-CHURN" in codes


def test_run_ml_inference_demand_and_churn(client: TestClient):
    # 1. Demand Forecaster Inference
    demand_req = {
        "model_code": "ML-DEMAND-PROP",
        "features": {
            "base_demand": 78.0,
            "seasonality_factor": 1.15,
            "event_multiplier": 1.05,
            "base_rate": 6000.0
        }
    }
    dem_res = client.post("/api/v1/lakehouse/models/ML-DEMAND-PROP/predict", json=demand_req)
    assert dem_res.status_code == 200
    dem_data = dem_res.json()
    assert dem_data["confidence"] == "HIGH"
    pred = dem_data["prediction"]
    assert "predicted_demand_percent" in pred
    assert "recommended_rate_inr" in pred
    assert pred["pricing_tier"] in ("SURGE", "PEAK", "NOMINAL", "DISCOUNT")

    # 2. Guest Churn Classifier Inference
    churn_req = {
        "model_code": "ML-GUEST-CHURN",
        "features": {
            "days_since_last_stay": 120,
            "total_bookings": 2,
            "nps_rating": 7
        }
    }
    churn_res = client.post("/api/v1/lakehouse/models/ML-GUEST-CHURN/predict", json=churn_req)
    assert churn_res.status_code == 200
    churn_data = churn_res.json()
    churn_pred = churn_data["prediction"]
    assert "churn_probability_percent" in churn_pred
    assert "risk_tier" in churn_pred
    assert churn_pred["risk_tier"] in ("LOW", "MODERATE", "CRITICAL")


def test_get_lakehouse_metrics(client: TestClient):
    response = client.get("/api/v1/lakehouse/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["total_datasets"] >= 4
    assert float(metrics["total_parquet_size_mb"]) > 0
    assert float(metrics["overall_compression_ratio"]) > 1.0
    assert metrics["active_pipelines_count"] >= 4
    assert metrics["daily_records_ingested"] > 0
    assert float(metrics["avg_model_accuracy_percent"]) > 80.0
