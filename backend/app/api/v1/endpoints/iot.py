"""Victory Crest One - IoT & Smart Device Gateway REST API Endpoints
Device fleet registry, high-frequency sensor telemetry ingestion,
alert threshold dispatching, remote device control, and fleet health KPIs.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status

from backend.app.schemas.iot import (
    IoTDeviceCreate,
    IoTDeviceUpdate,
    IoTDeviceOut,
    IoTTelemetryIngestRequest,
    IoTTelemetryReadingOut,
    IoTDeviceCommandRequest,
    IoTDeviceCommandResponse,
    IoTMetricsOut
)
from backend.app.services.iot_service import iot_service

router = APIRouter()


@router.get("/devices", response_model=List[IoTDeviceOut])
def list_iot_devices(
    property_id: Optional[str] = Query(None, description="Filter devices by property"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by status (ONLINE, OFFLINE, ALERT, MAINTENANCE)")
):
    """Retrieve all registered IoT devices matching query filters."""
    return iot_service.get_devices(property_id=property_id, device_type=device_type, status=status)


@router.get("/devices/{device_id}", response_model=IoTDeviceOut)
def get_iot_device(device_id: str):
    """Retrieve a single IoT device by UUID or code."""
    device = iot_service.get_device_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IoT device '{device_id}' not found."
        )
    return device


@router.post("/devices", response_model=IoTDeviceOut, status_code=status.HTTP_201_CREATED)
def register_iot_device(device_in: IoTDeviceCreate):
    """Register a new smart sensor, thermostat, meter, or actuator node."""
    return iot_service.create_device(device_in)


@router.put("/devices/{device_id}", response_model=IoTDeviceOut)
def update_iot_device(device_id: str, device_in: IoTDeviceUpdate):
    """Modify device configurations, thresholds, or status."""
    return iot_service.update_device(device_id, device_in)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def decommission_iot_device(device_id: str):
    """Decommission and remove an IoT device."""
    iot_service.delete_device(device_id)
    return None


@router.post("/telemetry/ingest", response_model=IoTTelemetryReadingOut, status_code=status.HTTP_201_CREATED)
def ingest_sensor_telemetry(payload: IoTTelemetryIngestRequest):
    """
    Ingest sensor telemetry reading from edge device gateway.
    Evaluates threshold bounds, flags breaches, and auto-dispatches workflow triggers.
    """
    return iot_service.ingest_telemetry(payload)


@router.get("/telemetry/history", response_model=List[IoTTelemetryReadingOut])
def get_telemetry_history(
    property_id: Optional[str] = Query(None, description="Filter telemetry by property"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    device_code: Optional[str] = Query(None, description="Filter by device code"),
    limit: int = Query(100, ge=1, le=1000, description="Max readings to return")
):
    """Retrieve sensor telemetry streams ordered by timestamp descending."""
    return iot_service.get_telemetry_history(
        property_id=property_id,
        device_id=device_id,
        device_code=device_code,
        limit=limit
    )


@router.post("/devices/{device_id}/command", response_model=IoTDeviceCommandResponse)
def send_device_command(device_id: str, command_in: IoTDeviceCommandRequest):
    """Send remote actuator command to IoT device (thermostat setpoint, lock state, etc.)."""
    return iot_service.send_device_command(
        device_id_or_code=device_id,
        command=command_in.command,
        parameters=command_in.parameters
    )


@router.get("/metrics", response_model=IoTMetricsOut)
def get_iot_portfolio_metrics(
    property_id: Optional[str] = Query(None, description="Filter metrics by property")
):
    """Calculate aggregate fleet metrics, power load, and cold storage compliance."""
    return iot_service.get_portfolio_metrics(property_id=property_id)
