"""Victory Crest One - Desktop UI Tests for Hospitality PMS & Dining View
Verifies headless PySide6 components, tabs, tables, filtering, and MainWindow navigation routing for hotel and restaurant.
"""

from desktop.ui.views.hospitality_view import HospitalityView
from desktop.ui.main_window import MainWindow


def test_hospitality_view_initialization(qapp):
    view = HospitalityView()
    assert view is not None
    assert view.tabs.count() == 5
    assert view.table_reservations.rowCount() >= 2
    assert view.table_rooms.rowCount() >= 6
    assert view.table_folios.rowCount() >= 1
    assert view.table_dining.rowCount() >= 1


def test_hospitality_view_room_and_res_filtering(qapp):
    view = HospitalityView()
    initial_res_rows = view.table_reservations.rowCount()

    # Search for Vikramaditya
    view.txt_res_search.setText("Vikramaditya")
    assert view.table_reservations.rowCount() <= initial_res_rows
    assert view.table_reservations.rowCount() >= 1

    # Clear search
    view.txt_res_search.setText("")
    assert view.table_reservations.rowCount() == initial_res_rows

    # Room filter
    initial_rooms = view.table_rooms.rowCount()
    view.combo_room_status.setCurrentText("AVAILABLE_CLEAN")
    assert view.table_rooms.rowCount() >= 1
    assert view.table_rooms.rowCount() <= initial_rooms


def test_main_window_hotel_and_restaurant_navigation(qapp):
    window = MainWindow()
    assert "hotel" in window.nav_buttons
    assert "restaurant" in window.nav_buttons

    # Navigate to Hotel (stack index 13, tab 0: Reservations & Check-In)
    window.navigate_to("hotel")
    assert window.view_stack.currentIndex() == 13
    assert window.current_nav_key == "hotel"
    assert window.hospitality_view.tabs.currentIndex() == 0

    # Navigate to Restaurant (stack index 13, tab 3: Restaurant & KDS Tickets)
    window.navigate_to("restaurant")
    assert window.view_stack.currentIndex() == 13
    assert window.current_nav_key == "restaurant"
    assert window.hospitality_view.tabs.currentIndex() == 3
