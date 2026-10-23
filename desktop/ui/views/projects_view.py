"""Victory Crest One - Project Management & Professional Services (PSA) View
Work Breakdown Structures (WBS), Contract Deliverables & Milestones,
Billable Timesheets, Direct Expenses, and Automated Double-Entry GL Revenue Recognition.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDoubleSpinBox, QDateEdit, QTextEdit, QScrollArea,
    QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, QDate

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from shared.calculations import (
    to_decimal,
    calculate_project_budget_variance,
    calculate_project_burn_rate,
    calculate_milestone_invoice,
    calculate_timesheet_totals
)


class ProjectsView(QWidget):
    """Central Project Management & Professional Services Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_projects: List[Dict[str, Any]] = []
        self.cached_milestones: List[Dict[str, Any]] = []
        self.cached_tasks: List[Dict[str, Any]] = []
        self.cached_timesheets: List[Dict[str, Any]] = []
        self.cached_expenses: List[Dict[str, Any]] = []
        self.cached_metrics: Dict[str, Any] = {}

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # -----------------------------------------------------
        # 1. Header Section
        # -----------------------------------------------------
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("Project Management & Professional Services (PSA)")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("WBS work packages, billable timesheets, project costing, milestone invoicing, and double-entry General Ledger revenue recognition.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_new_prj = QPushButton("➕ New Project")
        btn_new_prj.setProperty("class", "btn_primary")
        btn_new_prj.clicked.connect(self.open_create_project_dialog)

        btn_log_time = QPushButton("⏱️ Log Timesheet")
        btn_log_time.setProperty("class", "btn_primary")
        btn_log_time.clicked.connect(self.open_log_timesheet_dialog)

        btn_add_task = QPushButton("🌲 Add Task")
        btn_add_task.setProperty("class", "btn_secondary")
        btn_add_task.clicked.connect(self.open_create_task_dialog)

        btn_log_exp = QPushButton("💵 Log Expense")
        btn_log_exp.setProperty("class", "btn_secondary")
        btn_log_exp.clicked.connect(self.open_log_expense_dialog)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_new_prj)
        header_row.addWidget(btn_log_time)
        header_row.addWidget(btn_add_task)
        header_row.addWidget(btn_log_exp)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_active_projects = self.create_metric_card("ACTIVE PROJECTS", "0 Projects", "Under Portfolio Delivery", "#3B82F6")
        self.card_total_contract = self.create_metric_card("CONTRACT VALUE", "₹0.00", "Baseline Portfolio Scope", "#10B981")
        self.card_total_billed = self.create_metric_card("BILLED REVENUE", "₹0.00", "Recognized Invoices (CR 4040)", "#8B5CF6")
        self.card_logged_hours = self.create_metric_card("LOGGED HOURS", "0.0 hrs", "Actual Timesheet Labor", "#F59E0B")
        self.card_billable_util = self.create_metric_card("BILLABLE UTILIZATION", "0.0%", "Target Allowance ≥ 85.0%", "#06B6D4")

        cards_row.addWidget(self.card_active_projects)
        cards_row.addWidget(self.card_total_contract)
        cards_row.addWidget(self.card_total_billed)
        cards_row.addWidget(self.card_logged_hours)
        cards_row.addWidget(self.card_billable_util)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Main Operational Tabs
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

        # Tab 1: Portfolios & Progress
        self.tab_projects = QWidget()
        self.setup_projects_tab()
        self.tab_widget.addTab(self.tab_projects, "📋 Portfolios & Progress")

        # Tab 2: WBS Task Hierarchies
        self.tab_tasks = QWidget()
        self.setup_tasks_tab()
        self.tab_widget.addTab(self.tab_tasks, "🌲 WBS Task Hierarchies")

        # Tab 3: Milestones & GL Invoicing
        self.tab_milestones = QWidget()
        self.setup_milestones_tab()
        self.tab_widget.addTab(self.tab_milestones, "🎯 Milestones & GL Invoicing")

        # Tab 4: Timesheets & Billable Hours
        self.tab_timesheets = QWidget()
        self.setup_timesheets_tab()
        self.tab_widget.addTab(self.tab_timesheets, "⏱️ Timesheets & Billable Hours")

        # Tab 5: Direct Expenses & Profitability
        self.tab_expenses = QWidget()
        self.setup_expenses_tab()
        self.tab_widget.addTab(self.tab_expenses, "💵 Direct Expenses & Profitability")

        main_layout.addWidget(self.tab_widget)

    def create_metric_card(self, title: str, value: str, subtitle: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 14px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ThemeColors.TEXT_MUTED}; letter-spacing: 0.5px;")

        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color}; margin: 2px 0;")
        card.value_label = lbl_val

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)
        return card

    # =========================================================================
    # Tab 1: Project Portfolios & Progress
    # =========================================================================
    def setup_projects_tab(self):
        layout = QVBoxLayout(self.tab_projects)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_st = QLabel("Status:")
        lbl_st.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        self.cb_project_status = QComboBox()
        self.cb_project_status.addItems(["All Statuses", "PLANNING", "ACTIVE", "ON_HOLD", "COMPLETED", "CANCELLED"])
        self.cb_project_status.currentTextChanged.connect(self.filter_projects_table)

        lbl_pri = QLabel("Priority:")
        lbl_pri.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        self.cb_project_priority = QComboBox()
        self.cb_project_priority.addItems(["All Priorities", "LOW", "NORMAL", "HIGH", "URGENT"])
        self.cb_project_priority.currentTextChanged.connect(self.filter_projects_table)

        self.txt_project_search = QLineEdit()
        self.txt_project_search.setPlaceholderText("Search code, project name, customer, or PM...")
        self.txt_project_search.textChanged.connect(self.filter_projects_table)

        filter_row.addWidget(lbl_st)
        filter_row.addWidget(self.cb_project_status)
        filter_row.addWidget(lbl_pri)
        filter_row.addWidget(self.cb_project_priority)
        filter_row.addWidget(self.txt_project_search)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table_projects = QTableWidget()
        self.table_projects.setColumnCount(10)
        self.table_projects.setHorizontalHeaderLabels([
            "Code", "Project Title", "Client / Customer", "Billing Type", "Progress",
            "Contract Budget", "Billed Revenue", "Actual Cost", "Status", "Actions"
        ])
        self.table_projects.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_projects.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.table_projects.verticalHeader().setVisible(False)
        self.table_projects.setAlternatingRowColors(True)

        layout.addWidget(self.table_projects)

    def filter_projects_table(self):
        st_filter = self.cb_project_status.currentText().upper()
        pri_filter = self.cb_project_priority.currentText().upper()
        q_txt = self.txt_project_search.text().lower().strip()

        filtered = []
        for p in self.cached_projects:
            if st_filter != "ALL STATUSES" and p.get("status", "").upper() != st_filter:
                continue
            if pri_filter != "ALL PRIORITIES" and p.get("priority", "").upper() != pri_filter:
                continue
            if q_txt:
                search_scope = f"{p.get('project_code', '')} {p.get('name', '')} {p.get('customer_name', '')} {p.get('project_manager_name', '')}".lower()
                if q_txt not in search_scope:
                    continue
            filtered.append(p)
        self.populate_projects_table(filtered)

    def populate_projects_table(self, projects: List[Dict[str, Any]]):
        self.table_projects.setRowCount(0)
        for row, p in enumerate(projects):
            self.table_projects.insertRow(row)

            item_code = QTableWidgetItem(p.get("project_code", ""))
            item_code.setTextAlignment(Qt.AlignCenter)
            item_title = QTableWidgetItem(p.get("name", ""))
            item_cust = QTableWidgetItem(p.get("customer_name", "N/A"))
            item_btype = QTableWidgetItem(p.get("billing_type", "MILESTONE_BASED"))
            item_btype.setTextAlignment(Qt.AlignCenter)

            prog = to_decimal(p.get("progress_percent", 0))
            item_prog = QTableWidgetItem(f"{prog:.1f}%")
            item_prog.setTextAlignment(Qt.AlignCenter)

            budget = to_decimal(p.get("budget_amount", 0))
            item_bud = QTableWidgetItem(f"₹{budget:,.2f}")
            item_bud.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            billed = to_decimal(p.get("billed_amount", 0))
            item_bil = QTableWidgetItem(f"₹{billed:,.2f}")
            item_bil.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            cost = to_decimal(p.get("actual_cost", 0))
            item_cst = QTableWidgetItem(f"₹{cost:,.2f}")
            item_cst.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            st = p.get("status", "ACTIVE").upper()
            item_st = QTableWidgetItem(st)
            item_st.setTextAlignment(Qt.AlignCenter)
            if st == "COMPLETED":
                item_st.setForeground(Qt.darkGreen)
            elif st == "ACTIVE":
                item_st.setForeground(Qt.blue)
            elif st == "ON_HOLD":
                item_st.setForeground(Qt.darkYellow)
            else:
                item_st.setForeground(Qt.darkGray)

            btn_action = QPushButton("Update Status")
            btn_action.setStyleSheet("padding: 4px 8px; font-size: 11px;")
            p_id = p.get("id", "")
            btn_action.clicked.connect(lambda _, pid=p_id: self.open_update_project_dialog(pid))

            self.table_projects.setItem(row, 0, item_code)
            self.table_projects.setItem(row, 1, item_title)
            self.table_projects.setItem(row, 2, item_cust)
            self.table_projects.setItem(row, 3, item_btype)
            self.table_projects.setItem(row, 4, item_prog)
            self.table_projects.setItem(row, 5, item_bud)
            self.table_projects.setItem(row, 6, item_bil)
            self.table_projects.setItem(row, 7, item_cst)
            self.table_projects.setItem(row, 8, item_st)
            self.table_projects.setCellWidget(row, 9, btn_action)

    # =========================================================================
    # Tab 2: WBS Task Hierarchies
    # =========================================================================
    def setup_tasks_tab(self):
        layout = QVBoxLayout(self.tab_tasks)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_prj = QLabel("Filter Project:")
        lbl_prj.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        self.cb_task_project = QComboBox()
        self.cb_task_project.addItem("All Projects", None)
        self.cb_task_project.currentIndexChanged.connect(self.filter_tasks_table)

        lbl_st = QLabel("Status:")
        lbl_st.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        self.cb_task_status = QComboBox()
        self.cb_task_status.addItems(["All Statuses", "TODO", "IN_PROGRESS", "IN_REVIEW", "DONE", "BLOCKED"])
        self.cb_task_status.currentTextChanged.connect(self.filter_tasks_table)

        self.txt_task_search = QLineEdit()
        self.txt_task_search.setPlaceholderText("Search task code, title, or assigned staff...")
        self.txt_task_search.textChanged.connect(self.filter_tasks_table)

        btn_add = QPushButton("➕ Add Task")
        btn_add.setProperty("class", "btn_secondary")
        btn_add.clicked.connect(self.open_create_task_dialog)

        filter_row.addWidget(lbl_prj)
        filter_row.addWidget(self.cb_task_project)
        filter_row.addWidget(lbl_st)
        filter_row.addWidget(self.cb_task_status)
        filter_row.addWidget(self.txt_task_search)
        filter_row.addWidget(btn_add)
        layout.addLayout(filter_row)

        self.table_tasks = QTableWidget()
        self.table_tasks.setColumnCount(9)
        self.table_tasks.setHorizontalHeaderLabels([
            "Task Code", "Project", "Task Title", "Assigned Staff", "Est. Hours",
            "Act. Hours", "Status", "Due Date", "Action"
        ])
        self.table_tasks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_tasks.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.table_tasks.verticalHeader().setVisible(False)
        self.table_tasks.setAlternatingRowColors(True)

        layout.addWidget(self.table_tasks)

    def filter_tasks_table(self):
        sel_pid = self.cb_task_project.currentData()
        st_filter = self.cb_task_status.currentText().upper()
        q_txt = self.txt_task_search.text().lower().strip()

        filtered = []
        for t in self.cached_tasks:
            if sel_pid and t.get("project_id") != sel_pid:
                continue
            if st_filter != "ALL STATUSES" and t.get("status", "").upper() != st_filter:
                continue
            if q_txt:
                search_scope = f"{t.get('task_code', '')} {t.get('title', '')} {t.get('assigned_to_name', '')}".lower()
                if q_txt not in search_scope:
                    continue
            filtered.append(t)
        self.populate_tasks_table(filtered)

    def populate_tasks_table(self, tasks: List[Dict[str, Any]]):
        self.table_tasks.setRowCount(0)
        prj_map = {p.get("id"): p.get("project_code") for p in self.cached_projects}

        for row, t in enumerate(tasks):
            self.table_tasks.insertRow(row)

            item_code = QTableWidgetItem(t.get("task_code", ""))
            item_code.setTextAlignment(Qt.AlignCenter)
            item_prj = QTableWidgetItem(prj_map.get(t.get("project_id"), t.get("project_id", "")))
            item_prj.setTextAlignment(Qt.AlignCenter)
            item_title = QTableWidgetItem(t.get("title", ""))
            item_staff = QTableWidgetItem(t.get("assigned_to_name", "Unassigned"))

            eh = to_decimal(t.get("estimated_hours", 0))
            item_eh = QTableWidgetItem(f"{eh:.1f}h")
            item_eh.setTextAlignment(Qt.AlignCenter)

            ah = to_decimal(t.get("actual_hours", 0))
            item_ah = QTableWidgetItem(f"{ah:.1f}h")
            item_ah.setTextAlignment(Qt.AlignCenter)

            st = t.get("status", "TODO").upper()
            item_st = QTableWidgetItem(st)
            item_st.setTextAlignment(Qt.AlignCenter)
            if st == "DONE":
                item_st.setForeground(Qt.darkGreen)
            elif st == "IN_PROGRESS":
                item_st.setForeground(Qt.blue)
            elif st == "BLOCKED":
                item_st.setForeground(Qt.darkRed)
            else:
                item_st.setForeground(Qt.darkYellow)

            due_str = str(t.get("due_date", "")) if t.get("due_date") else "-"
            item_due = QTableWidgetItem(due_str)
            item_due.setTextAlignment(Qt.AlignCenter)

            next_status = "DONE" if st != "DONE" else "IN_PROGRESS"
            btn_act = QPushButton(f"Set {next_status}")
            btn_act.setStyleSheet("padding: 4px 8px; font-size: 11px;")
            p_id = t.get("project_id", "")
            t_id = t.get("id", "")
            btn_act.clicked.connect(lambda _, pid=p_id, tid=t_id, ns=next_status: self.change_task_status(pid, tid, ns))

            self.table_tasks.setItem(row, 0, item_code)
            self.table_tasks.setItem(row, 1, item_prj)
            self.table_tasks.setItem(row, 2, item_title)
            self.table_tasks.setItem(row, 3, item_staff)
            self.table_tasks.setItem(row, 4, item_eh)
            self.table_tasks.setItem(row, 5, item_ah)
            self.table_tasks.setItem(row, 6, item_st)
            self.table_tasks.setItem(row, 7, item_due)
            self.table_tasks.setCellWidget(row, 8, btn_act)

    def change_task_status(self, project_id: str, task_id: str, new_status: str):
        try:
            api_client.update_task_status(project_id, task_id, new_status)
            self.refresh_data()
        except Exception as e:
            QMessageBox.warning(self, "Status Update Error", str(e))

    # =========================================================================
    # Tab 3: Milestones & GL Invoicing
    # =========================================================================
    def setup_milestones_tab(self):
        layout = QVBoxLayout(self.tab_milestones)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # GL Posting Info Banner
        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(4, 4, 4, 4)
        b_layout.setSpacing(4)

        b_title = QLabel("⚡ Automated Milestone Customer Invoicing & General Ledger Revenue Recognition")
        b_title.setStyleSheet(f"font-weight: 700; color: {ThemeColors.PRIMARY}; font-size: 13px;")
        b_desc = QLabel(
            "<b>Double-Entry Financial Accounting Rule:</b> When a contractual milestone is invoiced, the system generates an official GST tax invoice and posts synchronous GL journals:<br>"
            "&nbsp;&nbsp;• <b>DR 1020 - Accounts Receivable</b> (Total Invoice Amount inclusive of 18% GST)<br>"
            "&nbsp;&nbsp;• <b>CR 4040 - Service & Event Fee Revenue</b> (Base Milestone Deliverable Revenue)<br>"
            "&nbsp;&nbsp;• <b>CR 2020 - GST Output Tax Payable</b> (18% Statutory Output GST Liability)"
        )
        b_desc.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MAIN}; line-height: 1.5;")
        b_layout.addWidget(b_title)
        b_layout.addWidget(b_desc)
        layout.addWidget(banner)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_prj = QLabel("Filter Project:")
        lbl_prj.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        self.cb_milestone_project = QComboBox()
        self.cb_milestone_project.addItem("All Projects", None)
        self.cb_milestone_project.currentIndexChanged.connect(self.filter_milestones_table)

        btn_new_ms = QPushButton("🎯 Create Milestone")
        btn_new_ms.setProperty("class", "btn_secondary")
        btn_new_ms.clicked.connect(self.open_create_milestone_dialog)

        filter_row.addWidget(lbl_prj)
        filter_row.addWidget(self.cb_milestone_project)
        filter_row.addStretch()
        filter_row.addWidget(btn_new_ms)
        layout.addLayout(filter_row)

        self.table_milestones = QTableWidget()
        self.table_milestones.setColumnCount(8)
        self.table_milestones.setHorizontalHeaderLabels([
            "Project", "Milestone Title", "Target Due Date", "Contract Amount",
            "Status", "Invoice / Ref", "Achieved Date", "Actions"
        ])
        self.table_milestones.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_milestones.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_milestones.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_milestones.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_milestones.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table_milestones.verticalHeader().setVisible(False)
        self.table_milestones.setAlternatingRowColors(True)

        layout.addWidget(self.table_milestones)

    def filter_milestones_table(self):
        sel_pid = self.cb_milestone_project.currentData()
        filtered = []
        for m in self.cached_milestones:
            if sel_pid and m.get("project_id") != sel_pid:
                continue
            filtered.append(m)
        self.populate_milestones_table(filtered)

    def populate_milestones_table(self, milestones: List[Dict[str, Any]]):
        self.table_milestones.setRowCount(0)
        prj_map = {p.get("id"): p.get("project_code") for p in self.cached_projects}

        for row, m in enumerate(milestones):
            self.table_milestones.insertRow(row)

            item_prj = QTableWidgetItem(prj_map.get(m.get("project_id"), m.get("project_id", "")))
            item_prj.setTextAlignment(Qt.AlignCenter)
            item_title = QTableWidgetItem(m.get("title", ""))

            due_str = str(m.get("due_date", "")) if m.get("due_date") else "-"
            item_due = QTableWidgetItem(due_str)
            item_due.setTextAlignment(Qt.AlignCenter)

            amt = to_decimal(m.get("milestone_amount", 0))
            item_amt = QTableWidgetItem(f"₹{amt:,.2f}")
            item_amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            st = m.get("status", "PENDING").upper()
            item_st = QTableWidgetItem(st)
            item_st.setTextAlignment(Qt.AlignCenter)
            if st == "INVOICED":
                item_st.setForeground(Qt.darkGreen)
            elif st == "ACHIEVED":
                item_st.setForeground(Qt.blue)
            elif st == "IN_PROGRESS":
                item_st.setForeground(Qt.darkCyan)
            else:
                item_st.setForeground(Qt.darkYellow)

            inv_ref = m.get("invoice_id") or "-"
            item_inv = QTableWidgetItem(inv_ref)
            item_inv.setTextAlignment(Qt.AlignCenter)

            ach_str = str(m.get("achieved_at", ""))[:10] if m.get("achieved_at") else "-"
            item_ach = QTableWidgetItem(ach_str)
            item_ach.setTextAlignment(Qt.AlignCenter)

            pid = m.get("project_id", "")
            mid = m.get("id", "")

            # Action buttons depending on state
            if st == "ACHIEVED":
                btn_act = QPushButton("⚡ Invoice & Post GL")
                btn_act.setStyleSheet("padding: 4px 10px; font-size: 11px; background-color: #10B981; color: white; font-weight: 600;")
                btn_act.clicked.connect(lambda _, p=pid, mi=mid, am=amt, ti=m.get("title", ""): self.open_invoice_milestone_dialog(p, mi, am, ti))
                self.table_milestones.setCellWidget(row, 7, btn_act)
            elif st in ("PENDING", "IN_PROGRESS"):
                btn_act = QPushButton("Sign Off Achieved")
                btn_act.setStyleSheet("padding: 4px 8px; font-size: 11px;")
                btn_act.clicked.connect(lambda _, p=pid, mi=mid: self.mark_milestone_achieved(p, mi))
                self.table_milestones.setCellWidget(row, 7, btn_act)
            else:
                lbl_done = QLabel("✅ GL Invoiced")
                lbl_done.setAlignment(Qt.AlignCenter)
                lbl_done.setStyleSheet("color: #10B981; font-weight: 600; font-size: 11px;")
                self.table_milestones.setCellWidget(row, 7, lbl_done)

            self.table_milestones.setItem(row, 0, item_prj)
            self.table_milestones.setItem(row, 1, item_title)
            self.table_milestones.setItem(row, 2, item_due)
            self.table_milestones.setItem(row, 3, item_amt)
            self.table_milestones.setItem(row, 4, item_st)
            self.table_milestones.setItem(row, 5, item_inv)
            self.table_milestones.setItem(row, 6, item_ach)

    def mark_milestone_achieved(self, project_id: str, milestone_id: str):
        try:
            api_client.mark_milestone_achieved(project_id, milestone_id)
            QMessageBox.information(self, "Milestone Achieved", "Milestone deliverable signed off successfully. You can now generate a customer tax invoice and post GL revenue.")
            self.refresh_data()
        except Exception as e:
            QMessageBox.warning(self, "Milestone Signoff Error", str(e))

    def open_invoice_milestone_dialog(self, project_id: str, milestone_id: str, amount: Decimal, title: str):
        dialog = QDialog(self)
        dialog.setWindowTitle("Milestone Customer Invoicing & GL Revenue Recognition")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        # Lookup project info
        prj = next((p for p in self.cached_projects if p.get("id") == project_id), {})
        cust_id = prj.get("customer_id", "cust_direct_01")
        cust_name = prj.get("customer_name", "Enterprise Client")

        # Tax calculations
        calc = calculate_milestone_invoice(amount, Decimal("18.00"))
        subtotal = calc["subtotal"]
        tax = calc["tax_amount"]
        total = calc["total_amount"]

        info_box = QGroupBox("Invoice Deliverable & Accounting Ledger Entry")
        ib_layout = QVBoxLayout(info_box)
        ib_text = (
            f"<b>Milestone:</b> {title}<br>"
            f"<b>Client:</b> {cust_name} ({cust_id})<br><br>"
            f"<b>Billing Breakdown:</b><br>"
            f"• Milestone Deliverable Subtotal: <b>₹{subtotal:,.2f}</b><br>"
            f"• Statutory GST (18.0%): <b>₹{tax:,.2f}</b><br>"
            f"• Total Customer Invoice: <b style='color: #10B981;'>₹{total:,.2f}</b><br><br>"
            f"<b>Synchronous Double-Entry General Ledger Postings:</b><br>"
            f"&nbsp;&nbsp;[DR] <b>1020 - Accounts Receivable:</b> ₹{total:,.2f}<br>"
            f"&nbsp;&nbsp;[CR] <b>4040 - Service & Event Fee Revenue:</b> ₹{subtotal:,.2f}<br>"
            f"&nbsp;&nbsp;[CR] <b>2020 - GST Output Tax Payable (18%):</b> ₹{tax:,.2f}"
        )
        lbl_info = QLabel(ib_text)
        lbl_info.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MAIN}; line-height: 1.5;")
        ib_layout.addWidget(lbl_info)
        layout.addWidget(info_box)

        form = QFormLayout()
        dt_inv = QDateEdit()
        dt_inv.setDate(QDate.currentDate())
        dt_inv.setCalendarPopup(True)

        txt_notes = QLineEdit("Progress milestone certification billing.")
        form.addRow("Invoice Date:", dt_inv)
        form.addRow("Notes / Memo:", txt_notes)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        btn_post = QPushButton("⚡ Post Customer Invoice & GL")
        btn_post.setStyleSheet("background-color: #10B981; color: white; font-weight: 700; padding: 6px 14px;")

        def do_invoice():
            req_data = {
                "customer_id": cust_id,
                "customer_name": cust_name,
                "invoice_date": dt_inv.date().toPython().isoformat(),
                "tax_rate_percent": 18.0,
                "notes": txt_notes.text().strip()
            }
            try:
                res = api_client.invoice_milestone(project_id, milestone_id, req_data)
                QMessageBox.information(
                    self, "Invoice Posted to GL",
                    f"Customer Invoice {res.get('invoice_number', '')} created successfully!\n"
                    f"Total Invoiced: ₹{to_decimal(res.get('total_amount', 0)):,.2f}\n"
                    f"Journal Entry: {res.get('journal_entry_id', '')} posted to General Ledger."
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.warning(dialog, "Invoicing Error", str(e))

        btn_post.clicked.connect(do_invoice)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_post)
        layout.addLayout(btn_row)

        dialog.exec()

    # =========================================================================
    # Tab 4: Timesheets & Billable Hours
    # =========================================================================
    def setup_timesheets_tab(self):
        layout = QVBoxLayout(self.tab_timesheets)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_prj = QLabel("Filter Project:")
        lbl_prj.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        self.cb_timesheet_project = QComboBox()
        self.cb_timesheet_project.addItem("All Projects", None)
        self.cb_timesheet_project.currentIndexChanged.connect(self.filter_timesheets_table)

        btn_log = QPushButton("⏱️ Log Timesheet")
        btn_log.setProperty("class", "btn_primary")
        btn_log.clicked.connect(self.open_log_timesheet_dialog)

        filter_row.addWidget(lbl_prj)
        filter_row.addWidget(self.cb_timesheet_project)
        filter_row.addStretch()
        filter_row.addWidget(btn_log)
        layout.addLayout(filter_row)

        self.table_timesheets = QTableWidget()
        self.table_timesheets.setColumnCount(10)
        self.table_timesheets.setHorizontalHeaderLabels([
            "Work Date", "Project", "Employee", "Hours", "Billable?",
            "Billing Rate", "Cost Rate", "Total Billable", "Labor Cost", "Status"
        ])
        self.table_timesheets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_timesheets.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_timesheets.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_timesheets.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_timesheets.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_timesheets.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.table_timesheets.verticalHeader().setVisible(False)
        self.table_timesheets.setAlternatingRowColors(True)

        layout.addWidget(self.table_timesheets)

    def filter_timesheets_table(self):
        sel_pid = self.cb_timesheet_project.currentData()
        filtered = []
        for ts in self.cached_timesheets:
            if sel_pid and ts.get("project_id") != sel_pid:
                continue
            filtered.append(ts)
        self.populate_timesheets_table(filtered)

    def populate_timesheets_table(self, timesheets: List[Dict[str, Any]]):
        self.table_timesheets.setRowCount(0)
        prj_map = {p.get("id"): p.get("project_code") for p in self.cached_projects}

        for row, ts in enumerate(timesheets):
            self.table_timesheets.insertRow(row)

            wdate_str = str(ts.get("work_date", ""))
            item_date = QTableWidgetItem(wdate_str)
            item_date.setTextAlignment(Qt.AlignCenter)

            item_prj = QTableWidgetItem(prj_map.get(ts.get("project_id"), ts.get("project_id", "")))
            item_prj.setTextAlignment(Qt.AlignCenter)

            item_emp = QTableWidgetItem(ts.get("employee_name", "Employee"))

            hrs = to_decimal(ts.get("hours", 0))
            item_hrs = QTableWidgetItem(f"{hrs:.1f}h")
            item_hrs.setTextAlignment(Qt.AlignCenter)

            is_b = ts.get("is_billable", True)
            item_bill = QTableWidgetItem("YES" if is_b else "NO")
            item_bill.setTextAlignment(Qt.AlignCenter)
            if is_b:
                item_bill.setForeground(Qt.darkGreen)
            else:
                item_bill.setForeground(Qt.darkGray)

            brate = to_decimal(ts.get("hourly_billing_rate", 0))
            item_brate = QTableWidgetItem(f"₹{brate:,.2f}")
            item_brate.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            crate = to_decimal(ts.get("hourly_cost_rate", 0))
            item_crate = QTableWidgetItem(f"₹{crate:,.2f}")
            item_crate.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            tot_b = to_decimal(ts.get("total_billing_amount", 0))
            item_totb = QTableWidgetItem(f"₹{tot_b:,.2f}")
            item_totb.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            tot_c = to_decimal(ts.get("total_cost_amount", 0))
            item_totc = QTableWidgetItem(f"₹{tot_c:,.2f}")
            item_totc.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            st = ts.get("status", "SUBMITTED").upper()
            item_st = QTableWidgetItem(st)
            item_st.setTextAlignment(Qt.AlignCenter)
            if st == "APPROVED":
                item_st.setForeground(Qt.darkGreen)
            else:
                item_st.setForeground(Qt.darkYellow)

            self.table_timesheets.setItem(row, 0, item_date)
            self.table_timesheets.setItem(row, 1, item_prj)
            self.table_timesheets.setItem(row, 2, item_emp)
            self.table_timesheets.setItem(row, 3, item_hrs)
            self.table_timesheets.setItem(row, 4, item_bill)
            self.table_timesheets.setItem(row, 5, item_brate)
            self.table_timesheets.setItem(row, 6, item_crate)
            self.table_timesheets.setItem(row, 7, item_totb)
            self.table_timesheets.setItem(row, 8, item_totc)
            self.table_timesheets.setItem(row, 9, item_st)

    # =========================================================================
    # Tab 5: Direct Expenses & Profitability
    # =========================================================================
    def setup_expenses_tab(self):
        layout = QVBoxLayout(self.tab_expenses)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Profitability & Burn Summary Box
        self.summary_box = QGroupBox("Project Financial Absorption & Burn Rate Analysis")
        sb_layout = QVBoxLayout(self.summary_box)
        self.lbl_burn_summary = QLabel("Loading burn rate calculations...")
        self.lbl_burn_summary.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MAIN}; line-height: 1.5;")
        sb_layout.addWidget(self.lbl_burn_summary)
        layout.addWidget(self.summary_box)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_prj = QLabel("Filter Project:")
        lbl_prj.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        self.cb_expense_project = QComboBox()
        self.cb_expense_project.addItem("All Projects", None)
        self.cb_expense_project.currentIndexChanged.connect(self.filter_expenses_table)

        btn_log = QPushButton("💵 Log Direct Expense")
        btn_log.setProperty("class", "btn_primary")
        btn_log.clicked.connect(self.open_log_expense_dialog)

        filter_row.addWidget(lbl_prj)
        filter_row.addWidget(self.cb_expense_project)
        filter_row.addStretch()
        filter_row.addWidget(btn_log)
        layout.addLayout(filter_row)

        self.table_expenses = QTableWidget()
        self.table_expenses.setColumnCount(7)
        self.table_expenses.setHorizontalHeaderLabels([
            "Date", "Project", "Category", "Description", "Billable?", "Expense Amount", "GL Ref"
        ])
        self.table_expenses.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_expenses.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_expenses.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_expenses.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_expenses.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_expenses.verticalHeader().setVisible(False)
        self.table_expenses.setAlternatingRowColors(True)

        layout.addWidget(self.table_expenses)

    def filter_expenses_table(self):
        sel_pid = self.cb_expense_project.currentData()
        filtered = []
        for e in self.cached_expenses:
            if sel_pid and e.get("project_id") != sel_pid:
                continue
            filtered.append(e)
        self.populate_expenses_table(filtered)

    def populate_expenses_table(self, expenses: List[Dict[str, Any]]):
        self.table_expenses.setRowCount(0)
        prj_map = {p.get("id"): p.get("project_code") for p in self.cached_projects}

        for row, exp in enumerate(expenses):
            self.table_expenses.insertRow(row)

            dt_str = str(exp.get("expense_date", ""))
            item_date = QTableWidgetItem(dt_str)
            item_date.setTextAlignment(Qt.AlignCenter)

            item_prj = QTableWidgetItem(prj_map.get(exp.get("project_id"), exp.get("project_id", "")))
            item_prj.setTextAlignment(Qt.AlignCenter)

            item_cat = QTableWidgetItem(exp.get("category", "OTHER"))
            item_cat.setTextAlignment(Qt.AlignCenter)

            item_desc = QTableWidgetItem(exp.get("description", ""))

            is_b = exp.get("is_billable", True)
            item_bill = QTableWidgetItem("YES" if is_b else "NO")
            item_bill.setTextAlignment(Qt.AlignCenter)

            amt = to_decimal(exp.get("amount", 0))
            item_amt = QTableWidgetItem(f"₹{amt:,.2f}")
            item_amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            ref = exp.get("journal_entry_id") or "DIRECT"
            item_ref = QTableWidgetItem(ref)
            item_ref.setTextAlignment(Qt.AlignCenter)

            self.table_expenses.setItem(row, 0, item_date)
            self.table_expenses.setItem(row, 1, item_prj)
            self.table_expenses.setItem(row, 2, item_cat)
            self.table_expenses.setItem(row, 3, item_desc)
            self.table_expenses.setItem(row, 4, item_bill)
            self.table_expenses.setItem(row, 5, item_amt)
            self.table_expenses.setItem(row, 6, item_ref)

    def update_profitability_summary(self):
        m = self.cached_metrics
        tot_budget = to_decimal(m.get("total_budget", 0))
        tot_billed = to_decimal(m.get("total_billed", 0))
        tot_cost = to_decimal(m.get("total_actual_cost", 0))
        burn_rate = to_decimal(m.get("burn_rate_percent", 0))
        util = to_decimal(m.get("billable_utilization_percent", 0))

        gross_margin = tot_billed - tot_cost
        margin_pct = (gross_margin / tot_billed * Decimal("100.00")) if tot_billed > Decimal("0") else Decimal("0")

        text = (
            f"<b>Active Portfolio Performance:</b><br>"
            f"• Total Contract Budget: <b>₹{tot_budget:,.2f}</b> | Recognized Revenue: <b>₹{tot_billed:,.2f}</b><br>"
            f"• Incurred Delivery Costs: <b>₹{tot_cost:,.2f}</b> (Burn Rate: <b>{burn_rate:.1f}%</b> of baseline scope)<br>"
            f"• Realized Gross Margin: <b style='color: #10B981;'>₹{gross_margin:,.2f}</b> ({margin_pct:.1f}% gross margin)<br>"
            f"• Professional Services Billable Staff Utilization: <b>{util:.1f}%</b>"
        )
        self.lbl_burn_summary.setText(text)

    # =========================================================================
    # Data Refresh & API Integration
    # =========================================================================
    def refresh_data(self):
        try:
            self.cached_projects = api_client.get_projects()
            self.cached_metrics = api_client.get_project_metrics()

            # Collect all milestones, tasks, timesheets, expenses
            all_milestones = []
            all_tasks = []
            all_timesheets = []
            all_expenses = []

            for p in self.cached_projects:
                pid = p.get("id")
                all_milestones.extend(api_client.get_project_milestones(pid))
                all_tasks.extend(api_client.get_project_tasks(pid))
                all_timesheets.extend(api_client.get_project_timesheets(pid))
                all_expenses.extend(api_client.get_project_expenses(pid))

            self.cached_milestones = all_milestones
            self.cached_tasks = all_tasks
            self.cached_timesheets = all_timesheets
            self.cached_expenses = all_expenses
        except Exception:
            pass

        # Update metric cards
        m = self.cached_metrics
        self.card_active_projects.value_label.setText(f"{m.get('active_projects', 0)} Projects")
        self.card_total_contract.value_label.setText(f"₹{to_decimal(m.get('total_budget', 0)):,.2f}")
        self.card_total_billed.value_label.setText(f"₹{to_decimal(m.get('total_billed', 0)):,.2f}")
        self.card_logged_hours.value_label.setText(f"{to_decimal(m.get('total_hours_logged', 0)):.1f} hrs")
        self.card_billable_util.value_label.setText(f"{to_decimal(m.get('billable_utilization_percent', 0)):.1f}%")

        # Update Project filter dropdowns in tabs 2, 3, 4, 5
        self.populate_project_dropdowns()

        # Update tables
        self.populate_projects_table(self.cached_projects)
        self.filter_tasks_table()
        self.filter_milestones_table()
        self.filter_timesheets_table()
        self.filter_expenses_table()
        self.update_profitability_summary()

    def populate_project_dropdowns(self):
        dropdowns = [
            self.cb_task_project,
            self.cb_milestone_project,
            self.cb_timesheet_project,
            self.cb_expense_project
        ]
        for cb in dropdowns:
            curr_id = cb.currentData()
            cb.blockSignals(True)
            cb.clear()
            cb.addItem("All Projects", None)
            for p in self.cached_projects:
                cb.addItem(f"{p.get('project_code')} - {p.get('name')}", p.get("id"))
            # Restore selection if exists
            idx = cb.findData(curr_id)
            if idx >= 0:
                cb.setCurrentIndex(idx)
            cb.blockSignals(False)

    # =========================================================================
    # Modals / Dialogs
    # =========================================================================
    def open_create_project_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register New Project Portfolio")
        dialog.setMinimumWidth(480)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        txt_name = QLineEdit()
        txt_name.setPlaceholderText("e.g. Presidential Suite IoT Automation")

        txt_desc = QTextEdit()
        txt_desc.setMaximumHeight(60)
        txt_desc.setPlaceholderText("Brief project scope & objectives...")

        txt_cust = QLineEdit("Heritage Hospitality Trust")
        txt_pm = QLineEdit("Siddharth Verma (PM)")

        cb_btype = QComboBox()
        cb_btype.addItems(["MILESTONE_BASED", "TIME_AND_MATERIALS", "FIXED_PRICE", "NON_BILLABLE"])

        cb_pri = QComboBox()
        cb_pri.addItems(["NORMAL", "HIGH", "URGENT", "LOW"])

        spn_budget = QDoubleSpinBox()
        spn_budget.setRange(1000, 50000000)
        spn_budget.setValue(1000000.0)

        dt_start = QDateEdit(QDate.currentDate())
        dt_start.setCalendarPopup(True)

        dt_end = QDateEdit(QDate.currentDate().addDays(60))
        dt_end.setCalendarPopup(True)

        form.addRow("Project Name *:", txt_name)
        form.addRow("Description:", txt_desc)
        form.addRow("Client / Customer *:", txt_cust)
        form.addRow("Project Manager *:", txt_pm)
        form.addRow("Billing Type:", cb_btype)
        form.addRow("Priority:", cb_pri)
        form.addRow("Contract Budget (₹) *:", spn_budget)
        form.addRow("Start Date:", dt_start)
        form.addRow("Target End Date:", dt_end)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        btn_save = QPushButton("➕ Create Project")
        btn_save.setProperty("class", "btn_primary")

        def save():
            name = txt_name.text().strip()
            cust = txt_cust.text().strip()
            pm = txt_pm.text().strip()
            if not name or not cust or not pm:
                QMessageBox.warning(dialog, "Missing Fields", "Please specify Project Name, Customer, and Project Manager.")
                return

            prop_id = self.cached_projects[0].get("property_id") if self.cached_projects else "prop_mdu_resort"
            org_id = self.cached_projects[0].get("organization_id") if self.cached_projects else "org_victory_crest"

            payload = {
                "organization_id": org_id,
                "property_id": prop_id,
                "name": name,
                "description": txt_desc.toPlainText().strip(),
                "customer_name": cust,
                "project_manager_name": pm,
                "billing_type": cb_btype.currentText(),
                "priority": cb_pri.currentText(),
                "budget_amount": float(spn_budget.value()),
                "start_date": dt_start.date().toPython().isoformat(),
                "end_date": dt_end.date().toPython().isoformat()
            }
            try:
                created = api_client.create_project(payload)
                QMessageBox.information(self, "Project Created", f"Project {created.get('project_code', '')} created successfully!")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.warning(dialog, "Creation Error", str(e))

        btn_save.clicked.connect(save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_update_project_dialog(self, project_id: str):
        prj = next((p for p in self.cached_projects if p.get("id") == project_id), None)
        if not prj:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Update Project: {prj.get('project_code')}")
        dialog.setMinimumWidth(420)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        cb_st = QComboBox()
        cb_st.addItems(["PLANNING", "ACTIVE", "ON_HOLD", "COMPLETED", "CANCELLED"])
        cb_st.setCurrentText(prj.get("status", "ACTIVE"))

        spn_prog = QDoubleSpinBox()
        spn_prog.setRange(0, 100)
        spn_prog.setValue(float(to_decimal(prj.get("progress_percent", 0))))

        form.addRow("Project Code:", QLabel(prj.get("project_code", "")))
        form.addRow("Project Title:", QLabel(prj.get("name", "")))
        form.addRow("Execution Status:", cb_st)
        form.addRow("Progress (%):", spn_prog)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        btn_save = QPushButton("Save Updates")
        btn_save.setProperty("class", "btn_primary")

        def save():
            update_data = {
                "status": cb_st.currentText(),
                "progress_percent": float(spn_prog.value())
            }
            try:
                api_client.update_project(project_id, update_data)
                QMessageBox.information(self, "Project Updated", f"Project {prj.get('project_code')} updated successfully.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.warning(dialog, "Update Error", str(e))

        btn_save.clicked.connect(save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_create_task_dialog(self):
        if not self.cached_projects:
            QMessageBox.warning(self, "No Projects", "Please create a project first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add WBS Task Deliverable")
        dialog.setMinimumWidth(440)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        cb_prj = QComboBox()
        for p in self.cached_projects:
            cb_prj.addItem(f"{p.get('project_code')} - {p.get('name')}", p.get("id"))

        txt_title = QLineEdit()
        txt_title.setPlaceholderText("e.g. Install Acoustic Ceiling Baffles")

        txt_staff = QLineEdit("Kavitha Ramanathan")

        spn_est = QDoubleSpinBox()
        spn_est.setRange(1, 500)
        spn_est.setValue(16.0)

        cb_pri = QComboBox()
        cb_pri.addItems(["NORMAL", "HIGH", "URGENT", "LOW"])

        dt_due = QDateEdit(QDate.currentDate().addDays(14))
        dt_due.setCalendarPopup(True)

        form.addRow("Target Project *:", cb_prj)
        form.addRow("Task Title *:", txt_title)
        form.addRow("Assigned Staff:", txt_staff)
        form.addRow("Estimated Hours:", spn_est)
        form.addRow("Priority:", cb_pri)
        form.addRow("Due Date:", dt_due)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        btn_save = QPushButton("➕ Add Task")
        btn_save.setProperty("class", "btn_primary")

        def save():
            title = txt_title.text().strip()
            if not title:
                QMessageBox.warning(dialog, "Missing Title", "Please enter a Task Title.")
                return
            pid = cb_prj.currentData()
            payload = {
                "title": title,
                "assigned_to_name": txt_staff.text().strip() or "Unassigned",
                "estimated_hours": float(spn_est.value()),
                "priority": cb_pri.currentText(),
                "due_date": dt_due.date().toPython().isoformat()
            }
            try:
                res = api_client.create_project_task(pid, payload)
                QMessageBox.information(self, "Task Created", f"Task {res.get('task_code', '')} added to project.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.warning(dialog, "Task Error", str(e))

        btn_save.clicked.connect(save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_create_milestone_dialog(self):
        if not self.cached_projects:
            QMessageBox.warning(self, "No Projects", "Please create a project first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Contractual Milestone")
        dialog.setMinimumWidth(440)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        cb_prj = QComboBox()
        for p in self.cached_projects:
            cb_prj.addItem(f"{p.get('project_code')} - {p.get('name')}", p.get("id"))

        txt_title = QLineEdit()
        txt_title.setPlaceholderText("e.g. Stage 2 Rigging Certification")

        spn_amt = QDoubleSpinBox()
        spn_amt.setRange(1000, 10000000)
        spn_amt.setValue(250000.0)

        dt_due = QDateEdit(QDate.currentDate().addDays(30))
        dt_due.setCalendarPopup(True)

        form.addRow("Target Project *:", cb_prj)
        form.addRow("Milestone Deliverable *:", txt_title)
        form.addRow("Billing Amount (₹) *:", spn_amt)
        form.addRow("Due Date:", dt_due)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        btn_save = QPushButton("🎯 Create Milestone")
        btn_save.setProperty("class", "btn_primary")

        def save():
            title = txt_title.text().strip()
            if not title:
                QMessageBox.warning(dialog, "Missing Title", "Please enter a Milestone Title.")
                return
            pid = cb_prj.currentData()
            payload = {
                "title": title,
                "milestone_amount": float(spn_amt.value()),
                "due_date": dt_due.date().toPython().isoformat()
            }
            try:
                res = api_client.create_project_milestone(pid, payload)
                QMessageBox.information(self, "Milestone Created", f"Milestone '{res.get('title')}' created.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.warning(dialog, "Milestone Error", str(e))

        btn_save.clicked.connect(save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_log_timesheet_dialog(self):
        if not self.cached_projects:
            QMessageBox.warning(self, "No Projects", "Please create a project first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Log Billable Labor Timesheet")
        dialog.setMinimumWidth(450)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        cb_prj = QComboBox()
        for p in self.cached_projects:
            cb_prj.addItem(f"{p.get('project_code')} - {p.get('name')}", p.get("id"))

        txt_emp = QLineEdit("Kavitha Ramanathan")

        spn_hrs = QDoubleSpinBox()
        spn_hrs.setRange(0.5, 24)
        spn_hrs.setValue(8.0)

        chk_bill = QCheckBox("Yes, this labor is billable to the client")
        chk_bill.setChecked(True)

        spn_brate = QDoubleSpinBox()
        spn_brate.setRange(0, 10000)
        spn_brate.setValue(2500.0)

        spn_crate = QDoubleSpinBox()
        spn_crate.setRange(0, 5000)
        spn_crate.setValue(850.0)

        dt_work = QDateEdit(QDate.currentDate())
        dt_work.setCalendarPopup(True)

        txt_desc = QLineEdit("Engineering installation and verification.")

        form.addRow("Project *:", cb_prj)
        form.addRow("Staff Member *:", txt_emp)
        form.addRow("Work Date:", dt_work)
        form.addRow("Hours Logged *:", spn_hrs)
        form.addRow("Billable:", chk_bill)
        form.addRow("Billing Rate (₹/hr):", spn_brate)
        form.addRow("Internal Cost (₹/hr):", spn_crate)
        form.addRow("Description:", txt_desc)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        btn_save = QPushButton("⏱️ Record Timesheet")
        btn_save.setProperty("class", "btn_primary")

        def save():
            pid = cb_prj.currentData()
            payload = {
                "employee_name": txt_emp.text().strip() or "Staff",
                "work_date": dt_work.date().toPython().isoformat(),
                "hours": float(spn_hrs.value()),
                "is_billable": chk_bill.isChecked(),
                "hourly_billing_rate": float(spn_brate.value()),
                "hourly_cost_rate": float(spn_crate.value()),
                "description": txt_desc.text().strip()
            }
            try:
                res = api_client.log_project_timesheet(pid, payload)
                QMessageBox.information(self, "Timesheet Recorded", f"Logged {res.get('hours')}h against project.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.warning(dialog, "Timesheet Error", str(e))

        btn_save.clicked.connect(save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_log_expense_dialog(self):
        if not self.cached_projects:
            QMessageBox.warning(self, "No Projects", "Please create a project first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Log Direct Project Expense")
        dialog.setMinimumWidth(450)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        cb_prj = QComboBox()
        for p in self.cached_projects:
            cb_prj.addItem(f"{p.get('project_code')} - {p.get('name')}", p.get("id"))

        cb_cat = QComboBox()
        cb_cat.addItems(["MATERIALS", "SUBCONTRACTOR", "EQUIPMENT", "TRAVEL", "PERMITS", "OTHER"])

        spn_amt = QDoubleSpinBox()
        spn_amt.setRange(10, 5000000)
        spn_amt.setValue(25000.0)

        chk_bill = QCheckBox("Yes, billable back to client")
        chk_bill.setChecked(True)

        dt_exp = QDateEdit(QDate.currentDate())
        dt_exp.setCalendarPopup(True)

        txt_desc = QLineEdit("Rigging safety equipment rental and harness set.")

        form.addRow("Project *:", cb_prj)
        form.addRow("Category *:", cb_cat)
        form.addRow("Expense Amount (₹) *:", spn_amt)
        form.addRow("Billable:", chk_bill)
        form.addRow("Expense Date:", dt_exp)
        form.addRow("Description *:", txt_desc)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        btn_save = QPushButton("💵 Record Expense")
        btn_save.setProperty("class", "btn_primary")

        def save():
            desc = txt_desc.text().strip()
            if not desc:
                QMessageBox.warning(dialog, "Missing Description", "Please enter an Expense Description.")
                return
            pid = cb_prj.currentData()
            payload = {
                "category": cb_cat.currentText(),
                "amount": float(spn_amt.value()),
                "is_billable": chk_bill.isChecked(),
                "expense_date": dt_exp.date().toPython().isoformat(),
                "description": desc
            }
            try:
                res = api_client.log_project_expense(pid, payload)
                QMessageBox.information(self, "Expense Recorded", f"Expense of ₹{to_decimal(res.get('amount', 0)):,.2f} recorded.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.warning(dialog, "Expense Error", str(e))

        btn_save.clicked.connect(save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        dialog.exec()
