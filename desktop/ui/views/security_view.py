"""Victory Crest One - Zero-Trust Security & Compliance Auditor View
Continuous compliance audit framework checks, real-time threat anomaly detection,
active quarantine sandbox containment, and credential entropy analytics.
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
    QDoubleSpinBox, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.core.session import session_manager
from desktop.services.api_client import api_client
from desktop.ui.components.status_badge import StatusBadge
from shared.enums import (
    ComplianceFramework,
    SecurityCheckStatus,
    SecurityThreatSeverity,
    SecurityEventType,
    SecurityRemediationAction,
)


class SecurityGovernanceView(QWidget):
    """Central Zero-Trust Security, Compliance Audit & Quarantine Governance Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_checks: List[Dict[str, Any]] = []
        self.cached_incidents: List[Dict[str, Any]] = []
        self.cached_quarantined: List[Dict[str, Any]] = []
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

        title = QLabel("Zero-Trust Security & Compliance Auditor")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Continuous automated compliance audits (SOC2, ISO 27001, GDPR, PCI-DSS v4.0), real-time threat sandbox & posture analytics.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_scan = QPushButton("⚡ Run Audit Scan")
        btn_scan.setProperty("class", "btn_secondary")
        btn_scan.clicked.connect(self.run_compliance_scan)

        btn_log_incident = QPushButton("🚨 Log Threat Event")
        btn_log_incident.setProperty("class", "btn_secondary")
        btn_log_incident.clicked.connect(self.open_log_incident_dialog)

        btn_quarantine = QPushButton("🛡️ Quarantine Entity")
        btn_quarantine.setProperty("class", "btn_primary")
        btn_quarantine.clicked.connect(self.open_quarantine_dialog)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_scan)
        header_row.addWidget(btn_log_incident)
        header_row.addWidget(btn_quarantine)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive KPI Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_posture = self.create_metric_card("ENTERPRISE POSTURE", "0.0%", "Grade: N/A", "#10B981")
        self.card_controls = self.create_metric_card("CONTROLS AUDITED", "0", "0 Passing", "#3B82F6")
        self.card_threats = self.create_metric_card("ACTIVE THREATS", "0", "0 Critical Threats", "#EF4444")
        self.card_quarantine = self.create_metric_card("QUARANTINED ACTORS", "0", "Sandboxed Containment", "#F59E0B")

        cards_row.addWidget(self.card_posture)
        cards_row.addWidget(self.card_controls)
        cards_row.addWidget(self.card_threats)
        cards_row.addWidget(self.card_quarantine)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Main Security Governance Tabs
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

        # Tab 1: Compliance Controls
        self.tab_compliance = QWidget()
        self.setup_compliance_tab()
        self.tab_widget.addTab(self.tab_compliance, "📜 Continuous Compliance Audit Checks")

        # Tab 2: Threat Log & Anomaly Stream
        self.tab_incidents = QWidget()
        self.setup_incidents_tab()
        self.tab_widget.addTab(self.tab_incidents, "🚨 Security Threat Log & Anomaly Stream")

        # Tab 3: Quarantine Sandbox & Verification
        self.tab_quarantine = QWidget()
        self.setup_quarantine_tab()
        self.tab_widget.addTab(self.tab_quarantine, "🛡️ Active Quarantine & Zero-Trust Sandbox")

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
    # TAB 1: CONTINUOUS COMPLIANCE AUDIT CHECKS
    # =========================================================================

    def setup_compliance_tab(self):
        layout = QVBoxLayout(self.tab_compliance)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filter bar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_fw = QLabel("Framework:")
        lbl_fw.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_fw_filter = QComboBox()
        self.combo_fw_filter.addItem("All Frameworks", None)
        for fw in ComplianceFramework:
            self.combo_fw_filter.addItem(fw.value, fw.value)
        self.combo_fw_filter.currentIndexChanged.connect(self.populate_compliance_table)

        lbl_st = QLabel("Status:")
        lbl_st.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_status_filter = QComboBox()
        self.combo_status_filter.addItem("All Statuses", None)
        for st in SecurityCheckStatus:
            self.combo_status_filter.addItem(st.value, st.value)
        self.combo_status_filter.currentIndexChanged.connect(self.populate_compliance_table)

        self.txt_check_search = QLineEdit()
        self.txt_check_search.setPlaceholderText("Search control code or title...")
        self.txt_check_search.textChanged.connect(self.populate_compliance_table)

        btn_run_scan = QPushButton("⚡ Scan Current Framework")
        btn_run_scan.setProperty("class", "btn_secondary")
        btn_run_scan.clicked.connect(self.run_compliance_scan)

        filter_row.addWidget(lbl_fw)
        filter_row.addWidget(self.combo_fw_filter)
        filter_row.addWidget(lbl_st)
        filter_row.addWidget(self.combo_status_filter)
        filter_row.addWidget(self.txt_check_search)
        filter_row.addWidget(btn_run_scan)
        layout.addLayout(filter_row)

        # Splitter: Table on top, Control Detail Viewer on bottom
        splitter = QSplitter(Qt.Vertical)

        self.table_checks = QTableWidget()
        self.table_checks.setColumnCount(6)
        self.table_checks.setHorizontalHeaderLabels([
            "Control Code", "Framework", "Control Title", "Category", "Status", "Last Scanned"
        ])
        self.table_checks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_checks.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_checks.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_checks.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_checks.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_checks.itemSelectionChanged.connect(self.on_check_selected)
        splitter.addWidget(self.table_checks)

        # Details Box
        detail_group = QGroupBox("Selected Compliance Control Detail & Remediation Guide")
        detail_group.setStyleSheet(f"QGroupBox {{ font-weight: 600; color: {ThemeColors.TEXT_MAIN}; }}")
        detail_layout = QVBoxLayout(detail_group)

        self.txt_check_details = QTextEdit()
        self.txt_check_details.setReadOnly(True)
        self.txt_check_details.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeColors.BG_BASE};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                font-family: monospace;
                font-size: 12px;
                border-radius: 4px;
            }}
        """)
        self.txt_check_details.setPlaceholderText("Select a compliance control row to view technical requirements and remediation procedures.")
        detail_layout.addWidget(self.txt_check_details)
        splitter.addWidget(detail_group)

        splitter.setSizes([320, 160])
        layout.addWidget(splitter)

    def populate_compliance_table(self):
        fw_filter = self.combo_fw_filter.currentData()
        st_filter = self.combo_status_filter.currentData()
        search_query = self.txt_check_search.text().strip().lower()

        filtered = []
        for chk in self.cached_checks:
            if fw_filter and chk.get("framework") != fw_filter:
                continue
            if st_filter and chk.get("status") != st_filter:
                continue
            if search_query:
                code = chk.get("control_code", "").lower()
                title = chk.get("title", "").lower()
                cat = chk.get("category", "").lower()
                if search_query not in code and search_query not in title and search_query not in cat:
                    continue
            filtered.append(chk)

        self.table_checks.setRowCount(len(filtered))
        for row, chk in enumerate(filtered):
            item_code = QTableWidgetItem(chk.get("control_code", ""))
            item_code.setData(Qt.UserRole, chk)
            item_fw = QTableWidgetItem(chk.get("framework", ""))
            item_title = QTableWidgetItem(chk.get("title", ""))
            item_cat = QTableWidgetItem(chk.get("category", ""))

            st_val = chk.get("status", "COMPLIANT")
            badge = StatusBadge(st_val)

            last_scan = str(chk.get("last_scanned_at") or "Just Now")[:19]
            item_scan = QTableWidgetItem(last_scan)

            self.table_checks.setItem(row, 0, item_code)
            self.table_checks.setItem(row, 1, item_fw)
            self.table_checks.setItem(row, 2, item_title)
            self.table_checks.setItem(row, 3, item_cat)
            self.table_checks.setCellWidget(row, 4, badge)
            self.table_checks.setItem(row, 5, item_scan)

    def on_check_selected(self):
        selected_items = self.table_checks.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        item_code = self.table_checks.item(row, 0)
        if not item_code:
            return
        chk = item_code.data(Qt.UserRole)
        if not chk:
            return

        detail_text = (
            f"Control Code: {chk.get('control_code')}\n"
            f"Title: {chk.get('title')}\n"
            f"Framework: {chk.get('framework')} | Category: {chk.get('category')}\n"
            f"Status: {chk.get('status')} | Automated: {chk.get('is_automated')}\n\n"
            f"--- Description ---\n{chk.get('description', 'N/A')}\n\n"
            f"--- Remediation Guide ---\n{chk.get('remediation_guide', 'N/A')}\n"
        )
        self.txt_check_details.setPlainText(detail_text)

    def run_compliance_scan(self):
        fw = self.combo_fw_filter.currentData()
        active_prop = session_manager.active_property
        prop_id = active_prop.get("id") if active_prop else None

        try:
            res = api_client.run_security_compliance_scan(framework=fw, property_id=prop_id)
            QMessageBox.information(
                self,
                "Compliance Scan Complete",
                f"Scanned {res.get('scanned_controls_count')} controls.\n"
                f"Overall Compliance: {res.get('overall_compliance_percent')}%\n"
                f"Posture Rating: {res.get('posture_rating')}"
            )
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Scan Error", f"Failed to execute compliance audit scan: {e}")

    # =========================================================================
    # TAB 2: SECURITY THREAT LOG & ANOMALY STREAM
    # =========================================================================

    def setup_incidents_tab(self):
        layout = QVBoxLayout(self.tab_incidents)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters Row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_sev = QLabel("Severity:")
        lbl_sev.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_inc_sev = QComboBox()
        self.combo_inc_sev.addItem("All Severities", None)
        for s in SecurityThreatSeverity:
            self.combo_inc_sev.addItem(s.value, s.value)
        self.combo_inc_sev.currentIndexChanged.connect(self.populate_incidents_table)

        lbl_st = QLabel("Status:")
        lbl_st.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_inc_status = QComboBox()
        self.combo_inc_status.addItem("All Incidents", None)
        self.combo_inc_status.addItem("INVESTIGATING", "INVESTIGATING")
        self.combo_inc_status.addItem("CONTAINED", "CONTAINED")
        self.combo_inc_status.addItem("RESOLVED", "RESOLVED")
        self.combo_inc_status.currentIndexChanged.connect(self.populate_incidents_table)

        self.txt_inc_search = QLineEdit()
        self.txt_inc_search.setPlaceholderText("Search threat event code, target or IP...")
        self.txt_inc_search.textChanged.connect(self.populate_incidents_table)

        btn_new_inc = QPushButton("🚨 Log Threat Event")
        btn_new_inc.setProperty("class", "btn_secondary")
        btn_new_inc.clicked.connect(self.open_log_incident_dialog)

        filter_row.addWidget(lbl_sev)
        filter_row.addWidget(self.combo_inc_sev)
        filter_row.addWidget(lbl_st)
        filter_row.addWidget(self.combo_inc_status)
        filter_row.addWidget(self.txt_inc_search)
        filter_row.addWidget(btn_new_inc)
        layout.addLayout(filter_row)

        # Incidents Table
        self.table_incidents = QTableWidget()
        self.table_incidents.setColumnCount(8)
        self.table_incidents.setHorizontalHeaderLabels([
            "Event Code", "Event Type", "Severity", "Risk Score", "Target Resource", "Actor / IP", "Status", "Action"
        ])
        self.table_incidents.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_incidents.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_incidents.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_incidents.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_incidents.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        layout.addWidget(self.table_incidents)

    def populate_incidents_table(self):
        sev_filter = self.combo_inc_sev.currentData()
        st_filter = self.combo_inc_status.currentData()
        search_query = self.txt_inc_search.text().strip().lower()

        filtered = []
        for inc in self.cached_incidents:
            if sev_filter and inc.get("severity") != sev_filter:
                continue
            if st_filter and inc.get("status") != st_filter:
                continue
            if search_query:
                code = inc.get("event_code", "").lower()
                target = inc.get("target_resource", "").lower()
                actor = (inc.get("actor_identity") or "").lower()
                ip = (inc.get("source_ip") or "").lower()
                if search_query not in code and search_query not in target and search_query not in actor and search_query not in ip:
                    continue
            filtered.append(inc)

        self.table_incidents.setRowCount(len(filtered))
        for row, inc in enumerate(filtered):
            item_code = QTableWidgetItem(inc.get("event_code", ""))
            item_type = QTableWidgetItem(inc.get("event_type", ""))

            sev_val = inc.get("severity", "HIGH")
            badge_sev = StatusBadge(sev_val)

            score_val = f"{float(inc.get('risk_score', 0)):.1f}"
            item_score = QTableWidgetItem(score_val)

            item_target = QTableWidgetItem(inc.get("target_resource", ""))

            actor_str = f"{inc.get('actor_identity') or 'N/A'} ({inc.get('source_ip') or 'N/A'})"
            item_actor = QTableWidgetItem(actor_str)

            st_val = inc.get("status", "INVESTIGATING")
            badge_st = StatusBadge(st_val)

            self.table_incidents.setItem(row, 0, item_code)
            self.table_incidents.setItem(row, 1, item_type)
            self.table_incidents.setCellWidget(row, 2, badge_sev)
            self.table_incidents.setItem(row, 3, item_score)
            self.table_incidents.setItem(row, 4, item_target)
            self.table_incidents.setItem(row, 5, item_actor)
            self.table_incidents.setCellWidget(row, 6, badge_st)

            # Action button
            if inc.get("is_resolved") or st_val == "RESOLVED":
                lbl_res = QLabel("✓ Resolved")
                lbl_res.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
                self.table_incidents.setCellWidget(row, 7, lbl_res)
            else:
                btn_resolve = QPushButton("Resolve")
                btn_resolve.setProperty("class", "btn_secondary")
                btn_resolve.clicked.connect(lambda _, inc_id=inc.get("id"): self.resolve_incident_action(inc_id))
                self.table_incidents.setCellWidget(row, 7, btn_resolve)

    def resolve_incident_action(self, incident_id: str):
        dialog = QDialog(self)
        dialog.setWindowTitle("Contain & Resolve Threat Incident")
        dialog.setMinimumWidth(400)
        d_layout = QFormLayout(dialog)

        txt_notes = QTextEdit()
        txt_notes.setPlaceholderText("Enter remediation actions taken and verification notes...")
        combo_action = QComboBox()
        for act in SecurityRemediationAction:
            combo_action.addItem(act.value, act.value)

        d_layout.addRow("Remediation Action:", combo_action)
        d_layout.addRow("Resolution Notes:", txt_notes)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Confirm Resolution")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            notes = txt_notes.toPlainText().strip()
            if not notes:
                QMessageBox.warning(dialog, "Input Required", "Please enter resolution notes.")
                return
            try:
                api_client.resolve_security_incident(
                    incident_id=incident_id,
                    resolution_notes=notes,
                    remediation_action=combo_action.currentData()
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to resolve incident: {e}")

        btn_submit.clicked.connect(submit)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_submit)
        d_layout.addRow(btn_box)
        dialog.exec()

    # =========================================================================
    # TAB 3: ACTIVE QUARANTINE SANDBOX & ZERO-TRUST TOOLS
    # =========================================================================

    def setup_quarantine_tab(self):
        layout = QVBoxLayout(self.tab_quarantine)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal)

        # Left: Active Quarantine Table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        left_hdr = QHBoxLayout()
        lbl_q_title = QLabel("Quarantined Entities & Containment History")
        lbl_q_title.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 14px;")
        btn_add_quar = QPushButton("➕ Quarantine Sandbox")
        btn_add_quar.setProperty("class", "btn_primary")
        btn_add_quar.clicked.connect(self.open_quarantine_dialog)

        left_hdr.addWidget(lbl_q_title)
        left_hdr.addStretch()
        left_hdr.addWidget(btn_add_quar)
        left_layout.addLayout(left_hdr)

        self.table_quarantine = QTableWidget()
        self.table_quarantine.setColumnCount(6)
        self.table_quarantine.setHorizontalHeaderLabels([
            "Entity ID / IP", "Type", "Reason", "Quarantined By", "Status", "Action"
        ])
        self.table_quarantine.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_quarantine.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_quarantine.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_quarantine.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_quarantine.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        left_layout.addWidget(self.table_quarantine)
        splitter.addWidget(left_widget)

        # Right: Zero-Trust Simulator & Entropy Tools
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(8, 0, 8, 8)
        right_layout.setSpacing(16)

        # 1. Threat Risk Evaluator
        group_threat = QGroupBox("⚡ Zero-Trust Threat Risk Simulator")
        group_threat.setStyleSheet(f"QGroupBox {{ font-weight: 600; color: {ThemeColors.TEXT_MAIN}; }}")
        f_threat = QFormLayout(group_threat)

        self.sim_sev = QComboBox()
        for s in SecurityThreatSeverity:
            self.sim_sev.addItem(s.value, s.value)
        self.sim_events = QSpinBox()
        self.sim_events.setRange(1, 100)
        self.sim_events.setValue(3)

        self.sim_fails = QSpinBox()
        self.sim_fails.setRange(0, 50)
        self.sim_fails.setValue(2)

        self.sim_priv = QCheckBox("Target Is Privileged Account")

        btn_eval_threat = QPushButton("Calculate Risk Score")
        btn_eval_threat.setProperty("class", "btn_secondary")
        btn_eval_threat.clicked.connect(self.calculate_simulated_threat)

        self.lbl_threat_res = QLabel("Risk Score: -- | Tier: -- | Action: --")
        self.lbl_threat_res.setStyleSheet(f"font-weight: 700; color: {ThemeColors.PRIMARY}; font-size: 13px;")

        f_threat.addRow("Threat Severity:", self.sim_sev)
        f_threat.addRow("Event Burst Count:", self.sim_events)
        f_threat.addRow("Failed Attempts:", self.sim_fails)
        f_threat.addRow("", self.sim_priv)
        f_threat.addRow(btn_eval_threat, self.lbl_threat_res)
        right_layout.addWidget(group_threat)

        # 2. Credential Entropy Evaluator
        group_entropy = QGroupBox("🔑 Shannon Credential Entropy Calculator")
        group_entropy.setStyleSheet(f"QGroupBox {{ font-weight: 600; color: {ThemeColors.TEXT_MAIN}; }}")
        f_entropy = QFormLayout(group_entropy)

        self.ent_len = QSpinBox()
        self.ent_len.setRange(6, 64)
        self.ent_len.setValue(16)

        self.ent_symbols = QCheckBox("Include Special Symbols (!@#$)")
        self.ent_symbols.setChecked(True)
        self.ent_numbers = QCheckBox("Include Numbers (0-9)")
        self.ent_numbers.setChecked(True)
        self.ent_mixed = QCheckBox("Include Mixed Case (A-Z, a-z)")
        self.ent_mixed.setChecked(True)

        btn_eval_entropy = QPushButton("Evaluate Entropy")
        btn_eval_entropy.setProperty("class", "btn_secondary")
        btn_eval_entropy.clicked.connect(self.calculate_simulated_entropy)

        self.lbl_entropy_res = QLabel("Entropy: -- bits | Rating: -- | Zero-Trust Compliant: --")
        self.lbl_entropy_res.setStyleSheet(f"font-weight: 700; color: {ThemeColors.PRIMARY}; font-size: 13px;")

        f_entropy.addRow("Password Length:", self.ent_len)
        f_entropy.addRow("", self.ent_symbols)
        f_entropy.addRow("", self.ent_numbers)
        f_entropy.addRow("", self.ent_mixed)
        f_entropy.addRow(btn_eval_entropy, self.lbl_entropy_res)
        right_layout.addWidget(group_entropy)

        right_layout.addStretch()
        right_scroll.setWidget(right_container)
        splitter.addWidget(right_scroll)

        splitter.setSizes([550, 400])
        layout.addWidget(splitter)

    def populate_quarantine_table(self):
        self.table_quarantine.setRowCount(len(self.cached_quarantined))
        for row, q in enumerate(self.cached_quarantined):
            item_id = QTableWidgetItem(q.get("entity_id_or_ip", ""))
            item_type = QTableWidgetItem(q.get("entity_type", ""))
            item_reason = QTableWidgetItem(q.get("reason", ""))
            item_by = QTableWidgetItem(q.get("quarantined_by", ""))

            st_val = q.get("status", "ACTIVE")
            badge = StatusBadge(st_val)

            self.table_quarantine.setItem(row, 0, item_id)
            self.table_quarantine.setItem(row, 1, item_type)
            self.table_quarantine.setItem(row, 2, item_reason)
            self.table_quarantine.setItem(row, 3, item_by)
            self.table_quarantine.setCellWidget(row, 4, badge)

            if q.get("is_active") and st_val != "RELEASED":
                btn_rel = QPushButton("🔓 Release")
                btn_rel.setProperty("class", "btn_secondary")
                btn_rel.clicked.connect(lambda _, q_id=q.get("id"): self.release_quarantine_action(q_id))
                self.table_quarantine.setCellWidget(row, 5, btn_rel)
            else:
                lbl_rel = QLabel("Released")
                lbl_rel.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
                self.table_quarantine.setCellWidget(row, 5, lbl_rel)

    def release_quarantine_action(self, quarantine_id: str):
        reply = QMessageBox.question(
            self,
            "Confirm Release",
            "Are you sure you want to release this entity from zero-trust quarantine isolation?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                api_client.release_quarantined_entity(quarantine_id)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to release quarantine: {e}")

    def calculate_simulated_threat(self):
        try:
            res = api_client.evaluate_threat(
                severity=self.sim_sev.currentData(),
                event_count=self.sim_events.value(),
                failed_attempts=self.sim_fails.value(),
                is_privileged=self.sim_priv.isChecked()
            )
            self.lbl_threat_res.setText(
                f"Risk: {float(res.get('risk_score', 0)):.1f} | Tier: {res.get('risk_tier')} | Action: {res.get('recommended_action')}"
            )
        except Exception as e:
            self.lbl_threat_res.setText(f"Error: {e}")

    def calculate_simulated_entropy(self):
        try:
            res = api_client.evaluate_credential_entropy(
                length=self.ent_len.value(),
                has_symbols=self.ent_symbols.isChecked(),
                has_numbers=self.ent_numbers.isChecked(),
                has_mixed_case=self.ent_mixed.isChecked()
            )
            compliant_str = "YES (Zero-Trust)" if res.get("is_zero_trust_compliant") else "NO (Deficient)"
            self.lbl_entropy_res.setText(
                f"Entropy: {res.get('entropy_bits')} bits | Strength: {res.get('strength_rating')} | Compliant: {compliant_str}"
            )
        except Exception as e:
            self.lbl_entropy_res.setText(f"Error: {e}")

    # =========================================================================
    # DIALOGS & CREATION
    # =========================================================================

    def open_log_incident_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Ingest Security Threat Incident")
        dialog.setMinimumWidth(450)
        d_layout = QFormLayout(dialog)

        txt_code = QLineEdit()
        txt_code.setText(f"SEC-2026-MAN-{len(self.cached_incidents) + 1:03d}")

        combo_type = QComboBox()
        for t in SecurityEventType:
            combo_type.addItem(t.value, t.value)

        combo_sev = QComboBox()
        for s in SecurityThreatSeverity:
            combo_sev.addItem(s.value, s.value)

        txt_source_ip = QLineEdit()
        txt_source_ip.setPlaceholderText("198.51.100.44")

        txt_actor = QLineEdit()
        txt_actor.setPlaceholderText("external_probe_bot")

        txt_target = QLineEdit()
        txt_target.setText("/api/v1/finance/ledgers")

        txt_details = QTextEdit()
        txt_details.setPlaceholderText("Describe anomaly indicators or SIEM log excerpt...")

        combo_action = QComboBox()
        for act in SecurityRemediationAction:
            combo_action.addItem(act.value, act.value)

        d_layout.addRow("Event Code:", txt_code)
        d_layout.addRow("Threat Classification:", combo_type)
        d_layout.addRow("Severity Tier:", combo_sev)
        d_layout.addRow("Source IP Address:", txt_source_ip)
        d_layout.addRow("Actor Identity:", txt_actor)
        d_layout.addRow("Target Resource:", txt_target)
        d_layout.addRow("Technical Details:", txt_details)
        d_layout.addRow("Recommended Action:", combo_action)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Log Incident")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            code = txt_code.text().strip()
            target = txt_target.text().strip()
            if not code or not target:
                QMessageBox.warning(dialog, "Input Required", "Event code and target resource are required.")
                return

            active_prop = session_manager.active_property
            prop_id = active_prop.get("id") if active_prop else None

            payload = {
                "event_code": code,
                "event_type": combo_type.currentData(),
                "severity": combo_sev.currentData(),
                "source_ip": txt_source_ip.text().strip() or None,
                "actor_identity": txt_actor.text().strip() or None,
                "target_resource": target,
                "details": txt_details.toPlainText().strip() or None,
                "recommended_action": combo_action.currentData(),
                "property_id": prop_id
            }

            try:
                api_client.create_security_incident(payload)
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to record incident: {e}")

        btn_submit.clicked.connect(submit)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_submit)
        d_layout.addRow(btn_box)
        dialog.exec()

    def open_quarantine_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Quarantine Sandbox Containment")
        dialog.setMinimumWidth(420)
        d_layout = QFormLayout(dialog)

        txt_entity = QLineEdit()
        txt_entity.setPlaceholderText("IP address, username, or token")

        combo_type = QComboBox()
        combo_type.addItem("IP_ADDRESS", "IP_ADDRESS")
        combo_type.addItem("USER_ACCOUNT", "USER_ACCOUNT")
        combo_type.addItem("API_KEY", "API_KEY")
        combo_type.addItem("DEVICE_MAC", "DEVICE_MAC")

        txt_reason = QTextEdit()
        txt_reason.setPlaceholderText("State rationale for zero-trust quarantine isolation...")

        d_layout.addRow("Target Entity / IP:", txt_entity)
        d_layout.addRow("Entity Classification:", combo_type)
        d_layout.addRow("Isolation Reason:", txt_reason)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Apply Quarantine")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            target = txt_entity.text().strip()
            reason = txt_reason.toPlainText().strip()
            if not target or not reason:
                QMessageBox.warning(dialog, "Input Required", "Target entity and reason are required.")
                return
            try:
                api_client.quarantine_entity(
                    entity_id_or_ip=target,
                    reason=reason,
                    entity_type=combo_type.currentData()
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to quarantine entity: {e}")

        btn_submit.clicked.connect(submit)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_submit)
        d_layout.addRow(btn_box)
        dialog.exec()

    # =========================================================================
    # REFRESH & STATE SYNCHRONIZATION
    # =========================================================================

    def refresh_data(self):
        """Fetch latest security compliance controls, threats, quarantine, and metrics."""
        active_prop = session_manager.active_property
        prop_id = active_prop.get("id") if active_prop else None

        try:
            self.cached_checks = api_client.get_security_compliance_checks(property_id=prop_id)
        except Exception:
            self.cached_checks = []

        try:
            self.cached_incidents = api_client.get_security_incidents(property_id=prop_id)
        except Exception:
            self.cached_incidents = []

        try:
            self.cached_quarantined = api_client.get_quarantined_entities()
        except Exception:
            self.cached_quarantined = []

        try:
            self.cached_metrics = api_client.get_security_metrics(property_id=prop_id)
        except Exception:
            self.cached_metrics = {}

        # Update metric cards
        score = self.cached_metrics.get("enterprise_posture_score", "0.0")
        grade = self.cached_metrics.get("posture_grade", "N/A")
        self.update_card(self.card_posture, f"{float(score):.1f}%", f"Grade: {grade}")

        total_ctrl = self.cached_metrics.get("total_controls_audited", len(self.cached_checks))
        fail_ctrl = self.cached_metrics.get("failing_controls_count", 0)
        passing_ctrl = total_ctrl - fail_ctrl
        self.update_card(self.card_controls, f"{passing_ctrl} / {total_ctrl}", f"{fail_ctrl} Deficiencies Found")

        open_inc = self.cached_metrics.get("open_incidents_count", 0)
        crit_inc = self.cached_metrics.get("critical_threats_count", 0)
        self.update_card(self.card_threats, f"{open_inc} Active", f"{crit_inc} Critical Threats")

        quar_cnt = self.cached_metrics.get("quarantined_actors_count", len([q for q in self.cached_quarantined if q.get("is_active")]))
        self.update_card(self.card_quarantine, f"{quar_cnt} Isolated", "Zero-Trust Active Sandbox")

        # Repopulate tables
        self.populate_compliance_table()
        self.populate_incidents_table()
        self.populate_quarantine_table()

    def update_card(self, card: QFrame, val: str, sub: str):
        layout = card.layout()
        if layout and layout.count() >= 3:
            lbl_val = layout.itemAt(1).widget()
            lbl_sub = layout.itemAt(2).widget()
            if isinstance(lbl_val, QLabel):
                lbl_val.setText(val)
            if isinstance(lbl_sub, QLabel):
                lbl_sub.setText(sub)
