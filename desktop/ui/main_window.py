"""Victory Crest One - Master Desktop Window
Enterprise application shell with persistent navigation sidebar, multi-tenant top toolbar,
organisation and property selectors, global search, and dynamic view stack.
"""

from typing import Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QStackedWidget,
    QScrollArea, QFrame, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime

from desktop.core.config import desktop_config
from desktop.core.theme import ThemeColors, ENTERPRISE_STYLE_SHEET
from desktop.core.session import session_manager
from desktop.services.api_client import api_client
from desktop.ui.views.dashboard_view import DashboardView
from desktop.ui.views.module_catalog_view import ModuleCatalogView
from desktop.ui.views.planned_module_view import PlannedModuleView
from desktop.ui.views.diagnostics_view import DiagnosticsView
from desktop.ui.components.status_badge import StatusBadge


class MainWindow(QMainWindow):
    """Primary enterprise desktop window for Victory Crest ONE."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{desktop_config.APP_NAME} — Enterprise Business Operating System")
        self.resize(desktop_config.DEFAULT_WINDOW_WIDTH, desktop_config.DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(desktop_config.MIN_WINDOW_WIDTH, desktop_config.MIN_WINDOW_HEIGHT)
        self.setStyleSheet(ENTERPRISE_STYLE_SHEET)

        self.nav_buttons: Dict[str, QPushButton] = {}
        self.current_nav_key = "dashboard"

        self.setup_ui()
        self.populate_selectors()
        self.check_initial_connectivity()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Persistent Sidebar
        sidebar = self.build_sidebar()
        root_layout.addWidget(sidebar)

        # 2. Main Content Column (Top Toolbar + View Stack)
        content_column = QWidget()
        content_layout = QVBoxLayout(content_column)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top Toolbar
        top_bar = self.build_top_toolbar()
        content_layout.addWidget(top_bar)

        # View Stack
        self.view_stack = QStackedWidget()
        
        # Build views
        self.dashboard_view = DashboardView(on_navigate_module=self.navigate_to_module)
        self.module_catalog_view = ModuleCatalogView(on_select_module=self.navigate_to_module)
        self.planned_module_view = PlannedModuleView(on_back=lambda: self.navigate_to("modules"))
        self.diagnostics_view = DiagnosticsView()

        self.view_stack.addWidget(self.dashboard_view)          # index 0: dashboard
        self.view_stack.addWidget(self.module_catalog_view)     # index 1: modules
        self.view_stack.addWidget(self.planned_module_view)      # index 2: planned
        self.view_stack.addWidget(self.diagnostics_view)        # index 3: diagnostics

        content_layout.addWidget(self.view_stack)
        root_layout.addWidget(content_column)

        # Status Bar
        self.setup_status_bar()

    def build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand Header
        brand_frame = QFrame()
        brand_frame.setObjectName("sidebar_header")
        brand_layout = QVBoxLayout(brand_frame)
        brand_layout.setContentsMargins(16, 16, 16, 16)
        brand_layout.setSpacing(4)

        brand_title = QLabel("👑  VICTORY CREST ONE")
        brand_title.setObjectName("brand_title")
        brand_tagline = QLabel(desktop_config.TAGLINE)
        brand_tagline.setObjectName("brand_tagline")

        brand_layout.addWidget(brand_title)
        brand_layout.addWidget(brand_tagline)
        layout.addWidget(brand_frame)

        # Scrollable Navigation Menu
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        menu_widget = QWidget()
        self.menu_layout = QVBoxLayout(menu_widget)
        self.menu_layout.setContentsMargins(0, 8, 0, 16)
        self.menu_layout.setSpacing(2)

        # Navigation Hierarchy
        nav_sections = [
            ("CORE & EXECUTIVE", [
                ("dashboard", "📊  Overview", "active"),
                ("modules", "🏢  Module Catalog", "active"),
                ("bi", "📈  Business Intelligence", "planned"),
                ("automation", "⚡  Workflow Automation", "planned"),
                ("ai_assistant", "🤖  AI Assistant", "planned"),
            ]),
            ("SALES & REVENUE", [
                ("sales", "💼  Sales & CRM", "planned"),
                ("marketing", "📣  Marketing", "planned"),
                ("commerce", "🛒  Commerce", "planned"),
                ("pos", "💳  Point of Sale", "planned"),
            ]),
            ("OPERATIONS & ERP", [
                ("finance", "💰  Finance & Banking", "planned"),
                ("accounting", "📑  General Accounting", "planned"),
                ("erp", "📦  Supply Chain & ERP", "planned"),
                ("inventory", "🏭  Inventory & Warehouse", "planned"),
                ("service", "🛠️  Customer & Field Service", "planned"),
                ("projects", "📋  Project Management", "planned"),
            ]),
            ("HOSPITALITY & DINING", [
                ("hotel", "🏨  Hotels & Resorts", "planned"),
                ("restaurant", "🍽️  Restaurants & Dining", "planned"),
            ]),
            ("PEOPLE & ADMINISTRATION", [
                ("hr", "👥  Human Resources", "planned"),
                ("documents", "📁  Documents Vault", "planned"),
                ("diagnostics", "⚙️  System Diagnostics", "active"),
                ("settings", "🔒  Administration & Security", "planned"),
            ]),
        ]

        for cat_title, items in nav_sections:
            cat_lbl = QLabel(cat_title)
            cat_lbl.setProperty("class", "nav_category_label")
            self.menu_layout.addWidget(cat_lbl)

            for key, label, status in items:
                btn = QPushButton(label)
                btn.setProperty("class", "nav_item")
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked, k=key: self.navigate_to(k))
                self.menu_layout.addWidget(btn)
                self.nav_buttons[key] = btn

        self.menu_layout.addStretch()
        scroll.setWidget(menu_widget)
        layout.addWidget(scroll)

        return sidebar

    def build_top_toolbar(self) -> QWidget:
        toolbar = QFrame()
        toolbar.setObjectName("top_toolbar")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(14)

        # Global Search
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search entities, folios, accounts, reports...")
        search_box.setMinimumWidth(260)
        search_box.setMaximumWidth(360)
        layout.addWidget(search_box)

        layout.addStretch()

        # Organisation Selector
        org_label = QLabel("Org:")
        org_label.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-weight: 600; font-size: 11px;")
        layout.addWidget(org_label)

        self.org_combo = QComboBox()
        self.org_combo.setMinimumWidth(240)
        self.org_combo.currentIndexChanged.connect(self.on_org_changed)
        layout.addWidget(self.org_combo)

        # Property / Branch Selector
        prop_label = QLabel("Property:")
        prop_label.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-weight: 600; font-size: 11px;")
        layout.addWidget(prop_label)

        self.prop_combo = QComboBox()
        self.prop_combo.setMinimumWidth(260)
        self.prop_combo.currentIndexChanged.connect(self.on_property_changed)
        layout.addWidget(self.prop_combo)

        # Connection Status Capsule
        self.conn_status_badge = StatusBadge("OFFLINE", "offline")
        layout.addWidget(self.conn_status_badge)

        # User Profile Avatar / Tag
        user_btn = QPushButton("👤 Administrator")
        user_btn.setProperty("class", "btn_secondary")
        layout.addWidget(user_btn)

        return toolbar

    def setup_status_bar(self):
        status_bar = self.statusBar()
        self.status_left = QLabel(f"Active Scope: {session_manager.get_context_title()}")
        self.status_center = QLabel("Offline SQLite Engine: Ready (Queue Active)")
        self.status_right = QLabel(f"System: v{desktop_config.APP_VERSION} • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        status_bar.addWidget(self.status_left, 1)
        status_bar.addPermanentWidget(self.status_center, 1)
        status_bar.addPermanentWidget(self.status_right)

    def populate_selectors(self):
        """Populate organisation and property dropdowns."""
        self.org_combo.blockSignals(True)
        self.org_combo.clear()
        for org in session_manager.organizations:
            self.org_combo.addItem(f"{org['name']} ({org['code']})", org["id"])
        self.org_combo.blockSignals(False)

        self.update_property_selector()

    def update_property_selector(self):
        """Refresh property dropdown options based on active organisation."""
        self.prop_combo.blockSignals(True)
        self.prop_combo.clear()
        for prop in session_manager.active_organization.get("properties", []):
            sim_tag = " [Simulated]" if prop.get("is_simulated") else ""
            self.prop_combo.addItem(f"{prop['name']}{sim_tag}", prop["id"])
        self.prop_combo.blockSignals(False)

    def on_org_changed(self, index: int):
        org_id = self.org_combo.currentData()
        if org_id:
            session_manager.set_active_organization(org_id)
            self.update_property_selector()
            self.refresh_active_views()

    def on_property_changed(self, index: int):
        prop_id = self.prop_combo.currentData()
        if prop_id:
            session_manager.set_active_property(prop_id)
            self.refresh_active_views()

    def refresh_active_views(self):
        self.status_left.setText(f"Active Scope: {session_manager.get_context_title()}")
        self.dashboard_view.refresh_data()

    def check_initial_connectivity(self):
        """Perform non-blocking health check on startup."""
        is_online, health_data = api_client.check_health()
        if is_online:
            db_conn = health_data.get("database", {}).get("is_connected", False)
            if db_conn:
                self.conn_status_badge.set_status("CENTRAL ONLINE", "connected")
            else:
                self.conn_status_badge.set_status("DB DEGRADED", "degraded")
        else:
            self.conn_status_badge.set_status("DEV OFFLINE", "offline")

    def navigate_to(self, key: str):
        """Route central stack widget based on navigation key."""
        self.current_nav_key = key
        # Update checked states
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)

        if key == "dashboard":
            self.dashboard_view.refresh_data()
            self.view_stack.setCurrentIndex(0)
        elif key == "modules":
            self.view_stack.setCurrentIndex(1)
        elif key == "diagnostics":
            self.diagnostics_view.run_diagnostics()
            self.view_stack.setCurrentIndex(3)
        else:
            # Planned module roadmap view
            self.planned_module_view.load_module(key)
            self.view_stack.setCurrentIndex(2)

    def navigate_to_module(self, module_id: str):
        self.navigate_to(module_id)
