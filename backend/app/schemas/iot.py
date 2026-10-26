"""Victory Crest One - IoT & Smart Device Gateway Schemas
Pydantic schemas for device registry, sensor telemetry ingestion,
threshold alert dispatching, remote device control, and fleet KPIs.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from shared.enums import DeviceType, DeviceStatus, SensorTelemetryType, AlertSeverity


class IoTDeviceBase(BaseModel):
    """Base schema attributes for IoT device."""
    device_code: str = Field(..., description="Unique device code e.g. IOT-MDR-ENG-01")
    name: str = Field(..., description="Human-readable device label")
    device_type: DeviceType = Field(..., description="Device functional type")
    location_zone: str = Field(..., description="Physical location or zone")
    status: DeviceStatus = Field(default=DeviceStatus.ONLINE)
    min_threshold: Optional[Decimal] = Field(default=None, description="Lower threshold bound")
    max_threshold: Optional[Decimal] = Field(default=None, description="Upper threshold bound")
    unit_of_measure: str = Field(default="°C", description="Engineering unit of measure")
    battery_level_percent: Optional[Decimal] = Field(default=None, description="Battery level % if wireless")
    firmware_version: Optional[str] = Field(default="v2.4.1")
    ip_address: Optional[str] = Field(default=None)
    property_id: Optional[str] = Field(default=None)


class IoTDeviceCreate(IoTDeviceBase):
    """Payload to register a new IoT device."""
    pass


class IoTDeviceUpdate(BaseModel):
    """Payload to modify device configurations or status."""
    name: Optional[str] = None
    device_type: Optional[DeviceType] = None
    location_zone: Optional[str] = None
    status: Optional[DeviceStatus] = None
    min_threshold: Optional[Decimal] = None
    max_threshold: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    battery_level_percent: Optional[Decimal] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    property_id: Optional[str] = None
    is_active: Optional[bool] = None


class IoTDeviceOut(IoTDeviceBase):
    """Device output representation."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    last_reading_value: Optional[Decimal] = None
    last_reading_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IoTTelemetryIngestRequest(BaseModel):
    """Real-time sensor telemetry payload submitted by IoT edge gateways."""
    device_code: str = Field(..., description="Target device code")
    telemetry_type: SensorTelemetryType = Field(..., description="Telemetry sensor measurement type")
    reading_value: Decimal = Field(..., description="Numerical reading")
    unit: Optional[str] = Field(default=None, description="Optional unit override")
    metadata_json: Optional[str] = Field(default=None, description="Optional edge device metadata")
    property_id: Optional[str] = Field(default=None)


class IoTTelemetryReadingOut(BaseModel):
    """Recorded sensor telemetry item with alert status."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    property_id: Optional[str] = None
    device_id: str
    device_code: str
    device_type: str
    telemetry_type: str
    reading_value: Decimal
    unit: str
    is_breach: bool
    alert_severity: Optional[str] = None
    alert_message: Optional[str] = None
    metadata_json: Optional[str] = None
    recorded_at: datetime



class IoTDeviceCommandRequest(BaseModel):
    """Remote actuator command dispatched to smart device."""
    command: str = Field(..., description="Command name e.g. SET_TEMPERATURE, LOCK_DOOR, UNLOCK_DOOR, RECALIBRATE")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Command parameters e.g. {'target_temp': 22.0}")


class IoTDeviceCommandResponse(BaseModel):
    """Execution acknowledgement from IoT device/actuator."""
    device_id: str
    device_code: str
    command: str
    status: str
    message: str
    executed_at: datetime


class IoTMetricsOut(BaseModel):
    """Aggregated IoT fleet operational metrics."""
    total_devices: int
    online_devices: int
    offline_devices: int
    alert_devices: int
    maintenance_devices: int
    online_rate_percent: Decimal
    total_power_kwh: Decimal
    total_power_cost: Decimal
    cold_storage_compliance_percent: Decimal
    active_alerts_count: int
    avg_battery_percent: Decimal
