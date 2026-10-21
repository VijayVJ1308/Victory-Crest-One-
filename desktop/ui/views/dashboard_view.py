"""Victory Crest One - Executive Dashboard View
Unified executive telemetry, key business KPIs, database connectivity diagnostics,
and cross-property performance overview.
"""

from typing import Callable, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.core.session import session_manager
from desktop.services.api_client import api_client
from desktop.ui.components.metric_card import MetricCard
from desktop.ui.components.status_badge import StatusBadge
from shared.calculations import (
    calculate_occupancy_rate,
    calculate_adr,
    calculate_revpar,
    calculate_gross_profit
)


class DashboardView(QWidget):
    """Executive Dashboard showcasing live/simulated operations and system status."""

    def __init__(self, on_navigate_module: Optional[Callable[[str], None]] = None, parent=None):
        super().__init__(parent)
        self.on_navigate_module = on_navigate_module
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(20)

        # Scroll Area for responsive sizing
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(20)

        # Header Title & Refresh Button
        header_row = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(4)

        title = QLabel("Executive Business Dashboard")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {ThemeColors.TEXT_MAIN};
        """)
        
        self.subtitle = QLabel(f"Active Scope: {session_manager.get_context_title()} • Live Telemetry")
        self.subtitle.setStyleSheet(f"""
            font-size: 13px;
            color: {ThemeColors.TEXT_MUTED};
        """)

        header_text_layout.addWidget(title)
        header_text_layout.addWidget(self.subtitle)
        header_row.addLayout(header_text_layout)
        header_row.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh Telemetry")
        self.refresh_btn.setProperty("class", "btn_secondary")
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_row.addWidget(self.refresh_btn)

        self.layout.addLayout(header_row)

        # System Connectivity Diagnostic Banner
        self.conn_banner = QFrame()
        self.conn_banner.setProperty("class", "content_card")
        self.conn_banner_layout = QHBoxLayout(self.conn_banner)
        self.conn_banner_layout.setContentsMargins(16, 12, 16, 12)
        self.layout.addWidget(self.conn_banner)

        # Top Executive KPI Metric Cards
        self.metrics_grid = QGridLayout()
        self.metrics_grid.setSpacing(14)
        self.layout.addLayout(self.metrics_grid)

        # Operational Modules Quick Overview Section
        overview_header = QLabel("Core Enterprise Operations Status")
        overview_header.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 700;
            color: {ThemeColors.TEXT_MAIN};
            margin-top: 10px;
        """)
        self.layout.addWidget(overview_header)

        # Operations Grid
        self.ops_card = QFrame()
        self.ops_card.setProperty("class", "content_card")
        ops_layout = QVBoxLayout(self.ops_card)
        ops_layout.setContentsMargins(16, 16, 16, 16)
        ops_layout.setSpacing(12)

        ops_desc = QLabel(
            "Victory Crest ONE centralizes cross-module workflows across hospitality, dining, "
            "commerce, ERP, supply chain, HR, finance, and CRM. Explore individual modules below."
        )
        ops_desc.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED};")
        ops_layout.addWidget(ops_desc)

        # Button row to jump to catalog or diagnostics
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        btn_catalog = QPushButton("Browse All 18+ Business Modules")
        btn_catalog.setProperty("class", "btn_primary")
        if self.on_navigate_module:
            btn_catalog.clicked.connect(lambda: self.on_navigate_module("modules"))
        btn_row.addWidget(btn_catalog)

        btn_diag = QPushButton("System & Database Diagnostics")
        btn_diag.setProperty("class", "btn_secondary")
        if self.on_navigate_module:
            btn_diag.clicked.connect(lambda: self.on_navigate_module("diagnostics"))
        btn_row.addWidget(btn_diag)
        btn_row.addStretch()

        ops_layout.addLayout(btn_row)
        self.layout.addWidget(self.ops_card)

        self.layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def refresh_data(self):
        """Update KPI metrics and database health telemetry."""
        self.subtitle.setText(f"Active Scope: {session_manager.get_context_title()} • Live Telemetry")
        
        # Test backend connection
        is_online, health_info = api_client.check_health()

        # Update Connectivity Banner
        self.update_connectivity_banner(is_online, health_info)

        # Calculate Sample Metrics using shared/calculations.py
        # Occupancy: 211 occupied / 269 total rooms across properties
        occ_rate = calculate_occupancy_rate(211, 269)
        # ADR: ₹1,023,350 room revenue / 211 rooms sold
        adr = calculate_adr(1023350, 211)
        # RevPAR: ₹1,023,350 / 269 available
        revpar = calculate_revpar(1023350, 269)
        # Gross profit: ₹2,450,000 rev - ₹980,000 direct cost
        gross_profit = calculate_gross_profit(2450000, 980000)

        # Clear and repopulate metrics grid
        while self.metrics_grid.count():
            item = self.metrics_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        card_occ = MetricCard(
            "Portfolio Occupancy",
            f"{occ_rate}%",
            icon="🏨",
            subtext="Simulated across 3 properties",
            is_positive=True
        )
        card_adr = MetricCard(
            "Average Daily Rate (ADR)",
            f"₹{adr:,.2f}",
            icon="💳",
            subtext="Hospitality division",
            is_positive=True
        )
        card_revpar = MetricCard(
            "RevPAR",
            f"₹{revpar:,.2f}",
            icon="📊",
            subtext="Revenue per available room",
            is_positive=True
        )
        card_profit = MetricCard(
            "Monthly Gross Profit",
            f"₹{gross_profit:,.2f}",
            icon="💰",
            subtext="Margin: ~60.0% (Simulated)",
            is_positive=True
        )

        self.metrics_grid.addWidget(card_occ, 0, 0)
        self.metrics_grid.addWidget(card_adr, 0, 1)
        self.metrics_grid.addWidget(card_revpar, 0, 2)
        self.metrics_grid.addWidget(card_profit, 0, 3)

    def update_connectivity_banner(self, is_online: bool, health_info: dict):
        # Clear previous banner contents
        while self.conn_banner_layout.count():
            item = self.conn_banner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if is_online:
            db_data = health_info.get("database", {})
            if isinstance(db_data, str):
                db_conn = db_data.lower() in ("connected", "healthy", "ok", "true")
                db_status = db_data.capitalize()
                db_engine = "PostgreSQL"
                latency = "N/A"
            elif isinstance(db_data, dict):
                db_conn = db_data.get("is_connected", False)
                db_status = "Connected" if db_conn else "Disconnected"
                db_engine = db_data.get('engine', 'PostgreSQL')
                latency = db_data.get("latency_ms", "N/A")
            else:
                db_conn = False
                db_status = "Unknown"
                db_engine = "PostgreSQL"
                latency = "N/A"

            icon_lbl = QLabel("🟢")
            info_lbl = QLabel(
                f"<b>Central Backend Online:</b> FastAPI active • "
                f"PostgreSQL Database: <b>{db_status}</b> ({db_engine}, {latency} ms latency) • "
                f"Offline SQLite Cache: <b>Ready</b>"
            )
            info_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MAIN}; font-size: 12px;")

            self.conn_banner_layout.addWidget(icon_lbl)
            self.conn_banner_layout.addWidget(info_lbl)
            self.conn_banner_layout.addStretch()

            badge = StatusBadge("SYSTEM HEALTHY" if db_conn else "DB DEGRADED", "active" if db_conn else "degraded")
            self.conn_banner_layout.addWidget(badge)
        else:
            icon_lbl = QLabel("🟡")
            info_lbl = QLabel(
                "<b>Development Offline Mode Active:</b> Central FastAPI backend is currently offline. "
                "The desktop interface is operating via local storage. "
                "<i>To connect central API: run `uvicorn backend.app.main:app` in a terminal.</i>"
            )
            info_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")

            self.conn_banner_layout.addWidget(icon_lbl)
            self.conn_banner_layout.addWidget(info_lbl)
            self.conn_banner_layout.addStretch()

            badge = StatusBadge("DEV OFFLINE", "offline")
            self.conn_banner_layout.addWidget(badge)
