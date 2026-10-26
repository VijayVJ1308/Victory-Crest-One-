"""Victory Crest One - Integration Tests for IoT & Smart Device Gateway REST API
Verifies endpoints for device fleet management, telemetry ingestion, threshold alerts,
actuator commands, and fleet KPIs.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_iot_devices(client: TestClient):
    response = client.get("/api/v1/iot/devices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8

    codes = [d["device_code"] for d in data]
    assert "IOT-MDR-ENG-01" in codes
    assert "IOT-MDR-CHILL-01" in codes
    assert "IOT-MDR-LOCK-401" in codes


def test_get_iot_device_by_id_and_not_found(client: TestClient):
    response = client.get("/api/v1/iot/devices/iot_dev_1001")
    assert response.status_code == 200
    data = response.json()
    assert data["device_code"] == "IOT-MDR-ENG-01"
    assert data["device_type"] == "SMART_ENERGY_METER"
    assert data["status"] == "ONLINE"

    # Also lookup by code
    res_code = client.get("/api/v1/iot/devices/IOT-MDR-CHILL-01")
    assert res_code.status_code == 200
    assert res_code.json()["name"] == "Main Kitchen Walk-in Food Safety Chiller"

    # 404 test
    bad = client.get("/api/v1/iot/devices/non_existent_device")
    assert bad.status_code == 404


def test_create_update_and_delete_iot_device(client: TestClient):
    new_device = {
        "device_code": "IOT-KOD-CHILL-99",
        "name": "Kodaikanal Lakeside Chiller Aux Probe",
        "device_type": "KITCHEN_COLD_STORAGE_SENSOR",
        "location_zone": "Basement Storage Vault B",
        "status": "ONLINE",
        "min_threshold": 0.0,
        "max_threshold": 4.0,
        "unit_of_measure": "°C",
        "battery_level_percent": 88.0,
        "firmware_version": "v2.1.0"
    }

    create_res = client.post("/api/v1/iot/devices", json=new_device)
    assert create_res.status_code == 201
    created = create_res.json()
    dev_id = created["id"]
    assert created["device_code"] == "IOT-KOD-CHILL-99"

    # Update
    update_res = client.put(f"/api/v1/iot/devices/{dev_id}", json={"max_threshold": 3.5, "status": "MAINTENANCE"})
    assert update_res.status_code == 200
    assert float(update_res.json()["max_threshold"]) == 3.5
    assert update_res.json()["status"] == "MAINTENANCE"

    # Delete
    del_res = client.delete(f"/api/v1/iot/devices/{dev_id}")
    assert del_res.status_code == 204

    # Verify deleted
    verify_res = client.get(f"/api/v1/iot/devices/{dev_id}")
    assert verify_res.status_code == 404


def test_ingest_telemetry_nominal_and_breach(client: TestClient):
    # 1. Nominal Ingestion for Chiller (2.2°C within 0.0 - 4.0°C)
    nominal_payload = {
        "device_code": "IOT-MDR-CHILL-01",
        "telemetry_type": "TEMPERATURE_CELSIUS",
        "reading_value": 2.2,
        "unit": "°C"
    }
    nom_res = client.post("/api/v1/iot/telemetry/ingest", json=nominal_payload)
    assert nom_res.status_code == 201
    nom_data = nom_res.json()
    assert not nom_data["is_breach"]
    assert nom_data["alert_severity"] == "INFO"

    # 2. Critical Breach Ingestion (9.2°C > 4.0°C max threshold by 5.2°C)
    breach_payload = {
        "device_code": "IOT-MDR-CHILL-01",
        "telemetry_type": "TEMPERATURE_CELSIUS",
        "reading_value": 9.2,
        "unit": "°C"
    }
    breach_res = client.post("/api/v1/iot/telemetry/ingest", json=breach_payload)
    assert breach_res.status_code == 201
    breach_data = breach_res.json()
    assert breach_data["is_breach"]
    assert breach_data["alert_severity"] == "CRITICAL"
    assert "exceeded upper threshold" in breach_data["alert_message"]

    # Verify device status switched to ALERT
    dev_res = client.get("/api/v1/iot/devices/IOT-MDR-CHILL-01")
    assert dev_res.status_code == 200
    assert dev_res.json()["status"] == "ALERT"


def test_get_telemetry_history(client: TestClient):
    response = client.get("/api/v1/iot/telemetry/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "reading_value" in data[0]
    assert "telemetry_type" in data[0]


def test_send_device_command(client: TestClient):
    # Test setting thermostat temperature
    cmd_payload = {
        "command": "SET_TEMPERATURE",
        "parameters": {"target_temp": 23.5}
    }
    res = client.post("/api/v1/iot/devices/IOT-MDR-STAT-401/command", json=cmd_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "EXECUTED"
    assert "23.5°C" in data["message"]

    # Test lock door
    lock_res = client.post("/api/v1/iot/devices/IOT-MDR-LOCK-401/command", json={"command": "LOCK_DOOR"})
    assert lock_res.status_code == 200
    assert "LOCKED" in lock_res.json()["message"]


def test_get_iot_portfolio_metrics(client: TestClient):
    response = client.get("/api/v1/iot/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["total_devices"] >= 8
    assert "online_rate_percent" in metrics
    assert "total_power_kwh" in metrics
    assert "total_power_cost" in metrics
    assert "cold_storage_compliance_percent" in metrics
    assert "avg_battery_percent" in metrics
