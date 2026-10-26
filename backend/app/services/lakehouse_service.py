"""Victory Crest One - Data Lakehouse & Predictive ML Service
Orchestrates distributed Apache Parquet dataset partitions, scheduled ETL compactions,
and real-time machine learning inference engines.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timezone
import time
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.lakehouse import (
    LakeDatasetCreate,
    LakeDatasetOut,
    DataPipelineJobCreate,
    DataPipelineJobOut,
    MlModelOut,
    MlInferenceRequest,
    MlInferenceResponse,
    LakehouseMetricsOut
)
from shared.enums import (
    LakeDatasetType,
    PipelineRunStatus,
    MlModelType,
    PredictionConfidence,
    DatasetFormat
)
from shared.calculations import (
    to_decimal,
    calculate_lake_storage_efficiency,
    evaluate_demand_forecast,
    calculate_guest_churn_risk,
    calculate_lakehouse_metrics
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory stores
_DATASETS_STORE: Dict[str, Dict[str, Any]] = {}
_PIPELINES_STORE: Dict[str, Dict[str, Any]] = {}
_ML_MODELS_STORE: Dict[str, Dict[str, Any]] = {}
_DATASET_COUNTER = 1005
_PIPELINE_COUNTER = 1005


def _seed_lakehouse_data():
    """Seed default Parquet datasets, ETL pipelines, and ML model registry."""
    global _DATASET_COUNTER, _PIPELINE_COUNTER
    if _DATASETS_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]
    now = datetime.now(timezone.utc)

    # 1. Columnar Datasets (Apache Parquet)
    seed_datasets = [
        {
            "id": "ds_lake_1001",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "dataset_code": "DS-FIN-GL",
            "name": "Financial General Ledger Parquet Archive",
            "dataset_type": LakeDatasetType.FINANCIAL_LEDGER.value,
            "format": DatasetFormat.PARQUET.value,
            "partition_key": "year=YYYY/quarter=Q",
            "record_count": 145000,
            "size_bytes": Decimal("12582912.00"),      # 12 MB
            "raw_size_bytes": Decimal("46137344.00"),  # 44 MB
            "compression_ratio": Decimal("3.67"),
            "compression_codec": "SNAPPY",
            "storage_uri": "s3://victory-lakehouse/gold/gl_transactions/",
            "last_compacted_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "ds_lake_1002",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "dataset_code": "DS-HOSP-FOLIOS",
            "name": "Hospitality Folios & Guest Billing Lake",
            "dataset_type": LakeDatasetType.GUEST_FOLIOS.value,
            "format": DatasetFormat.PARQUET.value,
            "partition_key": "property=PROP/year=YYYY",
            "record_count": 89000,
            "size_bytes": Decimal("8388608.00"),       # 8 MB
            "raw_size_bytes": Decimal("29360128.00"),  # 28 MB
            "compression_ratio": Decimal("3.50"),
            "compression_codec": "SNAPPY",
            "storage_uri": "s3://victory-lakehouse/gold/hospitality_folios/",
            "last_compacted_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "ds_lake_1003",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "dataset_code": "DS-IOT-TELEMETRY",
            "name": "Edge Sensor Telemetry Timeseries Lake",
            "dataset_type": LakeDatasetType.IOT_SENSOR_STREAM.value,
            "format": DatasetFormat.PARQUET.value,
            "partition_key": "device_type=TYPE/date=YYYY-MM-DD",
            "record_count": 520000,
            "size_bytes": Decimal("33554432.00"),      # 32 MB
            "raw_size_bytes": Decimal("134217728.00"), # 128 MB
            "compression_ratio": Decimal("4.00"),
            "compression_codec": "SNAPPY",
            "storage_uri": "s3://victory-lakehouse/silver/iot_telemetry/",
            "last_compacted_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "ds_lake_1004",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "dataset_code": "DS-POS-COMMERCE",
            "name": "POS & Omnichannel Commerce Parquet Store",
            "dataset_type": LakeDatasetType.POS_COMMERCE_TRANSACTIONS.value,
            "format": DatasetFormat.PARQUET.value,
            "partition_key": "property=PROP/date=YYYY-MM-DD",
            "record_count": 210000,
            "size_bytes": Decimal("18874368.00"),      # 18 MB
            "raw_size_bytes": Decimal("67108864.00"),  # 64 MB
            "compression_ratio": Decimal("3.56"),
            "compression_codec": "SNAPPY",
            "storage_uri": "s3://victory-lakehouse/gold/pos_transactions/",
            "last_compacted_at": now,
            "is_active": True,
            "created_at": now
        }
    ]

    for ds in seed_datasets:
        _DATASETS_STORE[ds["id"]] = ds

    # 2. ETL Pipelines & Batch Compactor Jobs
    seed_pipelines = [
        {
            "id": "pipe_1001",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "pipeline_code": "ETL-GL-NIGHTLY",
            "name": "Finance GL Double-Entry Ingestion & Compactor",
            "source_module": "finance",
            "target_dataset_code": "DS-FIN-GL",
            "schedule_cron": "0 1 * * *",
            "status": PipelineRunStatus.COMPLETED.value,
            "records_processed": 14500,
            "duration_seconds": Decimal("4.20"),
            "last_run_at": now,
            "error_log": None,
            "created_at": now
        },
        {
            "id": "pipe_1002",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "pipeline_code": "ETL-FOLIOS-SYNC",
            "name": "Night Audit Folio Reconciliation & Partition Sync",
            "source_module": "hospitality",
            "target_dataset_code": "DS-HOSP-FOLIOS",
            "schedule_cron": "30 2 * * *",
            "status": PipelineRunStatus.COMPLETED.value,
            "records_processed": 8200,
            "duration_seconds": Decimal("2.80"),
            "last_run_at": now,
            "error_log": None,
            "created_at": now
        },
        {
            "id": "pipe_1003",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "pipeline_code": "ETL-IOT-HOURLY",
            "name": "IoT Sensor Stream Micro-Batch Parquet Packager",
            "source_module": "iot_gateways",
            "target_dataset_code": "DS-IOT-TELEMETRY",
            "schedule_cron": "0 * * * *",
            "status": PipelineRunStatus.COMPLETED.value,
            "records_processed": 45000,
            "duration_seconds": Decimal("6.50"),
            "last_run_at": now,
            "error_log": None,
            "created_at": now
        },
        {
            "id": "pipe_1004",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "pipeline_code": "ETL-POS-STREAM",
            "name": "POS Commerce Transaction Stream & Revenue Rollup",
            "source_module": "pos",
            "target_dataset_code": "DS-POS-COMMERCE",
            "schedule_cron": "*/15 * * * *",
            "status": PipelineRunStatus.COMPLETED.value,
            "records_processed": 19500,
            "duration_seconds": Decimal("1.90"),
            "last_run_at": now,
            "error_log": None,
            "created_at": now
        }
    ]

    for p in seed_pipelines:
        _PIPELINES_STORE[p["id"]] = p

    # 3. Predictive Machine Learning Models
    seed_models = [
        {
            "id": "ml_mod_1001",
            "organization_id": org_id,
            "model_code": "ML-DEMAND-PROP",
            "name": "Hospitality Occupancy & Dining Demand Forecaster",
            "model_type": MlModelType.DEMAND_FORECAST_REGRESSOR.value,
            "algorithm": "Prophet TimeSeries + LightGBM Regressor",
            "version": "v2.1.0",
            "accuracy_score": Decimal("0.9420"),
            "feature_drift_percent": Decimal("1.20"),
            "status": "DEPLOYED",
            "parameters_json": '{"horizon_days": 30, "seasonality_prior": 10.0, "changepoint_prior": 0.05}',
            "trained_at": now
        },
        {
            "id": "ml_mod_1002",
            "organization_id": org_id,
            "model_code": "ML-DYNAMIC-RATE",
            "name": "RevPAR Dynamic Rate Elasticity Optimizer",
            "model_type": MlModelType.DYNAMIC_RATE_OPTIMIZER.value,
            "algorithm": "Reinforcement Elasticity Pricing Model",
            "version": "v1.8.4",
            "accuracy_score": Decimal("0.9150"),
            "feature_drift_percent": Decimal("2.10"),
            "status": "DEPLOYED",
            "parameters_json": '{"max_surge_pct": 25, "min_discount_pct": 15, "lead_time_decay": 0.02}',
            "trained_at": now
        },
        {
            "id": "ml_mod_1003",
            "organization_id": org_id,
            "model_code": "ML-GUEST-CHURN",
            "name": "Guest Churn & Loyalty Retention Classifier",
            "model_type": MlModelType.GUEST_CHURN_CLASSIFIER.value,
            "algorithm": "XGBoost Classifier + SHAP Explainability",
            "version": "v3.0.1",
            "accuracy_score": Decimal("0.9380"),
            "feature_drift_percent": Decimal("0.85"),
            "status": "DEPLOYED",
            "parameters_json": '{"max_depth": 6, "learning_rate": 0.05, "n_estimators": 200}',
            "trained_at": now
        }
    ]

    for m in seed_models:
        _ML_MODELS_STORE[m["id"]] = m


class LakehouseService:
    """Enterprise Data Lakehouse & Predictive Machine Learning Service Engine."""

    def __init__(self):
        _seed_lakehouse_data()

    def get_datasets(
        self,
        org_id: Optional[str] = None,
        property_id: Optional[str] = None,
        dataset_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve columnar datasets catalog with storage efficiencies."""
        _seed_lakehouse_data()
        results = list(_DATASETS_STORE.values())

        if org_id:
            results = [ds for ds in results if ds.get("organization_id") == org_id]
        if property_id:
            results = [ds for ds in results if ds.get("property_id") in (None, property_id)]
        if dataset_type:
            results = [ds for ds in results if str(ds.get("dataset_type", "")).upper() == dataset_type.upper()]

        return sorted(results, key=lambda x: x["dataset_code"])

    def get_dataset_by_id(self, dataset_id_or_code: str, org_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Look up dataset by ID or unique code."""
        _seed_lakehouse_data()
        for ds in _DATASETS_STORE.values():
            if ds["id"] == dataset_id_or_code or ds["dataset_code"].upper() == dataset_id_or_code.upper():
                if org_id and ds.get("organization_id") != org_id:
                    continue
                return ds
        return None

    def create_dataset(self, dataset_in: LakeDatasetCreate, org_id: Optional[str] = None) -> Dict[str, Any]:
        """Register a new columnar dataset in the lakehouse catalog."""
        global _DATASET_COUNTER
        _seed_lakehouse_data()

        existing = self.get_dataset_by_id(dataset_in.dataset_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset code '{dataset_in.dataset_code}' already exists."
            )

        resolved_org = org_id or DEMO_ORGANISATIONS[0]["id"]
        _DATASET_COUNTER += 1
        new_id = f"ds_lake_{_DATASET_COUNTER}"
        now = datetime.now(timezone.utc)

        record = {
            "id": new_id,
            "organization_id": resolved_org,
            "property_id": dataset_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"],
            "dataset_code": dataset_in.dataset_code.strip().upper(),
            "name": dataset_in.name.strip(),
            "dataset_type": dataset_in.dataset_type.value if hasattr(dataset_in.dataset_type, "value") else str(dataset_in.dataset_type),
            "format": dataset_in.format.value if hasattr(dataset_in.format, "value") else str(dataset_in.format),
            "partition_key": dataset_in.partition_key.strip(),
            "record_count": 0,
            "size_bytes": Decimal("0.00"),
            "raw_size_bytes": Decimal("0.00"),
            "compression_ratio": Decimal("1.00"),
            "compression_codec": dataset_in.compression_codec or "SNAPPY",
            "storage_uri": dataset_in.storage_uri.strip(),
            "last_compacted_at": now,
            "is_active": True,
            "created_at": now
        }

        _DATASETS_STORE[new_id] = record
        return record

    def get_pipelines(
        self,
        org_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve ETL data pipelines and compactor jobs."""
        _seed_lakehouse_data()
        results = list(_PIPELINES_STORE.values())

        if org_id:
            results = [p for p in results if p.get("organization_id") == org_id]
        if property_id:
            results = [p for p in results if p.get("property_id") in (None, property_id)]

        return sorted(results, key=lambda x: x["pipeline_code"])

    def get_pipeline_by_id(self, pipeline_id_or_code: str, org_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Look up pipeline by ID or code."""
        _seed_lakehouse_data()
        for p in _PIPELINES_STORE.values():
            if p["id"] == pipeline_id_or_code or p["pipeline_code"].upper() == pipeline_id_or_code.upper():
                if org_id and p.get("organization_id") != org_id:
                    continue
                return p
        return None

    def run_pipeline(self, pipeline_id_or_code: str, org_id: Optional[str] = None) -> Dict[str, Any]:
        """Trigger an execution run of an ETL compaction/ingestion pipeline."""
        pipe = self.get_pipeline_by_id(pipeline_id_or_code, org_id)
        if not pipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data pipeline '{pipeline_id_or_code}' not found."
            )

        start_time = time.time()
        now = datetime.now(timezone.utc)

        # Pipeline execution simulation
        batch_size = 5400
        pipe["status"] = PipelineRunStatus.COMPLETED.value
        pipe["records_processed"] = int(pipe.get("records_processed", 0)) + batch_size
        elapsed = Decimal(str(round(time.time() - start_time + 0.85, 2)))
        pipe["duration_seconds"] = elapsed
        pipe["last_run_at"] = now

        # Update target dataset metrics
        target_code = pipe.get("target_dataset_code")
        ds = self.get_dataset_by_id(target_code)
        if ds:
            ds["record_count"] = int(ds.get("record_count", 0)) + batch_size
            added_bytes = Decimal("524288.00")  # +512 KB
            ds["size_bytes"] = to_decimal(ds.get("size_bytes", 0)) + added_bytes
            ds["raw_size_bytes"] = to_decimal(ds.get("raw_size_bytes", 0)) + (added_bytes * Decimal("3.60"))
            eff = calculate_lake_storage_efficiency(ds["raw_size_bytes"], ds["size_bytes"])
            ds["compression_ratio"] = eff["compression_ratio"]
            ds["last_compacted_at"] = now

        return pipe

    def get_ml_models(
        self,
        org_id: Optional[str] = None,
        model_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve deployed predictive machine learning models."""
        _seed_lakehouse_data()
        results = list(_ML_MODELS_STORE.values())

        if org_id:
            results = [m for m in results if m.get("organization_id") == org_id]
        if model_type:
            results = [m for m in results if str(m.get("model_type", "")).upper() == model_type.upper()]

        return sorted(results, key=lambda x: x["model_code"])

    def get_ml_model_by_id(self, model_id_or_code: str, org_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Look up ML model by ID or unique model code."""
        _seed_lakehouse_data()
        for m in _ML_MODELS_STORE.values():
            if m["id"] == model_id_or_code or m["model_code"].upper() == model_id_or_code.upper():
                if org_id and m.get("organization_id") != org_id:
                    continue
                return m
        return None

    def predict(self, request: MlInferenceRequest, org_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute real-time model inference using mathematical algorithms and feature inputs.
        """
        _seed_lakehouse_data()
        model = self.get_ml_model_by_id(request.model_code, org_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine learning model '{request.model_code}' not found in registry."
            )

        start_t = time.time()
        m_type = model["model_type"]
        feats = request.features
        now = datetime.now(timezone.utc)

        if m_type in (MlModelType.DEMAND_FORECAST_REGRESSOR.value, MlModelType.DYNAMIC_RATE_OPTIMIZER.value):
            base_dem = feats.get("base_demand", 70.0)
            seas = feats.get("seasonality_factor", 1.10)
            evt = feats.get("event_multiplier", 1.05)
            rate = feats.get("base_rate", 5500.0)

            forecast = evaluate_demand_forecast(
                base_demand=base_dem,
                seasonality_factor=seas,
                event_multiplier=evt,
                base_rate=rate
            )
            prediction = {
                "predicted_demand_percent": float(forecast["predicted_demand"]),
                "confidence_interval": [float(forecast["confidence_lower"]), float(forecast["confidence_upper"])],
                "recommended_rate_inr": float(forecast["recommended_rate"]),
                "pricing_tier": forecast["pricing_tier"],
                "elasticity_index": 1.25 if forecast["pricing_tier"] == "SURGE" else 1.00
            }
            confidence = PredictionConfidence.HIGH.value

        elif m_type == MlModelType.GUEST_CHURN_CLASSIFIER.value:
            days = feats.get("days_since_last_stay", 60)
            bookings = feats.get("total_bookings", 3)
            nps = feats.get("nps_rating", 8)

            prob, tier = calculate_guest_churn_risk(
                days_since_last_stay=days,
                total_bookings=bookings,
                nps_rating=nps
            )
            prediction = {
                "churn_probability_percent": float(prob),
                "retention_probability_percent": float(Decimal("100.00") - prob),
                "risk_tier": tier,
                "recommended_intervention": "Executive Loyalty Concierge Call" if tier == "CRITICAL" else "Personalized Stay Promotion"
            }
            confidence = PredictionConfidence.HIGH.value

        else:
            prediction = {
                "inferred_value": 0.88,
                "status": "NORMAL",
                "notes": "Feature regression nominal."
            }
            confidence = PredictionConfidence.MEDIUM.value

        latency = Decimal(str(round((time.time() - start_t) * 1000 + 12.5, 2)))

        return {
            "model_code": model["model_code"],
            "model_name": model["name"],
            "model_type": model["model_type"],
            "prediction": prediction,
            "confidence": confidence,
            "latency_ms": latency,
            "evaluated_at": now
        }

    def get_metrics(
        self,
        org_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Aggregate data lakehouse, ETL, and ML performance metrics."""
        datasets = self.get_datasets(org_id=org_id, property_id=property_id)
        pipelines = self.get_pipelines(org_id=org_id, property_id=property_id)
        models = self.get_ml_models(org_id=org_id)
        return calculate_lakehouse_metrics(pipelines, datasets, models)


# Global singleton instance
lakehouse_service = LakehouseService()
