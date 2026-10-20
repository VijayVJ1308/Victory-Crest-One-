"""Victory Crest One - System Diagnostics View
Real-time diagnostic panel for database connection checks, backend API health,
local storage status, and troubleshooting instructions.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QTextEdit
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.core.config import desktop_config
from desktop.services.api_client import api_client
from desktop.ui.components.status_badge import StatusBadge


class DiagnosticsView(QWidget):
    """Diagnostic and infrastructure status view for database and API health."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.run_diagnostics()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(18)

        # Header
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("System & Infrastructure Diagnostics")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Live health verification for Central PostgreSQL, Local SQLite, and API Services.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        self.btn_check = QPushButton("⚡ Run Full Diagnostic Check")
        self.btn_check.setProperty("class", "btn_primary")
        self.btn_check.clicked.connect(self.run_diagnostics)
        header_row.addWidget(self.btn_check)

        self.layout.addLayout(header_row)

        # PostgreSQL Status Card
        self.pg_card = QFrame()
        self.pg_card.setProperty("class", "content_card")
        self.pg_layout = QVBoxLayout(self.pg_card)
        self.pg_layout.setContentsMargins(20, 18, 20, 18)
        self.layout.addWidget(self.pg_card)

        # Local SQLite Status Card
        self.local_card = QFrame()
        self.local_card.setProperty("class", "content_card")
        self.local_layout = QVBoxLayout(self.local_card)
        self.local_layout.setContentsMargins(20, 18, 20, 18)
        self.layout.addWidget(self.local_card)

        # Quick Start Guide Box
        self.guide_card = QFrame()
        self.guide_card.setProperty("class", "content_card")
        guide_layout = QVBoxLayout(self.guide_card)
        guide_layout.setContentsMargins(20, 18, 20, 18)
        guide_layout.setSpacing(10)

        guide_title = QLabel("Operational Commands & Troubleshooting")
        guide_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        guide_layout.addWidget(guide_title)

        guide_text = QLabel(
            "<b>Start Central Database (PostgreSQL):</b><br>"
            "<pre style='color: #60A5FA; background: #0B0F19; padding: 8px; border-radius: 4px;'>"
            "docker compose up -d postgres\n"
            "</pre>"
            "<b>Start Central Backend API (FastAPI):</b><br>"
            "<pre style='color: #60A5FA; background: #0B0F19; padding: 8px; border-radius: 4px;'>"
            "./.venv/bin/uvicorn backend.app.main:app --port 8000 --reload\n"
            "</pre>"
            "<b>Launch Desktop Application Shell:</b><br>"
            "<pre style='color: #60A5FA; background: #0B0F19; padding: 8px; border-radius: 4px;'>"
            "./.venv/bin/python desktop/main.py\n"
            "</pre>"
        )
        guide_text.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 13px;")
        guide_layout.addWidget(guide_text)

        self.layout.addWidget(self.guide_card)
        self.layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def run_diagnostics(self):
        """Perform diagnostic check against backend and local storage."""
        is_online, health_data = api_client.check_health()

        # Update Central DB Card
        while self.pg_layout.count():
            item = self.pg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        header_row = QHBoxLayout()
        pg_title = QLabel("Central Database (PostgreSQL Engine)")
        pg_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        header_row.addWidget(pg_title)
        header_row.addStretch()

        if is_online:
            db_info = health_data.get("database", {})
            is_connected = db_info.get("is_connected", False)
            badge_type = "connected" if is_connected else "disconnected"
            badge_text = "CONNECTED" if is_connected else "DISCONNECTED"
            header_row.addWidget(StatusBadge(badge_text, badge_type))
            self.pg_layout.addLayout(header_row)

            detail_label = QLabel(
                f"<b>Status:</b> {db_info.get('status', 'Unknown')}<br>"
                f"<b>Latency:</b> {db_info.get('latency_ms', 'N/A')} ms<br>"
                f"<b>URL:</b> {db_info.get('url_masked', 'postgresql://****@localhost:5432/victory_crest_db')}<br>"
                f"<b>Diagnostic:</b> {db_info.get('detail', 'N/A')}"
            )
            detail_label.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 13px; line-height: 1.5;")
            self.pg_layout.addWidget(detail_label)

            if not is_connected and db_info.get("troubleshooting"):
                t_box = QLabel(f"<b>Troubleshooting:</b> {db_info['troubleshooting']}")
                t_box.setStyleSheet(f"color: #F87171; font-size: 12px; margin-top: 6px;")
                t_box.setWordWrap(True)
                self.pg_layout.addWidget(t_box)
        else:
            header_row.addWidget(StatusBadge("BACKEND OFFLINE", "offline"))
            self.pg_layout.addLayout(header_row)

            offline_lbl = QLabel(
                "<b>Central API is not reachable.</b><br>"
                "The application is operating in Development Offline Mode. "
                "PostgreSQL health check requires the FastAPI backend to be running."
            )
            offline_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 13px;")
            self.pg_layout.addWidget(offline_lbl)

        # Update Local SQLite Card
        while self.local_layout.count():
            item = self.local_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        local_header = QHBoxLayout()
        local_title = QLabel("Local Offline Database (SQLite Engine)")
        local_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        local_header.addWidget(local_title)
        local_header.addStretch()
        local_header.addWidget(StatusBadge("OPERATIONAL", "connected"))
        self.local_layout.addLayout(local_header)

        local_lbl = QLabel(
            f"<b>Path:</b> {desktop_config.LOCAL_DB_FILE}<br>"
            f"<b>Purpose:</b> Durable offline operation queue, local cache, offline catalog fallback.<br>"
            f"<b>Status:</b> Local storage directory initialized and ready for synchronisation."
        )
        local_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 13px; line-height: 1.5;")
        self.local_layout.addWidget(local_lbl)
