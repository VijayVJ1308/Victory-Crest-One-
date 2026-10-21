"""Victory Crest One - Desktop UI Tests for Marketing View
Verifies headless PySide6 components, tabs, and MainWindow navigation routing for marketing.
"""

from desktop.ui.views.marketing_view import MarketingView
from desktop.ui.main_window import MainWindow


def test_marketing_view_initialization(qapp):
    view = MarketingView()
    assert view is not None
    assert view.tabs.count() == 5
    assert view.campaigns_table.rowCount() >= 3
    assert view.segments_table.rowCount() >= 3


def test_main_window_marketing_navigation(qapp):
    window = MainWindow()
    assert "marketing" in window.nav_buttons

    # Navigate to marketing
    window.navigate_to("marketing")
    assert window.view_stack.currentIndex() == 9
    assert window.current_nav_key == "marketing"
