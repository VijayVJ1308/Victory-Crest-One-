"""Victory Crest One - IoT & Smart Device Gateways View
Real-time edge sensor telemetry, cold-storage HACCP food safety compliance,
power consumption monitoring, remote smart lock access control, and automated breach alerts.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QTextEdit, QGroupBox, QScrollArea, QSplitter,
    QDoubleSpinBox
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.core.session import session_manager
from desktop.services.api_client import api_client
from desktop.ui.components.status_badge import StatusBadge
from shared.enums import DeviceType, DeviceStatus, SensorTelemetryType


class IoTGatewaysView(QWidget):
    """Central IoT Edge Gateway & Smart Device Fleet Management Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_devices: List[Dict[str, Any]] = []
        self.cached_telemetry: List[Dict[str, Any]] = []
        self.cached_metrics: Dict[str, Any] = {}

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # -----------------------------------------------------
        # 1. Executive Header Section
        # -----------------------------------------------------
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("IoT & Smart Device Gateways")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Real-time sensor telemetry, HACCP cold storage safety, power submetering, and smart room automation.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_simulate = QPushButton("🧪 Ingest Telemetry")
        btn_simulate.setProperty("class", "btn_secondary")
        btn_simulate.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))

        btn_new_dev = QPushButton("➕ Register Device")
        btn_new_dev.setProperty("class", "btn_primary")
        btn_new_dev.clicked.connect(self.open_register_device_dialog)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_simulate)
        header_row.addWidget(btn_new_dev)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive Fleet KPI Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_total_dev = self.create_metric_card("FLEET DEVICES", "0", "0 Online | 0 Alert", "#3B82F6")
        self.card_online_rate = self.create_metric_card("ONLINE AVAILABILITY", "0.0%", "Edge Gateway Liveness", "#10B981")
        self.card_cold_haccp = self.create_metric_card("COLD STORAGE HACCP", "100.0%", "Food Safety Threshold Compliance", "#06B6D4")
        self.card_power_load = self.create_metric_card("POWER CONSUMPTION", "0 kWh", "Estimated Cost: ₹0.00", "#F59E0B")

        cards_row.addWidget(self.card_total_dev)
        cards_row.addWidget(self.card_online_rate)
        cards_row.addWidget(self.card_cold_haccp)
        cards_row.addWidget(self.card_power_load)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Main IoT Gateways Tabs
        # -----------------------------------------------------
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
                background: {ThemeColors.BG_CARD};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {ThemeColors.BG_CARD};
                color: {ThemeColors.TEXT_MUTED};
                padding: 10px 18px;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {ThemeColors.TEXT_MAIN};
                border-bottom: 2px solid {ThemeColors.PRIMARY};
            }}
            QTabBar::tab:hover {{
                color: {ThemeColors.TEXT_MAIN};
            }}
        """)

        # Tab 1: Device Fleet & Telemetry Grid
        self.tab_devices = QWidget()
        self.setup_devices_tab()
        self.tab_widget.addTab(self.tab_devices, "📡 Device Fleet & Status Grid")

        # Tab 2: Live Telemetry Stream & Edge Ingestion
        self.tab_telemetry = QWidget()
        self.setup_telemetry_tab()
        self.tab_widget.addTab(self.tab_telemetry, "📊 Live Sensor Telemetry Stream")

        # Tab 3: Smart Actuator Controls & Remote Playground
        self.tab_controls = QWidget()
        self.setup_controls_tab()
        self.tab_widget.addTab(self.tab_controls, "🎛️ Remote Actuator Controls")

        main_layout.addWidget(self.tab_widget)

    def create_metric_card(self, title: str, value: str, subtext: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 14px 16px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ThemeColors.TEXT_MUTED}; letter-spacing: 0.5px;")

        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {accent_color};")

        lbl_sub = QLabel(subtext)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)
        return card

    # =========================================================================
    # TAB 1: DEVICE FLEET & STATUS GRID
    # =========================================================================

    def setup_devices_tab(self):
        layout = QVBoxLayout(self.tab_devices)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_type = QLabel("Device Type:")
        lbl_type.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_filter_type = QComboBox()
        self.combo_filter_type.addItems(["ALL TYPES", "SMART_ENERGY_METER", "KITCHEN_COLD_STORAGE_SENSOR", "ROOM_CLIMATE_THERMOSTAT", "SMART_DOOR_LOCK", "HVAC_AIR_QUALITY_MONITOR"])
        self.combo_filter_type.currentIndexChanged.connect(self.apply_device_filters)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_filter_status = QComboBox()
        self.combo_filter_status.addItems(["ALL STATUSES", "ONLINE", "ALERT", "OFFLINE", "MAINTENANCE"])
        self.combo_filter_status.currentIndexChanged.connect(self.apply_device_filters)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Search by code, name, or zone...")
        self.txt_search.textChanged.connect(self.apply_device_filters)

        filter_row.addWidget(lbl_type)
        filter_row.addWidget(self.combo_filter_type)
        filter_row.addWidget(lbl_status)
        filter_row.addWidget(self.combo_filter_status)
        filter_row.addWidget(self.txt_search)
        layout.addLayout(filter_row)

        # Devices Table
        self.table_devices = QTableWidget()
        self.table_devices.setColumnCount(9)
        self.table_devices.setHorizontalHeaderLabels([
            "Device Code", "Device Name", "Type", "Location / Zone",
            "Status", "Last Reading", "Safe Thresholds", "Battery / IP", "Actions"
        ])
        self.table_devices.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_devices.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_devices.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_devices.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.table_devices.verticalHeader().setVisible(False)
        self.table_devices.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_devices.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_devices.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_INPUT};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
                border: none;
                border-bottom: 1px solid {ThemeColors.BORDER_DEFAULT};
            }}
        """)
        layout.addWidget(self.table_devices)

    def populate_devices_table(self, devices: List[Dict[str, Any]]):
        self.table_devices.setRowCount(len(devices))
        for row, dev in enumerate(devices):
            # 0: Code
            code_item = QTableWidgetItem(dev.get("device_code", ""))
            code_item.setFont(self.font())
            self.table_devices.setItem(row, 0, code_item)

            # 1: Name
            name_item = QTableWidgetItem(dev.get("name", ""))
            self.table_devices.setItem(row, 1, name_item)

            # 2: Type
            type_val = dev.get("device_type", "").replace("_", " ").title()
            self.table_devices.setItem(row, 2, QTableWidgetItem(type_val))

            # 3: Zone
            self.table_devices.setItem(row, 3, QTableWidgetItem(dev.get("location_zone", "")))

            # 4: Status Badge
            st = dev.get("status", "ONLINE").upper()
            badge = StatusBadge(st)
            cell_widget = QWidget()
            b_layout = QHBoxLayout(cell_widget)
            b_layout.setContentsMargins(4, 2, 4, 2)
            b_layout.setAlignment(Qt.AlignCenter)
            b_layout.addWidget(badge)
            self.table_devices.setCellWidget(row, 4, cell_widget)

            # 5: Last Reading
            val = dev.get("last_reading_value")
            unit = dev.get("unit_of_measure", "")
            if val is not None:
                reading_str = f"{val} {unit}"
            else:
                reading_str = "No telemetry"
            self.table_devices.setItem(row, 5, QTableWidgetItem(reading_str))

            # 6: Thresholds
            min_t = dev.get("min_threshold")
            max_t = dev.get("max_threshold")
            if min_t is not None and max_t is not None:
                thresh_str = f"{min_t} ~ {max_t} {unit}"
            elif max_t is not None:
                thresh_str = f"<= {max_t} {unit}"
            elif min_t is not None:
                thresh_str = f">= {min_t} {unit}"
            else:
                thresh_str = "Unbounded"
            self.table_devices.setItem(row, 6, QTableWidgetItem(thresh_str))

            # 7: Battery / IP
            batt = dev.get("battery_level_percent")
            ip = dev.get("ip_address") or "DHCP"
            if batt is not None:
                spec_str = f"🔋 {batt}% ({ip})"
            else:
                spec_str = f"⚡ Mains ({ip})"
            self.table_devices.setItem(row, 7, QTableWidgetItem(spec_str))

            # 8: Action button (Command)
            btn_act = QPushButton("🎛️ Command")
            btn_act.setStyleSheet(f"font-size: 11px; padding: 3px 8px; background: {ThemeColors.BG_INPUT}; color: {ThemeColors.TEXT_MAIN}; border: 1px solid {ThemeColors.BORDER_DEFAULT}; border-radius: 4px;")
            btn_act.clicked.connect(lambda checked=False, d=dev: self.open_command_dialog(d))
            self.table_devices.setCellWidget(row, 8, btn_act)

    def apply_device_filters(self):
        f_type = self.combo_filter_type.currentText()
        f_status = self.combo_filter_status.currentText()
        search_query = self.txt_search.text().lower().strip()

        filtered = []
        for d in self.cached_devices:
            if f_type != "ALL TYPES" and d.get("device_type", "").upper() != f_type.upper():
                continue
            if f_status != "ALL STATUSES" and d.get("status", "").upper() != f_status.upper():
                continue
            if search_query:
                haystack = f"{d.get('device_code', '')} {d.get('name', '')} {d.get('location_zone', '')}".lower()
                if search_query not in haystack:
                    continue
            filtered.append(d)

        self.populate_devices_table(filtered)

    # =========================================================================
    # TAB 2: LIVE TELEMETRY STREAM & EDGE INGESTION
    # =========================================================================

    def setup_telemetry_tab(self):
        layout = QHBoxLayout(self.tab_telemetry)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Splitter: Left = Telemetry Stream Table, Right = Ingestion Simulator Form
        splitter = QSplitter(Qt.Horizontal)

        # Left Column: Stream Table
        left_box = QWidget()
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        lbl_stream = QLabel("High-Frequency Sensor Telemetry History (Latest 100)")
        lbl_stream.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {ThemeColors.TEXT_MAIN};")
        left_layout.addWidget(lbl_stream)

        self.table_telemetry = QTableWidget()
        self.table_telemetry.setColumnCount(7)
        self.table_telemetry.setHorizontalHeaderLabels([
            "Timestamp", "Device Code", "Sensor Metric", "Reading",
            "Breach?", "Alert Severity", "Operational Message"
        ])
        self.table_telemetry.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_telemetry.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_telemetry.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_telemetry.verticalHeader().setVisible(False)
        self.table_telemetry.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_telemetry.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_telemetry.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_INPUT};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
                border: none;
                border-bottom: 1px solid {ThemeColors.BORDER_DEFAULT};
            }}
        """)
        left_layout.addWidget(self.table_telemetry)
        splitter.addWidget(left_box)

        # Right Column: Edge Sensor Ingestion Simulator
        right_box = QFrame()
        right_box.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_INPUT};
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        right_layout = QVBoxLayout(right_box)
        right_layout.setSpacing(12)

        lbl_sim_title = QLabel("📡 Edge Sensor Telemetry Simulator")
        lbl_sim_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        lbl_sim_desc = QLabel("Submit edge telemetry to test dynamic threshold evaluation, alert generation, and automated cross-module workflow rules.")
        lbl_sim_desc.setWordWrap(True)
        lbl_sim_desc.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MUTED};")

        right_layout.addWidget(lbl_sim_title)
        right_layout.addWidget(lbl_sim_desc)

        form = QFormLayout()
        form.setSpacing(10)

        self.combo_sim_device = QComboBox()
        self.combo_sim_device.currentIndexChanged.connect(self.on_sim_device_changed)

        self.combo_sim_type = QComboBox()
        self.combo_sim_type.addItems([
            "TEMPERATURE_CELSIUS",
            "POWER_KWH",
            "AIR_QUALITY_AQI",
            "DOOR_STATE",
            "HUMIDITY_PERCENT"
        ])

        self.spin_sim_reading = QDoubleSpinBox()
        self.spin_sim_reading.setRange(-50.0, 5000.0)
        self.spin_sim_reading.setDecimals(2)
        self.spin_sim_reading.setValue(2.5)

        self.txt_sim_unit = QLineEdit("°C")

        form.addRow("Target Device:", self.combo_sim_device)
        form.addRow("Telemetry Type:", self.combo_sim_type)
        form.addRow("Reading Value:", self.spin_sim_reading)
        form.addRow("Engineering Unit:", self.txt_sim_unit)
        right_layout.addLayout(form)

        btn_ingest = QPushButton("🚀 Ingest Telemetry Reading")
        btn_ingest.setProperty("class", "btn_primary")
        btn_ingest.clicked.connect(self.trigger_telemetry_ingest)
        right_layout.addWidget(btn_ingest)

        # Ingestion result output area
        lbl_res = QLabel("Ingestion & Workflow Response:")
        lbl_res.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ThemeColors.TEXT_MUTED}; margin-top: 10px;")
        right_layout.addWidget(lbl_res)

        self.txt_ingest_output = QTextEdit()
        self.txt_ingest_output.setReadOnly(True)
        self.txt_ingest_output.setPlaceholderText("Telemetry evaluation result and cross-module workflow triggers will display here...")
        self.txt_ingest_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                color: {ThemeColors.TEXT_MAIN};
                font-family: monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)
        right_layout.addWidget(self.txt_ingest_output)
        right_layout.addStretch()

        splitter.addWidget(right_box)
        splitter.setSizes([600, 360])
        layout.addWidget(splitter)

    def populate_telemetry_table(self, telemetry: List[Dict[str, Any]]):
        self.table_telemetry.setRowCount(len(telemetry))
        for row, t in enumerate(telemetry):
            # 0: Time
            rec_at = t.get("recorded_at", "")
            if isinstance(rec_at, datetime):
                rec_str = rec_at.strftime("%H:%M:%S")
            else:
                rec_str = str(rec_at)[:19].replace("T", " ")
            self.table_telemetry.setItem(row, 0, QTableWidgetItem(rec_str))

            # 1: Code
            self.table_telemetry.setItem(row, 1, QTableWidgetItem(t.get("device_code", "")))

            # 2: Type
            m_type = t.get("telemetry_type", "").replace("_", " ")
            self.table_telemetry.setItem(row, 2, QTableWidgetItem(m_type))

            # 3: Reading
            val = t.get("reading_value", 0)
            unit = t.get("unit", "")
            self.table_telemetry.setItem(row, 3, QTableWidgetItem(f"{val} {unit}"))

            # 4: Breach Badge
            is_breach = t.get("is_breach", False)
            badge_text = "BREACH" if is_breach else "NOMINAL"
            badge = StatusBadge(badge_text)
            cell_widget = QWidget()
            b_layout = QHBoxLayout(cell_widget)
            b_layout.setContentsMargins(4, 2, 4, 2)
            b_layout.setAlignment(Qt.AlignCenter)
            b_layout.addWidget(badge)
            self.table_telemetry.setCellWidget(row, 4, cell_widget)

            # 5: Severity
            sev = t.get("alert_severity", "INFO")
            sev_item = QTableWidgetItem(sev)
            if sev == "CRITICAL":
                sev_item.setForeground(Qt.red)
            elif sev == "WARNING":
                sev_item.setForeground(Qt.yellow)
            self.table_telemetry.setItem(row, 5, sev_item)

            # 6: Message
            self.table_telemetry.setItem(row, 6, QTableWidgetItem(t.get("alert_message", "")))

    def on_sim_device_changed(self):
        code = self.combo_sim_device.currentText()
        for d in self.cached_devices:
            if d.get("device_code") == code:
                dev_type = d.get("device_type", "")
                unit = d.get("unit_of_measure", "")
                self.txt_sim_unit.setText(unit)

                if "ENERGY" in dev_type:
                    self.combo_sim_type.setCurrentText("POWER_KWH")
                    self.spin_sim_reading.setValue(450.0)
                elif "COLD" in dev_type or "THERMOSTAT" in dev_type:
                    self.combo_sim_type.setCurrentText("TEMPERATURE_CELSIUS")
                    self.spin_sim_reading.setValue(float(d.get("last_reading_value") or 3.0))
                elif "AQI" in dev_type:
                    self.combo_sim_type.setCurrentText("AIR_QUALITY_AQI")
                    self.spin_sim_reading.setValue(45.0)
                elif "LOCK" in dev_type:
                    self.combo_sim_type.setCurrentText("DOOR_STATE")
                    self.spin_sim_reading.setValue(1.0)
                break

    def trigger_telemetry_ingest(self):
        dev_code = self.combo_sim_device.currentText()
        t_type = self.combo_sim_type.currentText()
        val = self.spin_sim_reading.value()
        unit = self.txt_sim_unit.text().strip()

        payload = {
            "device_code": dev_code,
            "telemetry_type": t_type,
            "reading_value": val,
            "unit": unit
        }

        try:
            res = api_client.ingest_iot_telemetry(payload)
            is_breach = res.get("is_breach", False)
            sev = res.get("alert_severity", "INFO")
            msg = res.get("alert_message", "")

            formatted = json.dumps({
                "status": "INGESTED_SUCCESSFULLY",
                "device_code": dev_code,
                "reading": f"{val} {unit}",
                "is_threshold_breach": is_breach,
                "alert_severity": sev,
                "operational_message": msg,
                "workflow_dispatched": is_breach,
                "timestamp": str(res.get("recorded_at", ""))
            }, indent=2)

            self.txt_ingest_output.setPlainText(formatted)
            self.refresh_data()
        except Exception as e:
            self.txt_ingest_output.setPlainText(f"❌ Ingestion Error:\n{str(e)}")

    # =========================================================================
    # TAB 3: SMART ACTUATOR CONTROLS & REMOTE PLAYGROUND
    # =========================================================================

    def setup_controls_tab(self):
        layout = QVBoxLayout(self.tab_controls)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        lbl_desc = QLabel("Remote Actuator Controls & Building Automation Gateway")
        lbl_desc.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(lbl_desc)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        cards_container = QWidget()
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setSpacing(14)

        # 1. Thermostat Climate Actuator Card
        card_thermo = self.create_actuator_card(
            title="🌡️ Room Climate Thermostat Control (IOT-MDR-STAT-401)",
            description="Adjust room temperature setpoint for Presidential Suite 401. Automatically sends command to HVAC variable refrigerant flow unit.",
            actions=[
                ("Cool to 20°C", lambda: self.dispatch_command("IOT-MDR-STAT-401", "SET_TEMPERATURE", {"target_temp": 20.0})),
                ("Eco Mode 23°C", lambda: self.dispatch_command("IOT-MDR-STAT-401", "SET_TEMPERATURE", {"target_temp": 23.0})),
                ("Warm to 25°C", lambda: self.dispatch_command("IOT-MDR-STAT-401", "SET_TEMPERATURE", {"target_temp": 25.0}))
            ]
        )
        cards_layout.addWidget(card_thermo)

        # 2. Smart Door Lock Access Control Card
        card_lock = self.create_actuator_card(
            title="🔐 RFID/BLE Smart Door Lock (IOT-MDR-LOCK-401)",
            description="Manage electronic lock mechanism for Suite 401 entrance portico. Dispatches encrypted cryptographic lock/unlock signals.",
            actions=[
                ("🔒 Lock Door", lambda: self.dispatch_command("IOT-MDR-LOCK-401", "LOCK_DOOR")),
                ("🔓 Unlock Door", lambda: self.dispatch_command("IOT-MDR-LOCK-401", "UNLOCK_DOOR"))
            ]
        )
        cards_layout.addWidget(card_lock)

        # 3. Cold Storage Chiller Sensor Calibration Card
        card_chiller = self.create_actuator_card(
            title="❄️ HACCP Cold Storage Chiller Recalibration (IOT-MDR-CHILL-01)",
            description="Execute electronic zero-point offset calibration on food safety walk-in chiller temperature sensor probe.",
            actions=[
                ("🔧 Recalibrate Sensor Probe", lambda: self.dispatch_command("IOT-MDR-CHILL-01", "RECALIBRATE")),
                ("🔄 Reboot Edge Gateway Node", lambda: self.dispatch_command("IOT-MDR-CHILL-01", "RESET"))
            ]
        )
        cards_layout.addWidget(card_chiller)

        # Command Output Log Area
        lbl_cmd_log = QLabel("Actuator Command Dispatch Audit Stream:")
        lbl_cmd_log.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {ThemeColors.TEXT_MAIN}; margin-top: 10px;")
        cards_layout.addWidget(lbl_cmd_log)

        self.txt_cmd_output = QTextEdit()
        self.txt_cmd_output.setReadOnly(True)
        self.txt_cmd_output.setFixedHeight(120)
        self.txt_cmd_output.setPlaceholderText("Command dispatch acknowledgements and edge device telemetry will appear here...")
        self.txt_cmd_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeColors.BG_INPUT};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                color: {ThemeColors.TEXT_MAIN};
                font-family: monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)
        cards_layout.addWidget(self.txt_cmd_output)

        scroll.setWidget(cards_container)
        layout.addWidget(scroll)

    def create_actuator_card(self, title: str, description: str, actions: List[tuple]) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 14px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")

        lbl_d = QLabel(description)
        lbl_d.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MUTED};")
        lbl_d.setWordWrap(True)

        layout.addWidget(lbl_t)
        layout.addWidget(lbl_d)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        for label, handler in actions:
            btn = QPushButton(label)
            btn.setProperty("class", "btn_secondary")
            btn.clicked.connect(handler)
            btn_row.addWidget(btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return card

    def dispatch_command(self, device_id: str, command: str, parameters: Optional[Dict[str, Any]] = None):
        try:
            res = api_client.send_iot_device_command(device_id, command, parameters)
            now_str = datetime.now().strftime("%H:%M:%S")
            log_line = f"[{now_str}] DISPATCH -> Device '{device_id}' | Command '{command}' | Status: {res.get('status')} | Message: {res.get('message')}"
            self.txt_cmd_output.append(log_line)
            self.refresh_data()
        except Exception as e:
            self.txt_cmd_output.append(f"❌ Error sending command to {device_id}: {str(e)}")

    # =========================================================================
    # MODAL DIALOGS
    # =========================================================================

    def open_register_device_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register New IoT Device")
        dialog.setMinimumWidth(440)
        dialog.setStyleSheet(f"background-color: {ThemeColors.BG_CARD}; color: {ThemeColors.TEXT_MAIN};")

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        txt_code = QLineEdit()
        txt_code.setPlaceholderText("e.g. IOT-MDR-HVAC-03")

        txt_name = QLineEdit()
        txt_name.setPlaceholderText("e.g. Banquet Hall Variable Air Volume Damper")

        combo_type = QComboBox()
        combo_type.addItems([
            "SMART_ENERGY_METER",
            "KITCHEN_COLD_STORAGE_SENSOR",
            "ROOM_CLIMATE_THERMOSTAT",
            "SMART_DOOR_LOCK",
            "HVAC_AIR_QUALITY_MONITOR"
        ])

        txt_zone = QLineEdit()
        txt_zone.setPlaceholderText("e.g. North Banquet Hall Ceiling Zone")

        spin_min = QDoubleSpinBox()
        spin_min.setRange(-50.0, 10000.0)
        spin_min.setValue(0.0)

        spin_max = QDoubleSpinBox()
        spin_max.setRange(-50.0, 10000.0)
        spin_max.setValue(100.0)

        txt_unit = QLineEdit("°C")

        form.addRow("Device Code *:", txt_code)
        form.addRow("Device Name *:", txt_name)
        form.addRow("Device Type *:", combo_type)
        form.addRow("Location / Zone *:", txt_zone)
        form.addRow("Min Safe Threshold:", spin_min)
        form.addRow("Max Safe Threshold:", spin_max)
        form.addRow("Unit of Measure:", txt_unit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)

        btn_save = QPushButton("Register Device")
        btn_save.setProperty("class", "btn_primary")

        def on_save():
            code = txt_code.text().strip().upper()
            name = txt_name.text().strip()
            zone = txt_zone.text().strip()
            if not code or not name or not zone:
                QMessageBox.warning(dialog, "Validation Error", "Device Code, Name, and Zone are required.")
                return

            prop_id = session_manager.active_property.get("id") if session_manager.active_property else None
            payload = {
                "device_code": code,
                "name": name,
                "device_type": combo_type.currentText(),
                "location_zone": zone,
                "status": "ONLINE",
                "min_threshold": spin_min.value(),
                "max_threshold": spin_max.value(),
                "unit_of_measure": txt_unit.text().strip() or "°C",
                "property_id": prop_id
            }

            try:
                api_client.create_iot_device(payload)
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to register device: {str(e)}")

        btn_save.clicked.connect(on_save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_command_dialog(self, dev: Dict[str, Any]):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Actuator Command - {dev.get('device_code')}")
        dialog.setMinimumWidth(380)
        dialog.setStyleSheet(f"background-color: {ThemeColors.BG_CARD}; color: {ThemeColors.TEXT_MAIN};")

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        lbl = QLabel(f"Send command to {dev.get('name')}:")
        lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(lbl)

        combo_cmd = QComboBox()
        dev_type = dev.get("device_type", "")
        if "THERMOSTAT" in dev_type:
            combo_cmd.addItems(["SET_TEMPERATURE", "RESET"])
        elif "LOCK" in dev_type:
            combo_cmd.addItems(["LOCK_DOOR", "UNLOCK_DOOR", "RESET"])
        else:
            combo_cmd.addItems(["RECALIBRATE", "RESET"])

        spin_param = QDoubleSpinBox()
        spin_param.setRange(16.0, 32.0)
        spin_param.setValue(22.0)

        form = QFormLayout()
        form.addRow("Command:", combo_cmd)
        form.addRow("Temperature Param (if applicable):", spin_param)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)

        btn_dispatch = QPushButton("Dispatch Command")
        btn_dispatch.setProperty("class", "btn_primary")

        def on_dispatch():
            cmd = combo_cmd.currentText()
            params = {}
            if cmd == "SET_TEMPERATURE":
                params["target_temp"] = spin_param.value()

            self.dispatch_command(dev.get("device_code"), cmd, params)
            dialog.accept()

        btn_dispatch.clicked.connect(on_dispatch)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_dispatch)
        layout.addLayout(btn_row)

        dialog.exec()

    # =========================================================================
    # DATA REFRESH
    # =========================================================================

    def refresh_data(self):
        prop_id = session_manager.active_property.get("id") if session_manager.active_property else None

        # Fetch devices
        try:
            self.cached_devices = api_client.get_iot_devices(property_id=prop_id)
        except Exception:
            self.cached_devices = []

        # Fetch telemetry history
        try:
            self.cached_telemetry = api_client.get_iot_telemetry_history(property_id=prop_id, limit=100)
        except Exception:
            self.cached_telemetry = []

        # Fetch metrics
        try:
            self.cached_metrics = api_client.get_iot_metrics(property_id=prop_id)
        except Exception:
            self.cached_metrics = {}

        # Update metric cards
        tot = self.cached_metrics.get("total_devices", len(self.cached_devices))
        onl = self.cached_metrics.get("online_devices", 0)
        alt = self.cached_metrics.get("alert_devices", 0)
        off = self.cached_metrics.get("offline_devices", 0)
        rate = self.cached_metrics.get("online_rate_percent", "0.00")
        haccp = self.cached_metrics.get("cold_storage_compliance_percent", "100.00")
        kwh = self.cached_metrics.get("total_power_kwh", "0.00")
        cost = self.cached_metrics.get("total_power_cost", "0.00")

        self.update_card_labels(self.card_total_dev, str(tot), f"{onl} Online | {alt} Alert | {off} Offline")
        self.update_card_labels(self.card_online_rate, f"{rate}%", "Edge Gateway Liveness")
        self.update_card_labels(self.card_cold_haccp, f"{haccp}%", "Food Safety Threshold Compliance")
        self.update_card_labels(self.card_power_load, f"{kwh} kWh", f"Estimated Cost: ₹{cost}")

        # Update simulator combo
        current_sel = self.combo_sim_device.currentText()
        self.combo_sim_device.clear()
        for d in self.cached_devices:
            self.combo_sim_device.addItem(d.get("device_code", ""))
        if current_sel:
            idx = self.combo_sim_device.findText(current_sel)
            if idx >= 0:
                self.combo_sim_device.setCurrentIndex(idx)

        # Populate tables
        self.apply_device_filters()
        self.populate_telemetry_table(self.cached_telemetry)

    def update_card_labels(self, card: QFrame, val: str, sub: str):
        layout = card.layout()
        if layout and layout.count() >= 3:
            lbl_val = layout.itemAt(1).widget()
            lbl_sub = layout.itemAt(2).widget()
            if isinstance(lbl_val, QLabel):
                lbl_val.setText(val)
            if isinstance(lbl_sub, QLabel):
                lbl_sub.setText(sub)
