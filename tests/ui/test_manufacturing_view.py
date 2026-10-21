"""Victory Crest One - UI Tests for Manufacturing & BOM View
Tests ManufacturingView widget hierarchy, metric cards, table population,
filter interactions, and MainWindow routing stack integration.
"""

import pytest
from PySide6.QtWidgets import QApplication
from desktop.ui.views.manufacturing_view import ManufacturingView
from desktop.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_manufacturing_view_initialization(qapp):
    view = ManufacturingView()
    assert view is not None

    # Check metric cards
    assert hasattr(view, "card_active_orders")
    assert hasattr(view, "card_units_produced")
    assert hasattr(view, "card_scrap_rate")
    assert hasattr(view, "card_wip_val")
    assert hasattr(view, "card_capacity_util")

    assert "Orders" in view.card_active_orders.value_label.text()
    assert "%" in view.card_scrap_rate.value_label.text()

    # Check tabs
    assert view.tab_widget.count() == 5

    # Check tables have rows populated from seed data
    assert view.table_orders.rowCount() >= 3
    assert view.table_boms.rowCount() >= 2
    assert view.table_work_centers.rowCount() >= 4
    assert view.table_quality.rowCount() >= 2


def test_manufacturing_view_order_filtering(qapp):
    view = ManufacturingView()
    total_initial = view.table_orders.rowCount()

    # Filter to COMPLETED orders
    view.cb_order_status.setCurrentText("COMPLETED")
    completed_count = view.table_orders.rowCount()
    assert completed_count > 0
    assert completed_count <= total_initial

    # Filter by search text
    view.cb_order_status.setCurrentText("All Statuses")
    view.txt_order_search.setText("Heritage")
    filtered_search_count = view.table_orders.rowCount()
    assert filtered_search_count > 0
    assert filtered_search_count <= total_initial


def test_main_window_manufacturing_navigation(qapp):
    window = MainWindow()
    assert hasattr(window, "manufacturing_view")

    # Navigate to manufacturing
    window.navigate_to("manufacturing")
    assert window.view_stack.currentIndex() == 14
    assert isinstance(window.view_stack.currentWidget(), ManufacturingView)
