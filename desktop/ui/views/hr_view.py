"""Victory Crest One - Human Resources & Payroll Desktop View
Staff Directory, Shift Attendance, Leave Approvals, Statutory Salary Structures,
Batch Payroll Processing, Automated GL Postings, and Itemized Payslips.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDoubleSpinBox, QDateEdit, QTextEdit, QScrollArea,
    QSpinBox, QGroupBox
)
from PySide6.QtCore import Qt, QDate

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from shared.calculations import to_decimal, calculate_salary_breakdown


class HrPayrollView(QWidget):
    """Central Human Resources, Shift Attendance & Payroll Management Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_employees: List[Dict[str, Any]] = []
        self.cached_attendance: List[Dict[str, Any]] = []
        self.cached_leaves: List[Dict[str, Any]] = []
        self.cached_runs: List[Dict[str, Any]] = []

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

        title = QLabel("Human Resources & Payroll Management")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Staff master directory, shift rosters, leave requests, statutory salary breakdown, and automated GL payroll disbursements.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)
        header_row.addWidget(btn_refresh)

        btn_apply_leave = QPushButton("🏖️ Apply Leave")
        btn_apply_leave.setProperty("class", "btn_secondary")
        btn_apply_leave.clicked.connect(self.open_apply_leave_dialog)
        header_row.addWidget(btn_apply_leave)

        btn_onboard = QPushButton("➕ Onboard Employee")
        btn_onboard.setProperty("class", "btn_primary")
        btn_onboard.clicked.connect(self.open_onboard_employee_dialog)
        header_row.addWidget(btn_onboard)

        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive KPI Summary Cards
        # -----------------------------------------------------
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_headcount = self.create_summary_card("Total Headcount", "0 Staff", "Active Personnel", ThemeColors.PRIMARY_LIGHT)
        self.kpi_attendance = self.create_summary_card("Today's Attendance", "0.00 %", "Shift Check-in Rate", ThemeColors.STATUS_SUCCESS)
        self.kpi_payroll_cost = self.create_summary_card("Monthly Payroll Cost", "₹0.00", "Gross Compensation", ThemeColors.STATUS_WARNING)
        self.kpi_pending_leaves = self.create_summary_card("Pending Leaves", "0 Requests", "Awaiting Approval", ThemeColors.ACCENT_PRIMARY)
        self.kpi_net_disbursed = self.create_summary_card("Net Disbursed (MTD)", "₹0.00", "Direct Salary Transfers", ThemeColors.STATUS_SUCCESS)

        kpi_row.addWidget(self.kpi_headcount)
        kpi_row.addWidget(self.kpi_attendance)
        kpi_row.addWidget(self.kpi_payroll_cost)
        kpi_row.addWidget(self.kpi_pending_leaves)
        kpi_row.addWidget(self.kpi_net_disbursed)
        main_layout.addLayout(kpi_row)

        # -----------------------------------------------------
        # 3. Main Navigation Tabs
        # -----------------------------------------------------
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                background: {ThemeColors.BG_SURFACE};
                border-radius: 8px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {ThemeColors.BG_SECONDARY};
                color: {ThemeColors.TEXT_MUTED};
                padding: 10px 18px;
                margin-right: 4px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {ThemeColors.BG_SURFACE};
                color: {ThemeColors.PRIMARY_LIGHT};
                border-bottom: 2px solid {ThemeColors.PRIMARY_LIGHT};
            }}
        """)

        # Tab 1: Staff Directory
        tab_directory = self.build_directory_tab()
        self.tabs.addTab(tab_directory, "👥 Staff Directory")

        # Tab 2: Shift Attendance
        tab_attendance = self.build_attendance_tab()
        self.tabs.addTab(tab_attendance, "🕒 Shift Attendance")

        # Tab 3: Leave Management
        tab_leaves = self.build_leaves_tab()
        self.tabs.addTab(tab_leaves, "🏖️ Leave Requests")

        # Tab 4: Monthly Payroll Processing
        tab_payroll = self.build_payroll_tab()
        self.tabs.addTab(tab_payroll, "💵 Payroll Runs & GL Posting")

        # Tab 5: Payslips Viewer
        tab_payslips = self.build_payslips_tab()
        self.tabs.addTab(tab_payslips, "📑 Payslips & Compensation")

        main_layout.addWidget(self.tabs)

    def create_summary_card(self, title: str, value: str, subtext: str, color_accent: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ThemeColors.TEXT_MUTED};")
        layout.addWidget(t_lbl)

        v_lbl = QLabel(value)
        v_lbl.setObjectName("kpi_value")
        v_lbl.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {color_accent};")
        layout.addWidget(v_lbl)

        s_lbl = QLabel(subtext)
        s_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        layout.addWidget(s_lbl)
        return card

    # ---------------------------------------------------------
    # TAB 1: Staff Directory
    # ---------------------------------------------------------
    def build_directory_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.emp_search = QLineEdit()
        self.emp_search.setPlaceholderText("🔍 Search by staff name, code, or designation...")
        self.emp_search.textChanged.connect(self.filter_employee_table)
        ctrl_row.addWidget(self.emp_search, 2)

        lbl_dept = QLabel("Department:")
        lbl_dept.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_dept)

        self.emp_dept_combo = QComboBox()
        self.emp_dept_combo.addItems([
            "All Departments", "Front Office & Concierge", "Culinary & F&B Service",
            "Housekeeping & Facilities", "Finance & General Accounting",
            "Sales & Revenue Optimization", "Engineering & Asset Maintenance"
        ])
        self.emp_dept_combo.currentIndexChanged.connect(self.filter_employee_table)
        ctrl_row.addWidget(self.emp_dept_combo, 2)

        lbl_st = QLabel("Status:")
        lbl_st.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_st)

        self.emp_status_combo = QComboBox()
        self.emp_status_combo.addItems(["All Statuses", "ACTIVE", "ON_LEAVE", "PROBATION", "TERMINATED"])
        self.emp_status_combo.currentIndexChanged.connect(self.filter_employee_table)
        ctrl_row.addWidget(self.emp_status_combo, 1)

        btn_view_salary = QPushButton("👁️ View Salary Structure")
        btn_view_salary.setProperty("class", "btn_secondary")
        btn_view_salary.clicked.connect(self.view_selected_employee_salary)
        ctrl_row.addWidget(btn_view_salary)

        layout.addLayout(ctrl_row)

        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(8)
        self.emp_table.setHorizontalHeaderLabels([
            "Employee Code", "Full Name", "Department", "Designation",
            "Type", "Monthly Gross", "Status", "Contact Phone"
        ])
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.emp_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.emp_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.emp_table.setAlternatingRowColors(True)
        self.emp_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.emp_table)

        return container

    # ---------------------------------------------------------
    # TAB 2: Shift Attendance & Rosters
    # ---------------------------------------------------------
    def build_attendance_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Quick Clock-In / Clock-Out Station
        station_box = QGroupBox("🕒 Quick Shift Clock-In / Clock-Out Station")
        station_layout = QHBoxLayout(station_box)
        station_layout.setSpacing(10)

        lbl_emp = QLabel("Select Staff:")
        lbl_emp.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        station_layout.addWidget(lbl_emp)

        self.att_emp_combo = QComboBox()
        self.att_emp_combo.setMinimumWidth(260)
        station_layout.addWidget(self.att_emp_combo)

        lbl_sh = QLabel("Shift:")
        lbl_sh.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        station_layout.addWidget(lbl_sh)

        self.att_shift_combo = QComboBox()
        self.att_shift_combo.addItems(["MORNING (09:00 - 18:00)", "EVENING (14:00 - 23:00)", "NIGHT (22:00 - 07:00)"])
        station_layout.addWidget(self.att_shift_combo)

        btn_clock_in = QPushButton("🟢 Clock In")
        btn_clock_in.setProperty("class", "btn_primary")
        btn_clock_in.clicked.connect(self.execute_quick_clock_in)
        station_layout.addWidget(btn_clock_in)

        btn_clock_out = QPushButton("🔴 Clock Out")
        btn_clock_out.setProperty("class", "btn_secondary")
        btn_clock_out.clicked.connect(self.execute_quick_clock_out)
        station_layout.addWidget(btn_clock_out)

        station_layout.addStretch()
        layout.addWidget(station_box)

        # Attendance Table
        self.att_table = QTableWidget()
        self.att_table.setColumnCount(8)
        self.att_table.setHorizontalHeaderLabels([
            "Date", "Employee Code", "Staff Name", "Shift",
            "Clock In", "Clock Out", "Work Hours", "Status"
        ])
        self.att_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.att_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.att_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.att_table.setAlternatingRowColors(True)
        self.att_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.att_table)

        return container

    # ---------------------------------------------------------
    # TAB 3: Leave Management
    # ---------------------------------------------------------
    def build_leaves_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        ctrl_row = QHBoxLayout()
        lbl_l_stat = QLabel("Filter Status:")
        lbl_l_stat.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_l_stat)

        self.leave_status_combo = QComboBox()
        self.leave_status_combo.addItems(["All Leaves", "PENDING", "APPROVED", "REJECTED"])
        self.leave_status_combo.currentIndexChanged.connect(self.populate_leaves_table)
        ctrl_row.addWidget(self.leave_status_combo)
        ctrl_row.addStretch()

        btn_reject = QPushButton("❌ Reject Selected")
        btn_reject.setProperty("class", "btn_secondary")
        btn_reject.clicked.connect(lambda: self.review_selected_leave("REJECTED"))
        ctrl_row.addWidget(btn_reject)

        btn_approve = QPushButton("✅ Approve Selected")
        btn_approve.setProperty("class", "btn_primary")
        btn_approve.clicked.connect(lambda: self.review_selected_leave("APPROVED"))
        ctrl_row.addWidget(btn_approve)

        layout.addLayout(ctrl_row)

        self.leave_table = QTableWidget()
        self.leave_table.setColumnCount(8)
        self.leave_table.setHorizontalHeaderLabels([
            "Employee Code", "Staff Name", "Type", "Start Date",
            "End Date", "Days", "Reason", "Status"
        ])
        self.leave_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.leave_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.leave_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.leave_table.setAlternatingRowColors(True)
        self.leave_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.leave_table)

        return container

    # ---------------------------------------------------------
    # TAB 4: Monthly Payroll Processing & GL Postings
    # ---------------------------------------------------------
    def build_payroll_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        ctrl_row = QHBoxLayout()
        lbl_pr = QLabel("Monthly Enterprise Compensation Runs:")
        lbl_pr.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_pr)
        ctrl_row.addStretch()

        btn_new_run = QPushButton("➕ Calculate New Payroll Batch")
        btn_new_run.setProperty("class", "btn_secondary")
        btn_new_run.clicked.connect(self.open_new_payroll_dialog)
        ctrl_row.addWidget(btn_new_run)

        btn_disburse = QPushButton("🏦 Disburse Payroll & Post to GL")
        btn_disburse.setProperty("class", "btn_primary")
        btn_disburse.clicked.connect(self.disburse_selected_payroll_run)
        ctrl_row.addWidget(btn_disburse)

        layout.addLayout(ctrl_row)

        self.run_table = QTableWidget()
        self.run_table.setColumnCount(9)
        self.run_table.setHorizontalHeaderLabels([
            "Run Code", "Period", "Total Staff", "Gross Compensation",
            "Statutory Deductions", "Net Disbursement", "Status", "GL Ref", "Disbursed At"
        ])
        self.run_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.run_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.run_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.run_table.setAlternatingRowColors(True)
        self.run_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.run_table)

        return container

    # ---------------------------------------------------------
    # TAB 5: Payslips & Compensation Viewer
    # ---------------------------------------------------------
    def build_payslips_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        ctrl_row = QHBoxLayout()
        lbl_run = QLabel("Select Payroll Run:")
        lbl_run.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_run)

        self.payslip_run_combo = QComboBox()
        self.payslip_run_combo.currentIndexChanged.connect(self.populate_payslips_table)
        ctrl_row.addWidget(self.payslip_run_combo)
        ctrl_row.addStretch()

        btn_view_slip = QPushButton("🖨️ View Itemized Payslip")
        btn_view_slip.setProperty("class", "btn_primary")
        btn_view_slip.clicked.connect(self.view_selected_payslip)
        ctrl_row.addWidget(btn_view_slip)

        layout.addLayout(ctrl_row)

        self.payslip_table = QTableWidget()
        self.payslip_table.setColumnCount(9)
        self.payslip_table.setHorizontalHeaderLabels([
            "Staff Code", "Staff Name", "Department", "Designation",
            "Gross Earnings", "PF Deduction", "TDS Deduction", "Net Pay", "Status"
        ])
        self.payslip_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payslip_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.payslip_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.payslip_table.setAlternatingRowColors(True)
        self.payslip_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.payslip_table)

        return container

    # ---------------------------------------------------------
    # Data Refresh & Table Population
    # ---------------------------------------------------------
    def refresh_data(self):
        # 1. Fetch Metrics
        metrics = api_client.get_hr_metrics()
        self.update_summary_card(self.kpi_headcount, f"{metrics.get('total_headcount', 0)} Staff")
        self.update_summary_card(self.kpi_attendance, f"{metrics.get('today_attendance_rate', 0):,.2f} %")
        self.update_summary_card(self.kpi_payroll_cost, f"₹{metrics.get('current_month_payroll_cost', 0):,.2f}")
        self.update_summary_card(self.kpi_pending_leaves, f"{metrics.get('pending_leaves_count', 0)} Requests")
        self.update_summary_card(self.kpi_net_disbursed, f"₹{metrics.get('current_month_net_disbursed', 0):,.2f}")

        # 2. Fetch Employees
        self.cached_employees = api_client.get_employees()
        self.populate_employee_table(self.cached_employees)

        # Update attendance station combo
        self.att_emp_combo.blockSignals(True)
        self.att_emp_combo.clear()
        for e in self.cached_employees:
            self.att_emp_combo.addItem(f"{e['employee_code']} — {e['full_name']} ({e['designation']})", e["id"])
        self.att_emp_combo.blockSignals(False)

        # 3. Fetch Attendance
        self.cached_attendance = api_client.get_attendance()
        self.populate_attendance_table()

        # 4. Fetch Leaves
        self.cached_leaves = api_client.get_leaves()
        self.populate_leaves_table()

        # 5. Fetch Payroll Runs
        self.cached_runs = api_client.get_payroll_runs()
        self.populate_payroll_runs_table()

        # Update payslip run combo
        self.payslip_run_combo.blockSignals(True)
        self.payslip_run_combo.clear()
        for r in self.cached_runs:
            self.payslip_run_combo.addItem(f"{r['run_code']} ({r['status']})", r["id"])
        self.payslip_run_combo.blockSignals(False)
        self.populate_payslips_table()

    def update_summary_card(self, card: QFrame, val: str):
        lbl = card.findChild(QLabel, "kpi_value")
        if lbl:
            lbl.setText(val)

    def populate_employee_table(self, emps: List[Dict[str, Any]]):
        self.emp_table.setRowCount(0)
        for e in emps:
            r = self.emp_table.rowCount()
            self.emp_table.insertRow(r)

            code_item = QTableWidgetItem(e.get("employee_code", ""))
            code_item.setData(Qt.UserRole, e)
            code_item.setFont(self._bold_font())

            self.emp_table.setItem(r, 0, code_item)
            self.emp_table.setItem(r, 1, QTableWidgetItem(e.get("full_name", "")))
            self.emp_table.setItem(r, 2, QTableWidgetItem(e.get("department_name", "")))
            self.emp_table.setItem(r, 3, QTableWidgetItem(e.get("designation", "")))
            self.emp_table.setItem(r, 4, QTableWidgetItem(e.get("employment_type", "")))

            sal = to_decimal(e.get("monthly_gross_salary", 0))
            sal_item = QTableWidgetItem(f"₹{sal:,.2f}")
            sal_item.setFont(self._bold_font())
            self.emp_table.setItem(r, 5, sal_item)

            st = e.get("status", "ACTIVE")
            st_item = QTableWidgetItem(st)
            if st == "ACTIVE":
                st_item.setForeground(Qt.green)
            elif st == "ON_LEAVE":
                st_item.setForeground(Qt.yellow)
            else:
                st_item.setForeground(Qt.red)
            self.emp_table.setItem(r, 6, st_item)

            self.emp_table.setItem(r, 7, QTableWidgetItem(e.get("phone") or "N/A"))

    def filter_employee_table(self):
        query = self.emp_search.text().strip().lower()
        dept_filter = self.emp_dept_combo.currentText()
        stat_filter = self.emp_status_combo.currentText()

        filtered = []
        for e in self.cached_employees:
            if dept_filter != "All Departments" and e.get("department_name") != dept_filter:
                continue
            if stat_filter != "All Statuses" and e.get("status") != stat_filter:
                continue
            if query:
                code = e.get("employee_code", "").lower()
                name = e.get("full_name", "").lower()
                desig = e.get("designation", "").lower()
                if query not in code and query not in name and query not in desig:
                    continue
            filtered.append(e)

        self.populate_employee_table(filtered)

    def populate_attendance_table(self):
        self.att_table.setRowCount(0)
        for a in self.cached_attendance:
            r = self.att_table.rowCount()
            self.att_table.insertRow(r)

            self.att_table.setItem(r, 0, QTableWidgetItem(str(a.get("date", ""))))
            self.att_table.setItem(r, 1, QTableWidgetItem(a.get("employee_code", "")))
            self.att_table.setItem(r, 2, QTableWidgetItem(a.get("employee_name", "")))
            self.att_table.setItem(r, 3, QTableWidgetItem(a.get("shift_type", "")))

            cin = a.get("clock_in")
            cin_str = str(cin)[11:16] if cin else "--:--"
            self.att_table.setItem(r, 4, QTableWidgetItem(cin_str))

            cout = a.get("clock_out")
            cout_str = str(cout)[11:16] if cout else "--:--"
            self.att_table.setItem(r, 5, QTableWidgetItem(cout_str))

            hrs = to_decimal(a.get("work_hours", 0))
            ot = to_decimal(a.get("overtime_hours", 0))
            ot_str = f" (+{ot} OT)" if ot > 0 else ""
            self.att_table.setItem(r, 6, QTableWidgetItem(f"{hrs:,.2f} hrs{ot_str}"))

            st = a.get("status", "PRESENT")
            st_item = QTableWidgetItem(st)
            if st == "PRESENT":
                st_item.setForeground(Qt.green)
            elif st == "LATE":
                st_item.setForeground(Qt.yellow)
            else:
                st_item.setForeground(Qt.red)
            self.att_table.setItem(r, 7, st_item)

    def populate_leaves_table(self):
        self.leave_table.setRowCount(0)
        filt = self.leave_status_combo.currentText()

        for l in self.cached_leaves:
            st = l.get("status", "PENDING")
            if filt != "All Leaves" and st != filt:
                continue

            r = self.leave_table.rowCount()
            self.leave_table.insertRow(r)

            code_item = QTableWidgetItem(l.get("employee_code", ""))
            code_item.setData(Qt.UserRole, l)
            code_item.setFont(self._bold_font())

            self.leave_table.setItem(r, 0, code_item)
            self.leave_table.setItem(r, 1, QTableWidgetItem(l.get("employee_name", "")))
            self.leave_table.setItem(r, 2, QTableWidgetItem(l.get("leave_type", "")))
            self.leave_table.setItem(r, 3, QTableWidgetItem(str(l.get("start_date", ""))))
            self.leave_table.setItem(r, 4, QTableWidgetItem(str(l.get("end_date", ""))))
            self.leave_table.setItem(r, 5, QTableWidgetItem(f"{to_decimal(l.get('total_days', 0)):,.1f}"))
            self.leave_table.setItem(r, 6, QTableWidgetItem(l.get("reason", "")))

            st_item = QTableWidgetItem(st)
            if st == "APPROVED":
                st_item.setForeground(Qt.green)
            elif st == "PENDING":
                st_item.setForeground(Qt.yellow)
            else:
                st_item.setForeground(Qt.red)
            self.leave_table.setItem(r, 7, st_item)

    def populate_payroll_runs_table(self):
        self.run_table.setRowCount(0)
        for pr in self.cached_runs:
            r = self.run_table.rowCount()
            self.run_table.insertRow(r)

            code_item = QTableWidgetItem(pr.get("run_code", ""))
            code_item.setData(Qt.UserRole, pr)
            code_item.setFont(self._bold_font())

            self.run_table.setItem(r, 0, code_item)
            period_str = f"{pr.get('month', 0):02d}/{pr.get('year', 0)}"
            self.run_table.setItem(r, 1, QTableWidgetItem(period_str))
            self.run_table.setItem(r, 2, QTableWidgetItem(str(pr.get("total_employees", 0))))

            gross = to_decimal(pr.get("total_gross_earnings", 0))
            ded = to_decimal(pr.get("total_statutory_deductions", 0))
            net = to_decimal(pr.get("total_net_disbursement", 0))

            self.run_table.setItem(r, 3, QTableWidgetItem(f"₹{gross:,.2f}"))
            self.run_table.setItem(r, 4, QTableWidgetItem(f"₹{ded:,.2f}"))

            net_item = QTableWidgetItem(f"₹{net:,.2f}")
            net_item.setFont(self._bold_font())
            net_item.setForeground(Qt.green)
            self.run_table.setItem(r, 5, net_item)

            st = pr.get("status", "DRAFT")
            st_item = QTableWidgetItem(st)
            if st == "DISBURSED":
                st_item.setForeground(Qt.green)
            elif st == "CALCULATED":
                st_item.setForeground(Qt.cyan)
            else:
                st_item.setForeground(Qt.yellow)
            self.run_table.setItem(r, 6, st_item)

            self.run_table.setItem(r, 7, QTableWidgetItem(pr.get("journal_entry_id") or "Pending"))
            self.run_table.setItem(r, 8, QTableWidgetItem(str(pr.get("disbursed_at") or "Pending")[:19]))

    def populate_payslips_table(self):
        self.payslip_table.setRowCount(0)
        run_id = self.payslip_run_combo.currentData()
        if not run_id:
            return

        run_obj = next((r for r in self.cached_runs if r["id"] == run_id), None)
        if not run_obj:
            return

        slips = run_obj.get("payslips", [])
        for ps in slips:
            r = self.payslip_table.rowCount()
            self.payslip_table.insertRow(r)

            code_item = QTableWidgetItem(ps.get("employee_code", ""))
            code_item.setData(Qt.UserRole, ps)
            code_item.setFont(self._bold_font())

            self.payslip_table.setItem(r, 0, code_item)
            self.payslip_table.setItem(r, 1, QTableWidgetItem(ps.get("employee_name", "")))
            self.payslip_table.setItem(r, 2, QTableWidgetItem(ps.get("department_name", "")))
            self.payslip_table.setItem(r, 3, QTableWidgetItem(ps.get("designation", "")))

            gross = to_decimal(ps.get("gross_earnings", 0))
            pf = to_decimal(ps.get("pf_deduction", 0))
            tds = to_decimal(ps.get("tds_deduction", 0))
            net = to_decimal(ps.get("net_pay", 0))

            self.payslip_table.setItem(r, 4, QTableWidgetItem(f"₹{gross:,.2f}"))
            self.payslip_table.setItem(r, 5, QTableWidgetItem(f"₹{pf:,.2f}"))
            self.payslip_table.setItem(r, 6, QTableWidgetItem(f"₹{tds:,.2f}"))

            net_item = QTableWidgetItem(f"₹{net:,.2f}")
            net_item.setFont(self._bold_font())
            net_item.setForeground(Qt.green)
            self.payslip_table.setItem(r, 7, net_item)

            st = ps.get("payment_status", "PENDING")
            st_item = QTableWidgetItem(st)
            if st == "DISBURSED":
                st_item.setForeground(Qt.green)
            else:
                st_item.setForeground(Qt.yellow)
            self.payslip_table.setItem(r, 8, st_item)

    # ---------------------------------------------------------
    # Dialogs & Actions
    # ---------------------------------------------------------
    def open_onboard_employee_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Onboard New Staff Member — Victory Crest ONE")
        dialog.resize(550, 480)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        form = QFormLayout()

        fn_edit = QLineEdit()
        ln_edit = QLineEdit()
        email_edit = QLineEdit()
        phone_edit = QLineEdit()

        form.addRow("First Name:", fn_edit)
        form.addRow("Last Name:", ln_edit)
        form.addRow("Corporate Email:", email_edit)
        form.addRow("Phone Number:", phone_edit)

        dept_combo = QComboBox()
        dept_combo.addItem("Front Office & Concierge", "dep_front_office")
        dept_combo.addItem("Culinary & F&B Service", "dep_culinary_fnb")
        dept_combo.addItem("Housekeeping & Facilities", "dep_housekeeping")
        dept_combo.addItem("Finance & General Accounting", "dep_finance_acc")
        dept_combo.addItem("Sales & Revenue Optimization", "dep_sales_mktg")
        dept_combo.addItem("Engineering & Asset Maintenance", "dep_engineering")
        form.addRow("Department:", dept_combo)

        desig_edit = QLineEdit()
        desig_edit.setPlaceholderText("E.g., Senior Guest Service Agent, Demi Chef de Partie...")
        form.addRow("Designation / Title:", desig_edit)

        type_combo = QComboBox()
        type_combo.addItems(["FULL_TIME", "CONTRACT", "PART_TIME", "INTERN"])
        form.addRow("Employment Type:", type_combo)

        salary_spin = QDoubleSpinBox()
        salary_spin.setRange(10000, 1000000)
        salary_spin.setValue(45000.0)
        salary_spin.setPrefix("₹ ")
        form.addRow("Monthly Gross Salary:", salary_spin)

        pan_edit = QLineEdit()
        pan_edit.setPlaceholderText("ABCDE1234F")
        form.addRow("Income Tax PAN:", pan_edit)

        bank_edit = QLineEdit()
        bank_edit.setPlaceholderText("Account Number (Direct Deposit)")
        form.addRow("Bank Account:", bank_edit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("👤 Complete Onboarding")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            fn = fn_edit.text().strip()
            ln = ln_edit.text().strip()
            em = email_edit.text().strip()
            des = desig_edit.text().strip()
            if not fn or not em or not des:
                QMessageBox.warning(dialog, "Validation Error", "First Name, Email, and Designation are required.")
                return

            payload = {
                "first_name": fn,
                "last_name": ln,
                "email": em,
                "phone": phone_edit.text().strip(),
                "department_id": dept_combo.currentData(),
                "department_name": dept_combo.currentText(),
                "designation": des,
                "employment_type": type_combo.currentText(),
                "status": "ACTIVE",
                "monthly_gross_salary": float(salary_spin.value()),
                "pan_number": pan_edit.text().strip().upper(),
                "bank_account_number": bank_edit.text().strip()
            }
            try:
                res = api_client.create_employee(payload)
                QMessageBox.information(
                    dialog, "Onboarding Complete",
                    f"Staff record created for {res.get('full_name')}!\nEmployee Code: {res.get('employee_code')}"
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Onboarding Error", f"Failed: {str(e)}")

        btn_submit.clicked.connect(submit)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)

        dialog.exec()

    def view_selected_employee_salary(self):
        row = self.emp_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Staff", "Please select an employee to view salary structure.")
            return

        emp_data = self.emp_table.item(row, 0).data(Qt.UserRole)
        if not emp_data:
            return

        brk = calculate_salary_breakdown(emp_data.get("monthly_gross_salary", 0))

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Compensation Structure — {emp_data.get('full_name')}")
        dialog.resize(460, 420)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        header = QLabel(f"👤 {emp_data.get('full_name')} ({emp_data.get('employee_code')})\n{emp_data.get('designation')} • {emp_data.get('department_name')}")
        header.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header)

        form = QFormLayout()
        form.addRow("Monthly Gross Salary:", QLabel(f"₹{brk['gross_salary']:,.2f}"))
        form.addRow("— Basic Salary (50%):", QLabel(f"₹{brk['basic']:,.2f}"))
        form.addRow("— House Rent Allowance (20%):", QLabel(f"₹{brk['hra']:,.2f}"))
        form.addRow("— Conveyance Allowance:", QLabel(f"₹{brk['conveyance']:,.2f}"))
        form.addRow("— Special Allowance:", QLabel(f"₹{brk['special_allowance']:,.2f}"))

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        form.addRow(line)

        form.addRow("PF Deduction (12% of Basic):", QLabel(f"- ₹{brk['pf_deduction']:,.2f}"))
        form.addRow("Professional Tax (PT):", QLabel(f"- ₹{brk['professional_tax']:,.2f}"))
        form.addRow("TDS (Income Tax Deducted):", QLabel(f"- ₹{brk['tds_deduction']:,.2f}"))
        form.addRow("Total Statutory Deductions:", QLabel(f"- ₹{brk['total_deductions']:,.2f}"))

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        form.addRow(line2)

        net_lbl = QLabel(f"₹{brk['net_salary']:,.2f}")
        net_lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {ThemeColors.STATUS_SUCCESS};")
        form.addRow("Net Direct Bank Deposit:", net_lbl)

        layout.addLayout(form)

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "btn_secondary")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.exec()

    def execute_quick_clock_in(self):
        emp_id = self.att_emp_combo.currentData()
        if not emp_id:
            return
        shift_text = self.att_shift_combo.currentText().split()[0]
        try:
            res = api_client.clock_in({
                "employee_id": emp_id,
                "shift_type": shift_text,
                "notes": "Manual station clock-in"
            })
            QMessageBox.information(self, "Clock-In Recorded", f"Clock-in confirmed for {res.get('employee_name')} on {res.get('shift_type')} shift.")
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Clock-In Error", f"Failed: {str(e)}")

    def execute_quick_clock_out(self):
        emp_id = self.att_emp_combo.currentData()
        if not emp_id:
            return
        try:
            res = api_client.clock_out(emp_id, {"notes": "Shift ended"})
            QMessageBox.information(self, "Clock-Out Recorded", f"Shift concluded for {res.get('employee_name')}.\nHours: {res.get('work_hours')} hrs.")
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Clock-Out Error", f"Failed: {str(e)}")

    def open_apply_leave_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Apply Staff Time-Off / Leave — Victory Crest ONE")
        dialog.resize(460, 320)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        form = QFormLayout()

        emp_combo = QComboBox()
        for e in self.cached_employees:
            emp_combo.addItem(f"{e['employee_code']} — {e['full_name']}", e["id"])
        form.addRow("Staff Member:", emp_combo)

        type_combo = QComboBox()
        type_combo.addItems(["CASUAL", "SICK", "EARNED", "UNPAID"])
        form.addRow("Leave Category:", type_combo)

        days_spin = QDoubleSpinBox()
        days_spin.setRange(0.5, 30.0)
        days_spin.setValue(1.0)
        days_spin.setSingleStep(0.5)
        form.addRow("Total Days:", days_spin)

        reason_edit = QLineEdit()
        reason_edit.setPlaceholderText("Reason for leave request...")
        form.addRow("Reason:", reason_edit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("🏖️ Submit Application")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            rsn = reason_edit.text().strip()
            if not rsn:
                QMessageBox.warning(dialog, "Validation Error", "Please provide a reason for the leave.")
                return

            now_d = datetime.utcnow().date()
            payload = {
                "employee_id": emp_combo.currentData(),
                "leave_type": type_combo.currentText(),
                "start_date": str(now_d),
                "end_date": str(now_d),
                "total_days": float(days_spin.value()),
                "reason": rsn
            }
            try:
                api_client.create_leave_request(payload)
                QMessageBox.information(dialog, "Leave Applied", "Leave request submitted for managerial review.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed: {str(e)}")

        btn_submit.clicked.connect(submit)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)

        dialog.exec()

    def review_selected_leave(self, decision: str):
        row = self.leave_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Request", "Please select a leave request row to review.")
            return

        leave_data = self.leave_table.item(row, 0).data(Qt.UserRole)
        if not leave_data:
            return

        if leave_data.get("status") != "PENDING":
            QMessageBox.information(self, "Already Reviewed", f"This leave request is already {leave_data.get('status')}.")
            return

        try:
            api_client.review_leave_request(leave_data["id"], {
                "status": decision,
                "reviewed_by": "General Manager",
                "notes": f"Manager decision: {decision}"
            })
            QMessageBox.information(self, "Decision Recorded", f"Leave request for {leave_data.get('employee_name')} is now {decision}.")
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Review Error", f"Failed: {str(e)}")

    def open_new_payroll_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Calculate Monthly Payroll Batch — Victory Crest ONE")
        dialog.resize(400, 240)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        form = QFormLayout()

        month_spin = QSpinBox()
        month_spin.setRange(1, 12)
        month_spin.setValue(datetime.utcnow().month)
        form.addRow("Payroll Month:", month_spin)

        year_spin = QSpinBox()
        year_spin.setRange(2025, 2030)
        year_spin.setValue(datetime.utcnow().year)
        form.addRow("Payroll Year:", year_spin)

        notes_edit = QLineEdit()
        notes_edit.setPlaceholderText("E.g., October 2026 Monthly Salary Run")
        form.addRow("Batch Notes:", notes_edit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("⚙️ Calculate Batch")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            payload = {
                "month": int(month_spin.value()),
                "year": int(year_spin.value()),
                "notes": notes_edit.text().strip()
            }
            try:
                res = api_client.create_payroll_run(payload)
                QMessageBox.information(
                    dialog, "Payroll Calculated",
                    f"Payroll batch {res.get('run_code')} computed for {res.get('total_employees')} employees!\n"
                    f"Gross Earnings: ₹{res.get('total_gross_earnings', 0):,.2f}\n"
                    f"Net Disbursement: ₹{res.get('total_net_disbursement', 0):,.2f}"
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Calculation Error", f"Failed: {str(e)}")

        btn_submit.clicked.connect(submit)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)

        dialog.exec()

    def disburse_selected_payroll_run(self):
        row = self.run_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Run", "Please select a payroll run to disburse.")
            return

        run_data = self.run_table.item(row, 0).data(Qt.UserRole)
        if not run_data:
            return

        if run_data.get("status") == "DISBURSED":
            QMessageBox.information(self, "Already Disbursed", f"Payroll run {run_data.get('run_code')} is already fully disbursed.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Executive Payroll Disbursement",
            f"Authorize direct salary disbursement for {run_data.get('run_code')}?\n\n"
            f"Total Staff: {run_data.get('total_employees')} Employees\n"
            f"Gross Earnings: ₹{to_decimal(run_data.get('total_gross_earnings', 0)):,.2f}\n"
            f"Statutory Liabilities: ₹{to_decimal(run_data.get('total_statutory_deductions', 0)):,.2f}\n"
            f"Net Direct Deposits: ₹{to_decimal(run_data.get('total_net_disbursement', 0)):,.2f}\n\n"
            f"This will:\n"
            f"1. Mark all individual employee payslips as DISBURSED\n"
            f"2. Automatically post balanced double-entry GL journal entry:\n"
            f"   — DR 6010 Payroll & Staff Compensation\n"
            f"   — CR 2030 Accrued Payroll & Statutory Liabilities\n"
            f"   — CR 1010 Main Operating Account (HDFC Bank)",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                res = api_client.disburse_payroll_run(run_data["id"])
                QMessageBox.information(
                    self, "Disbursement & GL Posting Complete",
                    f"Payroll {res.get('run_code')} disbursed successfully!\n\n"
                    f"GL Journal Posting: {res.get('journal_entry_id')}\n"
                    f"Status updated to DISBURSED."
                )
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Disbursement Error", f"Failed: {str(e)}")

    def view_selected_payslip(self):
        row = self.payslip_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Payslip", "Please select an employee payslip row to view.")
            return

        ps = self.payslip_table.item(row, 0).data(Qt.UserRole)
        if not ps:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Payslip — {ps.get('employee_name')} ({ps.get('employee_code')})")
        dialog.resize(520, 500)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 14px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(6)

        header = QLabel("👑 VICTORY CREST ENTERPRISES PRIVATE LIMITED\nCONFIDENTIAL SALARY PAYSLIP")
        header.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {ThemeColors.PRIMARY_LIGHT};")
        c_layout.addWidget(header)

        sub_info = QLabel(f"Staff Name: {ps.get('employee_name')}   |   Staff Code: {ps.get('employee_code')}\nDesignation: {ps.get('designation')}   |   Department: {ps.get('department_name')}\nDays Worked: {ps.get('days_worked')}   |   Status: {ps.get('payment_status')}")
        sub_info.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
        c_layout.addWidget(sub_info)

        layout.addWidget(card)

        # Earnings & Deductions Split
        split_row = QHBoxLayout()

        # Left: Earnings
        earn_box = QGroupBox("Gross Earnings (₹)")
        earn_form = QFormLayout(earn_box)
        earn_form.addRow("Basic Salary:", QLabel(f"₹{to_decimal(ps.get('basic_salary', 0)):,.2f}"))
        earn_form.addRow("House Rent Allowance:", QLabel(f"₹{to_decimal(ps.get('hra', 0)):,.2f}"))
        earn_form.addRow("Conveyance Allowance:", QLabel(f"₹{to_decimal(ps.get('conveyance', 0)):,.2f}"))
        earn_form.addRow("Special Allowance:", QLabel(f"₹{to_decimal(ps.get('special_allowance', 0)):,.2f}"))
        earn_form.addRow("Overtime Pay:", QLabel(f"₹{to_decimal(ps.get('overtime_pay', 0)):,.2f}"))
        gross_lbl = QLabel(f"₹{to_decimal(ps.get('gross_earnings', 0)):,.2f}")
        gross_lbl.setFont(self._bold_font())
        earn_form.addRow("Total Gross Earnings:", gross_lbl)
        split_row.addWidget(earn_box)

        # Right: Deductions
        ded_box = QGroupBox("Statutory Deductions (₹)")
        ded_form = QFormLayout(ded_box)
        ded_form.addRow("Provident Fund (12%):", QLabel(f"₹{to_decimal(ps.get('pf_deduction', 0)):,.2f}"))
        ded_form.addRow("Professional Tax:", QLabel(f"₹{to_decimal(ps.get('professional_tax', 0)):,.2f}"))
        ded_form.addRow("TDS (Income Tax):", QLabel(f"₹{to_decimal(ps.get('tds_deduction', 0)):,.2f}"))
        tot_ded_lbl = QLabel(f"₹{to_decimal(ps.get('total_deductions', 0)):,.2f}")
        tot_ded_lbl.setFont(self._bold_font())
        tot_ded_lbl.setForeground(Qt.red)
        ded_form.addRow("Total Deductions:", tot_ded_lbl)
        split_row.addWidget(ded_box)

        layout.addLayout(split_row)

        # Net Pay Box
        net_box = QFrame()
        net_box.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 2px solid {ThemeColors.STATUS_SUCCESS};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        n_layout = QHBoxLayout(net_box)
        lbl_net_title = QLabel("NET SALARY TRANSFERRED:")
        lbl_net_title.setStyleSheet("font-size: 13px; font-weight: 700;")
        n_layout.addWidget(lbl_net_title)
        n_layout.addStretch()
        lbl_net_val = QLabel(f"₹{to_decimal(ps.get('net_pay', 0)):,.2f}")
        lbl_net_val.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {ThemeColors.STATUS_SUCCESS};")
        n_layout.addWidget(lbl_net_val)
        layout.addWidget(net_box)

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "btn_secondary")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.exec()

    # ---------------------------------------------------------
    # Styling Helpers
    # ---------------------------------------------------------
    def _bold_font(self):
        f = self.font()
        f.setBold(True)
        return f

    def _table_stylesheet(self) -> str:
        return f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                color: {ThemeColors.TEXT_MAIN};
                selection-background-color: {ThemeColors.BG_SECONDARY};
                selection-color: {ThemeColors.PRIMARY_LIGHT};
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_SECONDARY};
                color: {ThemeColors.TEXT_MUTED};
                padding: 6px;
                border: none;
                font-weight: 700;
                font-size: 11px;
            }}
        """
