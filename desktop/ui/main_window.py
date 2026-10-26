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
from desktop.ui.views.settings_view import SettingsView
from desktop.ui.views.documents_view import DocumentsView
from desktop.ui.views.finance_view import FinanceView
from desktop.ui.views.crm_view import SalesCrmView
from desktop.ui.views.pos_view import PosCommerceView
from desktop.ui.views.marketing_view import MarketingView
from desktop.ui.views.inventory_view import InventoryView
from desktop.ui.views.hr_view import HrPayrollView
from desktop.ui.views.service_view import ServiceManagementView
from desktop.ui.views.hospitality_view import HospitalityView
from desktop.ui.views.manufacturing_view import ManufacturingView
from desktop.ui.views.projects_view import ProjectsView
from desktop.ui.views.bi_view import BusinessIntelligenceView
from desktop.ui.views.automation_view import WorkflowAutomationView
from desktop.ui.views.ai_assistant_view import AiAssistantView
from desktop.ui.views.iot_view import IoTGatewaysView
from desktop.ui.views.lakehouse_view import LakehouseView
from desktop.ui.login_window import LoginDialog
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
        self.settings_view = SettingsView(on_change_user=self.open_login_dialog)
        self.documents_view = DocumentsView()
        self.finance_view = FinanceView()
        self.crm_view = SalesCrmView()
        self.pos_view = PosCommerceView()
        self.marketing_view = MarketingView()
        self.inventory_view = InventoryView()
        self.hr_view = HrPayrollView()
        self.service_view = ServiceManagementView()
        self.hospitality_view = HospitalityView()
        self.manufacturing_view = ManufacturingView()
        self.projects_view = ProjectsView()
        self.bi_view = BusinessIntelligenceView()
        self.automation_view = WorkflowAutomationView()
        self.ai_assistant_view = AiAssistantView()
        self.iot_view = IoTGatewaysView()
        self.lakehouse_view = LakehouseView()

        self.view_stack.addWidget(self.dashboard_view)          # index 0: dashboard
        self.view_stack.addWidget(self.module_catalog_view)     # index 1: modules
        self.view_stack.addWidget(self.planned_module_view)      # index 2: planned
        self.view_stack.addWidget(self.diagnostics_view)        # index 3: diagnostics
        self.view_stack.addWidget(self.settings_view)           # index 4: settings
        self.view_stack.addWidget(self.documents_view)          # index 5: documents
        self.view_stack.addWidget(self.finance_view)            # index 6: finance & accounting
        self.view_stack.addWidget(self.crm_view)                # index 7: sales & crm
        self.view_stack.addWidget(self.pos_view)                # index 8: pos & commerce
        self.view_stack.addWidget(self.marketing_view)          # index 9: marketing
        self.view_stack.addWidget(self.inventory_view)          # index 10: inventory & erp
        self.view_stack.addWidget(self.hr_view)                 # index 11: hr & payroll
        self.view_stack.addWidget(self.service_view)             # index 12: customer & field service
        self.view_stack.addWidget(self.hospitality_view)         # index 13: hospitality & dining
        self.view_stack.addWidget(self.manufacturing_view)       # index 14: manufacturing & assets
        self.view_stack.addWidget(self.projects_view)            # index 15: project management & psa
        self.view_stack.addWidget(self.bi_view)                  # index 16: business intelligence & analytics
        self.view_stack.addWidget(self.automation_view)          # index 17: workflow automation & rules engine
        self.view_stack.addWidget(self.ai_assistant_view)       # index 18: ai business assistant
        self.view_stack.addWidget(self.iot_view)                # index 19: iot & smart device gateways
        self.view_stack.addWidget(self.lakehouse_view)          # index 20: data lakehouse & predictive ml


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
                ("bi", "📈  Business Intelligence", "active"),
                ("automation", "⚡  Workflow Automation", "active"),
                ("ai_assistant", "🤖  AI Assistant", "active"),
                ("iot_gateways", "📡  IoT & Smart Devices", "active"),
                ("analytics_lake", "🔮  Data Lakehouse & ML", "active"),
            ]),
            ("SALES & REVENUE", [
                ("sales", "💼  Sales & CRM", "active"),
                ("marketing", "📣  Marketing", "active"),
                ("commerce", "🛒  Commerce", "active"),
                ("pos", "💳  Point of Sale", "active"),
            ]),
            ("OPERATIONS & ERP", [
                ("finance", "💰  Finance & Banking", "active"),
                ("accounting", "📑  General Accounting", "active"),
                ("erp", "📦  Supply Chain & ERP", "active"),
                ("inventory", "🏭  Inventory & Warehouse", "active"),
                ("manufacturing", "⚙️  Manufacturing & Assets", "active"),
                ("service", "🛠️  Customer & Field Service", "active"),
                ("projects", "📋  Project Management", "active"),
            ]),
            ("HOSPITALITY & DINING", [
                ("hotel", "🏨  Hotels & Resorts", "active"),
                ("restaurant", "🍽️  Restaurants & Dining", "active"),
            ]),
            ("PEOPLE & ADMINISTRATION", [
                ("hr", "👥  Human Resources", "active"),
                ("payroll", "💵  Payroll Management", "active"),
                ("documents", "📁  Documents Vault", "active"),
                ("diagnostics", "⚙️  System Diagnostics", "active"),
                ("settings", "🔒  Administration & Security", "active"),
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

        # Notification Bell Button
        unread = api_client.get_unread_notification_count()
        self.notif_btn = QPushButton(f"🔔 {unread}")
        self.notif_btn.setProperty("class", "btn_secondary")
        self.notif_btn.clicked.connect(self.open_notifications_dialog)
        layout.addWidget(self.notif_btn)

        # User Profile Button (Clickable to switch accounts)
        user_info = session_manager.current_user.get("full_name", "Administrator")
        self.user_btn = QPushButton(f"👤 {user_info}")
        self.user_btn.setProperty("class", "btn_secondary")
        self.user_btn.clicked.connect(self.open_login_dialog)
        layout.addWidget(self.user_btn)

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
        if hasattr(self, "finance_view"):
            self.finance_view.refresh_data()
        if hasattr(self, "crm_view"):
            self.crm_view.refresh_data()
        if hasattr(self, "pos_view"):
            self.pos_view.refresh_data()
        if hasattr(self, "marketing_view"):
            self.marketing_view.refresh_data()
        if hasattr(self, "inventory_view"):
            self.inventory_view.refresh_data()
        if hasattr(self, "hr_view"):
            self.hr_view.refresh_data()
        if hasattr(self, "service_view"):
            self.service_view.refresh_data()
        if hasattr(self, "hospitality_view"):
            self.hospitality_view.refresh_data()
        if hasattr(self, "manufacturing_view"):
            self.manufacturing_view.refresh_data()
        if hasattr(self, "projects_view"):
            self.projects_view.refresh_data()
        if hasattr(self, "bi_view"):
            self.bi_view.refresh_data()
        if hasattr(self, "automation_view"):
            self.automation_view.refresh_data()
        if hasattr(self, "ai_assistant_view"):
            self.ai_assistant_view.refresh_data()
        if hasattr(self, "iot_view"):
            self.iot_view.refresh_data()
        if hasattr(self, "lakehouse_view"):
            self.lakehouse_view.refresh_data()

    def check_initial_connectivity(self):
        """Perform non-blocking health check on startup."""
        is_online, health_data = api_client.check_health()
        if is_online:
            db_val = health_data.get("database", {})
            if isinstance(db_val, str):
                db_conn = db_val.lower() in ("connected", "healthy", "ok", "true")
            elif isinstance(db_val, dict):
                db_conn = db_val.get("is_connected", False)
            else:
                db_conn = False

            if db_conn:
                self.conn_status_badge.set_status("CENTRAL ONLINE", "connected")
            else:
                self.conn_status_badge.set_status("DB DEGRADED", "degraded")
        else:
            self.conn_status_badge.set_status("DEV OFFLINE", "offline")

    def open_login_dialog(self):
        """Open the authentication and account switching dialog."""
        dialog = LoginDialog(on_success=self.on_user_authenticated, parent=self)
        dialog.exec()

    def on_user_authenticated(self):
        """Handle successful authentication."""
        user = session_manager.current_user
        name = user.get("full_name") or user.get("username", "User")
        role = user.get("role", "Staff")
        self.user_btn.setText(f"👤 {name} ({role})")
        self.refresh_active_views()
        if hasattr(self, "settings_view"):
            self.settings_view.refresh_data()

    def open_notifications_dialog(self):
        """Open notification center dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("Notifications & Alerts — Victory Crest ONE")
        dialog.resize(460, 360)
        dialog.setStyleSheet(ENTERPRISE_STYLE_SHEET)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QLabel("Notifications & System Alerts")
        header.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(header)

        list_widget = QListWidget()
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 6px;
                color: {ThemeColors.TEXT_MAIN};
            }}
        """)

        notifs = api_client.get_notifications()
        for n in notifs:
            icon = "ℹ️" if n.get("notification_type") == "INFO" else "⚡"
            status_tag = "" if n.get("is_read") else " [NEW]"
            item = QListWidgetItem(f"{icon} {n.get('title')}{status_tag}\n   {n.get('message')}")
            list_widget.addItem(item)
            if not n.get("is_read"):
                api_client.mark_notification_read(n.get("id"))

        layout.addWidget(list_widget)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "btn_secondary")
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dialog.exec()
        self.notif_btn.setText(f"🔔 {api_client.get_unread_notification_count()}")

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
            self.module_catalog_view.filter_modules("")
            self.view_stack.setCurrentIndex(1)
        elif key == "diagnostics":
            self.diagnostics_view.run_diagnostics()
            self.view_stack.setCurrentIndex(3)
        elif key == "settings":
            self.settings_view.refresh_data()
            self.view_stack.setCurrentIndex(4)
        elif key == "documents":
            self.documents_view.refresh_data()
            self.view_stack.setCurrentIndex(5)
        elif key == "finance":
            self.finance_view.refresh_data()
            self.finance_view.tabs.setCurrentIndex(2)  # AR / Invoices
            self.view_stack.setCurrentIndex(6)
        elif key == "accounting":
            self.finance_view.refresh_data()
            self.finance_view.tabs.setCurrentIndex(0)  # Journals / GL
            self.view_stack.setCurrentIndex(6)
        elif key == "sales":
            self.crm_view.refresh_data()
            self.view_stack.setCurrentIndex(7)
        elif key in ("pos", "commerce"):
            self.pos_view.refresh_data()
            self.view_stack.setCurrentIndex(8)
        elif key == "marketing":
            self.marketing_view.refresh_data()
            self.view_stack.setCurrentIndex(9)
        elif key == "inventory":
            self.inventory_view.refresh_data()
            self.inventory_view.tabs.setCurrentIndex(0)  # Warehouse Stock Catalog
            self.view_stack.setCurrentIndex(10)
        elif key == "erp":
            self.inventory_view.refresh_data()
            self.inventory_view.tabs.setCurrentIndex(1)  # Purchase Orders & Receiving
            self.view_stack.setCurrentIndex(10)
        elif key == "hr":
            self.hr_view.refresh_data()
            self.hr_view.tabs.setCurrentIndex(0)  # Staff Directory
            self.view_stack.setCurrentIndex(11)
        elif key == "payroll":
            self.hr_view.refresh_data()
            self.hr_view.tabs.setCurrentIndex(3)  # Payroll Processing
            self.view_stack.setCurrentIndex(11)
        elif key == "service":
            self.service_view.refresh_data()
            self.view_stack.setCurrentIndex(12)
        elif key == "hotel":
            self.hospitality_view.refresh_data()
            self.hospitality_view.tabs.setCurrentIndex(0)  # Reservations & Front Desk
            self.view_stack.setCurrentIndex(13)
        elif key == "restaurant":
            self.hospitality_view.refresh_data()
            self.hospitality_view.tabs.setCurrentIndex(3)  # Restaurant Dining & KDS
            self.view_stack.setCurrentIndex(13)
        elif key == "manufacturing":
            self.manufacturing_view.refresh_data()
            self.manufacturing_view.tabs.setCurrentIndex(0)  # Production Orders
            self.view_stack.setCurrentIndex(14)
        elif key == "projects":
            self.projects_view.refresh_data()
            self.projects_view.tabs.setCurrentIndex(0)  # Project Portfolios
            self.view_stack.setCurrentIndex(15)
        elif key == "bi":
            self.bi_view.refresh_data()
            self.bi_view.tabs.setCurrentIndex(0)  # Executive Overview
            self.view_stack.setCurrentIndex(16)
        elif key == "automation":
            self.automation_view.refresh_data()
            self.automation_view.tabs.setCurrentIndex(0)  # Rules & Pipelines
            self.view_stack.setCurrentIndex(17)
        elif key == "ai_assistant":
            self.ai_assistant_view.refresh_data()
            self.view_stack.setCurrentIndex(18)
        elif key == "iot_gateways":
            self.iot_view.refresh_data()
            self.view_stack.setCurrentIndex(19)
        elif key == "analytics_lake":
            self.lakehouse_view.refresh_data()
            self.view_stack.setCurrentIndex(20)
        else:
            # Planned module roadmap view
            self.planned_module_view.load_module(key)
            self.view_stack.setCurrentIndex(2)

    def navigate_to_module(self, module_id: str):
        self.navigate_to(module_id)
