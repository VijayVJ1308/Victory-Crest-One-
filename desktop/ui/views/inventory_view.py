"""Victory Crest One - Supply Chain, ERP & Warehouse Inventory Desktop View
Multi-warehouse stock balances, procurement purchase orders, automated GL/AP receiving,
inter-warehouse transfers, replenishment alerts, and stocktaking cycle counts.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDoubleSpinBox, QDateEdit, QTextEdit, QScrollArea,
    QSpinBox, QGroupBox
)
from PySide6.QtCore import Qt, QDate

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from shared.calculations import to_decimal, calculate_po_totals, calculate_stock_variance


class InventoryView(QWidget):
    """Central Supply Chain, ERP & Warehouse Inventory Management Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_warehouses: List[Dict[str, Any]] = []
        self.cached_stocks: List[Dict[str, Any]] = []
        self.cached_pos: List[Dict[str, Any]] = []
        self.cached_alerts: List[Dict[str, Any]] = []
        self.cached_movements: List[Dict[str, Any]] = []
        self.cached_counts: List[Dict[str, Any]] = []

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # -----------------------------------------------------
        # 1. Header Section
        # -----------------------------------------------------
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("Supply Chain, ERP & Warehouse Inventory")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Multi-warehouse logistics, purchase orders, automated GL/AP receipts, inter-warehouse transfers, and stocktaking.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)
        header_row.addWidget(btn_refresh)

        btn_transfer = QPushButton("🚚 Transfer Stock")
        btn_transfer.setProperty("class", "btn_secondary")
        btn_transfer.clicked.connect(self.open_transfer_dialog)
        header_row.addWidget(btn_transfer)

        btn_new_po = QPushButton("📦 New Purchase Order")
        btn_new_po.setProperty("class", "btn_primary")
        btn_new_po.clicked.connect(self.open_new_po_dialog)
        header_row.addWidget(btn_new_po)

        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive KPI Summary Cards
        # -----------------------------------------------------
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_valuation = self.create_summary_card("Total Stock Valuation", "₹0.00", "AVCO Aggregate Valuation", ThemeColors.STATUS_SUCCESS)
        self.kpi_total_units = self.create_summary_card("Total Stock Units", "0", "Across All Warehouses", ThemeColors.PRIMARY_LIGHT)
        self.kpi_active_skus = self.create_summary_card("Active Catalog SKUs", "0", "Managed Line Items", ThemeColors.TEXT_MAIN)
        self.kpi_low_stock = self.create_summary_card("Replenishment Alerts", "0 Items", "Below Reorder Threshold", ThemeColors.STATUS_WARNING)
        self.kpi_open_pos = self.create_summary_card("Open Purchase Orders", "0 POs (₹0.00)", "Procurement Commitments", ThemeColors.ACCENT_PRIMARY)

        kpi_row.addWidget(self.kpi_valuation)
        kpi_row.addWidget(self.kpi_total_units)
        kpi_row.addWidget(self.kpi_active_skus)
        kpi_row.addWidget(self.kpi_low_stock)
        kpi_row.addWidget(self.kpi_open_pos)
        main_layout.addLayout(kpi_row)

        # -----------------------------------------------------
        # 3. Main Navigation Tabs
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
                padding: 10px 18px;
                margin-right: 4px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {ThemeColors.BG_SURFACE};
                color: {ThemeColors.PRIMARY_LIGHT};
                border-bottom: 2px solid {ThemeColors.PRIMARY_LIGHT};
            }}
        """)

        # Tab 1: Stock Balances & Catalog
        tab_stock = self.build_stock_tab()
        self.tabs.addTab(tab_stock, "🏭 Warehouse Stock Catalog")

        # Tab 2: Purchase Orders & Receiving
        tab_po = self.build_po_tab()
        self.tabs.addTab(tab_po, "📦 Purchase Orders & Receiving")

        # Tab 3: Replenishment Alerts
        tab_alerts = self.build_alerts_tab()
        self.tabs.addTab(tab_alerts, "⚠️ Replenishment Alerts")

        # Tab 4: Stock Transfers & Audit Movements
        tab_transfers = self.build_transfers_tab()
        self.tabs.addTab(tab_transfers, "🚚 Transfers & Movements")

        # Tab 5: Cycle Counts & Stocktaking
        tab_cycle = self.build_cycle_counts_tab()
        self.tabs.addTab(tab_cycle, "📋 Cycle Counts & Stocktaking")

        main_layout.addWidget(self.tabs)

    def create_summary_card(self, title: str, value: str, subtext: str, color_accent: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ThemeColors.TEXT_MUTED};")
        layout.addWidget(t_lbl)

        v_lbl = QLabel(value)
        v_lbl.setObjectName("kpi_value")
        v_lbl.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {color_accent};")
        layout.addWidget(v_lbl)

        s_lbl = QLabel(subtext)
        s_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        layout.addWidget(s_lbl)
        return card

    # ---------------------------------------------------------
    # TAB 1: Warehouse Stock Balances
    # ---------------------------------------------------------
    def build_stock_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.stock_search = QLineEdit()
        self.stock_search.setPlaceholderText("🔍 Search by SKU or product name...")
        self.stock_search.textChanged.connect(self.filter_stock_table)
        ctrl_row.addWidget(self.stock_search, 2)

        lbl_wh = QLabel("Warehouse:")
        lbl_wh.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_wh)

        self.stock_wh_combo = QComboBox()
        self.stock_wh_combo.addItem("All Warehouses", "")
        self.stock_wh_combo.currentIndexChanged.connect(self.filter_stock_table)
        ctrl_row.addWidget(self.stock_wh_combo, 2)

        lbl_cat = QLabel("Category:")
        lbl_cat.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_cat)

        self.stock_cat_combo = QComboBox()
        self.stock_cat_combo.addItems(["All Categories", "Beverages", "Bakery", "Snacks", "Boutique", "Merchandise", "Wellness", "Retail", "General"])
        self.stock_cat_combo.currentIndexChanged.connect(self.filter_stock_table)
        ctrl_row.addWidget(self.stock_cat_combo, 1)

        lbl_stat = QLabel("Status:")
        lbl_stat.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_stat)

        self.stock_status_combo = QComboBox()
        self.stock_status_combo.addItems(["All Statuses", "IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"])
        self.stock_status_combo.currentIndexChanged.connect(self.filter_stock_table)
        ctrl_row.addWidget(self.stock_status_combo, 1)

        layout.addLayout(ctrl_row)

        # Stock Table
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(11)
        self.stock_table.setHorizontalHeaderLabels([
            "SKU", "Product Name", "Warehouse", "Category", "UOM",
            "On Hand", "Available", "Reorder Pt", "Unit Cost (AVCO)", "Total Value", "Status"
        ])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stock_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.stock_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.stock_table.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeToContents)
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.stock_table)

        return container

    # ---------------------------------------------------------
    # TAB 2: Purchase Orders & Receiving (ERP)
    # ---------------------------------------------------------
    def build_po_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        lbl_po_stat = QLabel("PO Status:")
        lbl_po_stat.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_po_stat)

        self.po_status_combo = QComboBox()
        self.po_status_combo.addItems(["All Statuses", "ISSUED", "RECEIVED", "DRAFT", "CLOSED"])
        self.po_status_combo.currentIndexChanged.connect(self.populate_pos_table)
        ctrl_row.addWidget(self.po_status_combo)
        ctrl_row.addStretch()

        btn_view_po = QPushButton("👁️ View Details")
        btn_view_po.setProperty("class", "btn_secondary")
        btn_view_po.clicked.connect(self.view_selected_po_details)
        ctrl_row.addWidget(btn_view_po)

        btn_receive_po = QPushButton("📥 Receive Goods & Post to GL/AP")
        btn_receive_po.setProperty("class", "btn_primary")
        btn_receive_po.clicked.connect(self.receive_selected_po)
        ctrl_row.addWidget(btn_receive_po)

        layout.addLayout(ctrl_row)

        self.po_table = QTableWidget()
        self.po_table.setColumnCount(8)
        self.po_table.setHorizontalHeaderLabels([
            "PO Number", "Issue Date", "Supplier", "Delivery Depot",
            "Subtotal", "Tax (18%)", "Total Amount", "Status"
        ])
        self.po_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.po_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.po_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.po_table.setAlternatingRowColors(True)
        self.po_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.po_table)

        return container

    # ---------------------------------------------------------
    # TAB 3: Replenishment Alerts
    # ---------------------------------------------------------
    def build_alerts_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-left: 4px solid {ThemeColors.STATUS_WARNING};
                border-radius: 4px;
                padding: 10px 14px;
            }}
        """)
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(0, 0, 0, 0)
        lbl_msg = QLabel("⚠️ Automated Reorder Point Watchdog: The items below have breached their buffer safety threshold. Immediate replenishment purchase orders are recommended.")
        lbl_msg.setStyleSheet(f"color: {ThemeColors.TEXT_MAIN}; font-weight: 500;")
        b_layout.addWidget(lbl_msg)
        layout.addWidget(banner)

        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(8)
        self.alerts_table.setHorizontalHeaderLabels([
            "SKU", "Product Name", "Warehouse", "Stock on Hand",
            "Reorder Point", "Shortage Qty", "Suggested Order Qty", "Recommended Vendor"
        ])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alerts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.alerts_table.setAlternatingRowColors(True)
        self.alerts_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.alerts_table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_quick_po = QPushButton("⚡ Generate PO for Selected Alert")
        btn_quick_po.setProperty("class", "btn_primary")
        btn_quick_po.clicked.connect(self.generate_po_from_alert)
        btn_row.addWidget(btn_quick_po)
        layout.addLayout(btn_row)

        return container

    # ---------------------------------------------------------
    # TAB 4: Inter-Warehouse Transfers & Movements
    # ---------------------------------------------------------
    def build_transfers_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        ctrl_row = QHBoxLayout()
        lbl_mov = QLabel("Stock Movement Ledger (Receipts, Transfers, Issues, Adjustments):")
        lbl_mov.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_mov)
        ctrl_row.addStretch()

        btn_new_transfer = QPushButton("🚚 New Stock Transfer")
        btn_new_transfer.setProperty("class", "btn_primary")
        btn_new_transfer.clicked.connect(self.open_transfer_dialog)
        ctrl_row.addWidget(btn_new_transfer)
        layout.addLayout(ctrl_row)

        self.mov_table = QTableWidget()
        self.mov_table.setColumnCount(9)
        self.mov_table.setHorizontalHeaderLabels([
            "Movement #", "Type", "SKU", "Product Name", "Qty",
            "Unit Cost", "Total Value", "Reference Doc", "Timestamp"
        ])
        self.mov_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mov_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.mov_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.mov_table.setAlternatingRowColors(True)
        self.mov_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.mov_table)

        return container

    # ---------------------------------------------------------
    # TAB 5: Cycle Counts & Stocktaking
    # ---------------------------------------------------------
    def build_cycle_counts_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        ctrl_row = QHBoxLayout()
        lbl_cc = QLabel("Scheduled & Completed Stocktaking Cycle Counts:")
        lbl_cc.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
        ctrl_row.addWidget(lbl_cc)
        ctrl_row.addStretch()

        btn_new_cc = QPushButton("➕ Start Cycle Count")
        btn_new_cc.setProperty("class", "btn_secondary")
        btn_new_cc.clicked.connect(self.open_new_cycle_count_dialog)
        ctrl_row.addWidget(btn_new_cc)

        btn_reconcile = QPushButton("⚖️ Reconcile Counted Stock")
        btn_reconcile.setProperty("class", "btn_primary")
        btn_reconcile.clicked.connect(self.open_reconcile_dialog)
        ctrl_row.addWidget(btn_reconcile)
        layout.addLayout(ctrl_row)

        self.cc_table = QTableWidget()
        self.cc_table.setColumnCount(7)
        self.cc_table.setHorizontalHeaderLabels([
            "Session Code", "Warehouse", "Status", "Items Counted",
            "Variance Value", "Reconciled At", "Notes"
        ])
        self.cc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.cc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cc_table.setAlternatingRowColors(True)
        self.cc_table.setStyleSheet(self._table_stylesheet())
        layout.addWidget(self.cc_table)

        return container

    # ---------------------------------------------------------
    # Data Refresh & Table Populations
    # ---------------------------------------------------------
    def refresh_data(self):
        """Fetch live telemetry and populate all tabs and metric cards."""
        # 1. Fetch Warehouses
        self.cached_warehouses = api_client.get_warehouses()
        self.stock_wh_combo.blockSignals(True)
        curr_wh_data = self.stock_wh_combo.currentData()
        self.stock_wh_combo.clear()
        self.stock_wh_combo.addItem("All Warehouses", "")
        for w in self.cached_warehouses:
            self.stock_wh_combo.addItem(f"{w['name']} ({w['warehouse_code']})", w["id"])
        if curr_wh_data:
            idx = self.stock_wh_combo.findData(curr_wh_data)
            if idx >= 0:
                self.stock_wh_combo.setCurrentIndex(idx)
        self.stock_wh_combo.blockSignals(False)

        # 2. Fetch Metrics
        metrics = api_client.get_inventory_metrics()
        self.update_summary_card(self.kpi_valuation, f"₹{metrics.get('total_inventory_valuation', 0):,.2f}")
        self.update_summary_card(self.kpi_total_units, f"{metrics.get('total_stock_units', 0):,.0f} Units")
        self.update_summary_card(self.kpi_active_skus, f"{metrics.get('total_active_skus', 0)} SKUs")
        self.update_summary_card(self.kpi_low_stock, f"{metrics.get('low_stock_items_count', 0)} Items")
        self.update_summary_card(self.kpi_open_pos, f"{metrics.get('active_purchase_orders_count', 0)} POs (₹{metrics.get('total_open_po_value', 0):,.2f})")

        # 3. Fetch Stock Catalog
        self.cached_stocks = api_client.get_stock()
        self.populate_stock_table(self.cached_stocks)

        # 4. Fetch Purchase Orders
        self.cached_pos = api_client.get_purchase_orders()
        self.populate_pos_table()

        # 5. Fetch Replenishment Alerts
        self.cached_alerts = api_client.get_replenishment_alerts()
        self.populate_alerts_table()

        # 6. Fetch Stock Movements
        self.cached_movements = api_client.get_stock_movements(limit=50)
        self.populate_movements_table()

        # 7. Fetch Cycle Counts
        self.cached_counts = api_client.get_cycle_counts()
        self.populate_cycle_counts_table()

    def update_summary_card(self, card: QFrame, val: str):
        lbl = card.findChild(QLabel, "kpi_value")
        if lbl:
            lbl.setText(val)

    def populate_stock_table(self, stocks: List[Dict[str, Any]]):
        self.stock_table.setRowCount(0)
        for s in stocks:
            r = self.stock_table.rowCount()
            self.stock_table.insertRow(r)

            sku_item = QTableWidgetItem(s.get("sku", ""))
            sku_item.setData(Qt.UserRole, s)
            sku_item.setFont(self._bold_font())

            self.stock_table.setItem(r, 0, sku_item)
            self.stock_table.setItem(r, 1, QTableWidgetItem(s.get("product_name", "")))
            self.stock_table.setItem(r, 2, QTableWidgetItem(s.get("warehouse_name", "")))
            self.stock_table.setItem(r, 3, QTableWidgetItem(s.get("category", "")))
            self.stock_table.setItem(r, 4, QTableWidgetItem(s.get("unit_of_measure", "")))

            qoh = to_decimal(s.get("quantity_on_hand", 0))
            qavail = to_decimal(s.get("quantity_available", 0))
            rop = to_decimal(s.get("reorder_point", 0))
            cost = to_decimal(s.get("unit_cost", 0))
            val = to_decimal(s.get("total_value", 0))

            qoh_item = QTableWidgetItem(f"{qoh:,.2f}")
            qavail_item = QTableWidgetItem(f"{qavail:,.2f}")
            rop_item = QTableWidgetItem(f"{rop:,.2f}")
            cost_item = QTableWidgetItem(f"₹{cost:,.2f}")
            val_item = QTableWidgetItem(f"₹{val:,.2f}")
            val_item.setFont(self._bold_font())

            self.stock_table.setItem(r, 5, qoh_item)
            self.stock_table.setItem(r, 6, qavail_item)
            self.stock_table.setItem(r, 7, rop_item)
            self.stock_table.setItem(r, 8, cost_item)
            self.stock_table.setItem(r, 9, val_item)

            stat = s.get("stock_status", "IN_STOCK")
            stat_item = QTableWidgetItem(stat)
            if stat == "LOW_STOCK":
                stat_item.setForeground(Qt.yellow)
            elif stat == "OUT_OF_STOCK":
                stat_item.setForeground(Qt.red)
            else:
                stat_item.setForeground(Qt.green)
            self.stock_table.setItem(r, 10, stat_item)

    def filter_stock_table(self):
        query = self.stock_search.text().strip().lower()
        wh_filter = self.stock_wh_combo.currentData()
        cat_filter = self.stock_cat_combo.currentText()
        stat_filter = self.stock_status_combo.currentText()

        filtered = []
        for s in self.cached_stocks:
            if wh_filter and s.get("warehouse_id") != wh_filter:
                continue
            if cat_filter != "All Categories" and s.get("category") != cat_filter:
                continue
            if stat_filter != "All Statuses" and s.get("stock_status") != stat_filter:
                continue
            if query:
                sku = s.get("sku", "").lower()
                name = s.get("product_name", "").lower()
                if query not in sku and query not in name:
                    continue
            filtered.append(s)

        self.populate_stock_table(filtered)

    def populate_pos_table(self):
        self.po_table.setRowCount(0)
        filter_stat = self.po_status_combo.currentText()

        for po in self.cached_pos:
            st = po.get("status", "DRAFT")
            if filter_stat != "All Statuses" and st != filter_stat:
                continue

            r = self.po_table.rowCount()
            self.po_table.insertRow(r)

            po_num_item = QTableWidgetItem(po.get("po_number", ""))
            po_num_item.setData(Qt.UserRole, po)
            po_num_item.setFont(self._bold_font())

            dt_raw = po.get("issue_date") or ""
            dt_str = str(dt_raw)[:10]

            self.po_table.setItem(r, 0, po_num_item)
            self.po_table.setItem(r, 1, QTableWidgetItem(dt_str))
            self.po_table.setItem(r, 2, QTableWidgetItem(po.get("supplier_name", "")))
            self.po_table.setItem(r, 3, QTableWidgetItem(po.get("warehouse_name", "")))

            sub = to_decimal(po.get("subtotal", 0))
            tax = to_decimal(po.get("tax_amount", 0))
            tot = to_decimal(po.get("total_amount", 0))

            self.po_table.setItem(r, 4, QTableWidgetItem(f"₹{sub:,.2f}"))
            self.po_table.setItem(r, 5, QTableWidgetItem(f"₹{tax:,.2f}"))

            tot_item = QTableWidgetItem(f"₹{tot:,.2f}")
            tot_item.setFont(self._bold_font())
            self.po_table.setItem(r, 6, tot_item)

            st_item = QTableWidgetItem(st)
            if st == "RECEIVED":
                st_item.setForeground(Qt.green)
            elif st == "ISSUED":
                st_item.setForeground(Qt.cyan)
            else:
                st_item.setForeground(Qt.yellow)
            self.po_table.setItem(r, 7, st_item)

    def populate_alerts_table(self):
        self.alerts_table.setRowCount(0)
        for a in self.cached_alerts:
            r = self.alerts_table.rowCount()
            self.alerts_table.insertRow(r)

            sku_item = QTableWidgetItem(a.get("sku", ""))
            sku_item.setData(Qt.UserRole, a)
            sku_item.setFont(self._bold_font())
            sku_item.setForeground(Qt.yellow)

            self.alerts_table.setItem(r, 0, sku_item)
            self.alerts_table.setItem(r, 1, QTableWidgetItem(a.get("product_name", "")))
            self.alerts_table.setItem(r, 2, QTableWidgetItem(a.get("warehouse_name", "")))

            qoh = to_decimal(a.get("quantity_on_hand", 0))
            rop = to_decimal(a.get("reorder_point", 0))
            short = to_decimal(a.get("shortage_quantity", 0))
            sug = to_decimal(a.get("suggested_order_quantity", 0))

            self.alerts_table.setItem(r, 3, QTableWidgetItem(f"{qoh:,.2f}"))
            self.alerts_table.setItem(r, 4, QTableWidgetItem(f"{rop:,.2f}"))

            short_item = QTableWidgetItem(f"{short:,.2f}")
            short_item.setForeground(Qt.red)
            short_item.setFont(self._bold_font())
            self.alerts_table.setItem(r, 5, short_item)

            sug_item = QTableWidgetItem(f"{sug:,.0f} units")
            sug_item.setForeground(Qt.green)
            sug_item.setFont(self._bold_font())
            self.alerts_table.setItem(r, 6, sug_item)

            self.alerts_table.setItem(r, 7, QTableWidgetItem(a.get("recommended_supplier_name", "Primary Vendor")))

    def populate_movements_table(self):
        self.mov_table.setRowCount(0)
        for m in self.cached_movements:
            r = self.mov_table.rowCount()
            self.mov_table.insertRow(r)

            m_num = QTableWidgetItem(m.get("movement_number", ""))
            m_num.setFont(self._bold_font())
            self.mov_table.setItem(r, 0, m_num)

            m_type = m.get("movement_type", "")
            m_type_item = QTableWidgetItem(m_type)
            if m_type == "RECEIPT":
                m_type_item.setForeground(Qt.green)
            elif m_type == "TRANSFER":
                m_type_item.setForeground(Qt.cyan)
            else:
                m_type_item.setForeground(Qt.yellow)
            self.mov_table.setItem(r, 1, m_type_item)

            self.mov_table.setItem(r, 2, QTableWidgetItem(m.get("sku", "")))
            self.mov_table.setItem(r, 3, QTableWidgetItem(m.get("product_name", "")))

            qty = to_decimal(m.get("quantity", 0))
            cost = to_decimal(m.get("unit_cost", 0))
            val = to_decimal(m.get("total_value", 0))

            self.mov_table.setItem(r, 4, QTableWidgetItem(f"{qty:,.2f}"))
            self.mov_table.setItem(r, 5, QTableWidgetItem(f"₹{cost:,.2f}"))

            val_item = QTableWidgetItem(f"₹{val:,.2f}")
            val_item.setFont(self._bold_font())
            self.mov_table.setItem(r, 6, val_item)

            self.mov_table.setItem(r, 7, QTableWidgetItem(m.get("reference_doc") or "DIRECT"))
            self.mov_table.setItem(r, 8, QTableWidgetItem(str(m.get("created_at", ""))[:19]))

    def populate_cycle_counts_table(self):
        self.cc_table.setRowCount(0)
        for c in self.cached_counts:
            r = self.cc_table.rowCount()
            self.cc_table.insertRow(r)

            code_item = QTableWidgetItem(c.get("session_code", ""))
            code_item.setData(Qt.UserRole, c)
            code_item.setFont(self._bold_font())
            self.cc_table.setItem(r, 0, code_item)

            self.cc_table.setItem(r, 1, QTableWidgetItem(c.get("warehouse_name", "")))

            st = c.get("status", "OPEN")
            st_item = QTableWidgetItem(st)
            if st == "RECONCILED":
                st_item.setForeground(Qt.green)
            else:
                st_item.setForeground(Qt.yellow)
            self.cc_table.setItem(r, 2, st_item)

            self.cc_table.setItem(r, 3, QTableWidgetItem(str(c.get("total_items_counted", 0))))

            v_val = to_decimal(c.get("total_variance_value", 0))
            v_item = QTableWidgetItem(f"₹{v_val:,.2f}")
            if v_val != Decimal("0.00"):
                v_item.setForeground(Qt.red)
            self.cc_table.setItem(r, 4, v_item)

            rec_at = str(c.get("reconciled_at") or "Pending")[:19]
            self.cc_table.setItem(r, 5, QTableWidgetItem(rec_at))
            self.cc_table.setItem(r, 6, QTableWidgetItem(c.get("notes") or ""))

    # ---------------------------------------------------------
    # Dialogs & User Actions
    # ---------------------------------------------------------
    def open_new_po_dialog(self, prefill_alert: Optional[Dict[str, Any]] = None):
        """Open modal to issue a new Purchase Order."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Issue Procurement Purchase Order (ERP) — Victory Crest ONE")
        dialog.resize(600, 520)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        form = QFormLayout()

        supp_combo = QComboBox()
        supp_combo.addItem("Coimbatore Luxury Linens & Fabrics", "supp_linen_textiles")
        supp_combo.addItem("Nilgiri Organics & Gourmet Supplies", "supp_organic_foods")
        supp_combo.addItem("Madurai Fresh Produce & Dairy Ltd", "supp_dairy_fresh")
        form.addRow("Supplier:", supp_combo)

        wh_combo = QComboBox()
        for w in self.cached_warehouses:
            wh_combo.addItem(w["name"], w["id"])
        form.addRow("Receiving Warehouse:", wh_combo)

        tax_spin = QDoubleSpinBox()
        tax_spin.setRange(0, 30)
        tax_spin.setValue(18.0)
        tax_spin.setSuffix(" %")
        form.addRow("Tax Rate (GST):", tax_spin)

        # Line Item Box
        item_group = QGroupBox("Order Line Item")
        item_layout = QFormLayout(item_group)

        sku_edit = QLineEdit()
        name_edit = QLineEdit()
        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(1, 10000)
        qty_spin.setValue(10)

        price_spin = QDoubleSpinBox()
        price_spin.setRange(1, 100000)
        price_spin.setValue(500.0)
        price_spin.setPrefix("₹ ")

        if prefill_alert:
            sku_edit.setText(prefill_alert.get("sku", ""))
            name_edit.setText(prefill_alert.get("product_name", ""))
            sug_qty = float(prefill_alert.get("suggested_order_quantity", 10))
            qty_spin.setValue(sug_qty)
            wh_id = prefill_alert.get("warehouse_id")
            if wh_id:
                idx = wh_combo.findData(wh_id)
                if idx >= 0:
                    wh_combo.setCurrentIndex(idx)
        else:
            sku_edit.setText("RAW-COF-ARABICA")
            name_edit.setText("Estate Arabica Green & Roasted Coffee Beans 5kg")
            price_spin.setValue(2500.0)

        item_layout.addRow("Item SKU:", sku_edit)
        item_layout.addRow("Description / Name:", name_edit)
        item_layout.addRow("Quantity Ordered:", qty_spin)
        item_layout.addRow("Unit Price:", price_spin)

        form.addRow(item_group)

        notes_edit = QTextEdit()
        notes_edit.setMaximumHeight(60)
        notes_edit.setPlaceholderText("Procurement specifications, delivery notes, or terms...")
        form.addRow("Notes:", notes_edit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("📦 Issue Purchase Order")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            sku = sku_edit.text().strip()
            name = name_edit.text().strip()
            if not sku or not name:
                QMessageBox.warning(dialog, "Validation Error", "SKU and Item Name are required.")
                return

            po_payload = {
                "supplier_id": supp_combo.currentData(),
                "supplier_name": supp_combo.currentText(),
                "warehouse_id": wh_combo.currentData(),
                "payment_terms_days": 30,
                "tax_rate_percent": float(tax_spin.value()),
                "lines": [
                    {
                        "sku": sku,
                        "name": name,
                        "unit_of_measure": "UNIT",
                        "quantity_ordered": float(qty_spin.value()),
                        "unit_price": float(price_spin.value())
                    }
                ],
                "notes": notes_edit.toPlainText().strip()
            }
            try:
                res = api_client.create_purchase_order(po_payload)
                QMessageBox.information(
                    dialog, "PO Issued Successfully",
                    f"Purchase Order {res.get('po_number')} created for ₹{res.get('total_amount', 0):,.2f}!\nStatus: ISSUED to {res.get('supplier_name')}."
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to issue PO: {str(e)}")

        btn_submit.clicked.connect(submit)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)

        dialog.exec()

    def receive_selected_po(self):
        """Receive goods for selected PO, posting to GL and AP."""
        row = self.po_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Purchase Order", "Please select a Purchase Order to receive goods.")
            return

        po_data = self.po_table.item(row, 0).data(Qt.UserRole)
        if not po_data:
            return

        if po_data.get("status") == "RECEIVED":
            QMessageBox.information(self, "Already Received", f"PO {po_data.get('po_number')} is already fully received.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Receiving & Finance Posting",
            f"Receive goods for {po_data.get('po_number')} from {po_data.get('supplier_name')}?\n\n"
            f"Total Amount: ₹{to_decimal(po_data.get('total_amount', 0)):,.2f}\n"
            f"This will:\n"
            f"1. Increment physical stock balances in warehouse: {po_data.get('warehouse_name')}\n"
            f"2. Recalculate Weighted Average Cost (AVCO)\n"
            f"3. Generate Goods Receipt Note (GRN)\n"
            f"4. Post balanced GL Journal Entry (DR 1200 Inventory Asset, CR 2010 AP Liability)\n"
            f"5. Create Accounts Payable Supplier Bill in Phase 4 Finance",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                res = api_client.receive_purchase_order(po_data["id"], {"notes": "Full receiving at logistics bay"})
                QMessageBox.information(
                    self,
                    "Receiving & Automated GL Posting Complete",
                    f"Goods received successfully for {res.get('po_number')}!\n\n"
                    f"Stock balances updated.\n"
                    f"Automated GL Journal and Accounts Payable bill generated."
                )
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Receiving Error", f"Failed to receive goods: {str(e)}")

    def view_selected_po_details(self):
        row = self.po_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Purchase Order", "Please select a Purchase Order to view details.")
            return

        po_data = self.po_table.item(row, 0).data(Qt.UserRole)
        if not po_data:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Purchase Order Details — {po_data.get('po_number')}")
        dialog.resize(550, 420)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        header_lbl = QLabel(f"📦 {po_data.get('po_number')} — {po_data.get('status')}")
        header_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header_lbl)

        info_lbl = QLabel(f"Supplier: {po_data.get('supplier_name')}\nWarehouse: {po_data.get('warehouse_name')}\nTotal: ₹{to_decimal(po_data.get('total_amount', 0)):,.2f}")
        info_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(info_lbl)

        lines_table = QTableWidget()
        lines_table.setColumnCount(5)
        lines_table.setHorizontalHeaderLabels(["SKU", "Item Name", "Qty Ordered", "Unit Price", "Total"])
        lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lines_table.setStyleSheet(self._table_stylesheet())

        lines = po_data.get("lines", [])
        lines_table.setRowCount(len(lines))
        for idx, l in enumerate(lines):
            lines_table.setItem(idx, 0, QTableWidgetItem(l.get("sku", "")))
            lines_table.setItem(idx, 1, QTableWidgetItem(l.get("name", "")))
            lines_table.setItem(idx, 2, QTableWidgetItem(f"{to_decimal(l.get('quantity_ordered', 0)):,.2f}"))
            lines_table.setItem(idx, 3, QTableWidgetItem(f"₹{to_decimal(l.get('unit_price', 0)):,.2f}"))
            lines_table.setItem(idx, 4, QTableWidgetItem(f"₹{to_decimal(l.get('total_amount', 0)):,.2f}"))

        layout.addWidget(lines_table)

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "btn_secondary")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.exec()

    def generate_po_from_alert(self):
        row = self.alerts_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Alert", "Please select a replenishment alert row to generate a PO.")
            return

        alert_data = self.alerts_table.item(row, 0).data(Qt.UserRole)
        self.open_new_po_dialog(prefill_alert=alert_data)

    def open_transfer_dialog(self):
        """Open inter-warehouse transfer modal."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Inter-Warehouse Stock Transfer — Victory Crest ONE")
        dialog.resize(500, 360)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        form = QFormLayout()

        source_wh = QComboBox()
        target_wh = QComboBox()
        for w in self.cached_warehouses:
            source_wh.addItem(w["name"], w["id"])
            target_wh.addItem(w["name"], w["id"])

        if len(self.cached_warehouses) > 1:
            target_wh.setCurrentIndex(1)

        form.addRow("Source Warehouse:", source_wh)
        form.addRow("Target Warehouse:", target_wh)

        sku_combo = QComboBox()

        def update_sku_options():
            sku_combo.clear()
            wh_id = source_wh.currentData()
            for s in self.cached_stocks:
                if s.get("warehouse_id") == wh_id:
                    avail = to_decimal(s.get("quantity_available", 0))
                    sku_combo.addItem(f"{s.get('sku')} - {s.get('product_name')} (Avail: {avail})", s.get("sku"))

        source_wh.currentIndexChanged.connect(update_sku_options)
        update_sku_options()
        form.addRow("Select Item to Transfer:", sku_combo)

        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(1, 10000)
        qty_spin.setValue(10)
        form.addRow("Transfer Quantity:", qty_spin)

        notes_edit = QLineEdit()
        notes_edit.setPlaceholderText("Transfer justification or vehicle/gate pass ref...")
        form.addRow("Notes:", notes_edit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("🚚 Execute Transfer")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            src_id = source_wh.currentData()
            tgt_id = target_wh.currentData()
            if src_id == tgt_id:
                QMessageBox.warning(dialog, "Transfer Error", "Source and target warehouses cannot be identical.")
                return

            sku = sku_combo.currentData()
            if not sku:
                QMessageBox.warning(dialog, "Transfer Error", "Please select an item to transfer.")
                return

            payload = {
                "source_warehouse_id": src_id,
                "target_warehouse_id": tgt_id,
                "sku": sku,
                "quantity": float(qty_spin.value()),
                "notes": notes_edit.text().strip()
            }
            try:
                res = api_client.transfer_stock(payload)
                QMessageBox.information(
                    dialog, "Transfer Completed",
                    f"Transferred {res.get('quantity')} units of {sku}!\nMovement Number: {res.get('movement_number')}"
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Transfer Error", f"Transfer failed: {str(e)}")

        btn_submit.clicked.connect(submit)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_new_cycle_count_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Initiate Stocktaking Cycle Count Session — Victory Crest ONE")
        dialog.resize(460, 260)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)

        form = QFormLayout()

        wh_combo = QComboBox()
        for w in self.cached_warehouses:
            wh_combo.addItem(w["name"], w["id"])
        form.addRow("Audit Warehouse:", wh_combo)

        notes_edit = QLineEdit()
        notes_edit.setPlaceholderText("E.g., Quarterly linen & beverage stock verification...")
        form.addRow("Audit Notes:", notes_edit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("📋 Create Session")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            payload = {
                "warehouse_id": wh_combo.currentData(),
                "notes": notes_edit.text().strip()
            }
            try:
                res = api_client.create_cycle_count(payload)
                QMessageBox.information(
                    dialog, "Session Created",
                    f"Cycle count session {res.get('session_code')} initialized for {res.get('warehouse_name')}!"
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to initialize cycle count: {str(e)}")

        btn_submit.clicked.connect(submit)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_reconcile_dialog(self):
        """Open physical inventory reconciliation dialog."""
        row = self.cc_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Session", "Please select a cycle count session to reconcile.")
            return

        session_data = self.cc_table.item(row, 0).data(Qt.UserRole)
        if not session_data:
            return

        if session_data.get("status") == "RECONCILED":
            QMessageBox.information(self, "Already Reconciled", f"Session {session_data.get('session_code')} is already reconciled.")
            return

        wh_id = session_data.get("warehouse_id")
        wh_stocks = [s for s in self.cached_stocks if s.get("warehouse_id") == wh_id]

        if not wh_stocks:
            QMessageBox.information(self, "No Items", "No items found in this warehouse to count.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Reconcile Physical Inventory — {session_data.get('session_code')}")
        dialog.resize(650, 460)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        desc = QLabel(f"Enter physical counted quantities for warehouse: {session_data.get('warehouse_name')}")
        desc.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(desc)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["SKU", "Item Name", "Book Qty", "Counted Qty", "Unit Cost (₹)"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setStyleSheet(self._table_stylesheet())
        table.setRowCount(len(wh_stocks))

        spin_widgets = []
        for idx, s in enumerate(wh_stocks):
            table.setItem(idx, 0, QTableWidgetItem(s.get("sku", "")))
            table.setItem(idx, 1, QTableWidgetItem(s.get("product_name", "")))
            b_qty = to_decimal(s.get("quantity_on_hand", 0))
            table.setItem(idx, 2, QTableWidgetItem(f"{b_qty:,.2f}"))

            spin = QDoubleSpinBox()
            spin.setRange(0, 50000)
            spin.setValue(float(b_qty))  # default to book
            table.setCellWidget(idx, 3, spin)
            spin_widgets.append((s, spin))

            table.setItem(idx, 4, QTableWidgetItem(f"₹{to_decimal(s.get('unit_cost', 0)):,.2f}"))

        layout.addWidget(table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("⚖️ Reconcile & Adjust Ledger")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            variance_list = []
            for s, spin in spin_widgets:
                book = to_decimal(s.get("quantity_on_hand", 0))
                counted = to_decimal(spin.value())
                cost = to_decimal(s.get("unit_cost", 0))
                var_dict = calculate_stock_variance(book, counted, cost)

                variance_list.append({
                    "sku": s.get("sku"),
                    "product_name": s.get("product_name"),
                    "book_quantity": float(book),
                    "counted_quantity": float(counted),
                    "unit_cost": float(cost),
                    "variance_quantity": float(var_dict["variance_quantity"]),
                    "variance_value": float(var_dict["variance_value"]),
                    "is_discrepant": var_dict["is_discrepant"]
                })

            payload = {
                "counts": variance_list,
                "notes": "Physical audit verification reconciled against warehouse ledger"
            }
            try:
                res = api_client.reconcile_cycle_count(session_data["id"], payload)
                QMessageBox.information(
                    dialog, "Reconciliation Complete",
                    f"Session {res.get('session_code')} reconciled!\n"
                    f"Items Counted: {res.get('total_items_counted')}\n"
                    f"Total Discrepancy Value: ₹{res.get('total_variance_value', 0):,.2f}\n"
                    f"Inventory ledger adjusted."
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Reconciliation Error", f"Failed: {str(e)}")

        btn_submit.clicked.connect(submit)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)

        dialog.exec()

    # ---------------------------------------------------------
    # UI Styling Helpers
    # ---------------------------------------------------------
    def _bold_font(self):
        f = self.font()
        f.setBold(True)
        return f

    def _table_stylesheet(self) -> str:
        return f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                color: {ThemeColors.TEXT_MAIN};
                selection-background-color: {ThemeColors.BG_SECONDARY};
                selection-color: {ThemeColors.PRIMARY_LIGHT};
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_SECONDARY};
                color: {ThemeColors.TEXT_MUTED};
                padding: 6px;
                border: none;
                font-weight: 700;
                font-size: 11px;
            }}
        """
