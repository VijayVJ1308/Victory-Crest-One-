"""Victory Crest One - Desktop UI Tests for Inventory View
Verifies headless PySide6 components, tabs, tables, filtering, and MainWindow navigation routing for Inventory and ERP.
"""

from desktop.ui.views.inventory_view import InventoryView
from desktop.ui.main_window import MainWindow


def test_inventory_view_initialization(qapp):
    view = InventoryView()
    assert view is not None
    assert view.tabs.count() == 5
    assert view.stock_table.rowCount() >= 5
    assert view.po_table.rowCount() >= 2
    assert view.alerts_table.rowCount() >= 1
    assert view.mov_table.rowCount() >= 2
    assert len(view.cached_warehouses) >= 4


def test_inventory_view_stock_filtering(qapp):
    view = InventoryView()
    initial_rows = view.stock_table.rowCount()

    # Search filter
    view.stock_search.setText("Coffee")
    assert view.stock_table.rowCount() <= initial_rows
    assert view.stock_table.rowCount() >= 1

    # Clear search
    view.stock_search.setText("")
    assert view.stock_table.rowCount() == initial_rows


def test_inventory_view_edit_stock(qapp, monkeypatch):
    called = []
    view = InventoryView()
    monkeypatch.setattr(view, "open_edit_stock_dialog", lambda s: called.append(s))
    view.on_stock_double_clicked(0, 0)
    assert len(called) == 1
    assert "sku" in called[0]


def test_main_window_inventory_and_erp_navigation(qapp):
    window = MainWindow()
    assert "inventory" in window.nav_buttons
    assert "erp" in window.nav_buttons

    # Navigate to inventory (Warehouse stock catalog tab 0)
    window.navigate_to("inventory")
    assert window.view_stack.currentIndex() == 10
    assert window.current_nav_key == "inventory"
    assert window.inventory_view.tabs.currentIndex() == 0

    # Navigate to erp (Procurement & POs tab 1)
    window.navigate_to("erp")
    assert window.view_stack.currentIndex() == 10
    assert window.current_nav_key == "erp"
    assert window.inventory_view.tabs.currentIndex() == 1
