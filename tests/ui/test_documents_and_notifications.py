"""Victory Crest One - Desktop UI Tests for Documents Vault & Notifications
"""

import pytest
from desktop.ui.views.documents_view import DocumentsView
from desktop.ui.main_window import MainWindow


def test_documents_view_initialization(qapp):
    doc_view = DocumentsView()
    assert doc_view is not None
    assert doc_view.doc_table.rowCount() >= 1
    assert doc_view.cat_filter.count() >= 5


def test_main_window_documents_navigation(qapp):
    window = MainWindow()
    window.navigate_to("documents")
    # documents view is at index 5
    assert window.view_stack.currentIndex() == 5
    assert window.documents_view is not None


def test_main_window_notifications_button(qapp):
    window = MainWindow()
    assert window.notif_btn is not None
    assert "🔔" in window.notif_btn.text()
