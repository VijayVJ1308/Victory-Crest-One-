"""Victory Crest One - Data Lakehouse & Predictive ML Schemas
Pydantic schemas for columnar lake datasets, Parquet partitions,
ETL pipeline jobs, ML model registry, and real-time inferencing.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from shared.enums import (
    LakeDatasetType,
    PipelineRunStatus,
    MlModelType,
    PredictionConfidence,
    DatasetFormat
)


class LakeDatasetBase(BaseModel):
    """Base schema attributes for columnar lake dataset."""
    dataset_code: str = Field(..., description="Unique dataset identifier e.g. DS-FIN-GL")
    name: str = Field(..., description="Descriptive dataset name")
    dataset_type: LakeDatasetType = Field(..., description="Business domain dataset classification")
    format: DatasetFormat = Field(default=DatasetFormat.PARQUET, description="Storage format")
    partition_key: str = Field(default="year=YYYY/month=MM", description="Partition directory layout")
    compression_codec: str = Field(default="SNAPPY", description="Columnar compression codec")
    storage_uri: str = Field(..., description="Virtual URI or S3/Lake path")
    property_id: Optional[str] = Field(default=None)


class LakeDatasetCreate(LakeDatasetBase):
    """Payload to register a new lake dataset."""
    pass


class LakeDatasetOut(LakeDatasetBase):
    """Dataset catalog representation with storage footprint."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    record_count: int
    size_bytes: Decimal
    raw_size_bytes: Decimal
    compression_ratio: Decimal
    last_compacted_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


class DataPipelineJobCreate(BaseModel):
    """Payload to configure a new lakehouse ETL pipeline."""
    pipeline_code: str = Field(..., description="Unique job code e.g. ETL-GL-NIGHTLY")
    name: str = Field(..., description="Pipeline job title")
    source_module: str = Field(..., description="Source module e.g. finance, hospitality, iot")
    target_dataset_code: str = Field(..., description="Destination dataset code")
    schedule_cron: str = Field(default="0 2 * * *", description="Cron schedule")
    property_id: Optional[str] = Field(default=None)


class DataPipelineJobOut(BaseModel):
    """ETL pipeline execution state and performance metrics."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    property_id: Optional[str] = None
    pipeline_code: str
    name: str
    source_module: str
    target_dataset_code: str
    schedule_cron: str
    status: str
    records_processed: int
    duration_seconds: Decimal
    last_run_at: Optional[datetime] = None
    error_log: Optional[str] = None
    created_at: Optional[datetime] = None


class MlModelOut(BaseModel):
    """Catalog metadata for deployed machine learning model."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    model_code: str
    name: str
    model_type: str
    algorithm: str
    version: str
    accuracy_score: Decimal
    feature_drift_percent: Decimal
    status: str
    parameters_json: Optional[str] = None
    trained_at: datetime


class MlInferenceRequest(BaseModel):
    """Input payload to request predictive model inference."""
    model_code: str = Field(..., description="Target model identifier")
    features: Dict[str, Any] = Field(default_factory=dict, description="Feature dictionary input")


class MlInferenceResponse(BaseModel):
    """Machine learning model prediction result."""
    model_code: str
    model_name: str
    model_type: str
    prediction: Dict[str, Any]
    confidence: str
    latency_ms: Decimal
    evaluated_at: datetime


class LakehouseMetricsOut(BaseModel):
    """Aggregated data lake storage, pipeline throughput, and ML performance KPIs."""
    total_datasets: int
    total_parquet_size_mb: Decimal
    total_raw_size_mb: Decimal
    overall_compression_ratio: Decimal
    active_pipelines_count: int
    daily_records_ingested: int
    pipeline_success_rate_percent: Decimal
    deployed_ml_models_count: int
    avg_model_accuracy_percent: Decimal
