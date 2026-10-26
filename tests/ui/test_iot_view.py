"""Victory Crest One - Desktop UI Tests for IoT & Smart Device Gateways View
Verifies initialization, metric cards, fleet table population, telemetry ingestion simulator,
actuator control playground, and MainWindow stack navigation at index 19.
"""

import pytest
from desktop.ui.views.iot_view import IoTGatewaysView
from desktop.ui.main_window import MainWindow


def test_iot_view_initialization(qapp):
    view = IoTGatewaysView()
    assert view is not None

    # Check metric cards
    assert view.card_total_dev is not None
    assert view.card_online_rate is not None
    assert view.card_cold_haccp is not None
    assert view.card_power_load is not None

    # Check 3 tabs
    assert view.tab_widget.count() == 3

    # Check device fleet table populated for active property (Madurai has 6 devices, total fleet has >= 8)
    assert view.table_devices.rowCount() >= 6
    assert len(view.cached_devices) >= 6

    # Check telemetry stream table
    assert view.table_telemetry.rowCount() >= 1

    # Check simulator controls
    assert view.combo_sim_device.count() >= 6
    assert view.combo_filter_type.count() >= 5
    assert view.combo_filter_status.count() >= 4


def test_iot_view_telemetry_simulation(qapp):
    view = IoTGatewaysView()

    # Select chiller and ingest a nominal reading
    view.combo_sim_device.setCurrentText("IOT-MDR-CHILL-01")
    view.spin_sim_reading.setValue(2.4)
    view.trigger_telemetry_ingest()

    output = view.txt_ingest_output.toPlainText()
    assert "INGESTED_SUCCESSFULLY" in output
    assert "IOT-MDR-CHILL-01" in output


def test_main_window_iot_navigation(qapp):
    window = MainWindow()
    assert "iot_gateways" in window.nav_buttons

    window.navigate_to("iot_gateways")
    assert window.view_stack.currentIndex() == 19
    assert window.current_nav_key == "iot_gateways"
    assert window.iot_view is not None
