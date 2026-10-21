"""Victory Crest One - Desktop UI Tests for Customer & Field Service View
Verifies headless PySide6 components, tabs, tables, filtering, and MainWindow navigation routing.
"""

from desktop.ui.views.service_view import ServiceManagementView
from desktop.ui.main_window import MainWindow


def test_service_view_initialization(qapp):
    view = ServiceManagementView()
    assert view is not None
    assert view.tabs.count() == 5
    assert view.table_tickets.rowCount() >= 3
    assert view.table_work_orders.rowCount() >= 2
    assert view.table_parts.rowCount() >= 2
    assert view.table_invoicing.rowCount() >= 2
    assert view.table_sla.rowCount() >= 4


def test_service_view_ticket_filtering(qapp):
    view = ServiceManagementView()
    initial_rows = view.table_tickets.rowCount()

    # Search for Apollo
    view.txt_ticket_search.setText("Apollo")
    assert view.table_tickets.rowCount() <= initial_rows
    assert view.table_tickets.rowCount() >= 1

    # Filter by Priority
    view.txt_ticket_search.setText("")
    view.combo_ticket_priority.setCurrentText("CRITICAL")
    assert view.table_tickets.rowCount() >= 1
    assert view.table_tickets.rowCount() <= initial_rows


def test_main_window_service_navigation(qapp):
    window = MainWindow()
    assert "service" in window.nav_buttons

    # Navigate to Service (stack index 12)
    window.navigate_to("service")
    assert window.view_stack.currentIndex() == 12
    assert window.current_nav_key == "service"
    assert window.service_view.tabs.currentIndex() == 0
