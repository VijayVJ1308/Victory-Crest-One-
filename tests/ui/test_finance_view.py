"""Victory Crest One - Desktop UI Tests for Finance and Accounting View
"""

import pytest
from desktop.ui.views.finance_view import FinanceView
from desktop.ui.main_window import MainWindow


def test_finance_view_initialization(qapp):
    fin_view = FinanceView()
    assert fin_view is not None
    assert fin_view.tabs.count() == 5
    # Verify tables have rows from seed data
    assert fin_view.journals_table.rowCount() >= 3
    assert fin_view.coa_table.rowCount() >= 15
    assert fin_view.ar_table.rowCount() >= 1
    assert fin_view.ap_table.rowCount() >= 1
    assert fin_view.reports_table.rowCount() >= 4


def test_main_window_finance_navigation(qapp):
    window = MainWindow()
    window.navigate_to("finance")
    # Finance view is at stack index 6
    assert window.view_stack.currentIndex() == 6
    # Finance navigation defaults to AR tab (index 2)
    assert window.finance_view.tabs.currentIndex() == 2


def test_main_window_accounting_navigation(qapp):
    window = MainWindow()
    window.navigate_to("accounting")
    # Accounting view is at stack index 6
    assert window.view_stack.currentIndex() == 6
    # Accounting navigation defaults to GL Journals tab (index 0)
    assert window.finance_view.tabs.currentIndex() == 0
