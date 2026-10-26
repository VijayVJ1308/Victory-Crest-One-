"""Victory Crest One - Data Lakehouse & Predictive ML Models
Persistent lake datasets, partition metadata, ETL pipeline jobs, and ML model registry.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, Integer
from backend.app.models.base import Base, BaseModelMixin


class LakeDataset(Base, BaseModelMixin):
    """Columnar data lake dataset metadata and partition schema."""
    __tablename__ = "lake_datasets"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    dataset_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    dataset_type = Column(String(50), nullable=False, index=True)  # LakeDatasetType
    format = Column(String(20), default="PARQUET", nullable=False)
    partition_key = Column(String(100), default="year=YYYY/month=MM", nullable=False)

    record_count = Column(Integer, default=0, nullable=False)
    size_bytes = Column(Numeric(16, 0), default=0, nullable=False)
    raw_size_bytes = Column(Numeric(16, 0), default=0, nullable=False)
    compression_codec = Column(String(20), default="SNAPPY", nullable=False)
    storage_uri = Column(String(255), nullable=False)

    last_compacted_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class DataPipelineJob(Base, BaseModelMixin):
    """Batch and streaming lakehouse ETL extraction, compaction, and orchestration job."""
    __tablename__ = "lake_pipeline_jobs"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    pipeline_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    source_module = Column(String(50), nullable=False)
    target_dataset_code = Column(String(50), nullable=False, index=True)
    schedule_cron = Column(String(50), default="0 2 * * *", nullable=False)

    status = Column(String(30), default="IDLE", nullable=False, index=True)  # PipelineRunStatus
    records_processed = Column(Integer, default=0, nullable=False)
    duration_seconds = Column(Numeric(10, 2), default=0.00, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    error_log = Column(Text, nullable=True)


class MlModelRegistry(Base, BaseModelMixin):
    """Catalog of deployed predictive machine learning models and inferencing endpoints."""
    __tablename__ = "lake_ml_models"

    organization_id = Column(String(36), nullable=False, index=True)

    model_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    model_type = Column(String(50), nullable=False, index=True)  # MlModelType
    algorithm = Column(String(100), nullable=False)
    version = Column(String(20), default="v1.2.0", nullable=False)

    accuracy_score = Column(Numeric(6, 4), default=0.9200, nullable=False)
    feature_drift_percent = Column(Numeric(5, 2), default=1.80, nullable=False)
    status = Column(String(30), default="DEPLOYED", nullable=False, index=True)
    parameters_json = Column(Text, nullable=True)
    trained_at = Column(DateTime, default=datetime.utcnow, nullable=False)
