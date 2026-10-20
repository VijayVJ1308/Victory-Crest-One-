"""Victory Crest One - Desktop UI Tests for Sales CRM View
"""

import pytest
from desktop.ui.views.crm_view import SalesCrmView
from desktop.ui.main_window import MainWindow


def test_sales_crm_view_initialization(qapp):
    crm_view = SalesCrmView()
    assert crm_view is not None
    assert crm_view.tabs.count() == 4
    # Verify tables have rows from seed data
    assert crm_view.deals_table.rowCount() >= 2
    assert crm_view.leads_table.rowCount() >= 3
    assert crm_view.quotes_table.rowCount() >= 1
    assert crm_view.activities_table.rowCount() >= 1


def test_main_window_sales_navigation(qapp):
    window = MainWindow()
    window.navigate_to("sales")
    # Sales view is at stack index 7
    assert window.view_stack.currentIndex() == 7
    assert window.crm_view is not None
