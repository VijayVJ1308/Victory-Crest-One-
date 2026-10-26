"""Victory Crest One - UI Tests for Business Intelligence & Executive Analytics View
Tests BusinessIntelligenceView widget hierarchy, metric cards, table population,
financial ratio displays, document export actions, and MainWindow routing stack integration.
"""

import pytest
from PySide6.QtWidgets import QApplication
from desktop.ui.views.bi_view import BusinessIntelligenceView
from desktop.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_bi_view_initialization(qapp):
    view = BusinessIntelligenceView()
    assert view is not None

    # Check metric cards
    assert hasattr(view, "card_total_rev")
    assert hasattr(view, "card_gop")
    assert hasattr(view, "card_ebitda")
    assert hasattr(view, "card_blended_occ")
    assert hasattr(view, "card_net_margin")

    assert "₹" in view.card_total_rev.value_label.text()
    assert "₹" in view.card_gop.value_label.text()
    assert "%" in view.card_blended_occ.value_label.text()

    # Check tabs
    assert view.tab_widget.count() == 5

    # Check tables have rows populated
    assert view.table_monthly.rowCount() == 12
    assert view.table_properties.rowCount() >= 3
    assert view.table_departments.rowCount() >= 4
    assert view.table_reports.rowCount() >= 2


def test_main_window_bi_navigation(qapp):
    window = MainWindow()
    assert hasattr(window, "bi_view")

    # Navigate to bi
    window.navigate_to("bi")
    assert window.view_stack.currentIndex() == 16
    assert isinstance(window.view_stack.currentWidget(), BusinessIntelligenceView)


def test_bi_financial_ratios_display(qapp):
    view = BusinessIntelligenceView()

    # Check ratio labels populated
    assert "%" in view.lbl_r_gross.text()
    assert "%" in view.lbl_r_gop.text()
    assert "%" in view.lbl_r_net.text()
    assert "x" in view.lbl_r_current.text()
    assert "₹" in view.lbl_r_cash.text()
