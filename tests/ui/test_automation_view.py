"""Victory Crest One - Desktop UI Tests for Workflow Automation View
Verifies initialization, metric cards, rules catalog filtering, inspector panel,
audit logs, simulator controls, and MainWindow stack navigation at index 17.
"""

import pytest
from PySide6.QtCore import Qt
from desktop.ui.views.automation_view import WorkflowAutomationView
from desktop.ui.main_window import MainWindow


def test_automation_view_initialization(qapp):
    view = WorkflowAutomationView()
    assert view is not None

    # Check metric cards
    assert view.card_active_rules is not None
    assert int(view.card_active_rules.lbl_val.text()) >= 1
    assert view.card_total_exec is not None
    assert view.card_success_rate is not None
    assert view.card_actions_triggered is not None

    # Check tabs
    assert view.tabs.count() == 3
    assert "Rules Catalog" in view.tabs.tabText(0)
    assert "Execution Audit" in view.tabs.tabText(1)
    assert "Event Dispatcher" in view.tabs.tabText(2)

    # Check rules table populated
    assert view.rules_table.rowCount() >= 5
    assert view.logs_table.rowCount() >= 1


def test_automation_view_filtering_and_inspector(qapp):
    view = WorkflowAutomationView()

    # Select first rule and verify inspector updates
    view.rules_table.selectRow(0)
    assert "WF-" in view.inspector_title.text()
    assert len(view.inspector_pipeline.text()) > 10

    # Filter by PAUSED
    view.rules_status_combo.setCurrentText("PAUSED")
    assert view.rules_table.rowCount() >= 1
    for r in range(view.rules_table.rowCount()):
        assert view.rules_table.item(r, 6).text() == "PAUSED"

    # Reset filter
    view.rules_status_combo.setCurrentText("All Statuses")
    assert view.rules_table.rowCount() >= 5

    # Check log selection
    view.logs_table.selectRow(0)
    assert "workflow_code" in view.log_detail_box.toPlainText() or "{" in view.log_detail_box.toPlainText()


def test_main_window_automation_navigation(qapp):
    window = MainWindow()
    assert "automation" in window.nav_buttons

    window.navigate_to("automation")
    assert window.view_stack.currentIndex() == 17
    assert window.current_nav_key == "automation"
    assert window.automation_view is not None
