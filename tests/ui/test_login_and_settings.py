"""Victory Crest One - Desktop UI Tests for Login & Settings Views
"""

import pytest
from desktop.ui.login_window import LoginDialog
from desktop.ui.views.settings_view import SettingsView
from desktop.ui.main_window import MainWindow


def test_login_dialog_presets(qapp):
    dialog = LoginDialog()
    assert dialog is not None
    assert dialog.username_input.text() == "admin"
    
    # Fill preset
    dialog.fill_preset("hotel_gm", "HotelPassword123!")
    assert dialog.username_input.text() == "hotel_gm"
    assert dialog.password_input.text() == "HotelPassword123!"


def test_settings_view_population(qapp):
    settings_view = SettingsView()
    assert settings_view is not None
    assert settings_view.users_table.rowCount() >= 4
    assert settings_view.roles_table.rowCount() >= 30
    assert settings_view.audit_table.rowCount() >= 1


def test_main_window_settings_navigation(qapp):
    window = MainWindow()
    window.navigate_to("settings")
    # settings is at view_stack index 4
    assert window.view_stack.currentIndex() == 4
    assert window.settings_view is not None
