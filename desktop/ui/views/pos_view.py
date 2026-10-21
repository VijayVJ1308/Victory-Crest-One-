"""Victory Crest One - Commerce & Point of Sale (POS) Desktop View
Touch-friendly cashier terminal, barcode scanning, live cart calculations,
multi-tender checkout, thermal receipt formatting, and drawer reconciliation.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDoubleSpinBox, QSpinBox, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from shared.calculations import (
    to_decimal, calculate_pos_change, calculate_drawer_variance,
    calculate_pos_order_totals
)


class PosCommerceView(QWidget):
    """Full-featured Point of Sale (POS) and Commerce Workstation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cart_lines: List[Dict[str, Any]] = []
        self.active_session: Optional[Dict[str, Any]] = None
        self.all_products: List[Dict[str, Any]] = []
        self.current_category: str = "All"
        self.active_held_order_id: Optional[str] = None

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(14)

        # -----------------------------------------------------
        # 1. Header & Register Status Toolbar
        # -----------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        title = QLabel("Point of Sale (POS) & Commerce")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Multi-register cashier terminals, fast barcode scanning, split tenders, and instant GL posting.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        # Session Telemetry Badges
        self.badge_terminal = QLabel("Terminal: Loading...")
        self.badge_terminal.setStyleSheet(f"""
            background: {ThemeColors.BG_SECONDARY};
            color: {ThemeColors.TEXT_MAIN};
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid {ThemeColors.BORDER_LIGHT};
            font-weight: 600;
        """)
        header_row.addWidget(self.badge_terminal)

        self.badge_shift_sales = QLabel("Shift Sales: ₹0.00")
        self.badge_shift_sales.setStyleSheet(f"""
            background: {ThemeColors.BG_SECONDARY};
            color: {ThemeColors.STATUS_SUCCESS};
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid {ThemeColors.BORDER_LIGHT};
            font-weight: 700;
        """)
        header_row.addWidget(self.badge_shift_sales)

        btn_held_orders = QPushButton("⏸️ Held Orders (0)")
        btn_held_orders.setObjectName("btn_held_orders")
        btn_held_orders.setProperty("class", "btn_secondary")
        btn_held_orders.clicked.connect(self.open_held_orders_dialog)
        self.btn_held_orders = btn_held_orders
        header_row.addWidget(btn_held_orders)

        btn_close_shift = QPushButton("🔒 End Shift / Reconcile")
        btn_close_shift.setProperty("class", "btn_secondary")
        btn_close_shift.clicked.connect(self.open_close_shift_dialog)
        header_row.addWidget(btn_close_shift)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)
        header_row.addWidget(btn_refresh)

        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Main Tabs (Terminal, Orders History, Registers)
        # -----------------------------------------------------
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                background: {ThemeColors.BG_SURFACE};
                border-radius: 8px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {ThemeColors.BG_SECONDARY};
                color: {ThemeColors.TEXT_MUTED};
                padding: 10px 20px;
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {ThemeColors.BG_SURFACE};
                color: {ThemeColors.PRIMARY_LIGHT};
                border-bottom: 2px solid {ThemeColors.PRIMARY_LIGHT};
            }}
        """)

        # Tab 1: Live Cashier Terminal Workstation
        terminal_tab = self.build_terminal_workstation()
        self.tabs.addTab(terminal_tab, "💳 Cashier Register")

        # Tab 2: Orders & Receipts History
        orders_tab = self.build_orders_history_tab()
        self.tabs.addTab(orders_tab, "📑 Completed Orders & Receipts")

        # Tab 3: Terminal Hardware & Shifts
        terminals_tab = self.build_terminals_overview_tab()
        self.tabs.addTab(terminals_tab, "🖥️ Register Terminals")

        main_layout.addWidget(self.tabs)

    # ---------------------------------------------------------
    # TAB 1: Live Cashier Terminal Workstation
    # ---------------------------------------------------------
    def build_terminal_workstation(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(18)

        # --- LEFT PANE (Catalog & Barcode Scanner) ---
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Scanner & Search Bar
        search_card = QFrame()
        search_card.setStyleSheet(f"""
            QFrame {{
                background: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 8px 12px;
            }}
        """)
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)

        scanner_lbl = QLabel("🔍 / 🏷️")
        scanner_lbl.setStyleSheet("font-size: 16px;")
        search_layout.addWidget(scanner_lbl)

        self.input_barcode = QLineEdit()
        self.input_barcode.setPlaceholderText("Scan barcode or type SKU (e.g., 890103000001) and press Enter...")
        self.input_barcode.setStyleSheet(f"""
            QLineEdit {{
                background: {ThemeColors.BG_SURFACE};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }}
        """)
        self.input_barcode.returnPressed.connect(self.handle_barcode_scan)
        search_layout.addWidget(self.input_barcode)

        btn_scan = QPushButton("Add Item ↵")
        btn_scan.setProperty("class", "btn_primary")
        btn_scan.clicked.connect(self.handle_barcode_scan)
        search_layout.addWidget(btn_scan)

        left_layout.addWidget(search_card)

        # Category Filter Buttons Row
        self.category_bar = QHBoxLayout()
        self.category_bar.setSpacing(6)
        categories = ["All", "Beverages", "Bakery", "Snacks", "Retail", "Wellness", "Merchandise"]
        self.cat_buttons = {}
        for cat in categories:
            b = QPushButton(cat)
            b.setCheckable(True)
            b.setChecked(cat == "All")
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {ThemeColors.BG_SECONDARY};
                    color: {ThemeColors.TEXT_MAIN};
                    border: 1px solid {ThemeColors.BORDER_LIGHT};
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:checked {{
                    background: {ThemeColors.PRIMARY_LIGHT};
                    color: #FFFFFF;
                    border: 1px solid {ThemeColors.PRIMARY_LIGHT};
                }}
            """)
            b.clicked.connect(lambda checked, c=cat: self.filter_category(c))
            self.category_bar.addWidget(b)
            self.cat_buttons[cat] = b
        self.category_bar.addStretch()
        left_layout.addLayout(self.category_bar)

        # Product Catalog Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                background: {ThemeColors.BG_SURFACE};
            }}
        """)
        self.grid_container = QWidget()
        self.product_grid = QGridLayout(self.grid_container)
        self.product_grid.setContentsMargins(12, 12, 12, 12)
        self.product_grid.setSpacing(12)
        scroll.setWidget(self.grid_container)
        left_layout.addWidget(scroll)

        layout.addWidget(left_pane, 6)

        # --- RIGHT PANE (Active Order & Cart Tape) ---
        right_pane = QFrame()
        right_pane.setStyleSheet(f"""
            QFrame {{
                background: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
            }}
        """)
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        # Order Header Details
        order_meta_row = QHBoxLayout()
        self.order_num_lbl = QLabel("Sale Ticket: [Active Register]")
        self.order_num_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        order_meta_row.addWidget(self.order_num_lbl)
        order_meta_row.addStretch()
        right_layout.addLayout(order_meta_row)

        cust_row = QHBoxLayout()
        cust_row.setSpacing(8)
        self.combo_customer = QComboBox()
        self.combo_customer.addItem("Walk-in Guest")
        self.combo_customer.addItem("Tata Consultancy Services (TCS)")
        self.combo_customer.addItem("Cognizant Global Solutions")
        self.combo_customer.setStyleSheet(f"""
            QComboBox {{
                background: {ThemeColors.BG_SURFACE};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 6px;
                font-size: 12px;
            }}
        """)
        cust_row.addWidget(QLabel("Customer:"))
        cust_row.addWidget(self.combo_customer, 1)

        self.input_table_room = QLineEdit()
        self.input_table_room.setPlaceholderText("Table / Room # (e.g. Table 2)")
        self.input_table_room.setStyleSheet(f"""
            QLineEdit {{
                background: {ThemeColors.BG_SURFACE};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 6px;
                font-size: 12px;
            }}
        """)
        cust_row.addWidget(self.input_table_room)
        right_layout.addLayout(cust_row)

        # Cart Items Table
        self.cart_table = QTableWidget(0, 5)
        self.cart_table.setHorizontalHeaderLabels(["Item Name", "Price", "Qty", "Total", "Action"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setStyleSheet(f"""
            QTableWidget {{
                background: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: {ThemeColors.BG_SECONDARY};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 700;
                padding: 6px;
                border: none;
            }}
        """)
        right_layout.addWidget(self.cart_table, 1)

        # Cart Calculations Card
        calc_card = QFrame()
        calc_card.setStyleSheet(f"""
            QFrame {{
                background: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        calc_layout = QVBoxLayout(calc_card)
        calc_layout.setSpacing(6)

        subtotal_row = QHBoxLayout()
        subtotal_row.addWidget(QLabel("Subtotal:"))
        subtotal_row.addStretch()
        self.lbl_subtotal = QLabel("₹0.00")
        self.lbl_subtotal.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        subtotal_row.addWidget(self.lbl_subtotal)
        calc_layout.addLayout(subtotal_row)

        discount_row = QHBoxLayout()
        discount_row.addWidget(QLabel("Discount (%):"))
        self.spin_discount = QSpinBox()
        self.spin_discount.setRange(0, 50)
        self.spin_discount.setValue(0)
        self.spin_discount.valueChanged.connect(self.update_cart_display)
        self.spin_discount.setStyleSheet(f"""
            QSpinBox {{
                background: {ThemeColors.BG_SECONDARY};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 4px;
                padding: 2px 6px;
            }}
        """)
        discount_row.addWidget(self.spin_discount)
        discount_row.addStretch()
        self.lbl_discount = QLabel("-₹0.00")
        self.lbl_discount.setStyleSheet(f"color: {ThemeColors.STATUS_WARNING};")
        discount_row.addWidget(self.lbl_discount)
        calc_layout.addLayout(discount_row)

        tax_row = QHBoxLayout()
        tax_row.addWidget(QLabel("Tax (GST 12%):"))
        tax_row.addStretch()
        self.lbl_tax = QLabel("₹0.00")
        self.lbl_tax.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED};")
        tax_row.addWidget(self.lbl_tax)
        calc_layout.addLayout(tax_row)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color: {ThemeColors.BORDER_LIGHT};")
        calc_layout.addWidget(divider)

        total_row = QHBoxLayout()
        total_lbl = QLabel("TOTAL DUE:")
        total_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {ThemeColors.TEXT_MAIN};")
        total_row.addWidget(total_lbl)
        total_row.addStretch()
        self.lbl_total_due = QLabel("₹0.00")
        self.lbl_total_due.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {ThemeColors.PRIMARY_LIGHT};")
        total_row.addWidget(self.lbl_total_due)
        calc_layout.addLayout(total_row)

        right_layout.addWidget(calc_card)

        # Action Buttons
        btn_action_row = QHBoxLayout()
        btn_action_row.setSpacing(8)

        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.setProperty("class", "btn_secondary")
        btn_clear.clicked.connect(self.clear_cart)
        btn_action_row.addWidget(btn_clear)

        btn_hold = QPushButton("⏸️ Hold Order (F4)")
        btn_hold.setProperty("class", "btn_secondary")
        btn_hold.clicked.connect(self.hold_current_order)
        btn_action_row.addWidget(btn_hold)

        right_layout.addLayout(btn_action_row)

        self.btn_pay = QPushButton("💳 TENDER & PAY (F12) ➔")
        self.btn_pay.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_LIGHT};
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 800;
                padding: 14px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.PRIMARY_HOVER};
            }}
        """)
        self.btn_pay.clicked.connect(self.open_tender_dialog)
        right_layout.addWidget(self.btn_pay)

        layout.addWidget(right_pane, 4)
        return container

    # ---------------------------------------------------------
    # TAB 2: Orders & Receipts History
    # ---------------------------------------------------------
    def build_orders_history_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filter & Action Row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.combo_order_filter = QComboBox()
        self.combo_order_filter.addItems(["ALL", "COMPLETED", "HELD", "VOIDED"])
        self.combo_order_filter.currentTextChanged.connect(self.load_orders_table)
        ctrl_row.addWidget(QLabel("Filter Status:"))
        ctrl_row.addWidget(self.combo_order_filter)
        ctrl_row.addStretch()

        btn_view_receipt = QPushButton("🧾 View Thermal Receipt")
        btn_view_receipt.setProperty("class", "btn_secondary")
        btn_view_receipt.clicked.connect(self.view_selected_order_receipt)
        ctrl_row.addWidget(btn_view_receipt)

        layout.addLayout(ctrl_row)

        # Orders Table
        self.orders_table = QTableWidget(0, 9)
        self.orders_table.setHorizontalHeaderLabels([
            "Order #", "Time", "Customer / Table", "Items", "Subtotal", "Tax", "Total Amount", "Status", "GL Ref"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.verticalHeader().setVisible(False)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setStyleSheet(f"""
            QTableWidget {{
                background: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
            }}
            QHeaderView::section {{
                background: {ThemeColors.BG_SECONDARY};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 700;
                padding: 8px;
                border: none;
            }}
        """)
        layout.addWidget(self.orders_table)
        return container

    # ---------------------------------------------------------
    # TAB 3: Terminals Overview
    # ---------------------------------------------------------
    def build_terminals_overview_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_lbl = QLabel("Point of Sale Register Stations")
        header_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header_lbl)

        self.terminals_table = QTableWidget(0, 5)
        self.terminals_table.setHorizontalHeaderLabels([
            "Terminal Code", "Counter / Location", "Property", "Status", "Active Station"
        ])
        self.terminals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.terminals_table.verticalHeader().setVisible(False)
        self.terminals_table.setStyleSheet(f"""
            QTableWidget {{
                background: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
            }}
            QHeaderView::section {{
                background: {ThemeColors.BG_SECONDARY};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 700;
                padding: 8px;
                border: none;
            }}
        """)
        layout.addWidget(self.terminals_table)
        return container

    # ---------------------------------------------------------
    # Data Loading & Catalog Rendering
    # ---------------------------------------------------------
    def refresh_data(self):
        """Fetch active session, products, and order telemetry."""
        # 1. Active Session
        self.active_session = api_client.get_active_pos_session()
        if self.active_session:
            t_code = self.active_session.get("terminal_code", "Terminal")
            cashier = self.active_session.get("cashier_name", "Cashier")
            sales = to_decimal(self.active_session.get("total_sales", 0))
            self.badge_terminal.setText(f"Register: {t_code} ({cashier})")
            self.badge_shift_sales.setText(f"Shift Sales: ₹{sales:,.2f}")
        else:
            self.badge_terminal.setText("Register: [NO ACTIVE SHIFT]")
            self.badge_shift_sales.setText("Shift Sales: ₹0.00")

        # 2. Products Catalog
        self.all_products = api_client.get_pos_products()
        self.render_product_grid()

        # 3. Orders and Held Orders
        self.load_orders_table()
        self.update_held_orders_counter()
        self.load_terminals_table()

    def filter_category(self, cat: str):
        self.current_category = cat
        for c_name, btn in self.cat_buttons.items():
            btn.setChecked(c_name == cat)
        self.render_product_grid()

    def render_product_grid(self):
        """Populate product grid with cards."""
        # Clear existing grid
        while self.product_grid.count():
            item = self.product_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered = [
            p for p in self.all_products
            if self.current_category == "All" or p.get("category", "").lower() == self.current_category.lower()
        ]

        columns = 3
        for idx, prod in enumerate(filtered):
            row = idx // columns
            col = idx % columns
            card = self.create_product_card(prod)
            self.product_grid.addWidget(card, row, col)

    def create_product_card(self, prod: Dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                border: 1px solid {ThemeColors.PRIMARY_LIGHT};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        icon_lbl = QLabel(prod.get("icon", "📦"))
        icon_lbl.setStyleSheet("font-size: 26px;")
        layout.addWidget(icon_lbl)

        name_lbl = QLabel(prod.get("name", "Product"))
        name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        sku_lbl = QLabel(f"{prod.get('sku')} | {prod.get('category')}")
        sku_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        layout.addWidget(sku_lbl)

        price = to_decimal(prod.get("unit_price", 0))
        price_lbl = QLabel(f"₹{price:,.2f}")
        price_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {ThemeColors.STATUS_SUCCESS};")
        layout.addWidget(price_lbl)

        btn_add = QPushButton("➕ Add to Cart")
        btn_add.setProperty("class", "btn_primary")
        btn_add.clicked.connect(lambda _, p=prod: self.add_to_cart(p))
        layout.addWidget(btn_add)

        return card

    # ---------------------------------------------------------
    # Cart Operations
    # ---------------------------------------------------------
    def handle_barcode_scan(self):
        code = self.input_barcode.text().strip()
        if not code:
            return
        # Find product by exact barcode or SKU
        match = None
        for p in self.all_products:
            if p.get("barcode", "").lower() == code.lower() or p.get("sku", "").lower() == code.lower():
                match = p
                break
        if match:
            self.add_to_cart(match)
            self.input_barcode.clear()
        else:
            QMessageBox.warning(self, "Item Not Found", f"No catalog product found matching barcode/SKU '{code}'.")

    def add_to_cart(self, prod: Dict[str, Any]):
        """Add an item or increment quantity if already in cart."""
        p_id = prod.get("id") or prod.get("sku")
        existing = next((line for line in self.cart_lines if line.get("sku") == prod.get("sku")), None)

        if existing:
            existing["quantity"] += Decimal("1.00")
            existing["total_amount"] = existing["quantity"] * existing["unit_price"]
        else:
            price = to_decimal(prod.get("unit_price", 0))
            self.cart_lines.append({
                "product_id": prod.get("id"),
                "sku": prod.get("sku"),
                "barcode": prod.get("barcode"),
                "name": prod.get("name"),
                "category": prod.get("category", "General"),
                "unit_of_measure": prod.get("unit_of_measure", "UNIT"),
                "quantity": Decimal("1.00"),
                "unit_price": price,
                "discount_amount": Decimal("0.00"),
                "total_amount": price
            })

        self.update_cart_display()

    def update_cart_display(self):
        """Re-render cart table and recalculate itemized totals."""
        self.cart_table.setRowCount(len(self.cart_lines))

        for row, line in enumerate(self.cart_lines):
            # Name
            self.cart_table.setItem(row, 0, QTableWidgetItem(line["name"]))

            # Price
            self.cart_table.setItem(row, 1, QTableWidgetItem(f"₹{line['unit_price']:,.2f}"))

            # Qty with +/- buttons widget
            qty_widget = QWidget()
            qty_layout = QHBoxLayout(qty_widget)
            qty_layout.setContentsMargins(0, 0, 0, 0)
            qty_layout.setSpacing(4)

            btn_minus = QPushButton("-")
            btn_minus.setFixedSize(22, 22)
            btn_minus.clicked.connect(lambda _, r=row: self.adjust_qty(r, -1))
            qty_layout.addWidget(btn_minus)

            qty_lbl = QLabel(str(int(line["quantity"])))
            qty_lbl.setAlignment(Qt.AlignCenter)
            qty_layout.addWidget(qty_lbl)

            btn_plus = QPushButton("+")
            btn_plus.setFixedSize(22, 22)
            btn_plus.clicked.connect(lambda _, r=row: self.adjust_qty(r, 1))
            qty_layout.addWidget(btn_plus)

            self.cart_table.setCellWidget(row, 2, qty_widget)

            # Total
            total_amt = line["quantity"] * line["unit_price"]
            line["total_amount"] = total_amt
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"₹{total_amt:,.2f}"))

            # Remove action
            btn_remove = QPushButton("❌")
            btn_remove.setFixedSize(24, 24)
            btn_remove.setStyleSheet("color: red; font-size: 12px; background: transparent; border: none;")
            btn_remove.clicked.connect(lambda _, r=row: self.remove_from_cart(r))
            self.cart_table.setCellWidget(row, 4, btn_remove)

        # Calculate totals
        disc_pct = Decimal(str(self.spin_discount.value()))
        totals = calculate_pos_order_totals(self.cart_lines, discount_percent=disc_pct, tax_rate_percent=Decimal("12.00"))

        self.lbl_subtotal.setText(f"₹{totals['subtotal']:,.2f}")
        self.lbl_discount.setText(f"-₹{totals['discount_amount']:,.2f}")
        self.lbl_tax.setText(f"₹{totals['tax_amount']:,.2f}")
        self.lbl_total_due.setText(f"₹{totals['total_amount']:,.2f}")
        self.btn_pay.setText(f"💳 TENDER & PAY (F12) — ₹{totals['total_amount']:,.2f} ➔")

    def adjust_qty(self, row: int, delta: int):
        if 0 <= row < len(self.cart_lines):
            new_qty = self.cart_lines[row]["quantity"] + Decimal(str(delta))
            if new_qty <= Decimal("0"):
                self.remove_from_cart(row)
            else:
                self.cart_lines[row]["quantity"] = new_qty
                self.update_cart_display()

    def remove_from_cart(self, row: int):
        if 0 <= row < len(self.cart_lines):
            self.cart_lines.pop(row)
            self.update_cart_display()

    def clear_cart(self):
        self.cart_lines = []
        self.active_held_order_id = None
        self.order_num_lbl.setText("Sale Ticket: [Active Register]")
        self.update_cart_display()

    # ---------------------------------------------------------
    # Hold & Recall Order Operations
    # ---------------------------------------------------------
    def hold_current_order(self):
        if not self.cart_lines:
            QMessageBox.information(self, "Cart Empty", "Please add items to cart before parking an order.")
            return

        disc_pct = Decimal(str(self.spin_discount.value()))
        payload = {
            "session_id": self.active_session.get("id") if self.active_session else None,
            "customer_name": self.combo_customer.currentText(),
            "table_or_room": self.input_table_room.text().strip() or "Counter",
            "discount_percent": float(disc_pct),
            "tax_rate_percent": 12.00,
            "lines": [
                {
                    "sku": l["sku"],
                    "barcode": l.get("barcode"),
                    "name": l["name"],
                    "category": l["category"],
                    "unit_of_measure": l["unit_of_measure"],
                    "quantity": float(l["quantity"]),
                    "unit_price": float(l["unit_price"]),
                    "discount_amount": float(l["discount_amount"])
                }
                for l in self.cart_lines
            ],
            "notes": "Order parked at register"
        }

        # Create and hold order
        created = api_client.create_pos_order(payload)
        api_client.hold_pos_order(created["id"], reason="Customer browsing / waiting")

        QMessageBox.information(
            self,
            "Order Parked",
            f"Order {created['order_number']} has been parked to Held Orders queue."
        )
        self.clear_cart()
        self.refresh_data()

    def update_held_orders_counter(self):
        orders = api_client.get_pos_orders(status="HELD")
        self.btn_held_orders.setText(f"⏸️ Held Orders ({len(orders)})")

    def open_held_orders_dialog(self):
        dialog = HeldOrdersDialog(on_recall=self.recall_order_to_cart, parent=self)
        dialog.exec()

    def recall_order_to_cart(self, order_dict: Dict[str, Any]):
        """Populate current cart from recalled held order."""
        self.cart_lines = []
        for l in order_dict.get("lines", []):
            self.cart_lines.append({
                "product_id": l.get("product_id"),
                "sku": l.get("sku"),
                "barcode": l.get("barcode"),
                "name": l.get("name"),
                "category": l.get("category", "General"),
                "unit_of_measure": l.get("unit_of_measure", "UNIT"),
                "quantity": to_decimal(l.get("quantity", 1)),
                "unit_price": to_decimal(l.get("unit_price", 0)),
                "discount_amount": to_decimal(l.get("discount_amount", 0)),
                "total_amount": to_decimal(l.get("total_amount", 0))
            })
        self.active_held_order_id = order_dict["id"]
        self.order_num_lbl.setText(f"Sale Ticket: {order_dict['order_number']} [Recalled]")
        self.spin_discount.setValue(int(to_decimal(order_dict.get("discount_percent", 0))))
        self.input_table_room.setText(order_dict.get("table_or_room") or "")

        # Call recall endpoint on backend
        api_client.recall_pos_order(order_dict["id"])

        self.update_cart_display()
        self.tabs.setCurrentIndex(0)
        self.update_held_orders_counter()

    # ---------------------------------------------------------
    # Tender & Payment Checkout
    # ---------------------------------------------------------
    def open_tender_dialog(self):
        if not self.cart_lines:
            QMessageBox.information(self, "Cart Empty", "Please add items to cart before proceeding to checkout.")
            return

        disc_pct = Decimal(str(self.spin_discount.value()))
        totals = calculate_pos_order_totals(self.cart_lines, discount_percent=disc_pct, tax_rate_percent=Decimal("12.00"))
        total_due = totals["total_amount"]

        dialog = TenderDialog(
            total_amount=total_due,
            customer_name=self.combo_customer.currentText(),
            parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            tenders = dialog.get_tenders()

            # Ensure order exists on backend
            if self.active_held_order_id:
                order_id = self.active_held_order_id
            else:
                payload = {
                    "session_id": self.active_session.get("id") if self.active_session else None,
                    "customer_name": self.combo_customer.currentText(),
                    "table_or_room": self.input_table_room.text().strip() or "Counter",
                    "discount_percent": float(disc_pct),
                    "tax_rate_percent": 12.00,
                    "lines": [
                        {
                            "sku": l["sku"],
                            "barcode": l.get("barcode"),
                            "name": l["name"],
                            "category": l["category"],
                            "unit_of_measure": l["unit_of_measure"],
                            "quantity": float(l["quantity"]),
                            "unit_price": float(l["unit_price"]),
                            "discount_amount": float(l["discount_amount"])
                        }
                        for l in self.cart_lines
                    ],
                    "notes": "Standard POS register checkout"
                }
                created = api_client.create_pos_order(payload)
                order_id = created["id"]

            # Process payment tenders
            tender_payload = {
                "payments": [
                    {
                        "tender_type": t["tender_type"],
                        "amount": float(t["amount"]),
                        "reference_number": t.get("reference_number")
                    }
                    for t in tenders
                ],
                "notes": f"Tendered payment via {', '.join(t['tender_type'] for t in tenders)}"
            }
            completed_order = api_client.tender_pos_order(order_id, tender_payload)

            # Show thermal receipt dialog
            receipt_data = api_client.get_pos_receipt(order_id)
            rc_dialog = ReceiptDialog(receipt_data=receipt_data, parent=self)
            rc_dialog.exec()

            self.clear_cart()
            self.refresh_data()

    # ---------------------------------------------------------
    # Shift Drawer Reconcile & Close Dialog
    # ---------------------------------------------------------
    def open_close_shift_dialog(self):
        if not self.active_session:
            QMessageBox.information(self, "No Active Shift", "There is currently no open register shift session.")
            return

        dialog = CloseShiftDialog(session=self.active_session, parent=self)
        if dialog.exec() == QDialog.Accepted:
            counted = dialog.get_counted_cash()
            notes = dialog.get_notes()
            api_client.close_pos_session(self.active_session["id"], {"counted_cash": float(counted), "notes": notes})
            QMessageBox.information(self, "Shift Closed", "Cash register shift reconciled and closed successfully.")
            self.refresh_data()

    # ---------------------------------------------------------
    # Orders History Table
    # ---------------------------------------------------------
    def load_orders_table(self):
        status_filter = self.combo_order_filter.currentText()
        filt = None if status_filter == "ALL" else status_filter
        orders = api_client.get_pos_orders(status=filt, limit=100)

        self.orders_table.setRowCount(len(orders))
        for row, o in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(o.get("order_number", "")))

            created = o.get("created_at", "")
            time_str = created.split("T")[1][:8] if "T" in str(created) else str(created)[:19]
            self.orders_table.setItem(row, 1, QTableWidgetItem(time_str))

            cust = f"{o.get('customer_name', 'Guest')} ({o.get('table_or_room', 'Counter')})"
            self.orders_table.setItem(row, 2, QTableWidgetItem(cust))

            items_cnt = len(o.get("lines", []))
            self.orders_table.setItem(row, 3, QTableWidgetItem(f"{items_cnt} items"))

            sub = to_decimal(o.get("subtotal", 0))
            self.orders_table.setItem(row, 4, QTableWidgetItem(f"₹{sub:,.2f}"))

            tax = to_decimal(o.get("tax_amount", 0))
            self.orders_table.setItem(row, 5, QTableWidgetItem(f"₹{tax:,.2f}"))

            total = to_decimal(o.get("total_amount", 0))
            self.orders_table.setItem(row, 6, QTableWidgetItem(f"₹{total:,.2f}"))

            st = o.get("status", "")
            self.orders_table.setItem(row, 7, QTableWidgetItem(st))

            gl_ref = o.get("journal_entry_id") or "—"
            self.orders_table.setItem(row, 8, QTableWidgetItem(gl_ref))

    def view_selected_order_receipt(self):
        curr_row = self.orders_table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Select Order", "Please click on an order row to view its receipt.")
            return

        order_num = self.orders_table.item(curr_row, 0).text()
        orders = api_client.get_pos_orders(limit=100)
        selected = next((o for o in orders if o.get("order_number") == order_num), None)

        if selected:
            receipt_data = api_client.get_pos_receipt(selected["id"])
            rc_dialog = ReceiptDialog(receipt_data=receipt_data, parent=self)
            rc_dialog.exec()

    # ---------------------------------------------------------
    # Terminals Table
    # ---------------------------------------------------------
    def load_terminals_table(self):
        terms = api_client.get_pos_terminals()
        self.terminals_table.setRowCount(len(terms))
        for row, t in enumerate(terms):
            self.terminals_table.setItem(row, 0, QTableWidgetItem(t.get("terminal_code", "")))
            self.terminals_table.setItem(row, 1, QTableWidgetItem(t.get("counter_location", "")))
            self.terminals_table.setItem(row, 2, QTableWidgetItem(t.get("property_id", "")))
            self.terminals_table.setItem(row, 3, QTableWidgetItem(t.get("status", "")))
            active_str = "YES (Online)" if t.get("is_active") else "NO"
            self.terminals_table.setItem(row, 4, QTableWidgetItem(active_str))


# =============================================================
# MODALS & SUB-DIALOGS
# =============================================================
class TenderDialog(QDialog):
    """Multi-tender checkout payment modal with quick cash buttons and change calculator."""

    def __init__(self, total_amount: Decimal, customer_name: str, parent=None):
        super().__init__(parent)
        self.total_amount = total_amount
        self.customer_name = customer_name
        self.setWindowTitle("Process Payment Tender — Victory Crest ONE POS")
        self.resize(460, 480)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header Total
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setAlignment(Qt.AlignCenter)

        due_lbl = QLabel("TOTAL AMOUNT DUE")
        due_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {ThemeColors.TEXT_MUTED};")
        h_layout.addWidget(due_lbl, alignment=Qt.AlignCenter)

        self.amt_due_lbl = QLabel(f"₹{self.total_amount:,.2f}")
        self.amt_due_lbl.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {ThemeColors.PRIMARY_LIGHT};")
        h_layout.addWidget(self.amt_due_lbl, alignment=Qt.AlignCenter)

        cust_lbl = QLabel(f"Guest: {self.customer_name}")
        cust_lbl.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MAIN};")
        h_layout.addWidget(cust_lbl, alignment=Qt.AlignCenter)

        layout.addWidget(header_card)

        # Tender Type Selector
        form = QFormLayout()
        form.setSpacing(10)

        self.combo_tender = QComboBox()
        self.combo_tender.addItems(["CASH", "CREDIT_CARD", "UPI_QR", "ROOM_CHARGE"])
        self.combo_tender.currentTextChanged.connect(self.on_tender_type_changed)
        form.addRow("Payment Tender:", self.combo_tender)

        self.input_tendered = QDoubleSpinBox()
        self.input_tendered.setRange(0, 1000000)
        self.input_tendered.setDecimals(2)
        self.input_tendered.setValue(float(self.total_amount))
        self.input_tendered.setPrefix("₹ ")
        self.input_tendered.valueChanged.connect(self.update_change_calc)
        form.addRow("Tendered Amount:", self.input_tendered)

        self.input_ref = QLineEdit()
        self.input_ref.setPlaceholderText("Optional card last 4 / UPI UTR / Room folio #")
        form.addRow("Reference / Auth:", self.input_ref)

        layout.addLayout(form)

        # Quick Cash Buttons
        self.quick_cash_row = QHBoxLayout()
        self.quick_cash_row.setSpacing(8)
        quick_amounts = [
            ("Exact", float(self.total_amount)),
            ("₹500", 500.0),
            ("₹1,000", 1000.0),
            ("₹2,000", 2000.0),
            ("₹5,000", 5000.0)
        ]
        for label, val in quick_amounts:
            btn = QPushButton(label)
            btn.setProperty("class", "btn_secondary")
            btn.clicked.connect(lambda _, v=val: self.set_quick_cash(v))
            self.quick_cash_row.addWidget(btn)
        layout.addLayout(self.quick_cash_row)

        # Dynamic Change Calculator Display
        self.change_box = QFrame()
        self.change_box.setStyleSheet(f"""
            QFrame {{
                background: {ThemeColors.BG_SURFACE};
                border: 1px dashed {ThemeColors.STATUS_SUCCESS};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        c_layout = QHBoxLayout(self.change_box)
        c_layout.addWidget(QLabel("Change to Return to Guest:"))
        c_layout.addStretch()
        self.lbl_change = QLabel("₹0.00")
        self.lbl_change.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {ThemeColors.STATUS_SUCCESS};")
        c_layout.addWidget(self.lbl_change)
        layout.addWidget(self.change_box)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_confirm = QPushButton("✅ Complete Sale & Print Receipt")
        btn_confirm.setProperty("class", "btn_primary")
        btn_confirm.clicked.connect(self.validate_and_accept)
        btn_row.addWidget(btn_confirm)

        layout.addLayout(btn_row)

    def on_tender_type_changed(self, tender_type: str):
        is_cash = tender_type == "CASH"
        self.change_box.setVisible(is_cash)
        for i in range(self.quick_cash_row.count()):
            w = self.quick_cash_row.itemAt(i).widget()
            if w:
                w.setEnabled(is_cash)

    def set_quick_cash(self, amt: float):
        self.input_tendered.setValue(amt)
        self.update_change_calc()

    def update_change_calc(self):
        tendered = Decimal(str(self.input_tendered.value()))
        change = calculate_pos_change(tendered, self.total_amount)
        self.lbl_change.setText(f"₹{change:,.2f}")

    def validate_and_accept(self):
        tendered = Decimal(str(self.input_tendered.value()))
        if tendered < self.total_amount:
            QMessageBox.warning(
                self,
                "Insufficient Tender",
                f"Tendered amount ₹{tendered:,.2f} is less than total due ₹{self.total_amount:,.2f}."
            )
            return
        self.accept()

    def get_tenders(self) -> List[Dict[str, Any]]:
        tendered = Decimal(str(self.input_tendered.value()))
        return [{
            "tender_type": self.combo_tender.currentText(),
            "amount": tendered,
            "reference_number": self.input_ref.text().strip() or None
        }]


class ReceiptDialog(QDialog):
    """Formatted enterprise thermal receipt dialog with GL posting reference."""

    def __init__(self, receipt_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.receipt = receipt_data
        self.setWindowTitle(f"Receipt — {self.receipt.get('order_number')}")
        self.resize(440, 580)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        receipt_frame = QFrame()
        receipt_frame.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                color: #111827;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 16px;
                font-family: 'Courier New', Courier, monospace;
            }}
        """)
        rf_layout = QVBoxLayout(receipt_frame)
        rf_layout.setSpacing(4)

        # Receipt Header
        rf_layout.addWidget(QLabel("👑 VICTORY CREST ONE"), alignment=Qt.AlignCenter)
        tag_lbl = QLabel("One Platform. Every Business. Complete Control.")
        tag_lbl.setStyleSheet("font-size: 10px; color: #4B5563;")
        rf_layout.addWidget(tag_lbl, alignment=Qt.AlignCenter)

        prop_lbl = QLabel(self.receipt.get("property_name", "Victory Crest Hotel"))
        prop_lbl.setStyleSheet("font-weight: bold; font-size: 11px;")
        rf_layout.addWidget(prop_lbl, alignment=Qt.AlignCenter)

        line_sep = QLabel("----------------------------------------")
        rf_layout.addWidget(line_sep, alignment=Qt.AlignCenter)

        meta_info = (
            f"Receipt #: {self.receipt.get('order_number')}\n"
            f"Terminal:  {self.receipt.get('terminal_code')}\n"
            f"Cashier:   {self.receipt.get('cashier_name')}\n"
            f"Customer:  {self.receipt.get('customer_name')}\n"
            f"Date/Time: {str(self.receipt.get('timestamp'))[:19]}"
        )
        rf_layout.addWidget(QLabel(meta_info))

        rf_layout.addWidget(QLabel("----------------------------------------"), alignment=Qt.AlignCenter)

        # Lines table
        rf_layout.addWidget(QLabel(f"{'ITEM':<20} {'QTY':<4} {'PRICE':<7} {'TOTAL':>7}"))
        for item in self.receipt.get("lines", []):
            name = item.get("name", "")[:18]
            qty = int(to_decimal(item.get("quantity", 1)))
            price = to_decimal(item.get("unit_price", 0))
            tot = to_decimal(item.get("total_amount", 0))
            line_str = f"{name:<20} {qty:<4} {price:>7.2f} {tot:>7.2f}"
            rf_layout.addWidget(QLabel(line_str))

        rf_layout.addWidget(QLabel("----------------------------------------"), alignment=Qt.AlignCenter)

        # Totals
        sub = to_decimal(self.receipt.get("subtotal", 0))
        tax = to_decimal(self.receipt.get("tax_amount", 0))
        tot = to_decimal(self.receipt.get("total_amount", 0))
        paid = to_decimal(self.receipt.get("paid_amount", 0))
        change = to_decimal(self.receipt.get("change_returned", 0))

        rf_layout.addWidget(QLabel(f"{'SUBTOTAL:':<24} ₹{sub:>12.2f}"))
        rf_layout.addWidget(QLabel(f"{'GST TAX (12%):':<24} ₹{tax:>12.2f}"))
        rf_layout.addWidget(QLabel(f"{'TOTAL DUE:':<24} ₹{tot:>12.2f}"))
        rf_layout.addWidget(QLabel(f"{'TENDERED:':<24} ₹{paid:>12.2f}"))
        rf_layout.addWidget(QLabel(f"{'CHANGE RETURNED:':<24} ₹{change:>12.2f}"))

        rf_layout.addWidget(QLabel("----------------------------------------"), alignment=Qt.AlignCenter)

        # GL Journal Reference
        gl_ref = self.receipt.get("journal_entry_id") or "Auto-Posted"
        gl_lbl = QLabel(f"GL Journal Post: {gl_ref}\n(Balanced Double-Entry Posted)")
        gl_lbl.setStyleSheet("font-size: 10px; color: #059669; font-weight: bold;")
        rf_layout.addWidget(gl_lbl, alignment=Qt.AlignCenter)

        footer = QLabel(self.receipt.get("footer_message", "Thank you for your visit!"))
        footer.setStyleSheet("font-size: 10px; color: #4B5563; font-style: italic;")
        rf_layout.addWidget(footer, alignment=Qt.AlignCenter)

        layout.addWidget(receipt_frame)

        # Close / Print button
        btn_close = QPushButton("🖨️ Print Receipt & Close")
        btn_close.setProperty("class", "btn_primary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class HeldOrdersDialog(QDialog):
    """Dialog displaying parked / held orders with 1-click recall."""

    def __init__(self, on_recall, parent=None):
        super().__init__(parent)
        self.on_recall = on_recall
        self.setWindowTitle("Parked / Held Orders Queue — Victory Crest ONE POS")
        self.resize(540, 360)
        self.setup_ui()
        self.load_held_orders()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QLabel("Parked Orders Waiting at Register")
        header.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Order #", "Customer / Table", "Items", "Total Due", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "btn_secondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def load_held_orders(self):
        orders = api_client.get_pos_orders(status="HELD")
        self.table.setRowCount(len(orders))
        for row, o in enumerate(orders):
            self.table.setItem(row, 0, QTableWidgetItem(o.get("order_number", "")))
            cust = f"{o.get('customer_name', 'Guest')} ({o.get('table_or_room', 'Table')})"
            self.table.setItem(row, 1, QTableWidgetItem(cust))

            items_cnt = len(o.get("lines", []))
            self.table.setItem(row, 2, QTableWidgetItem(f"{items_cnt} items"))

            tot = to_decimal(o.get("total_amount", 0))
            self.table.setItem(row, 3, QTableWidgetItem(f"₹{tot:,.2f}"))

            btn_recall = QPushButton("↩️ Recall")
            btn_recall.setProperty("class", "btn_primary")
            btn_recall.clicked.connect(lambda _, ord_dict=o: self.trigger_recall(ord_dict))
            self.table.setCellWidget(row, 4, btn_recall)

    def trigger_recall(self, ord_dict: Dict[str, Any]):
        self.on_recall(ord_dict)
        self.accept()


class CloseShiftDialog(QDialog):
    """End-of-Shift Cash Drawer Reconciliation Modal."""

    def __init__(self, session: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("End Shift & Reconcile Drawer — Victory Crest ONE POS")
        self.resize(460, 420)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel(f"Reconcile Cash Drawer — {self.session.get('terminal_code')}")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        open_float = to_decimal(self.session.get("opening_float", 0))
        form.addRow("Opening Float:", QLabel(f"₹{open_float:,.2f}"))

        cash_sales = to_decimal(self.session.get("total_cash_sales", 0))
        form.addRow("Cash Sales (Net):", QLabel(f"₹{cash_sales:,.2f}"))

        card_sales = to_decimal(self.session.get("total_card_sales", 0))
        form.addRow("Card / Digital Sales:", QLabel(f"₹{card_sales:,.2f}"))

        self.expected_cash = open_float + cash_sales
        lbl_exp = QLabel(f"₹{self.expected_cash:,.2f}")
        lbl_exp.setStyleSheet(f"font-weight: 800; font-size: 14px; color: {ThemeColors.PRIMARY_LIGHT};")
        form.addRow("Expected Drawer Cash:", lbl_exp)

        self.input_counted = QDoubleSpinBox()
        self.input_counted.setRange(0, 1000000)
        self.input_counted.setDecimals(2)
        self.input_counted.setValue(float(self.expected_cash))
        self.input_counted.setPrefix("₹ ")
        self.input_counted.valueChanged.connect(self.update_variance)
        form.addRow("Counted Cash in Drawer:", self.input_counted)

        self.lbl_variance = QLabel("₹0.00 (Balanced)")
        self.lbl_variance.setStyleSheet(f"font-weight: 800; color: {ThemeColors.STATUS_SUCCESS};")
        form.addRow("Variance (Over/Short):", self.lbl_variance)

        self.input_notes = QLineEdit()
        self.input_notes.setPlaceholderText("Optional end-of-shift reconciliation notes")
        form.addRow("Shift Notes:", self.input_notes)

        layout.addLayout(form)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_confirm = QPushButton("🔒 Finalize & Close Register Shift")
        btn_confirm.setProperty("class", "btn_primary")
        btn_confirm.clicked.connect(self.accept)
        btn_row.addWidget(btn_confirm)

        layout.addLayout(btn_row)

    def update_variance(self):
        counted = Decimal(str(self.input_counted.value()))
        variance = calculate_drawer_variance(counted, self.expected_cash)
        if variance == Decimal("0.00"):
            self.lbl_variance.setText("₹0.00 (Balanced)")
            self.lbl_variance.setStyleSheet(f"font-weight: 800; color: {ThemeColors.STATUS_SUCCESS};")
        elif variance > Decimal("0.00"):
            self.lbl_variance.setText(f"+₹{variance:,.2f} (Overage)")
            self.lbl_variance.setStyleSheet(f"font-weight: 800; color: {ThemeColors.PRIMARY_LIGHT};")
        else:
            self.lbl_variance.setText(f"-₹{abs(variance):,.2f} (Shortage)")
            self.lbl_variance.setStyleSheet(f"font-weight: 800; color: red;")

    def get_counted_cash(self) -> Decimal:
        return Decimal(str(self.input_counted.value()))

    def get_notes(self) -> str:
        return self.input_notes.text().strip()
