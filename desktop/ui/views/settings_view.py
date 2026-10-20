"""Victory Crest One - Administration & Security View
Manages users, explores RBAC roles and permissions, and displays immutable security audit logs.
"""

from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.core.session import session_manager
from desktop.services.api_client import api_client
from desktop.ui.components.status_badge import StatusBadge
from shared.enums import UserRole


class SettingsView(QWidget):
    """Administration and Security Management view."""

    def __init__(self, on_change_user: Optional[Callable[[], None]] = None, parent=None):
        super().__init__(parent)
        self.on_change_user = on_change_user
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("Administration & Security Hub")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("User directory, Role-Based Access Control (RBAC), and immutable audit logs.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        if self.on_change_user:
            btn_switch = QPushButton("🔑 Switch Account / Login")
            btn_switch.setProperty("class", "btn_secondary")
            btn_switch.clicked.connect(self.on_change_user)
            header_row.addWidget(btn_switch)

        main_layout.addLayout(header_row)

        # Tabs: Users, Roles, Audit Logs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                background: {ThemeColors.BG_CARD};
                border-radius: 8px;
                padding: 12px;
            }}
            QTabBar::tab {{
                background: {ThemeColors.BG_SURFACE};
                color: {ThemeColors.TEXT_MUTED};
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {ThemeColors.BG_CARD};
                color: {ThemeColors.PRIMARY_LIGHT};
                border-bottom: 2px solid {ThemeColors.PRIMARY_LIGHT};
            }}
        """)

        # Tab 1: Users Table
        self.users_tab = QWidget()
        users_layout = QVBoxLayout(self.users_tab)
        users_layout.setContentsMargins(8, 8, 8, 8)
        
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["Full Name", "Username", "Email", "Assigned Role", "Status"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setStyleSheet(self._table_stylesheet())
        users_layout.addWidget(self.users_table)
        self.tabs.addTab(self.users_tab, "👥 User Directory")

        # Tab 2: Roles Matrix
        self.roles_tab = QWidget()
        roles_layout = QVBoxLayout(self.roles_tab)
        roles_layout.setContentsMargins(8, 8, 8, 8)

        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(3)
        self.roles_table.setHorizontalHeaderLabels(["Enterprise Role", "Primary Scope", "Separation of Duties"])
        self.roles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.roles_table.setStyleSheet(self._table_stylesheet())
        roles_layout.addWidget(self.roles_table)
        self.tabs.addTab(self.roles_tab, "🛡️ RBAC Roles Matrix (30 Roles)")

        # Tab 3: Audit Trail
        self.audit_tab = QWidget()
        audit_layout = QVBoxLayout(self.audit_tab)
        audit_layout.setContentsMargins(8, 8, 8, 8)

        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(5)
        self.audit_table.setHorizontalHeaderLabels(["Timestamp (UTC)", "Action", "Entity", "User", "Details"])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.audit_table.setStyleSheet(self._table_stylesheet())
        audit_layout.addWidget(self.audit_table)
        self.tabs.addTab(self.audit_tab, "📜 Immutable Audit Trail")

        main_layout.addWidget(self.tabs)

    def _table_stylesheet(self) -> str:
        return f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_SURFACE};
                gridline-color: {ThemeColors.BORDER_LIGHT};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_BASE};
                color: {ThemeColors.TEXT_MUTED};
                padding: 6px;
                border: none;
                font-weight: 700;
                font-size: 11px;
            }}
        """

    def refresh_data(self):
        """Populate tables with active users, roles, and audit trail."""
        # 1. Populate Users
        users = api_client.get_users()
        self.users_table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(u.get("full_name", "")))
            self.users_table.setItem(row, 1, QTableWidgetItem(u.get("username", "")))
            self.users_table.setItem(row, 2, QTableWidgetItem(u.get("email", "")))
            self.users_table.setItem(row, 3, QTableWidgetItem(u.get("role", "")))
            status_text = "Active" if u.get("is_active", True) else "Inactive"
            self.users_table.setItem(row, 4, QTableWidgetItem(status_text))

        # 2. Populate Roles
        roles = [r.value for r in UserRole]
        self.roles_table.setRowCount(len(roles))
        for row, r in enumerate(roles):
            self.roles_table.setItem(row, 0, QTableWidgetItem(r))
            scope = "All Modules (Superuser)" if "Admin" in r or "Owner" in r else "Domain Restricted"
            self.roles_table.setItem(row, 1, QTableWidgetItem(scope))
            sod = "Restricted Approvals" if "Accountant" in r or "Cashier" in r else "Standard Workflow"
            self.roles_table.setItem(row, 2, QTableWidgetItem(sod))

        # 3. Populate Audit Logs
        logs = api_client.get_audit_logs()
        self.audit_table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            ts = str(log.get("created_at", ""))[:19]
            self.audit_table.setItem(row, 0, QTableWidgetItem(ts))
            self.audit_table.setItem(row, 1, QTableWidgetItem(log.get("action", "")))
            self.audit_table.setItem(row, 2, QTableWidgetItem(log.get("entity_type", "")))
            self.audit_table.setItem(row, 3, QTableWidgetItem(log.get("user_email", "")))
            self.audit_table.setItem(row, 4, QTableWidgetItem(log.get("details", "")))
