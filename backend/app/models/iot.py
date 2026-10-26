"""Victory Crest One - IoT & Smart Device Gateway Models
Persistent IoT Device Registry, Actuators, and High-Frequency Sensor Telemetry Ingestion.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, Integer
from backend.app.models.base import Base, BaseModelMixin


class IoTDevice(Base, BaseModelMixin):
    """Registered smart device, sensor node, or environmental actuator."""
    __tablename__ = "iot_devices"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    device_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False, index=True)  # DeviceType enum
    location_zone = Column(String(100), nullable=False)
    status = Column(String(30), default="ONLINE", nullable=False, index=True)  # DeviceStatus enum

    min_threshold = Column(Numeric(10, 2), nullable=True)
    max_threshold = Column(Numeric(10, 2), nullable=True)
    unit_of_measure = Column(String(20), nullable=False, default="°C")

    last_reading_value = Column(Numeric(10, 2), nullable=True)
    last_reading_at = Column(DateTime, nullable=True)
    battery_level_percent = Column(Numeric(5, 2), nullable=True)
    firmware_version = Column(String(50), default="v2.4.1", nullable=True)
    ip_address = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class IoTTelemetryReading(Base, BaseModelMixin):
    """High-frequency sensor telemetry log with breach detection history."""
    __tablename__ = "iot_telemetry_readings"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    device_id = Column(String(36), nullable=False, index=True)
    device_code = Column(String(50), nullable=False, index=True)
    device_type = Column(String(50), nullable=False, index=True)
    telemetry_type = Column(String(50), nullable=False, index=True)  # SensorTelemetryType

    reading_value = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False)

    is_breach = Column(Boolean, default=False, nullable=False, index=True)
    alert_severity = Column(String(20), nullable=True)  # AlertSeverity enum
    alert_message = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)

    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
