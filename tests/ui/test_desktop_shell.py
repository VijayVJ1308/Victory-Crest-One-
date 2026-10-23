"""Victory Crest One - Desktop UI Shell Tests
Verifies headless PySide6 components, MainWindow layout, navigation routing,
and selector initialization.
"""

import pytest
from desktop.ui.main_window import MainWindow
from desktop.ui.components.metric_card import MetricCard
from desktop.ui.components.status_badge import StatusBadge
from desktop.core.session import session_manager


def test_metric_card_component(qapp):
    card = MetricCard(title="Test Metric", value="₹12,500", icon="💳", subtext="+12% growth")
    assert card.value_label.text() == "₹12,500"
    card.update_value("₹15,000")
    assert card.value_label.text() == "₹15,000"


def test_status_badge_component(qapp):
    badge = StatusBadge(text="Active", status_type="active")
    assert "ACTIVE" in badge.text()
    badge.set_status("Planned", "planned")
    assert "PLANNED" in badge.text()


def test_main_window_shell_initialization(qapp):
    window = MainWindow()
    assert window is not None
    assert "Victory Crest" in window.windowTitle()
    
    # Check selectors populated
    assert window.org_combo.count() >= 1
    assert window.prop_combo.count() >= 1
    
    # Check navigation items exist
    assert "dashboard" in window.nav_buttons
    assert "modules" in window.nav_buttons
    assert "diagnostics" in window.nav_buttons
    assert "sales" in window.nav_buttons
    assert "finance" in window.nav_buttons
    assert "projects" in window.nav_buttons
    
    # Test navigation to modules
    window.navigate_to("modules")
    assert window.view_stack.currentIndex() == 1
    
    # Test navigation to diagnostics
    window.navigate_to("diagnostics")
    assert window.view_stack.currentIndex() == 3
    
    # Test navigation to an active module (projects)
    window.navigate_to("projects")
    assert window.view_stack.currentIndex() == 15

    # Test navigation to a planned module (bi)
    window.navigate_to("bi")
    assert window.view_stack.currentIndex() == 2
    assert window.planned_module_view.current_module_id == "bi"
    
    # Return to dashboard
    window.navigate_to("dashboard")
    assert window.view_stack.currentIndex() == 0
