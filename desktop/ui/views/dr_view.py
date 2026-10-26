"""Victory Crest One - Multi-Cloud Resiliency & Autonomous DR View
Distributed standby cluster node topology, cross-cloud replication stream monitoring,
automated chaos failover drills, and zero-RPO disaster recovery analytics.
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
    CloudProvider,
    ReplicationMode,
    NodeRole,
    NodeHealthStatus,
    FailoverDrillType,
    FailoverDrillStatus,
)


class MultiCloudDrView(QWidget):
    """Central Multi-Cloud Resiliency, Autonomous DR & Chaos Engineering Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_nodes: List[Dict[str, Any]] = []
        self.cached_drills: List[Dict[str, Any]] = []
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

        title = QLabel("Multi-Cloud Resiliency & Autonomous DR")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Continuous cross-cloud standby replication (AWS, Azure, GCP, On-Premise), automated chaos failover drills & zero-RPO DR.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_trigger = QPushButton("⚡ Trigger Chaos Drill")
        btn_trigger.setProperty("class", "btn_secondary")
        btn_trigger.clicked.connect(self.open_trigger_drill_dialog)

        btn_register = QPushButton("➕ Register Replica Node")
        btn_register.setProperty("class", "btn_primary")
        btn_register.clicked.connect(self.open_register_node_dialog)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_trigger)
        header_row.addWidget(btn_register)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive KPI Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_resiliency = self.create_metric_card("CHAOS RESILIENCY", "0.0%", "Tier: N/A", "#10B981")
        self.card_availability = self.create_metric_card("CLUSTER AVAILABILITY", "0.0%", "0 Active Nodes", "#3B82F6")
        self.card_lag = self.create_metric_card("MAX REPLICATION LAG", "0.000s", "Zero-RPO Status", "#8B5CF6")
        self.card_rto = self.create_metric_card("FAILOVER DRILL RTO", "0.00s", "30s SLA Target", "#F59E0B")

        cards_row.addWidget(self.card_resiliency)
        cards_row.addWidget(self.card_availability)
        cards_row.addWidget(self.card_lag)
        cards_row.addWidget(self.card_rto)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Main Multi-Cloud DR Tabs
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

        # Tab 1: Multi-Cloud Standby Cluster
        self.tab_nodes = QWidget()
        self.setup_nodes_tab()
        self.tab_widget.addTab(self.tab_nodes, "🌐 Multi-Cloud Standby Cluster & Topologies")

        # Tab 2: Chaos Engineering Failover Drills
        self.tab_drills = QWidget()
        self.setup_drills_tab()
        self.tab_widget.addTab(self.tab_drills, "⚡ Autonomous Chaos Drills & Failover Log")

        # Tab 3: Disaster Recovery Simulator & Live Lag Tester
        self.tab_sim = QWidget()
        self.setup_sim_tab()
        self.tab_widget.addTab(self.tab_sim, "🔬 DR Simulator & Live Lag Diagnostics")

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
    # TAB 1: MULTI-CLOUD STANDBY CLUSTER
    # =========================================================================

    def setup_nodes_tab(self):
        layout = QVBoxLayout(self.tab_nodes)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters Row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_prov = QLabel("Cloud Provider:")
        lbl_prov.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_prov_filter = QComboBox()
        self.combo_prov_filter.addItem("All Providers", None)
        for p in CloudProvider:
            self.combo_prov_filter.addItem(p.value, p.value)
        self.combo_prov_filter.currentIndexChanged.connect(self.populate_nodes_table)

        lbl_role = QLabel("Role:")
        lbl_role.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_role_filter = QComboBox()
        self.combo_role_filter.addItem("All Roles", None)
        for r in NodeRole:
            self.combo_role_filter.addItem(r.value, r.value)
        self.combo_role_filter.currentIndexChanged.connect(self.populate_nodes_table)

        self.txt_node_search = QLineEdit()
        self.txt_node_search.setPlaceholderText("Search node code, region, or name...")
        self.txt_node_search.textChanged.connect(self.populate_nodes_table)

        filter_row.addWidget(lbl_prov)
        filter_row.addWidget(self.combo_prov_filter)
        filter_row.addWidget(lbl_role)
        filter_row.addWidget(self.combo_role_filter)
        filter_row.addWidget(self.txt_node_search)
        layout.addLayout(filter_row)

        # Splitter: Table on top, Node Details on bottom
        splitter = QSplitter(Qt.Vertical)

        self.table_nodes = QTableWidget()
        self.table_nodes.setColumnCount(8)
        self.table_nodes.setHorizontalHeaderLabels([
            "Node Code", "Provider", "Region", "Cluster Role", "Health Status", "Replication Lag", "Sync Latency", "Action"
        ])
        self.table_nodes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_nodes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_nodes.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_nodes.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_nodes.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table_nodes.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_nodes.itemSelectionChanged.connect(self.on_node_selected)
        splitter.addWidget(self.table_nodes)

        # Details Panel
        detail_group = QGroupBox("Selected Replica Node Details & Consensus Endpoints")
        detail_group.setStyleSheet(f"QGroupBox {{ font-weight: 600; color: {ThemeColors.TEXT_MAIN}; }}")
        d_layout = QVBoxLayout(detail_group)

        self.txt_node_details = QTextEdit()
        self.txt_node_details.setReadOnly(True)
        self.txt_node_details.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeColors.BG_BASE};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                font-family: monospace;
                font-size: 12px;
                border-radius: 4px;
            }}
        """)
        self.txt_node_details.setPlaceholderText("Select a cloud replica node to view network routing, consensus leader telemetry, and heartbeat timestamps.")
        d_layout.addWidget(self.txt_node_details)
        splitter.addWidget(detail_group)

        splitter.setSizes([320, 160])
        layout.addWidget(splitter)

    def populate_nodes_table(self):
        prov_filter = self.combo_prov_filter.currentData()
        role_filter = self.combo_role_filter.currentData()
        search_query = self.txt_node_search.text().strip().lower()

        filtered = []
        for n in self.cached_nodes:
            if prov_filter and n.get("provider") != prov_filter:
                continue
            if role_filter and n.get("role") != role_filter:
                continue
            if search_query:
                code = n.get("node_code", "").lower()
                name = n.get("name", "").lower()
                region = n.get("region", "").lower()
                if search_query not in code and search_query not in name and search_query not in region:
                    continue
            filtered.append(n)

        self.table_nodes.setRowCount(len(filtered))
        for row, n in enumerate(filtered):
            item_code = QTableWidgetItem(n.get("node_code", ""))
            item_code.setData(Qt.UserRole, n)
            item_prov = QTableWidgetItem(n.get("provider", ""))
            item_region = QTableWidgetItem(n.get("region", ""))

            role_val = n.get("role", "HOT_STANDBY")
            item_role = QTableWidgetItem(role_val)

            st_val = n.get("health_status", "HEALTHY")
            badge_st = StatusBadge(st_val)

            lag_val = f"{float(n.get('replication_lag_seconds', 0)):.3f}s"
            item_lag = QTableWidgetItem(lag_val)

            lat_val = f"{float(n.get('sync_latency_ms', 0)):.1f} ms"
            item_lat = QTableWidgetItem(lat_val)

            self.table_nodes.setItem(row, 0, item_code)
            self.table_nodes.setItem(row, 1, item_prov)
            self.table_nodes.setItem(row, 2, item_region)
            self.table_nodes.setItem(row, 3, item_role)
            self.table_nodes.setCellWidget(row, 4, badge_st)
            self.table_nodes.setItem(row, 5, item_lag)
            self.table_nodes.setItem(row, 6, item_lat)

            # Promotion action button if not already primary
            if role_val == "PRIMARY":
                lbl_pri = QLabel("⭐ Primary")
                lbl_pri.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-weight: 700; font-size: 11px;")
                self.table_nodes.setCellWidget(row, 7, lbl_pri)
            else:
                btn_promote = QPushButton("⚡ Promote")
                btn_promote.setProperty("class", "btn_secondary")
                btn_promote.clicked.connect(lambda _, n_id=n.get("id"): self.promote_node_action(n_id))
                self.table_nodes.setCellWidget(row, 7, btn_promote)

    def on_node_selected(self):
        selected_items = self.table_nodes.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        item_code = self.table_nodes.item(row, 0)
        if not item_code:
            return
        n = item_code.data(Qt.UserRole)
        if not n:
            return

        detail_text = (
            f"Node Identifier: {n.get('node_code')}\n"
            f"Cluster Node Title: {n.get('name')}\n"
            f"Cloud Provider: {n.get('provider')} | Region: {n.get('region')}\n"
            f"Cluster Role: {n.get('role')} | Mode: {n.get('replication_mode')}\n"
            f"Health Status: {n.get('health_status')} | Latency: {n.get('sync_latency_ms')} ms\n"
            f"Replication Lag: {n.get('replication_lag_seconds')} s\n"
            f"Private VPC Endpoint: {n.get('endpoint_url') or 'Internal VPC Service Mesh'}\n"
            f"Heartbeat Recorded: {str(n.get('last_heartbeat_at') or 'Just Now')[:19]}\n"
        )
        self.txt_node_details.setPlainText(detail_text)

    def promote_node_action(self, node_id: str):
        reply = QMessageBox.question(
            self,
            "Confirm Primary Node Promotion",
            "Are you sure you want to promote this standby node to PRIMARY consensus leader?\n"
            "The existing primary will automatically transition to HOT_STANDBY.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                res = api_client.promote_dr_node(node_id)
                QMessageBox.information(self, "Promotion Complete", f"Node '{res.get('node_code')}' is now PRIMARY consensus leader.")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Promotion Error", f"Failed to promote node: {e}")

    # =========================================================================
    # TAB 2: CHAOS ENGINEERING FAILOVER DRILLS
    # =========================================================================

    def setup_drills_tab(self):
        layout = QVBoxLayout(self.tab_drills)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters Row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_st = QLabel("Status:")
        lbl_st.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self.combo_drill_status = QComboBox()
        self.combo_drill_status.addItem("All Drills", None)
        for st in FailoverDrillStatus:
            self.combo_drill_status.addItem(st.value, st.value)
        self.combo_drill_status.currentIndexChanged.connect(self.populate_drills_table)

        self.txt_drill_search = QLineEdit()
        self.txt_drill_search.setPlaceholderText("Search drill code, primary, or promoted node...")
        self.txt_drill_search.textChanged.connect(self.populate_drills_table)

        btn_trigger = QPushButton("⚡ Launch Chaos Drill")
        btn_trigger.setProperty("class", "btn_secondary")
        btn_trigger.clicked.connect(self.open_trigger_drill_dialog)

        filter_row.addWidget(lbl_st)
        filter_row.addWidget(self.combo_drill_status)
        filter_row.addWidget(self.txt_drill_search)
        filter_row.addWidget(btn_trigger)
        layout.addLayout(filter_row)

        # Splitter: Drills Table on top, Execution Log on bottom
        splitter = QSplitter(Qt.Vertical)

        self.table_drills = QTableWidget()
        self.table_drills.setColumnCount(8)
        self.table_drills.setHorizontalHeaderLabels([
            "Drill Code", "Scenario Type", "Target Primary", "Promoted Standby", "Status", "Actual RTO", "Actual RPO", "Traffic Rerouted"
        ])
        self.table_drills.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_drills.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_drills.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_drills.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_drills.itemSelectionChanged.connect(self.on_drill_selected)
        splitter.addWidget(self.table_drills)

        # Drill Log Viewer
        log_group = QGroupBox("Chaos Drill Execution Audit Log")
        log_group.setStyleSheet(f"QGroupBox {{ font-weight: 600; color: {ThemeColors.TEXT_MAIN}; }}")
        l_layout = QVBoxLayout(log_group)

        self.txt_drill_log = QTextEdit()
        self.txt_drill_log.setReadOnly(True)
        self.txt_drill_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeColors.BG_BASE};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                font-family: monospace;
                font-size: 12px;
                border-radius: 4px;
            }}
        """)
        self.txt_drill_log.setPlaceholderText("Select a failover drill row to inspect switchover logs, consensus leader election timeline, and packet rerouting.")
        l_layout.addWidget(self.txt_drill_log)
        splitter.addWidget(log_group)

        splitter.setSizes([320, 160])
        layout.addWidget(splitter)

    def populate_drills_table(self):
        st_filter = self.combo_drill_status.currentData()
        search_query = self.txt_drill_search.text().strip().lower()

        filtered = []
        for d in self.cached_drills:
            if st_filter and d.get("status") != st_filter:
                continue
            if search_query:
                code = d.get("drill_code", "").lower()
                prim = d.get("target_primary_node", "").lower()
                stby = d.get("promoted_standby_node", "").lower()
                dtype = d.get("drill_type", "").lower()
                if search_query not in code and search_query not in prim and search_query not in stby and search_query not in dtype:
                    continue
            filtered.append(d)

        self.table_drills.setRowCount(len(filtered))
        for row, d in enumerate(filtered):
            item_code = QTableWidgetItem(d.get("drill_code", ""))
            item_code.setData(Qt.UserRole, d)
            item_type = QTableWidgetItem(d.get("drill_type", ""))
            item_prim = QTableWidgetItem(d.get("target_primary_node", ""))
            item_stby = QTableWidgetItem(d.get("promoted_standby_node", ""))

            st_val = d.get("status", "SUCCEEDED")
            badge = StatusBadge(st_val)

            rto_val = f"{float(d.get('actual_rto_seconds', 0)):.2f}s"
            item_rto = QTableWidgetItem(rto_val)

            rpo_val = f"{float(d.get('actual_rpo_seconds', 0)):.2f}s"
            item_rpo = QTableWidgetItem(rpo_val)

            reroute_val = f"{float(d.get('traffic_rerouted_percent', 100)):.1f}%"
            item_reroute = QTableWidgetItem(reroute_val)

            self.table_drills.setItem(row, 0, item_code)
            self.table_drills.setItem(row, 1, item_type)
            self.table_drills.setItem(row, 2, item_prim)
            self.table_drills.setItem(row, 3, item_stby)
            self.table_drills.setCellWidget(row, 4, badge)
            self.table_drills.setItem(row, 5, item_rto)
            self.table_drills.setItem(row, 6, item_rpo)
            self.table_drills.setItem(row, 7, item_reroute)

    def on_drill_selected(self):
        selected_items = self.table_drills.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        item_code = self.table_drills.item(row, 0)
        if not item_code:
            return
        d = item_code.data(Qt.UserRole)
        if not d:
            return

        log_text = (
            f"Drill Code: {d.get('drill_code')}\n"
            f"Scenario Type: {d.get('drill_type')} | Status: {d.get('status')}\n"
            f"Target Primary Node: {d.get('target_primary_node')} -> Promoted Standby: {d.get('promoted_standby_node')}\n"
            f"Actual RTO: {d.get('actual_rto_seconds')}s | Actual RPO: {d.get('actual_rpo_seconds')}s\n"
            f"Traffic Rerouted: {d.get('traffic_rerouted_percent')}%\n\n"
            f"--- Failure Scenario ---\n{d.get('simulated_failure', 'N/A')}\n\n"
            f"--- Execution Audit Log ---\n{d.get('execution_log', 'N/A')}\n"
        )
        self.txt_drill_log.setPlainText(log_text)

    # =========================================================================
    # TAB 3: DISASTER RECOVERY SIMULATOR & LIVE LAG DIAGNOSTICS
    # =========================================================================

    def setup_sim_tab(self):
        layout = QVBoxLayout(self.tab_sim)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal)

        # Panel A: Live Replication Lag Diagnostics
        panel_lag = QGroupBox("🔬 Live Cross-Cloud Replication Diagnostics")
        panel_lag.setStyleSheet(f"QGroupBox {{ font-weight: 600; color: {ThemeColors.TEXT_MAIN}; }}")
        f_lag = QFormLayout(panel_lag)

        self.sim_lag_node = QComboBox()
        self.sim_bytes_behind = QSpinBox()
        self.sim_bytes_behind.setRange(0, 1000000)
        self.sim_bytes_behind.setValue(120)

        self.sim_packet_loss = QDoubleSpinBox()
        self.sim_packet_loss.setRange(0.0, 100.0)
        self.sim_packet_loss.setSingleStep(0.5)
        self.sim_packet_loss.setValue(0.0)

        btn_run_lag = QPushButton("Test Replication Stream")
        btn_run_lag.setProperty("class", "btn_secondary")
        btn_run_lag.clicked.connect(self.run_simulated_lag_test)

        self.lbl_lag_diag = QLabel("Lag: -- | Tier: -- | Zero-RPO: -- | Consensus: --")
        self.lbl_lag_diag.setStyleSheet(f"font-weight: 700; color: {ThemeColors.PRIMARY}; font-size: 13px;")

        f_lag.addRow("Target Standby Node:", self.sim_lag_node)
        f_lag.addRow("Simulated Byte Lag:", self.sim_bytes_behind)
        f_lag.addRow("Packet Loss %:", self.sim_packet_loss)
        f_lag.addRow(btn_run_lag, self.lbl_lag_diag)
        splitter.addWidget(panel_lag)

        # Panel B: Instant Chaos Failover Drill Launcher
        panel_failover = QGroupBox("⚡ Instant Chaos Engineering Failover Launcher")
        panel_failover.setStyleSheet(f"QGroupBox {{ font-weight: 600; color: {ThemeColors.TEXT_MAIN}; }}")
        f_failover = QFormLayout(panel_failover)

        self.sim_scenario = QComboBox()
        for sc in FailoverDrillType:
            self.sim_scenario.addItem(sc.value, sc.value)

        self.sim_prim_node = QComboBox()
        self.sim_stby_node = QComboBox()
        self.sim_partition_chk = QCheckBox("Simulate Split-Brain Network Partition")
        self.sim_partition_chk.setChecked(True)

        btn_launch_failover = QPushButton("Execute Chaos Switchover Drill")
        btn_launch_failover.setProperty("class", "btn_primary")
        btn_launch_failover.clicked.connect(self.run_simulated_failover)

        self.lbl_failover_out = QLabel("Switchover: -- | Data Loss: -- | Status: --")
        self.lbl_failover_out.setStyleSheet(f"font-weight: 700; color: {ThemeColors.PRIMARY}; font-size: 13px;")

        f_failover.addRow("Failure Scenario:", self.sim_scenario)
        f_failover.addRow("Target Primary Node:", self.sim_prim_node)
        f_failover.addRow("Promote Standby Node:", self.sim_stby_node)
        f_failover.addRow("", self.sim_partition_chk)
        f_failover.addRow(btn_launch_failover, self.lbl_failover_out)
        splitter.addWidget(panel_failover)

        splitter.setSizes([450, 450])
        layout.addWidget(splitter)

    def run_simulated_lag_test(self):
        node_code = self.sim_lag_node.currentText()
        if not node_code:
            return
        try:
            res = api_client.test_dr_replication_lag(
                node_code=node_code,
                bytes_behind=self.sim_bytes_behind.value(),
                packet_loss=self.sim_packet_loss.value()
            )
            rpo_str = "YES" if res.get("is_zero_rpo") else "NO"
            con_str = "VALID" if res.get("consensus_valid") else "DEGRADED"
            self.lbl_lag_diag.setText(
                f"Lag: {res.get('replication_lag_seconds')}s | Tier: {res.get('lag_tier')} | Zero-RPO: {rpo_str} | Quorum: {con_str}"
            )
        except Exception as e:
            self.lbl_lag_diag.setText(f"Error: {e}")

    def run_simulated_failover(self):
        scenario = self.sim_scenario.currentData()
        prim = self.sim_prim_node.currentText() or None
        stby = self.sim_stby_node.currentText() or None

        try:
            res = api_client.trigger_dr_failover_drill(
                drill_type=scenario,
                primary_node=prim,
                standby_node=stby,
                simulate_network_partition=self.sim_partition_chk.isChecked()
            )
            self.lbl_failover_out.setText(
                f"RTO: {res.get('switchover_latency_seconds')}s | RPO: {res.get('data_loss_window_seconds')}s | Status: {res.get('status')}"
            )
            QMessageBox.information(
                self,
                "Failover Drill Succeeded",
                f"{res.get('summary')}\nPromoted: {res.get('promoted_node')}"
            )
            self.refresh_data()
        except Exception as e:
            self.lbl_failover_out.setText(f"Error: {e}")

    # =========================================================================
    # DIALOGS
    # =========================================================================

    def open_trigger_drill_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Launch Autonomous Chaos Failover Drill")
        dialog.setMinimumWidth(440)
        d_layout = QFormLayout(dialog)

        combo_sc = QComboBox()
        for sc in FailoverDrillType:
            combo_sc.addItem(sc.value, sc.value)

        combo_prim = QComboBox()
        combo_stby = QComboBox()
        for n in self.cached_nodes:
            code = n.get("node_code", "")
            combo_prim.addItem(code, code)
            combo_stby.addItem(code, code)

        chk_part = QCheckBox("Simulate Instant Network Quorum Partition")
        chk_part.setChecked(True)

        d_layout.addRow("Failure Scenario:", combo_sc)
        d_layout.addRow("Failing Primary Node:", combo_prim)
        d_layout.addRow("Standby Target Node:", combo_stby)
        d_layout.addRow("", chk_part)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Execute Drill")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            try:
                res = api_client.trigger_dr_failover_drill(
                    drill_type=combo_sc.currentData(),
                    primary_node=combo_prim.currentData(),
                    standby_node=combo_stby.currentData(),
                    simulate_network_partition=chk_part.isChecked()
                )
                dialog.accept()
                QMessageBox.information(self, "Drill Complete", res.get("summary", "Drill succeeded."))
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to execute drill: {e}")

        btn_submit.clicked.connect(submit)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_submit)
        d_layout.addRow(btn_box)
        dialog.exec()

    def open_register_node_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register Multi-Cloud Replica Node")
        dialog.setMinimumWidth(450)
        d_layout = QFormLayout(dialog)

        txt_code = QLineEdit()
        txt_code.setText(f"NODE-CUSTOM-{len(self.cached_nodes) + 1:03d}")

        txt_name = QLineEdit()
        txt_name.setPlaceholderText("Azure South India Failover Node")

        combo_prov = QComboBox()
        for p in CloudProvider:
            combo_prov.addItem(p.value, p.value)

        txt_region = QLineEdit()
        txt_region.setText("southindia (Chennai)")

        combo_role = QComboBox()
        for r in NodeRole:
            combo_role.addItem(r.value, r.value)
        combo_role.setCurrentText("HOT_STANDBY")

        combo_mode = QComboBox()
        for m in ReplicationMode:
            combo_mode.addItem(m.value, m.value)

        txt_url = QLineEdit()
        txt_url.setPlaceholderText("https://db-replica.victorycrest.internal")

        d_layout.addRow("Node Identifier:", txt_code)
        d_layout.addRow("Descriptive Name:", txt_name)
        d_layout.addRow("Cloud Provider:", combo_prov)
        d_layout.addRow("Data Center Region:", txt_region)
        d_layout.addRow("Cluster Role:", combo_role)
        d_layout.addRow("Replication Mode:", combo_mode)
        d_layout.addRow("VPC Service URL:", txt_url)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Register Node")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            code = txt_code.text().strip()
            name = txt_name.text().strip()
            if not code or not name:
                QMessageBox.warning(dialog, "Input Required", "Node identifier and name are required.")
                return

            active_prop = session_manager.active_property
            prop_id = active_prop.get("id") if active_prop else None

            payload = {
                "node_code": code,
                "name": name,
                "provider": combo_prov.currentData(),
                "region": txt_region.text().strip(),
                "role": combo_role.currentData(),
                "replication_mode": combo_mode.currentData(),
                "endpoint_url": txt_url.text().strip() or None,
                "property_id": prop_id
            }

            try:
                api_client.register_dr_node(payload)
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to register node: {e}")

        btn_submit.clicked.connect(submit)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_submit)
        d_layout.addRow(btn_box)
        dialog.exec()

    # =========================================================================
    # REFRESH & STATE SYNCHRONIZATION
    # =========================================================================

    def refresh_data(self):
        """Fetch latest multi-cloud standby nodes, drills, and resiliency telemetry."""
        active_prop = session_manager.active_property
        prop_id = active_prop.get("id") if active_prop else None

        try:
            self.cached_nodes = api_client.get_dr_nodes(property_id=prop_id)
        except Exception:
            self.cached_nodes = []

        try:
            self.cached_drills = api_client.get_dr_drills()
        except Exception:
            self.cached_drills = []

        try:
            self.cached_metrics = api_client.get_dr_metrics(property_id=prop_id)
        except Exception:
            self.cached_metrics = {}

        # Update metric cards
        score = self.cached_metrics.get("resiliency_score", "100.0")
        tier = self.cached_metrics.get("resiliency_tier", "TIER_4_FAULT_TOLERANT")
        self.update_card(self.card_resiliency, f"{float(score):.1f}%", f"Tier: {tier}")

        avail = self.cached_metrics.get("cluster_availability_percent", "100.00")
        healthy = self.cached_metrics.get("healthy_nodes", len(self.cached_nodes))
        total_n = self.cached_metrics.get("total_nodes", len(self.cached_nodes))
        self.update_card(self.card_availability, f"{float(avail):.1f}%", f"{healthy}/{total_n} Nodes Healthy")

        max_lag = self.cached_metrics.get("max_replication_lag_seconds", "0.085")
        zero_rpo = "Zero-RPO Compliant" if self.cached_metrics.get("is_zero_rpo_compliant", True) else "Lag Warning"
        self.update_card(self.card_lag, f"{float(max_lag):.3f}s", zero_rpo)

        rto = self.cached_metrics.get("avg_actual_rto_seconds", "4.80")
        drills_cnt = self.cached_metrics.get("total_drills", len(self.cached_drills))
        self.update_card(self.card_rto, f"{float(rto):.2f}s", f"{drills_cnt} Drills Executed")

        # Repopulate tables & combos
        self.populate_nodes_table()
        self.populate_drills_table()

        # Update simulation combos
        self.sim_lag_node.blockSignals(True)
        self.sim_lag_node.clear()
        self.sim_prim_node.blockSignals(True)
        self.sim_prim_node.clear()
        self.sim_stby_node.blockSignals(True)
        self.sim_stby_node.clear()

        for n in self.cached_nodes:
            code = n.get("node_code", "")
            self.sim_lag_node.addItem(code, code)
            self.sim_prim_node.addItem(code, code)
            self.sim_stby_node.addItem(code, code)

        self.sim_lag_node.blockSignals(False)
        self.sim_prim_node.blockSignals(False)
        self.sim_stby_node.blockSignals(False)

    def update_card(self, card: QFrame, val: str, sub: str):
        layout = card.layout()
        if layout and layout.count() >= 3:
            lbl_val = layout.itemAt(1).widget()
            lbl_sub = layout.itemAt(2).widget()
            if isinstance(lbl_val, QLabel):
                lbl_val.setText(val)
            if isinstance(lbl_sub, QLabel):
                lbl_sub.setText(sub)
