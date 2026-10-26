"""Victory Crest One - Data Lakehouse & Predictive ML REST API Endpoints
Columnar Parquet dataset catalog, ETL pipeline compactor triggers,
ML model registry, and real-time inferencing.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status

from backend.app.schemas.lakehouse import (
    LakeDatasetCreate,
    LakeDatasetOut,
    DataPipelineJobOut,
    MlModelOut,
    MlInferenceRequest,
    MlInferenceResponse,
    LakehouseMetricsOut
)
from backend.app.services.lakehouse_service import lakehouse_service

router = APIRouter()


@router.get("/datasets", response_model=List[LakeDatasetOut])
def list_lake_datasets(
    property_id: Optional[str] = Query(None, description="Filter datasets by property"),
    dataset_type: Optional[str] = Query(None, description="Filter by dataset type")
):
    """Retrieve all columnar lake datasets and partition metadata."""
    return lakehouse_service.get_datasets(property_id=property_id, dataset_type=dataset_type)


@router.get("/datasets/{dataset_id}", response_model=LakeDatasetOut)
def get_lake_dataset(dataset_id: str):
    """Retrieve single dataset metadata by ID or code."""
    ds = lakehouse_service.get_dataset_by_id(dataset_id)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lake dataset '{dataset_id}' not found."
        )
    return ds


@router.post("/datasets", response_model=LakeDatasetOut, status_code=status.HTTP_201_CREATED)
def register_lake_dataset(dataset_in: LakeDatasetCreate):
    """Register a new columnar dataset in the data lake catalog."""
    return lakehouse_service.create_dataset(dataset_in)


@router.get("/pipelines", response_model=List[DataPipelineJobOut])
def list_data_pipelines(
    property_id: Optional[str] = Query(None, description="Filter pipelines by property")
):
    """Retrieve lakehouse ETL and compaction orchestration pipelines."""
    return lakehouse_service.get_pipelines(property_id=property_id)


@router.post("/pipelines/{pipeline_id}/run", response_model=DataPipelineJobOut)
def run_data_pipeline(pipeline_id: str):
    """Trigger manual run of an ETL extraction and partition compaction job."""
    return lakehouse_service.run_pipeline(pipeline_id)


@router.get("/models", response_model=List[MlModelOut])
def list_ml_models(
    model_type: Optional[str] = Query(None, description="Filter by ML model type")
):
    """Retrieve deployed predictive machine learning models in registry."""
    return lakehouse_service.get_ml_models(model_type=model_type)


@router.post("/models/{model_code}/predict", response_model=MlInferenceResponse)
def run_ml_inference(model_code: str, request: MlInferenceRequest):
    """Execute predictive machine learning inference on feature payloads."""
    request.model_code = model_code
    return lakehouse_service.predict(request)


@router.get("/metrics", response_model=LakehouseMetricsOut)
def get_lakehouse_metrics(
    property_id: Optional[str] = Query(None, description="Filter metrics by property")
):
    """Retrieve lakehouse storage efficiency, throughput, and ML performance KPIs."""
    return lakehouse_service.get_metrics(property_id=property_id)
