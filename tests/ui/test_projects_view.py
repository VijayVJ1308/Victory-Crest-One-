"""Victory Crest One - UI Tests for Project Management & PSA View
Tests ProjectsView widget hierarchy, metric cards, table population,
filter interactions, task status transitions, and MainWindow routing stack integration.
"""

import pytest
from PySide6.QtWidgets import QApplication
from desktop.ui.views.projects_view import ProjectsView
from desktop.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_projects_view_initialization(qapp):
    view = ProjectsView()
    assert view is not None

    # Check metric cards
    assert hasattr(view, "card_active_projects")
    assert hasattr(view, "card_total_contract")
    assert hasattr(view, "card_total_billed")
    assert hasattr(view, "card_logged_hours")
    assert hasattr(view, "card_billable_util")

    assert "Projects" in view.card_active_projects.value_label.text()
    assert "₹" in view.card_total_contract.value_label.text()
    assert "hrs" in view.card_logged_hours.value_label.text()
    assert "%" in view.card_billable_util.value_label.text()

    # Check tabs
    assert view.tab_widget.count() == 5

    # Check tables have rows populated from seeded projects
    assert view.table_projects.rowCount() >= 3
    assert view.table_tasks.rowCount() >= 3
    assert view.table_milestones.rowCount() >= 3
    assert view.table_timesheets.rowCount() >= 3
    assert view.table_expenses.rowCount() >= 3


def test_projects_view_filtering(qapp):
    view = ProjectsView()
    total_projects = view.table_projects.rowCount()

    # Filter projects by status
    view.cb_project_status.setCurrentText("ACTIVE")
    active_count = view.table_projects.rowCount()
    assert active_count > 0
    assert active_count <= total_projects

    # Filter projects by text search
    view.cb_project_status.setCurrentText("All Statuses")
    view.txt_project_search.setText("Ballroom")
    search_count = view.table_projects.rowCount()
    assert search_count > 0
    assert search_count <= total_projects

    # Filter tasks by status
    view.cb_task_status.setCurrentText("DONE")
    done_tasks = view.table_tasks.rowCount()
    assert done_tasks > 0

    # Reset task filter
    view.cb_task_status.setCurrentText("All Statuses")
    assert view.table_tasks.rowCount() >= done_tasks


def test_main_window_projects_navigation(qapp):
    window = MainWindow()
    assert hasattr(window, "projects_view")

    # Navigate to projects
    window.navigate_to("projects")
    assert window.view_stack.currentIndex() == 15
    assert isinstance(window.view_stack.currentWidget(), ProjectsView)


def test_projects_view_status_transitions(qapp):
    view = ProjectsView()
    # Find a task to update
    assert len(view.cached_tasks) > 0
    t = view.cached_tasks[0]
    pid = t["project_id"]
    tid = t["id"]
    initial_st = t.get("status", "TODO")

    # Toggle status
    new_st = "DONE" if initial_st != "DONE" else "IN_PROGRESS"
    view.change_task_status(pid, tid, new_st)
    updated_t = next((task for task in view.cached_tasks if task["id"] == tid), None)
    assert updated_t is not None
    assert updated_t["status"] == new_st
