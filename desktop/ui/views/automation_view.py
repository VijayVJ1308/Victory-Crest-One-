"""Victory Crest One - Workflow Automation & Event Rules Engine View
Active Automation Rules, Action Pipelines, Execution Audit Logs,
and Real-time Event Dispatcher / Webhook Simulator.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QTextEdit, QGroupBox, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from desktop.ui.components.status_badge import StatusBadge


class WorkflowAutomationView(QWidget):
    """Central Automation and Event Rules Engine Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_rules: List[Dict[str, Any]] = []
        self.cached_logs: List[Dict[str, Any]] = []
        self.cached_telemetry: Dict[str, Any] = {}

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

        title = QLabel("Workflow Automation & Event Rules Engine")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Cross-module event triggers, conditional decision trees, automated multi-step pipelines, and live audit telemetry.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_simulate = QPushButton("⚡ Simulate Event")
        btn_simulate.setProperty("class", "btn_secondary")
        btn_simulate.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))

        btn_new_rule = QPushButton("➕ New Automation Rule")
        btn_new_rule.setProperty("class", "btn_primary")
        btn_new_rule.clicked.connect(self.open_new_rule_dialog)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_simulate)
        header_row.addWidget(btn_new_rule)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Automation Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_active_rules = self.create_metric_card("ACTIVE WORKFLOWS", "0", "0 Total Configured", "#10B981")
        self.card_total_exec = self.create_metric_card("TOTAL EXECUTIONS", "0", "Automated Events Dispatched", "#3B82F6")
        self.card_success_rate = self.create_metric_card("SUCCESS RATE", "0.0%", "Evaluated Without Error", "#8B5CF6")
        self.card_actions_triggered = self.create_metric_card("ACTIONS TRIGGERED", "0", "Tasks, POs, Alerts, Journals", "#F59E0B")

        cards_row.addWidget(self.card_active_rules)
        cards_row.addWidget(self.card_total_exec)
        cards_row.addWidget(self.card_success_rate)
        cards_row.addWidget(self.card_actions_triggered)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Main Automation Tabs
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
        self.tabs = self.tab_widget

        # Tab 1: Workflow Rules Catalog & Pipelines
        self.tab_rules = QWidget()
        self.setup_rules_tab()
        self.tab_widget.addTab(self.tab_rules, "⚡ Rules Catalog & Action Pipelines")

        # Tab 2: Execution Audit Trail Logs
        self.tab_logs = QWidget()
        self.setup_logs_tab()
        self.tab_widget.addTab(self.tab_logs, "📜 Execution Audit Logs")

        # Tab 3: Interactive Event Dispatcher & Webhook Simulator
        self.tab_simulator = QWidget()
        self.setup_simulator_tab()
        self.tab_widget.addTab(self.tab_simulator, "🧪 Event Dispatcher & Simulator")

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ThemeColors.TEXT_DIM}; letter-spacing: 0.5px;")

        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {accent_color};")

        lbl_sub = QLabel(subtext)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)
        card.lbl_val = lbl_val
        card.lbl_sub = lbl_sub
        return card

    # =========================================================================
    # TAB 1: Rules Catalog & Action Pipelines
    # =========================================================================
    def setup_rules_tab(self):
        layout = QVBoxLayout(self.tab_rules)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters Row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_filter = QLabel("Filter:")
        lbl_filter.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        filter_row.addWidget(lbl_filter)

        self.rules_status_combo = QComboBox()
        self.rules_status_combo.addItems(["All Statuses", "ACTIVE", "PAUSED"])
        self.rules_status_combo.currentIndexChanged.connect(self.apply_rules_filter)
        filter_row.addWidget(self.rules_status_combo)

        self.rules_trigger_combo = QComboBox()
        self.rules_trigger_combo.addItems(["All Triggers", "STATE_CHANGE", "THRESHOLD", "SCHEDULED_CRON", "WEBHOOK"])
        self.rules_trigger_combo.currentIndexChanged.connect(self.apply_rules_filter)
        filter_row.addWidget(self.rules_trigger_combo)

        self.rules_search = QLineEdit()
        self.rules_search.setPlaceholderText("Search rule code, title, or target event...")
        self.rules_search.textChanged.connect(self.apply_rules_filter)
        filter_row.addWidget(self.rules_search)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Splitter: Table above, details inspector below
        splitter = QSplitter(Qt.Vertical)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(8)
        self.rules_table.setHorizontalHeaderLabels([
            "Code", "Workflow Name", "Trigger Type", "Trigger Event",
            "Conditions", "Actions", "Status", "Quick Action"
        ])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.rules_table.itemSelectionChanged.connect(self.on_rule_selected)
        splitter.addWidget(self.rules_table)

        # Inspector Panel
        inspector_frame = QFrame()
        inspector_frame.setStyleSheet(f"background-color: {ThemeColors.BG_SURFACE}; border-radius: 6px; padding: 12px;")
        inspector_layout = QVBoxLayout(inspector_frame)
        inspector_layout.setContentsMargins(12, 10, 12, 10)
        inspector_layout.setSpacing(6)

        self.inspector_title = QLabel("Select a workflow rule above to inspect its condition logic and multi-step action pipeline.")
        self.inspector_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        self.inspector_desc = QLabel("")
        self.inspector_desc.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MUTED};")
        self.inspector_desc.setWordWrap(True)

        self.inspector_pipeline = QLabel("")
        self.inspector_pipeline.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MUTED}; font-family: monospace;")
        self.inspector_pipeline.setWordWrap(True)

        inspector_layout.addWidget(self.inspector_title)
        inspector_layout.addWidget(self.inspector_desc)
        inspector_layout.addWidget(self.inspector_pipeline)
        splitter.addWidget(inspector_frame)

        splitter.setSizes([320, 140])
        layout.addWidget(splitter)

    def populate_rules_table(self, rules: List[Dict[str, Any]]):
        self.rules_table.setRowCount(0)
        for row_idx, r in enumerate(rules):
            self.rules_table.insertRow(row_idx)

            code_item = QTableWidgetItem(r.get("code", ""))
            code_item.setData(Qt.UserRole, r)
            self.rules_table.setItem(row_idx, 0, code_item)

            name_item = QTableWidgetItem(r.get("name", ""))
            self.rules_table.setItem(row_idx, 1, name_item)

            trig_item = QTableWidgetItem(r.get("trigger_type", ""))
            self.rules_table.setItem(row_idx, 2, trig_item)

            event_item = QTableWidgetItem(r.get("trigger_event", ""))
            self.rules_table.setItem(row_idx, 3, event_item)

            conds = r.get("conditions") or []
            cond_str = f"{len(conds)} condition(s)" if conds else "Always (Unconditional)"
            if conds:
                c0 = conds[0]
                cond_str = f"{c0.get('field')} {c0.get('operator')} {c0.get('value')}"
                if len(conds) > 1:
                    cond_str += f" (+{len(conds)-1} more)"
            self.rules_table.setItem(row_idx, 4, QTableWidgetItem(cond_str))

            actions = r.get("actions") or []
            self.rules_table.setItem(row_idx, 5, QTableWidgetItem(f"{len(actions)} Action(s)"))

            status_str = r.get("status", "ACTIVE")
            status_item = QTableWidgetItem(status_str)
            if status_str == "ACTIVE":
                status_item.setForeground(Qt.green)
            else:
                status_item.setForeground(Qt.yellow)
            self.rules_table.setItem(row_idx, 6, status_item)

            # Toggle button
            rule_id = r.get("id")
            toggle_text = "Pause" if status_str == "ACTIVE" else "Activate"
            btn_toggle = QPushButton(toggle_text)
            btn_toggle.setProperty("class", "btn_secondary")
            btn_toggle.setStyleSheet("font-size: 11px; padding: 4px 8px;")
            btn_toggle.clicked.connect(lambda ch, rid=rule_id: self.toggle_rule_status(rid))
            self.rules_table.setCellWidget(row_idx, 7, btn_toggle)

    def apply_rules_filter(self):
        status_sel = self.rules_status_combo.currentText()
        trigger_sel = self.rules_trigger_combo.currentText()
        search_query = self.rules_search.text().strip().lower()

        filtered = self.cached_rules
        if status_sel != "All Statuses":
            filtered = [r for r in filtered if r.get("status", "").upper() == status_sel.upper()]
        if trigger_sel != "All Triggers":
            filtered = [r for r in filtered if r.get("trigger_type", "").upper() == trigger_sel.upper()]
        if search_query:
            filtered = [
                r for r in filtered
                if search_query in r.get("code", "").lower()
                or search_query in r.get("name", "").lower()
                or search_query in r.get("trigger_event", "").lower()
            ]

        self.populate_rules_table(filtered)

    def on_rule_selected(self):
        selected_rows = self.rules_table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item = self.rules_table.item(row, 0)
        if not item:
            return
        r = item.data(Qt.UserRole)
        if not r:
            return

        self.inspector_title.setText(f"📋 {r.get('code')}: {r.get('name')}")
        self.inspector_desc.setText(r.get("description") or "No description provided.")

        conds = r.get("conditions") or []
        actions = r.get("actions") or []

        cond_text = "None (Fires on all occurrences)"
        if conds:
            cond_lines = [f"   • {c.get('field')} {c.get('operator')} {c.get('value')}" for c in conds]
            cond_text = "\n" + "\n".join(cond_lines)

        action_lines = []
        for idx, act in enumerate(actions, 1):
            act_type = act.get("action_type")
            params = json.dumps(act.get("parameters", {}), ensure_ascii=False)
            action_lines.append(f"   Step {idx}: [{act_type}] -> {params}")
        action_text = "\n" + "\n".join(action_lines)

        pipeline_str = f"Trigger Event: {r.get('trigger_event')} ({r.get('trigger_type')})\nConditions Met Logic:{cond_text}\nExecution Pipeline:{action_text}"
        self.inspector_pipeline.setText(pipeline_str)

    def toggle_rule_status(self, rule_id: str):
        res = api_client.toggle_automation_rule(rule_id)
        if res:
            self.refresh_data()

    # =========================================================================
    # TAB 2: Execution Audit Trail Logs
    # =========================================================================
    def setup_logs_tab(self):
        layout = QVBoxLayout(self.tab_logs)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_filter = QLabel("Status:")
        lbl_filter.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        filter_row.addWidget(lbl_filter)

        self.logs_status_combo = QComboBox()
        self.logs_status_combo.addItems(["All Statuses", "SUCCESS", "SKIPPED", "FAILED"])
        self.logs_status_combo.currentIndexChanged.connect(self.apply_logs_filter)
        filter_row.addWidget(self.logs_status_combo)

        self.logs_search = QLineEdit()
        self.logs_search.setPlaceholderText("Search workflow code, name, or event...")
        self.logs_search.textChanged.connect(self.apply_logs_filter)
        filter_row.addWidget(self.logs_search)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        splitter = QSplitter(Qt.Vertical)

        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "Rule Code", "Workflow Name", "Trigger Event",
            "Status", "Latency", "Actions Run"
        ])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.logs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.logs_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.logs_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.logs_table.itemSelectionChanged.connect(self.on_log_selected)
        splitter.addWidget(self.logs_table)

        # Log details preview
        self.log_detail_box = QTextEdit()
        self.log_detail_box.setReadOnly(True)
        self.log_detail_box.setPlaceholderText("Select an execution log above to inspect event payload and action outputs...")
        self.log_detail_box.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                color: {ThemeColors.TEXT_MAIN};
                font-family: monospace;
                font-size: 11px;
                padding: 10px;
            }}
        """)
        splitter.addWidget(self.log_detail_box)

        splitter.setSizes([320, 140])
        layout.addWidget(splitter)

    def populate_logs_table(self, logs: List[Dict[str, Any]]):
        self.rules_table.blockSignals(True)
        self.logs_table.setRowCount(0)
        for row_idx, l in enumerate(logs):
            self.logs_table.insertRow(row_idx)

            ts_raw = l.get("executed_at", "")
            ts_str = str(ts_raw)[:19].replace("T", " ")
            ts_item = QTableWidgetItem(ts_str)
            ts_item.setData(Qt.UserRole, l)
            self.logs_table.setItem(row_idx, 0, ts_item)

            self.logs_table.setItem(row_idx, 1, QTableWidgetItem(l.get("workflow_code", "")))
            self.logs_table.setItem(row_idx, 2, QTableWidgetItem(l.get("workflow_name", "")))
            self.logs_table.setItem(row_idx, 3, QTableWidgetItem(l.get("trigger_event", "")))

            st = str(l.get("status", "")).upper()
            status_item = QTableWidgetItem(st)
            if st == "SUCCESS":
                status_item.setForeground(Qt.green)
            elif st == "FAILED":
                status_item.setForeground(Qt.red)
            else:
                status_item.setForeground(Qt.gray)
            self.logs_table.setItem(row_idx, 4, status_item)

            dur = l.get("duration_ms", 0)
            self.logs_table.setItem(row_idx, 5, QTableWidgetItem(f"{dur} ms"))

            actions = l.get("actions_executed") or []
            self.logs_table.setItem(row_idx, 6, QTableWidgetItem(f"{len(actions)} executed"))

        self.rules_table.blockSignals(False)

    def apply_logs_filter(self):
        status_sel = self.logs_status_combo.currentText()
        search_query = self.logs_search.text().strip().lower()

        filtered = self.cached_logs
        if status_sel != "All Statuses":
            filtered = [l for l in filtered if str(l.get("status", "")).upper() == status_sel.upper()]
        if search_query:
            filtered = [
                l for l in filtered
                if search_query in l.get("workflow_code", "").lower()
                or search_query in l.get("workflow_name", "").lower()
                or search_query in l.get("trigger_event", "").lower()
            ]

        self.populate_logs_table(filtered)

    def on_log_selected(self):
        selected_rows = self.logs_table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item = self.logs_table.item(row, 0)
        if not item:
            return
        log_data = item.data(Qt.UserRole)
        if not log_data:
            return

        formatted = json.dumps(log_data, indent=2, default=str)
        self.log_detail_box.setText(formatted)

    # =========================================================================
    # TAB 3: Interactive Event Dispatcher & Simulator
    # =========================================================================
    def setup_simulator_tab(self):
        layout = QVBoxLayout(self.tab_simulator)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        intro = QLabel("Dispatch custom or simulated events into the active rules engine to test triggers, conditions, and action outcomes.")
        intro.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")
        layout.addWidget(intro)

        form_frame = QFrame()
        form_frame.setStyleSheet(f"background-color: {ThemeColors.BG_SURFACE}; border-radius: 8px; padding: 16px;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(12)

        # Preset Event Selector
        preset_row = QHBoxLayout()
        lbl_preset = QLabel("Preset Enterprise Event:")
        lbl_preset.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")
        preset_row.addWidget(lbl_preset)

        self.sim_event_combo = QComboBox()
        self.sim_event_combo.addItems([
            "inventory.stock_level_low (SKU Reorder Alert)",
            "hospitality.vip_checkin (VIP Guest Concierge Alert)",
            "service.sla_warning (Critical P1 SLA Breach Alert)",
            "finance.invoice_overdue (High-Value AR Review)",
            "pos.shift_closed (Cash Drawer Variance Adjustment)"
        ])
        self.sim_event_combo.currentIndexChanged.connect(self.on_sim_preset_changed)
        preset_row.addWidget(self.sim_event_combo)
        form_layout.addLayout(preset_row)

        # Event Name Input
        name_row = QHBoxLayout()
        lbl_name = QLabel("Canonical Event Name:")
        lbl_name.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")
        name_row.addWidget(lbl_name)

        self.sim_event_input = QLineEdit("inventory.stock_level_low")
        name_row.addWidget(self.sim_event_input)
        form_layout.addLayout(name_row)

        # Payload Editor
        lbl_payload = QLabel("Event Payload (JSON):")
        lbl_payload.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")
        form_layout.addWidget(lbl_payload)

        self.sim_payload_editor = QTextEdit()
        self.sim_payload_editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                color: {ThemeColors.TEXT_MAIN};
                font-family: monospace;
                font-size: 12px;
                padding: 10px;
                min-height: 120px;
            }}
        """)
        self.sim_payload_editor.setText(json.dumps({
            "item_code": "SKU-HOSP-01",
            "current_stock": 8,
            "reorder_point": 15,
            "warehouse": "Main Central Stores"
        }, indent=2))
        form_layout.addWidget(self.sim_payload_editor)

        # Dispatch Button
        btn_dispatch = QPushButton("🚀 Dispatch Event to Rules Engine")
        btn_dispatch.setProperty("class", "btn_primary")
        btn_dispatch.setFixedHeight(38)
        btn_dispatch.clicked.connect(self.execute_event_dispatch)
        form_layout.addWidget(btn_dispatch)

        layout.addWidget(form_frame)

        # Results Output Box
        results_group = QGroupBox("Dispatch Execution Results")
        results_layout = QVBoxLayout(results_group)

        self.sim_results_box = QTextEdit()
        self.sim_results_box.setReadOnly(True)
        self.sim_results_box.setPlaceholderText("Execution response, matched rules, and actions triggered will appear here...")
        self.sim_results_box.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                color: {ThemeColors.TEXT_MAIN};
                font-family: monospace;
                font-size: 12px;
                padding: 10px;
            }}
        """)
        results_layout.addWidget(self.sim_results_box)
        layout.addWidget(results_group)

    def on_sim_preset_changed(self, idx: int):
        presets = [
            ("inventory.stock_level_low", {
                "item_code": "SKU-HOSP-01",
                "current_stock": 8,
                "reorder_point": 15,
                "warehouse": "Main Central Stores"
            }),
            ("hospitality.vip_checkin", {
                "reservation_id": "res_mdu_101",
                "guest": {
                    "name": "Ambassador Rajesh Kumar",
                    "tier": "VIP"
                },
                "room_number": "Suite 501"
            }),
            ("service.sla_warning", {
                "ticket_id": "TCK-4001",
                "priority": "P1",
                "hours_remaining": 0.5,
                "customer": "GrandVista Corporate"
            }),
            ("finance.invoice_overdue", {
                "invoice_id": "INV-7001",
                "customer": "Global Energy Corp",
                "balance_due": 95000,
                "days_overdue": 45
            }),
            ("pos.shift_closed", {
                "shift_id": "shift_102",
                "register_id": "REG-MDU-01",
                "cash_variance": -350.00
            })
        ]
        if 0 <= idx < len(presets):
            ev, payload = presets[idx]
            self.sim_event_input.setText(ev)
            self.sim_payload_editor.setText(json.dumps(payload, indent=2))

    def execute_event_dispatch(self):
        ev_name = self.sim_event_input.text().strip()
        if not ev_name:
            QMessageBox.warning(self, "Validation Error", "Please specify a valid event name.")
            return

        try:
            payload = json.loads(self.sim_payload_editor.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "JSON Parse Error", f"Invalid payload JSON:\n{str(e)}")
            return

        res = api_client.dispatch_automation_event(ev_name, payload)
        if res:
            formatted = json.dumps(res, indent=2, default=str)
            self.sim_results_box.setText(formatted)
            self.refresh_data()
        else:
            self.sim_results_box.setText("Event dispatch failed or no response from engine.")

    # =========================================================================
    # New Rule Dialog
    # =========================================================================
    def open_new_rule_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Automation Rule — Victory Crest ONE")
        dialog.resize(520, 460)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        in_name = QLineEdit()
        in_name.setPlaceholderText("e.g. VIP Reservation Express Alert")
        form.addRow("Rule Title *:", in_name)

        in_desc = QLineEdit()
        in_desc.setPlaceholderText("Detailed description of this automated workflow")
        form.addRow("Description:", in_desc)

        combo_trig = QComboBox()
        combo_trig.addItems(["STATE_CHANGE", "THRESHOLD", "SCHEDULED_CRON", "WEBHOOK"])
        form.addRow("Trigger Type:", combo_trig)

        in_event = QLineEdit()
        in_event.setPlaceholderText("e.g. hospitality.vip_checkin")
        form.addRow("Trigger Event *:", in_event)

        in_field = QLineEdit()
        in_field.setPlaceholderText("e.g. guest.tier or current_stock")
        form.addRow("Condition Field:", in_field)

        combo_op = QComboBox()
        combo_op.addItems(["EQUALS", "NOT_EQUALS", "GREATER_THAN", "GREATER_THAN_OR_EQUAL", "LESS_THAN", "LESS_THAN_OR_EQUAL", "CONTAINS"])
        form.addRow("Operator:", combo_op)

        in_value = QLineEdit()
        in_value.setPlaceholderText("e.g. VIP or 15")
        form.addRow("Target Value:", in_value)

        combo_act = QComboBox()
        combo_act.addItems(["SEND_NOTIFICATION", "CREATE_TASK", "TRIGGER_PURCHASE_ORDER", "POST_GL_JOURNAL", "WEBHOOK_CALL"])
        form.addRow("Action Type *:", combo_act)

        in_act_param = QLineEdit()
        in_act_param.setPlaceholderText("e.g. {'title': 'VIP Arrival Alert', 'recipient_role': 'General Manager'}")
        form.addRow("Action Parameters (JSON):", in_act_param)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Save Rule")
        btn_save.setProperty("class", "btn_primary")

        def _save():
            if not in_name.text().strip() or not in_event.text().strip():
                QMessageBox.warning(dialog, "Required Fields", "Title and Event Name are mandatory.")
                return

            conditions = []
            if in_field.text().strip():
                conditions.append({
                    "field": in_field.text().strip(),
                    "operator": combo_op.currentText(),
                    "value": in_value.text().strip()
                })

            act_params = {}
            if in_act_param.text().strip():
                try:
                    act_params = json.loads(in_act_param.text().strip().replace("'", '"'))
                except Exception:
                    act_params = {"summary": in_act_param.text().strip()}

            rule_payload = {
                "name": in_name.text().strip(),
                "description": in_desc.text().strip(),
                "trigger_type": combo_trig.currentText(),
                "trigger_event": in_event.text().strip(),
                "conditions": conditions,
                "actions": [
                    {
                        "action_type": combo_act.currentText(),
                        "parameters": act_params
                    }
                ],
                "status": "ACTIVE"
            }

            created = api_client.create_automation_rule(rule_payload)
            if created:
                self.refresh_data()
                dialog.accept()

        btn_save.clicked.connect(_save)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        dialog.exec()

    # =========================================================================
    # Data Refresh
    # =========================================================================
    def refresh_data(self):
        """Fetch latest rules, execution logs, and telemetry from backend API / service."""
        self.cached_rules = api_client.get_automation_rules()
        self.cached_logs = api_client.get_automation_logs(limit=50)
        self.cached_telemetry = api_client.get_automation_telemetry()

        # Update metric cards
        active_count = self.cached_telemetry.get("active_rules", len([r for r in self.cached_rules if r.get("is_active")]))
        total_rules = self.cached_telemetry.get("total_rules", len(self.cached_rules))
        self.card_active_rules.lbl_val.setText(str(active_count))
        self.card_active_rules.lbl_sub.setText(f"{total_rules} Total Configured")

        total_exec = self.cached_telemetry.get("total_executions", len(self.cached_logs))
        self.card_total_exec.lbl_val.setText(str(total_exec))

        success_rate = self.cached_telemetry.get("success_rate_percent", "100.00")
        self.card_success_rate.lbl_val.setText(f"{success_rate}%")

        actions_count = self.cached_telemetry.get("total_actions_triggered", 0)
        self.card_actions_triggered.lbl_val.setText(str(actions_count))

        # Repopulate tables
        self.apply_rules_filter()
        self.apply_logs_filter()
