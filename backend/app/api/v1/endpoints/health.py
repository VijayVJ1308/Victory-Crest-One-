"""Victory Crest One - Health & Telemetry Endpoints
Provides system diagnostic endpoints and liveness checks for desktop clients, monitoring, and health probes.
"""

from fastapi import APIRouter, status
from backend.app.schemas.health import SystemHealthSchema
from backend.app.services.health_service import health_service

router = APIRouter()


@router.get(
    "/health",
    response_model=SystemHealthSchema,
    summary="Comprehensive System Health & Diagnostics",
    description="Returns backend status, database connection telemetry, and local storage diagnostic info."
)
def get_health() -> SystemHealthSchema:
    return health_service.get_system_health()


@router.get(
    "/health/quick",
    summary="Fast Liveness Probe",
    description="Returns immediate 200 OK if FastAPI process is responsive."
)
def get_quick_health():
    return {
        "status": "ok",
        "app": "Victory Crest ONE",
        "healthy": True
    }
