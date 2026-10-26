"""Victory Crest One - Unit Tests for IoT & Smart Device Calculations
"""

from decimal import Decimal
import pytest

from shared.calculations import (
    evaluate_sensor_threshold,
    calculate_power_consumption_cost,
    calculate_iot_portfolio_metrics
)


def test_evaluate_sensor_threshold_nominal():
    # Cold storage chiller reading within nominal limits (min: 0.0, max: 4.0)
    breached, severity, msg = evaluate_sensor_threshold("TEMPERATURE_CELSIUS", 2.5, min_threshold=0.0, max_threshold=4.0)
    assert not breached
    assert severity == "INFO"
    assert "nominal" in msg


def test_evaluate_sensor_threshold_upper_warning_and_critical():
    # Slight breach (4.5°C vs 4.0°C max) -> diff = 0.5 (< 5 and 0.5/4.0 = 12.5% < 20%) -> WARNING
    breached, severity, msg = evaluate_sensor_threshold("TEMPERATURE_CELSIUS", 4.5, min_threshold=0.0, max_threshold=4.0)
    assert breached
    assert severity == "WARNING"
    assert "exceeded upper threshold" in msg

    # Large breach (9.5°C vs 4.0°C max) -> diff = 5.5 (>= 5) -> CRITICAL
    breached, severity, msg = evaluate_sensor_threshold("TEMPERATURE_CELSIUS", 9.5, min_threshold=0.0, max_threshold=4.0)
    assert breached
    assert severity == "CRITICAL"
    assert "exceeded upper threshold" in msg


def test_evaluate_sensor_threshold_lower_warning_and_critical():
    # Lower breach: Room temp drops below min threshold of 18.0°C
    # 17.0°C vs 18.0°C -> diff = 1.0 (< 5 and 1/18 = 5.5% < 20%) -> WARNING
    breached, severity, msg = evaluate_sensor_threshold("TEMPERATURE_CELSIUS", 17.0, min_threshold=18.0, max_threshold=26.0)
    assert breached
    assert severity == "WARNING"
    assert "fell below lower threshold" in msg

    # Extreme cold drop: 11.0°C vs 18.0°C -> diff = 7.0 (>= 5) -> CRITICAL
    breached, severity, msg = evaluate_sensor_threshold("TEMPERATURE_CELSIUS", 11.0, min_threshold=18.0, max_threshold=26.0)
    assert breached
    assert severity == "CRITICAL"


def test_calculate_power_consumption_cost():
    # 100 kWh at default ₹8.50 = ₹850.00
    cost = calculate_power_consumption_cost(100)
    assert cost == Decimal("850.00")

    # Custom tariff ₹9.20
    cost = calculate_power_consumption_cost(Decimal("150.5"), tariff_per_kwh=Decimal("9.20"))
    assert cost == Decimal("1384.60")

    # Zero or negative guards
    assert calculate_power_consumption_cost(0) == Decimal("0.00")
    assert calculate_power_consumption_cost(-50) == Decimal("0.00")


def test_calculate_iot_portfolio_metrics_empty():
    metrics = calculate_iot_portfolio_metrics([])
    assert metrics["total_devices"] == 0
    assert metrics["online_rate_percent"] == Decimal("0.00")
    assert metrics["total_power_kwh"] == Decimal("0.00")
    assert metrics["cold_storage_compliance_percent"] == Decimal("100.00")
    assert metrics["active_alerts_count"] == 0


def test_calculate_iot_portfolio_metrics_fleet():
    devices = [
        {"id": "d1", "status": "ONLINE", "battery_level_percent": 95},
        {"id": "d2", "status": "ONLINE", "battery_level_percent": 85},
        {"id": "d3", "status": "ALERT", "battery_level_percent": 75},
        {"id": "d4", "status": "OFFLINE", "battery_level_percent": None},
        {"id": "d5", "status": "MAINTENANCE", "battery_level_percent": 60},
    ]

    telemetry = [
        {"device_type": "SMART_ENERGY_METER", "telemetry_type": "POWER_KWH", "reading_value": 450.5, "is_breach": False},
        {"device_type": "SMART_ENERGY_METER", "telemetry_type": "POWER_KWH", "reading_value": 320.0, "is_breach": False},
        {"device_type": "KITCHEN_COLD_STORAGE_SENSOR", "telemetry_type": "TEMPERATURE_CELSIUS", "reading_value": 2.1, "is_breach": False},
        {"device_type": "KITCHEN_COLD_STORAGE_SENSOR", "telemetry_type": "TEMPERATURE_CELSIUS", "reading_value": 7.8, "is_breach": True},
    ]

    metrics = calculate_iot_portfolio_metrics(devices, telemetry)
    assert metrics["total_devices"] == 5
    assert metrics["online_devices"] == 2
    assert metrics["alert_devices"] == 1
    assert metrics["offline_devices"] == 1
    assert metrics["maintenance_devices"] == 1
    assert metrics["online_rate_percent"] == Decimal("40.00")
    assert metrics["total_power_kwh"] == Decimal("770.50")
    assert metrics["total_power_cost"] == Decimal("6549.25")  # 770.50 * 8.50
    assert metrics["cold_storage_compliance_percent"] == Decimal("50.00")  # 1 out of 2 compliant
    assert metrics["active_alerts_count"] == 1
    # Average battery: (95 + 85 + 75 + 60) / 4 = 315 / 4 = 78.75%
    assert metrics["avg_battery_percent"] == Decimal("78.75")
