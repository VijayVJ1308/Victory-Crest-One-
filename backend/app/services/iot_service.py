"""Victory Crest One - IoT & Smart Device Gateway Service
Manages smart device fleets, high-frequency telemetry ingestion,
real-time threshold breach detection, workflow event triggers, and remote actuator commands.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status

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
from backend.app.services.automation_service import automation_service
from shared.enums import DeviceType, DeviceStatus, SensorTelemetryType, AlertSeverity
from shared.calculations import (
    to_decimal,
    evaluate_sensor_threshold,
    calculate_iot_portfolio_metrics
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory stores
_DEVICES_STORE: Dict[str, Dict[str, Any]] = {}
_TELEMETRY_STORE: List[Dict[str, Any]] = []
_DEVICE_COUNTER = 1009


def _seed_iot_data():
    """Seed enterprise default IoT devices and initial sensor telemetry."""
    global _DEVICE_COUNTER
    if _DEVICES_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]
    now = datetime.now(timezone.utc)

    seed_devices = [
        {
            "id": "iot_dev_1001",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_code": "IOT-MDR-ENG-01",
            "name": "Main Incomer 11kV Grid Energy Meter",
            "device_type": DeviceType.SMART_ENERGY_METER.value,
            "location_zone": "Main Substation & HT Transformer Yard",
            "status": DeviceStatus.ONLINE.value,
            "min_threshold": Decimal("0.00"),
            "max_threshold": Decimal("850.00"),
            "unit_of_measure": "kWh",
            "last_reading_value": Decimal("485.60"),
            "last_reading_at": now,
            "battery_level_percent": None,
            "firmware_version": "v3.1.2",
            "ip_address": "192.168.10.15",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": "iot_dev_1002",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_code": "IOT-MDR-ENG-02",
            "name": "Central Chiller Plant Energy Monitor",
            "device_type": DeviceType.SMART_ENERGY_METER.value,
            "location_zone": "HVAC Chiller Basement Plant Room",
            "status": DeviceStatus.ONLINE.value,
            "min_threshold": Decimal("0.00"),
            "max_threshold": Decimal("500.00"),
            "unit_of_measure": "kWh",
            "last_reading_value": Decimal("295.40"),
            "last_reading_at": now,
            "battery_level_percent": None,
            "firmware_version": "v3.1.2",
            "ip_address": "192.168.10.18",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": "iot_dev_1003",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_code": "IOT-MDR-CHILL-01",
            "name": "Main Kitchen Walk-in Food Safety Chiller",
            "device_type": DeviceType.KITCHEN_COLD_STORAGE_SENSOR.value,
            "location_zone": "Commercial Kitchen Walk-In Cold Room",
            "status": DeviceStatus.ONLINE.value,
            "min_threshold": Decimal("0.00"),
            "max_threshold": Decimal("4.00"),
            "unit_of_measure": "°C",
            "last_reading_value": Decimal("2.80"),
            "last_reading_at": now,
            "battery_level_percent": Decimal("94.00"),
            "firmware_version": "v2.0.4",
            "ip_address": "192.168.20.45",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": "iot_dev_1004",
            "organization_id": org_id,
            "property_id": prop_kod,
            "device_code": "IOT-KOD-FREEZ-01",
            "name": "Pastry & Butchery Deep Freezer Probe",
            "device_type": DeviceType.KITCHEN_COLD_STORAGE_SENSOR.value,
            "location_zone": "Resort Kitchen Sub-Zero Vault",
            "status": DeviceStatus.ONLINE.value,
            "min_threshold": Decimal("-25.00"),
            "max_threshold": Decimal("-18.00"),
            "unit_of_measure": "°C",
            "last_reading_value": Decimal("-21.40"),
            "last_reading_at": now,
            "battery_level_percent": Decimal("88.00"),
            "firmware_version": "v2.0.4",
            "ip_address": "192.168.20.48",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": "iot_dev_1005",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_code": "IOT-MDR-STAT-401",
            "name": "Presidential Suite Smart Thermostat",
            "device_type": DeviceType.ROOM_CLIMATE_THERMOSTAT.value,
            "location_zone": "Presidential Suite 401 - Living Pavilion",
            "status": DeviceStatus.ONLINE.value,
            "min_threshold": Decimal("18.00"),
            "max_threshold": Decimal("26.00"),
            "unit_of_measure": "°C",
            "last_reading_value": Decimal("22.50"),
            "last_reading_at": now,
            "battery_level_percent": None,
            "firmware_version": "v4.0.1",
            "ip_address": "192.168.30.12",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": "iot_dev_1006",
            "organization_id": org_id,
            "property_id": prop_maa,
            "device_code": "IOT-MAA-STAT-202",
            "name": "Executive Boardroom Smart Thermostat",
            "device_type": DeviceType.ROOM_CLIMATE_THERMOSTAT.value,
            "location_zone": "Boardroom A (Level 2 Conference Wing)",
            "status": DeviceStatus.ONLINE.value,
            "min_threshold": Decimal("18.00"),
            "max_threshold": Decimal("24.00"),
            "unit_of_measure": "°C",
            "last_reading_value": Decimal("21.20"),
            "last_reading_at": now,
            "battery_level_percent": None,
            "firmware_version": "v4.0.1",
            "ip_address": "192.168.30.15",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": "iot_dev_1007",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_code": "IOT-MDR-LOCK-401",
            "name": "Presidential Suite RFID/BLE Smart Lock",
            "device_type": DeviceType.SMART_DOOR_LOCK.value,
            "location_zone": "Suite 401 - Main Entrance Portico",
            "status": DeviceStatus.ONLINE.value,
            "min_threshold": Decimal("0.00"),
            "max_threshold": Decimal("1.00"),
            "unit_of_measure": "STATE",
            "last_reading_value": Decimal("1.00"),
            "last_reading_at": now,
            "battery_level_percent": Decimal("91.00"),
            "firmware_version": "v1.8.9",
            "ip_address": "192.168.40.8",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": "iot_dev_1008",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_code": "IOT-MDR-AQI-BALL",
            "name": "Grand Ballroom HVAC Air Quality Monitor",
            "device_type": DeviceType.HVAC_AIR_QUALITY_MONITOR.value,
            "location_zone": "Grand Ballroom Ceiling Return Air Plenum",
            "status": DeviceStatus.ONLINE.value,
            "min_threshold": Decimal("0.00"),
            "max_threshold": Decimal("100.00"),
            "unit_of_measure": "AQI",
            "last_reading_value": Decimal("44.00"),
            "last_reading_at": now,
            "battery_level_percent": None,
            "firmware_version": "v2.5.0",
            "ip_address": "192.168.10.22",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
    ]

    for d in seed_devices:
        _DEVICES_STORE[d["id"]] = d

    # Seed baseline telemetry history
    seed_telemetry = [
        {
            "id": "tel_101",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_id": "iot_dev_1001",
            "device_code": "IOT-MDR-ENG-01",
            "device_type": DeviceType.SMART_ENERGY_METER.value,
            "telemetry_type": SensorTelemetryType.POWER_KWH.value,
            "reading_value": Decimal("485.60"),
            "unit": "kWh",
            "is_breach": False,
            "alert_severity": AlertSeverity.INFO.value,
            "alert_message": "Nominal power consumption load.",
            "metadata_json": '{"voltage_v": 415.2, "pf": 0.96}',
            "recorded_at": now
        },
        {
            "id": "tel_102",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_id": "iot_dev_1002",
            "device_code": "IOT-MDR-ENG-02",
            "device_type": DeviceType.SMART_ENERGY_METER.value,
            "telemetry_type": SensorTelemetryType.POWER_KWH.value,
            "reading_value": Decimal("295.40"),
            "unit": "kWh",
            "is_breach": False,
            "alert_severity": AlertSeverity.INFO.value,
            "alert_message": "Nominal chiller operation.",
            "metadata_json": '{"load_pct": 74}',
            "recorded_at": now
        },
        {
            "id": "tel_103",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_id": "iot_dev_1003",
            "device_code": "IOT-MDR-CHILL-01",
            "device_type": DeviceType.KITCHEN_COLD_STORAGE_SENSOR.value,
            "telemetry_type": SensorTelemetryType.TEMPERATURE_CELSIUS.value,
            "reading_value": Decimal("2.80"),
            "unit": "°C",
            "is_breach": False,
            "alert_severity": AlertSeverity.INFO.value,
            "alert_message": "HACCP compliant cold storage temperature.",
            "metadata_json": '{"compressor_duty": "active"}',
            "recorded_at": now
        },
        {
            "id": "tel_104",
            "organization_id": org_id,
            "property_id": prop_kod,
            "device_id": "iot_dev_1004",
            "device_code": "IOT-KOD-FREEZ-01",
            "device_type": DeviceType.KITCHEN_COLD_STORAGE_SENSOR.value,
            "telemetry_type": SensorTelemetryType.TEMPERATURE_CELSIUS.value,
            "reading_value": Decimal("-21.40"),
            "unit": "°C",
            "is_breach": False,
            "alert_severity": AlertSeverity.INFO.value,
            "alert_message": "Sub-zero deep freeze nominal.",
            "metadata_json": '{"defrost_cycle": false}',
            "recorded_at": now
        },
        {
            "id": "tel_105",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "device_id": "iot_dev_1008",
            "device_code": "IOT-MDR-AQI-BALL",
            "device_type": DeviceType.HVAC_AIR_QUALITY_MONITOR.value,
            "telemetry_type": SensorTelemetryType.AIR_QUALITY_AQI.value,
            "reading_value": Decimal("44.00"),
            "unit": "AQI",
            "is_breach": False,
            "alert_severity": AlertSeverity.INFO.value,
            "alert_message": "Good indoor air quality index.",
            "metadata_json": '{"pm25_ugm3": 12.4, "co2_ppm": 520}',
            "recorded_at": now
        }
    ]

    for t in seed_telemetry:
        _TELEMETRY_STORE.append(t)


class IoTService:
    """Enterprise IoT Fleet Registry & Sensor Telemetry Gateway Engine."""

    def __init__(self):
        _seed_iot_data()

    def get_devices(
        self,
        org_id: Optional[str] = None,
        property_id: Optional[str] = None,
        device_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query IoT devices filtered by property, type, and status."""
        _seed_iot_data()
        results = list(_DEVICES_STORE.values())

        if org_id:
            results = [d for d in results if d.get("organization_id") == org_id]
        if property_id:
            results = [d for d in results if d.get("property_id") in (None, property_id)]
        if device_type:
            results = [d for d in results if str(d.get("device_type", "")).upper() == device_type.upper()]
        if status:
            results = [d for d in results if str(d.get("status", "")).upper() == status.upper()]

        return sorted(results, key=lambda x: x["device_code"])

    def get_device_by_id(self, device_id_or_code: str, org_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Look up device by UUID or unique device code."""
        _seed_iot_data()
        for d in _DEVICES_STORE.values():
            if d["id"] == device_id_or_code or d["device_code"].upper() == device_id_or_code.upper():
                if org_id and d.get("organization_id") != org_id:
                    continue
                return d
        return None

    def create_device(self, device_in: IoTDeviceCreate, org_id: Optional[str] = None) -> Dict[str, Any]:
        """Register a new IoT device in the catalog."""
        global _DEVICE_COUNTER
        _seed_iot_data()

        # Check unique device code
        existing = self.get_device_by_id(device_in.device_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device code '{device_in.device_code}' is already registered."
            )

        resolved_org = org_id or DEMO_ORGANISATIONS[0]["id"]
        _DEVICE_COUNTER += 1
        new_id = f"iot_dev_{_DEVICE_COUNTER}"
        now = datetime.now(timezone.utc)

        record = {
            "id": new_id,
            "organization_id": resolved_org,
            "property_id": device_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"],
            "device_code": device_in.device_code.upper().strip(),
            "name": device_in.name.strip(),
            "device_type": device_in.device_type.value if hasattr(device_in.device_type, "value") else str(device_in.device_type),
            "location_zone": device_in.location_zone.strip(),
            "status": device_in.status.value if hasattr(device_in.status, "value") else str(device_in.status),
            "min_threshold": to_decimal(device_in.min_threshold) if device_in.min_threshold is not None else None,
            "max_threshold": to_decimal(device_in.max_threshold) if device_in.max_threshold is not None else None,
            "unit_of_measure": device_in.unit_of_measure,
            "last_reading_value": None,
            "last_reading_at": None,
            "battery_level_percent": to_decimal(device_in.battery_level_percent) if device_in.battery_level_percent is not None else None,
            "firmware_version": device_in.firmware_version or "v2.4.1",
            "ip_address": device_in.ip_address,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }

        _DEVICES_STORE[new_id] = record
        return record

    def update_device(
        self,
        device_id_or_code: str,
        device_in: IoTDeviceUpdate,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Modify device configuration, thresholds, or status."""
        device = self.get_device_by_id(device_id_or_code, org_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IoT device '{device_id_or_code}' not found."
            )

        patch = device_in.model_dump(exclude_unset=True)
        for k, v in patch.items():
            if k in ("device_type", "status") and hasattr(v, "value"):
                device[k] = v.value
            elif k in ("min_threshold", "max_threshold", "battery_level_percent") and v is not None:
                device[k] = to_decimal(v)
            else:
                device[k] = v

        device["updated_at"] = datetime.now(timezone.utc)
        return device

    def delete_device(self, device_id_or_code: str, org_id: Optional[str] = None) -> bool:
        """Decommission and remove an IoT device from the fleet."""
        device = self.get_device_by_id(device_id_or_code, org_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IoT device '{device_id_or_code}' not found."
            )
        del _DEVICES_STORE[device["id"]]
        return True

    def ingest_telemetry(
        self,
        payload: IoTTelemetryIngestRequest,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest real-time telemetry from edge sensors, evaluate threshold bounds,
        flag operational breaches, update device states, and dispatch automated workflow events.
        """
        _seed_iot_data()
        device = self.get_device_by_id(payload.device_code, org_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IoT device '{payload.device_code}' not registered in fleet."
            )

        now = datetime.now(timezone.utc)
        t_type = payload.telemetry_type.value if hasattr(payload.telemetry_type, "value") else str(payload.telemetry_type)
        val = to_decimal(payload.reading_value)
        unit = payload.unit or device.get("unit_of_measure", "°C")

        # Evaluate threshold breach
        is_breach, severity, msg = evaluate_sensor_threshold(
            sensor_type=t_type,
            reading=val,
            min_threshold=device.get("min_threshold"),
            max_threshold=device.get("max_threshold")
        )

        # Update device status and latest reading
        device["last_reading_value"] = val
        device["last_reading_at"] = now
        device["updated_at"] = now

        if is_breach:
            device["status"] = DeviceStatus.ALERT.value
            # Trigger Cross-Module Workflow Automation (Phase 15 Engine)
            automation_payload = {
                "device_code": device["device_code"],
                "device_name": device["name"],
                "device_type": device["device_type"],
                "location_zone": device["location_zone"],
                "reading_value": float(val),
                "temperature": float(val) if "TEMPERATURE" in t_type else None,
                "power_kwh": float(val) if "POWER" in t_type else None,
                "aqi": float(val) if "AQI" in t_type else None,
                "unit": unit,
                "alert_severity": severity,
                "alert_message": msg,
                "property_id": device.get("property_id")
            }
            try:
                automation_service.dispatch_event(
                    event_name="iot.threshold_breach",
                    payload=automation_payload,
                    org_id=device.get("organization_id"),
                    property_id=device.get("property_id")
                )
            except Exception:
                pass  # Graceful fallback if automation dispatcher encounters unhandled state
        else:
            # If device was in ALERT and reading is nominal, return to ONLINE
            if device.get("status") == DeviceStatus.ALERT.value:
                device["status"] = DeviceStatus.ONLINE.value

        telemetry_record = {
            "id": f"tel_{uuid.uuid4().hex[:8]}",
            "organization_id": device["organization_id"],
            "property_id": device.get("property_id"),
            "device_id": device["id"],
            "device_code": device["device_code"],
            "device_type": device["device_type"],
            "telemetry_type": t_type,
            "reading_value": val,
            "unit": unit,
            "is_breach": is_breach,
            "alert_severity": severity if is_breach else AlertSeverity.INFO.value,
            "alert_message": msg,
            "metadata_json": payload.metadata_json,
            "recorded_at": now
        }

        _TELEMETRY_STORE.append(telemetry_record)
        return telemetry_record

    def get_telemetry_history(
        self,
        org_id: Optional[str] = None,
        property_id: Optional[str] = None,
        device_id: Optional[str] = None,
        device_code: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve recent telemetry streams across the fleet or specific device."""
        _seed_iot_data()
        results = list(_TELEMETRY_STORE)

        if org_id:
            results = [t for t in results if t.get("organization_id") == org_id]
        if property_id:
            results = [t for t in results if t.get("property_id") in (None, property_id)]
        if device_id:
            results = [t for t in results if t.get("device_id") == device_id]
        if device_code:
            results = [t for t in results if t.get("device_code", "").upper() == device_code.upper()]

        results = sorted(results, key=lambda x: x["recorded_at"], reverse=True)
        return results[:limit]

    def send_device_command(
        self,
        device_id_or_code: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dispatch remote control or actuator instructions to edge device."""
        device = self.get_device_by_id(device_id_or_code, org_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IoT device '{device_id_or_code}' not found."
            )

        cmd_clean = command.strip().upper()
        now = datetime.now(timezone.utc)
        params = parameters or {}

        # Actuator command logic
        if cmd_clean == "SET_TEMPERATURE":
            target_temp = params.get("target_temp")
            if target_temp is not None:
                device["last_reading_value"] = to_decimal(target_temp)
                device["last_reading_at"] = now
                msg = f"Thermostat target set to {target_temp}°C successfully."
            else:
                msg = "Thermostat temperature command acknowledged."

        elif cmd_clean == "LOCK_DOOR":
            device["last_reading_value"] = Decimal("1.00")
            device["last_reading_at"] = now
            msg = "Smart door lock engaged (LOCKED)."

        elif cmd_clean == "UNLOCK_DOOR":
            device["last_reading_value"] = Decimal("0.00")
            device["last_reading_at"] = now
            msg = "Smart door lock disengaged (UNLOCKED)."

        elif cmd_clean == "RECALIBRATE":
            msg = f"Sensor calibration routine completed on firmware {device.get('firmware_version')}."

        elif cmd_clean == "RESET":
            device["status"] = DeviceStatus.ONLINE.value
            msg = "Device system reboot initiated."

        else:
            msg = f"Actuator command '{cmd_clean}' executed successfully."

        return {
            "device_id": device["id"],
            "device_code": device["device_code"],
            "command": cmd_clean,
            "status": "EXECUTED",
            "message": msg,
            "executed_at": now
        }

    def get_portfolio_metrics(
        self,
        org_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate aggregate fleet metrics using shared calculations."""
        devices = self.get_devices(org_id=org_id, property_id=property_id)
        telemetry = self.get_telemetry_history(org_id=org_id, property_id=property_id, limit=500)
        return calculate_iot_portfolio_metrics(devices, telemetry)


# Global singleton instance
iot_service = IoTService()
