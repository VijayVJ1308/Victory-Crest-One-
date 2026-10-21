"""Victory Crest One - Desktop UI Tests for HR & Payroll View
Verifies headless PySide6 components, tabs, tables, filtering, and MainWindow navigation routing for HR and Payroll.
"""

from desktop.ui.views.hr_view import HrPayrollView
from desktop.ui.main_window import MainWindow


def test_hr_payroll_view_initialization(qapp):
    view = HrPayrollView()
    assert view is not None
    assert view.tabs.count() == 5
    assert view.emp_table.rowCount() >= 7
    assert view.att_table.rowCount() >= 5
    assert view.leave_table.rowCount() >= 1
    assert view.run_table.rowCount() >= 1
    assert view.payslip_table.rowCount() >= 1


def test_hr_view_employee_filtering(qapp):
    view = HrPayrollView()
    initial_rows = view.emp_table.rowCount()

    # Search filter
    view.emp_search.setText("Meenakshi")
    assert view.emp_table.rowCount() <= initial_rows
    assert view.emp_table.rowCount() >= 1

    # Clear search
    view.emp_search.setText("")
    assert view.emp_table.rowCount() == initial_rows


def test_main_window_hr_and_payroll_navigation(qapp):
    window = MainWindow()
    assert "hr" in window.nav_buttons
    assert "payroll" in window.nav_buttons

    # Navigate to HR (Staff Directory tab 0)
    window.navigate_to("hr")
    assert window.view_stack.currentIndex() == 11
    assert window.current_nav_key == "hr"
    assert window.hr_view.tabs.currentIndex() == 0

    # Navigate to Payroll (Payroll Processing tab 3)
    window.navigate_to("payroll")
    assert window.view_stack.currentIndex() == 11
    assert window.current_nav_key == "payroll"
    assert window.hr_view.tabs.currentIndex() == 3
