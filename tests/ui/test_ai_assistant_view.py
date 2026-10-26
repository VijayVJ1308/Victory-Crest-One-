"""Victory Crest One - Desktop UI Tests for AI Business Assistant View
Verifies initialization, metric cards, thread switching, interactive prompts,
and MainWindow stack navigation at index 18.
"""

import pytest
from desktop.ui.views.ai_assistant_view import AiAssistantView
from desktop.ui.main_window import MainWindow


def test_ai_assistant_view_initialization(qapp):
    view = AiAssistantView()
    assert view is not None

    # Check metric cards
    assert view.card_queries is not None
    assert view.card_latency is not None
    assert view.card_safety is not None
    assert view.card_threads is not None
    assert int(view.card_threads.lbl_val.text()) >= 1

    # Check thread list and prompt controls
    assert view.thread_list.count() >= 1
    assert view.prompt_input is not None
    assert view.role_combo.count() >= 3


def test_ai_assistant_view_query_interaction(qapp):
    view = AiAssistantView()
    initial_child_count = view.chat_layout.count()

    view.send_prompt("What is our current hotel room occupancy and ADR?")
    new_child_count = view.chat_layout.count()
    assert new_child_count >= initial_child_count + 2
    assert view.active_thread_id is not None


def test_main_window_ai_assistant_navigation(qapp):
    window = MainWindow()
    assert "ai_assistant" in window.nav_buttons

    window.navigate_to("ai_assistant")
    assert window.view_stack.currentIndex() == 18
    assert window.current_nav_key == "ai_assistant"
    assert window.ai_assistant_view is not None
