"""Victory Crest One - Desktop UI Tests for POS & Commerce View
Verifies headless PySide6 components, catalog cards, cart operations,
and MainWindow navigation routing for pos and commerce.
"""

from decimal import Decimal
from desktop.ui.views.pos_view import PosCommerceView
from desktop.ui.main_window import MainWindow


def test_pos_view_initialization(qapp):
    view = PosCommerceView()
    assert view is not None
    assert view.tabs.count() == 3
    # Check catalog loaded
    assert len(view.all_products) >= 8
    # Check category buttons exist
    assert "All" in view.cat_buttons
    assert "Beverages" in view.cat_buttons


def test_pos_cart_item_addition_and_totals(qapp):
    view = PosCommerceView()
    view.clear_cart()
    assert len(view.cart_lines) == 0

    # Add item to cart
    coffee = next(p for p in view.all_products if "Coffee" in p["name"])
    view.add_to_cart(coffee)
    assert len(view.cart_lines) == 1
    assert view.cart_lines[0]["quantity"] == Decimal("1.00")

    # Add same item again -> increments quantity
    view.add_to_cart(coffee)
    assert len(view.cart_lines) == 1
    assert view.cart_lines[0]["quantity"] == Decimal("2.00")

    # Check totals updated: 2 * 180 = 360.00 subtotal, 12% GST = 43.20, Total = 403.20
    assert "₹360.00" in view.lbl_subtotal.text()
    assert "₹403.20" in view.lbl_total_due.text()

    # Clear cart
    view.clear_cart()
    assert len(view.cart_lines) == 0
    assert "₹0.00" in view.lbl_total_due.text()


def test_main_window_pos_navigation(qapp):
    window = MainWindow()
    assert "pos" in window.nav_buttons

    # Navigate to POS
    window.navigate_to("pos")
    assert window.view_stack.currentIndex() == 8
    assert window.current_nav_key == "pos"


def test_main_window_commerce_navigation(qapp):
    window = MainWindow()
    assert "commerce" in window.nav_buttons

    # Navigate to Commerce (shares POS & Commerce view)
    window.navigate_to("commerce")
    assert window.view_stack.currentIndex() == 8
    assert window.current_nav_key == "commerce"
