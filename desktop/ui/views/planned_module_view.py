"""Victory Crest One - Planned Module Roadmap View
Transparently displays specifications, planned workflows, and implementation phases
for upcoming modules without misrepresenting them as completed software.
"""

from typing import Callable, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.core.session import session_manager
from desktop.ui.components.status_badge import StatusBadge
from shared.constants import MODULE_CATALOG


class PlannedModuleView(QWidget):
    """View rendering detailed roadmap specifications for planned business modules."""

    def __init__(self, on_back: Optional[Callable[[], None]] = None, parent=None):
        super().__init__(parent)
        self.on_back = on_back
        self.current_module_id = ""
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # Back Button Bar
        back_bar = QHBoxLayout()
        back_btn = QPushButton("← Back to Module Catalog")
        back_btn.setProperty("class", "btn_secondary")
        if self.on_back:
            back_btn.clicked.connect(self.on_back)
        back_bar.addWidget(back_btn)
        back_bar.addStretch()
        main_layout.addLayout(back_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(18)

        # Header Card
        self.header_card = QFrame()
        self.header_card.setProperty("class", "content_card")
        header_layout = QVBoxLayout(self.header_card)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setSpacing(10)

        badge_row = QHBoxLayout()
        self.icon_label = QLabel("📦")
        self.icon_label.setStyleSheet("font-size: 32px;")
        badge_row.addWidget(self.icon_label)

        title_col = QVBoxLayout()
        self.title_label = QLabel("Module Name")
        self.title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {ThemeColors.TEXT_MAIN};
        """)
        self.cat_label = QLabel("Domain Category")
        self.cat_label.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 13px;")
        title_col.addWidget(self.title_label)
        title_col.addWidget(self.cat_label)
        badge_row.addLayout(title_col)
        badge_row.addStretch()

        self.phase_badge = StatusBadge("PHASE 4 PLANNED", "planned")
        badge_row.addWidget(self.phase_badge)
        header_layout.addLayout(badge_row)

        self.desc_label = QLabel("Description...")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 14px; margin-top: 8px;")
        header_layout.addWidget(self.desc_label)

        self.layout.addWidget(self.header_card)

        # Architectural Specifications Card
        self.spec_card = QFrame()
        self.spec_card.setProperty("class", "content_card")
        spec_layout = QVBoxLayout(self.spec_card)
        spec_layout.setContentsMargins(20, 20, 20, 20)
        spec_layout.setSpacing(14)

        spec_title = QLabel("Planned Architecture & Cross-Module Integrations")
        spec_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        spec_layout.addWidget(spec_title)

        notice_box = QFrame()
        notice_box.setStyleSheet(f"""
            background-color: rgba(139, 92, 246, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 6px;
            padding: 12px;
        """)
        notice_layout = QVBoxLayout(notice_box)
        notice_text = QLabel(
            "<b>Engineering Transparency Notice:</b> In accordance with Victory Crest ONE delivery rules, "
            "this module is scheduled for implementation in its designated phase. It is not presented "
            "as a pseudo-functional screen until backend data models, business logic, transactions, and "
            "automated tests are fully implemented."
        )
        notice_text.setWordWrap(True)
        notice_text.setStyleSheet(f"color: #DDD6FE; font-size: 12px;")
        notice_layout.addWidget(notice_text)
        spec_layout.addWidget(notice_box)

        self.specs_body = QLabel()
        self.specs_body.setWordWrap(True)
        self.specs_body.setStyleSheet(f"color: {ThemeColors.TEXT_MAIN}; font-size: 13px; line-height: 1.6;")
        spec_layout.addWidget(self.specs_body)

        self.layout.addWidget(self.spec_card)
        self.layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def load_module(self, module_id: str):
        """Populate view with module specifications from catalog."""
        self.current_module_id = module_id
        module = next((m for m in MODULE_CATALOG if m["id"] == module_id), None)
        if not module:
            return

        self.icon_label.setText(module["icon"])
        self.title_label.setText(module["name"])
        self.cat_label.setText(f"Enterprise Category: {module['category']}")
        self.desc_label.setText(module["description"])
        phase = module.get("phase", 1)
        self.phase_badge.set_status(f"PHASE {phase} PLANNED", "planned")

        specs_text = (
            f"<b>Core Capabilities:</b><br>"
            f"• Scoped to active organisation ({session_manager.active_organization.get('code')}) and property.<br>"
            f"• Double-entry transaction safety and durable operation queue.<br>"
            f"• Idempotency key protection preventing duplicate transactions.<br>"
            f"• Synchronized with central PostgreSQL and local offline SQLite storage.<br><br>"
            f"<b>Prerequisites:</b><br>"
            f"• Phase 1 Foundation & Shell (Current - Complete)<br>"
            f"• Phase 2 Identity, RBAC & Permissions Engine<br>"
            f"• Phase 3 Shared Master Data (Customers, Products, Documents)"
        )
        self.specs_body.setText(specs_text)
