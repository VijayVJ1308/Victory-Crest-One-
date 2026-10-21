"""Victory Crest One - Manufacturing & Production Management View
Work Centers, Multi-Level Bills of Materials (BOM), Production Orders (MO),
Component Explosion, Routing Steps, Quality Inspections, and Automated GL Costing.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date, timedelta
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
from shared.calculations import (
    to_decimal,
    calculate_bom_line_cost,
    calculate_bom_totals,
    calculate_production_order_cost
)


class ManufacturingView(QWidget):
    """Central Manufacturing & Production Operations Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_work_centers: List[Dict[str, Any]] = []
        self.cached_boms: List[Dict[str, Any]] = []
        self.cached_orders: List[Dict[str, Any]] = []
        self.cached_metrics: Dict[str, Any] = {}

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

        title = QLabel("Manufacturing & Production Orders / BOM")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Work centers, Bill of Materials recipe explosion, production routing, scrap control, and double-entry GL inventory absorption.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_new_order = QPushButton("➕ New Production Order")
        btn_new_order.setProperty("class", "btn_primary")
        btn_new_order.clicked.connect(self.open_create_production_order_dialog)

        btn_new_bom = QPushButton("📋 Create BOM")
        btn_new_bom.setProperty("class", "btn_primary")
        btn_new_bom.clicked.connect(self.open_create_bom_dialog)

        btn_new_wc = QPushButton("⚙️ Add Work Center")
        btn_new_wc.setProperty("class", "btn_secondary")
        btn_new_wc.clicked.connect(self.open_create_work_center_dialog)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_new_order)
        header_row.addWidget(btn_new_bom)
        header_row.addWidget(btn_new_wc)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_active_orders = self.create_metric_card("ACTIVE ORDERS", "0 Orders", "In-Process Production", "#3B82F6")
        self.card_units_produced = self.create_metric_card("UNITS PRODUCED", "0 Units", "Completed Finished Goods", "#10B981")
        self.card_scrap_rate = self.create_metric_card("SCRAP RATE", "0.0%", "Target Allowance ≤ 5.0%", "#F59E0B")
        self.card_wip_val = self.create_metric_card("WIP VALUATION", "₹0.00", "Work-in-Progress (DR 1220)", "#8B5CF6")
        self.card_capacity_util = self.create_metric_card("CAPACITY UTILIZATION", "0.0%", "Active Plant Load Factor", "#06B6D4")

        cards_row.addWidget(self.card_active_orders)
        cards_row.addWidget(self.card_units_produced)
        cards_row.addWidget(self.card_scrap_rate)
        cards_row.addWidget(self.card_wip_val)
        cards_row.addWidget(self.card_capacity_util)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Main Operational Tabs
        # -----------------------------------------------------
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
                background: {ThemeColors.BG_CARD};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {ThemeColors.BG_CARD};
                color: {ThemeColors.TEXT_MUTED};
                padding: 10px 18px;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {ThemeColors.TEXT_MAIN};
                border-bottom: 2px solid {ThemeColors.PRIMARY};
            }}
            QTabBar::tab:hover {{
                color: {ThemeColors.TEXT_MAIN};
            }}
        """)
        self.tabs = self.tab_widget

        # Tab 1: Production Orders
        self.tab_orders = QWidget()
        self.setup_orders_tab()
        self.tab_widget.addTab(self.tab_orders, "🏭 Production Orders (MO)")

        # Tab 2: Bill of Materials (BOM)
        self.tab_bom = QWidget()
        self.setup_bom_tab()
        self.tab_widget.addTab(self.tab_bom, "📑 Bills of Materials (BOM)")

        # Tab 3: Work Centers & Capacity
        self.tab_wc = QWidget()
        self.setup_work_centers_tab()
        self.tab_widget.addTab(self.tab_wc, "⚙️ Work Centers & Capacity")

        # Tab 4: Quality & Scrap Log
        self.tab_quality = QWidget()
        self.setup_quality_tab()
        self.tab_widget.addTab(self.tab_quality, "🔍 Quality & Scrap Checkpoints")

        # Tab 5: Manufacturing Telemetry & Cost Accounting
        self.tab_costing = QWidget()
        self.setup_costing_tab()
        self.tab_widget.addTab(self.tab_costing, "📊 Absorption Costing & GL")

        main_layout.addWidget(self.tab_widget)

    def create_metric_card(self, title: str, value: str, subtitle: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 14px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ThemeColors.TEXT_MUTED}; letter-spacing: 0.5px;")

        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color}; margin: 2px 0;")
        card.value_label = lbl_val  # Store handle for updating

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)
        return card

    # =========================================================================
    # Tab 1: Production Orders
    # =========================================================================
    def setup_orders_tab(self):
        layout = QVBoxLayout(self.tab_orders)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        lbl_filter = QLabel("Status:")
        lbl_filter.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")

        self.cb_order_status = QComboBox()
        self.cb_order_status.addItems(["All Statuses", "PLANNED", "IN_PROGRESS", "QUALITY_CHECK", "COMPLETED", "CANCELLED"])
        self.cb_order_status.currentTextChanged.connect(self.filter_orders_table)

        lbl_pri = QLabel("Priority:")
        lbl_pri.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        self.cb_order_priority = QComboBox()
        self.cb_order_priority.addItems(["All Priorities", "LOW", "NORMAL", "HIGH", "URGENT"])
        self.cb_order_priority.currentTextChanged.connect(self.filter_orders_table)

        self.txt_order_search = QLineEdit()
        self.txt_order_search.setPlaceholderText("Search Order #, product name, or supervisor...")
        self.txt_order_search.textChanged.connect(self.filter_orders_table)

        filter_row.addWidget(lbl_filter)
        filter_row.addWidget(self.cb_order_status)
        filter_row.addWidget(lbl_pri)
        filter_row.addWidget(self.cb_order_priority)
        filter_row.addWidget(self.txt_order_search)
        filter_row.addStretch()

        layout.addLayout(filter_row)

        # Production Orders Table
        self.table_orders = QTableWidget()
        self.table_orders.setColumnCount(11)
        self.table_orders.setHorizontalHeaderLabels([
            "Order #", "Product Name", "BOM Code", "Target Qty", "Produced",
            "Status", "Priority", "Work Center", "Supervisor", "Total Cost", "Actions"
        ])
        self.table_orders.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_orders.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_orders.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_orders.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_orders.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_orders.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table_orders.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeToContents)
        self.table_orders.verticalHeader().setVisible(False)
        self.table_orders.setAlternatingRowColors(True)

        layout.addWidget(self.table_orders)

    def filter_orders_table(self):
        st_filter = self.cb_order_status.currentText().upper()
        pri_filter = self.cb_order_priority.currentText().upper()
        search_txt = self.txt_order_search.text().lower().strip()

        filtered = []
        for o in self.cached_orders:
            if st_filter != "ALL STATUSES" and o.get("status", "").upper() != st_filter:
                continue
            if pri_filter != "ALL PRIORITIES" and o.get("priority", "").upper() != pri_filter:
                continue
            if search_txt:
                q_text = f"{o.get('order_number', '')} {o.get('product_name', '')} {o.get('supervisor_name', '')}".lower()
                if search_txt not in q_text:
                    continue
            filtered.append(o)

        self.populate_orders_table(filtered)

    def populate_orders_table(self, orders: List[Dict[str, Any]]):
        self.table_orders.setRowCount(0)
        for row, o in enumerate(orders):
            self.table_orders.insertRow(row)

            item_num = QTableWidgetItem(o.get("order_number", ""))
            item_num.setFont(self.font())
            item_num.setTextAlignment(Qt.AlignCenter)

            item_prd = QTableWidgetItem(o.get("product_name", ""))
            item_bom = QTableWidgetItem(o.get("bom_code", ""))

            t_qty = to_decimal(o.get("target_quantity", 0))
            p_qty = to_decimal(o.get("produced_quantity", 0))
            item_tqty = QTableWidgetItem(f"{t_qty:.0f}")
            item_tqty.setTextAlignment(Qt.AlignCenter)

            item_pqty = QTableWidgetItem(f"{p_qty:.0f}")
            item_pqty.setTextAlignment(Qt.AlignCenter)

            st = o.get("status", "PLANNED").upper()
            item_st = QTableWidgetItem(st)
            item_st.setTextAlignment(Qt.AlignCenter)
            if st == "COMPLETED":
                item_st.setForeground(Qt.darkGreen)
            elif st == "IN_PROGRESS":
                item_st.setForeground(Qt.blue)
            elif st == "QUALITY_CHECK":
                item_st.setForeground(Qt.darkCyan)
            else:
                item_st.setForeground(Qt.darkYellow)

            pri = o.get("priority", "NORMAL").upper()
            item_pri = QTableWidgetItem(pri)
            item_pri.setTextAlignment(Qt.AlignCenter)
            if pri in ("HIGH", "URGENT"):
                item_pri.setForeground(Qt.red)

            item_wc = QTableWidgetItem(o.get("work_center_name") or "-")
            item_sup = QTableWidgetItem(o.get("supervisor_name") or "-")

            cost = to_decimal(o.get("total_actual_cost", 0))
            item_cost = QTableWidgetItem(f"₹{cost:,.2f}" if cost > 0 else "—")
            item_cost.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Actions cell
            btn_cell = QWidget()
            btn_layout = QHBoxLayout(btn_cell)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            order_id = o.get("id", "")
            if st == "PLANNED":
                btn_start = QPushButton("▶ Start")
                btn_start.setStyleSheet("background-color: #3B82F6; color: white; padding: 4px 8px; border-radius: 4px;")
                btn_start.clicked.connect(lambda _, oid=order_id: self.start_order(oid))
                btn_layout.addWidget(btn_start)
            elif st in ("IN_PROGRESS", "QUALITY_CHECK"):
                btn_comp = QPushButton("✓ Complete & GL")
                btn_comp.setStyleSheet("background-color: #10B981; color: white; padding: 4px 8px; border-radius: 4px;")
                btn_comp.clicked.connect(lambda _, oid=order_id: self.open_complete_order_dialog(oid))
                btn_layout.addWidget(btn_comp)
            else:
                lbl_done = QLabel("Posted ✓")
                lbl_done.setStyleSheet("color: #10B981; font-weight: 600;")
                btn_layout.addWidget(lbl_done)

            self.table_orders.setItem(row, 0, item_num)
            self.table_orders.setItem(row, 1, item_prd)
            self.table_orders.setItem(row, 2, item_bom)
            self.table_orders.setItem(row, 3, item_tqty)
            self.table_orders.setItem(row, 4, item_pqty)
            self.table_orders.setItem(row, 5, item_st)
            self.table_orders.setItem(row, 6, item_pri)
            self.table_orders.setItem(row, 7, item_wc)
            self.table_orders.setItem(row, 8, item_sup)
            self.table_orders.setItem(row, 9, item_cost)
            self.table_orders.setCellWidget(row, 10, btn_cell)

    # =========================================================================
    # Tab 2: Bill of Materials (BOM)
    # =========================================================================
    def setup_bom_tab(self):
        layout = QVBoxLayout(self.tab_bom)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Top: Master BOM list
        lbl_master = QLabel("Active Bills of Materials Recipes:")
        lbl_master.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 14px;")
        layout.addWidget(lbl_master)

        self.table_boms = QTableWidget()
        self.table_boms.setColumnCount(8)
        self.table_boms.setHorizontalHeaderLabels([
            "BOM Code", "Finished Product", "SKU", "Batch Size",
            "Material Cost", "Operations Cost", "Unit Cost", "Status"
        ])
        self.table_boms.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_boms.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_boms.setSelectionMode(QTableWidget.SingleSelection)
        self.table_boms.itemSelectionChanged.connect(self.on_bom_selected)
        self.table_boms.setMaximumHeight(200)
        layout.addWidget(self.table_boms)

        # Bottom split: Components Table (left) and Routing Operations Table (right)
        detail_row = QHBoxLayout()
        detail_row.setSpacing(16)

        # Components Column
        col_comp = QVBoxLayout()
        lbl_comp = QLabel("📦 Component Raw Materials (with Scrap %):")
        lbl_comp.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")
        col_comp.addWidget(lbl_comp)

        self.table_bom_components = QTableWidget()
        self.table_bom_components.setColumnCount(6)
        self.table_bom_components.setHorizontalHeaderLabels(["Item Code", "Material Name", "Quantity", "UOM", "Scrap %", "Line Cost"])
        self.table_bom_components.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        col_comp.addWidget(self.table_bom_components)
        detail_row.addLayout(col_comp)

        # Operations Column
        col_ops = QVBoxLayout()
        lbl_ops = QLabel("⚙️ Routing Steps & Machine Operations:")
        lbl_ops.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")
        col_ops.addWidget(lbl_ops)

        self.table_bom_ops = QTableWidget()
        self.table_bom_ops.setColumnCount(6)
        self.table_bom_ops.setHorizontalHeaderLabels(["Seq", "Operation", "Work Center", "Setup (hrs)", "Run/Unit (hrs)", "Total Cost"])
        self.table_bom_ops.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        col_ops.addWidget(self.table_bom_ops)
        detail_row.addLayout(col_ops)

        layout.addLayout(detail_row)

    def populate_boms_table(self):
        self.table_boms.setRowCount(0)
        for row, b in enumerate(self.cached_boms):
            self.table_boms.insertRow(row)

            item_code = QTableWidgetItem(b.get("bom_code", ""))
            item_code.setTextAlignment(Qt.AlignCenter)
            item_name = QTableWidgetItem(b.get("product_name", ""))
            item_sku = QTableWidgetItem(b.get("product_sku", ""))

            b_qty = to_decimal(b.get("batch_quantity", 1))
            uom = b.get("uom", "Units")
            item_batch = QTableWidgetItem(f"{b_qty:.0f} {uom}")
            item_batch.setTextAlignment(Qt.AlignCenter)

            mat_cost = to_decimal(b.get("total_material_cost", 0))
            item_mat = QTableWidgetItem(f"₹{mat_cost:,.2f}")
            item_mat.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            lab_cost = to_decimal(b.get("total_labor_cost", 0))
            item_lab = QTableWidgetItem(f"₹{lab_cost:,.2f}")
            item_lab.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            u_cost = to_decimal(b.get("unit_cost", 0))
            item_ucost = QTableWidgetItem(f"₹{u_cost:,.2f}")
            item_ucost.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_ucost.setForeground(Qt.darkGreen)

            st = b.get("status", "ACTIVE")
            item_st = QTableWidgetItem(st)
            item_st.setTextAlignment(Qt.AlignCenter)

            self.table_boms.setItem(row, 0, item_code)
            self.table_boms.setItem(row, 1, item_name)
            self.table_boms.setItem(row, 2, item_sku)
            self.table_boms.setItem(row, 3, item_batch)
            self.table_boms.setItem(row, 4, item_mat)
            self.table_boms.setItem(row, 5, item_lab)
            self.table_boms.setItem(row, 6, item_ucost)
            self.table_boms.setItem(row, 7, item_st)

        if self.cached_boms:
            self.table_boms.selectRow(0)

    def on_bom_selected(self):
        sel = self.table_boms.selectedItems()
        if not sel:
            return
        row = sel[0].row()
        if row < len(self.cached_boms):
            bom = self.cached_boms[row]
            self.populate_bom_details(bom)

    def populate_bom_details(self, bom: Dict[str, Any]):
        # Populate components
        comps = bom.get("components", [])
        self.table_bom_components.setRowCount(0)
        for r, c in enumerate(comps):
            self.table_bom_components.insertRow(r)
            self.table_bom_components.setItem(r, 0, QTableWidgetItem(c.get("item_code", "")))
            self.table_bom_components.setItem(r, 1, QTableWidgetItem(c.get("item_name", "")))

            qty = to_decimal(c.get("quantity", 0))
            self.table_bom_components.setItem(r, 2, QTableWidgetItem(f"{qty:.2f}"))
            self.table_bom_components.setItem(r, 3, QTableWidgetItem(c.get("uom", "Units")))

            scrap = to_decimal(c.get("scrap_percent", 0))
            item_scrap = QTableWidgetItem(f"{scrap:.1f}%")
            if scrap > 0:
                item_scrap.setForeground(Qt.darkRed)
            self.table_bom_components.setItem(r, 4, item_scrap)

            tot = to_decimal(c.get("total_cost", 0))
            item_tot = QTableWidgetItem(f"₹{tot:,.2f}")
            item_tot.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_bom_components.setItem(r, 5, item_tot)

        # Populate operations
        ops = bom.get("operations", [])
        self.table_bom_ops.setRowCount(0)
        for r, o in enumerate(ops):
            self.table_bom_ops.insertRow(r)
            self.table_bom_ops.setItem(r, 0, QTableWidgetItem(str(o.get("sequence", 10))))
            self.table_bom_ops.setItem(r, 1, QTableWidgetItem(o.get("operation_name", "")))
            self.table_bom_ops.setItem(r, 2, QTableWidgetItem(o.get("work_center_name", "")))

            setup = to_decimal(o.get("setup_time_hours", 0))
            run = to_decimal(o.get("run_time_per_unit_hours", 0))
            self.table_bom_ops.setItem(r, 3, QTableWidgetItem(f"{setup:.1f}"))
            self.table_bom_ops.setItem(r, 4, QTableWidgetItem(f"{run:.2f}"))

            cost = to_decimal(o.get("cost", 0))
            item_cost = QTableWidgetItem(f"₹{cost:,.2f}")
            item_cost.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_bom_ops.setItem(r, 5, item_cost)

    # =========================================================================
    # Tab 3: Work Centers & Capacity
    # =========================================================================
    def setup_work_centers_tab(self):
        layout = QVBoxLayout(self.tab_wc)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Operational Work Centers, Machine Cells & Capacity:")
        lbl.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 14px;")
        layout.addWidget(lbl)

        self.table_work_centers = QTableWidget()
        self.table_work_centers.setColumnCount(8)
        self.table_work_centers.setHorizontalHeaderLabels([
            "Code", "Work Center Name", "Type / Department", "Labor Rate (₹/hr)",
            "Machine Rate (₹/hr)", "Daily Capacity (hrs)", "Status", "Actions"
        ])
        self.table_work_centers.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_work_centers.verticalHeader().setVisible(False)
        self.table_work_centers.setAlternatingRowColors(True)

        layout.addWidget(self.table_work_centers)

    def populate_work_centers_table(self):
        self.table_work_centers.setRowCount(0)
        for row, wc in enumerate(self.cached_work_centers):
            self.table_work_centers.insertRow(row)

            item_code = QTableWidgetItem(wc.get("code", ""))
            item_code.setTextAlignment(Qt.AlignCenter)
            item_name = QTableWidgetItem(wc.get("name", ""))
            item_type = QTableWidgetItem(wc.get("work_center_type", "ASSEMBLY"))
            item_type.setTextAlignment(Qt.AlignCenter)

            l_rate = to_decimal(wc.get("hourly_labor_rate", 0))
            item_lrate = QTableWidgetItem(f"₹{l_rate:,.2f}")
            item_lrate.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            m_rate = to_decimal(wc.get("hourly_machine_rate", 0))
            item_mrate = QTableWidgetItem(f"₹{m_rate:,.2f}")
            item_mrate.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            cap = to_decimal(wc.get("daily_capacity_hours", 8))
            item_cap = QTableWidgetItem(f"{cap:.1f} hrs/day")
            item_cap.setTextAlignment(Qt.AlignCenter)

            st = wc.get("status", "AVAILABLE").upper()
            item_st = QTableWidgetItem(st)
            item_st.setTextAlignment(Qt.AlignCenter)
            if st == "AVAILABLE":
                item_st.setForeground(Qt.darkGreen)
            elif st == "BUSY":
                item_st.setForeground(Qt.blue)
            else:
                item_st.setForeground(Qt.darkRed)

            btn_toggle = QPushButton("Toggle Status")
            btn_toggle.setStyleSheet("padding: 4px 8px; font-size: 11px;")
            wc_id = wc.get("id", "")
            next_st = "BUSY" if st == "AVAILABLE" else "AVAILABLE"
            btn_toggle.clicked.connect(lambda _, w=wc_id, ns=next_st: self.toggle_wc_status(w, ns))

            self.table_work_centers.setItem(row, 0, item_code)
            self.table_work_centers.setItem(row, 1, item_name)
            self.table_work_centers.setItem(row, 2, item_type)
            self.table_work_centers.setItem(row, 3, item_lrate)
            self.table_work_centers.setItem(row, 4, item_mrate)
            self.table_work_centers.setItem(row, 5, item_cap)
            self.table_work_centers.setItem(row, 6, item_st)
            self.table_work_centers.setCellWidget(row, 7, btn_toggle)

    def toggle_wc_status(self, wc_id: str, new_status: str):
        try:
            api_client.update_work_center(wc_id, {"status": new_status})
            self.refresh_data()
        except Exception as e:
            QMessageBox.warning(self, "Status Update Error", str(e))

    # =========================================================================
    # Tab 4: Quality & Scrap Log
    # =========================================================================
    def setup_quality_tab(self):
        layout = QVBoxLayout(self.tab_quality)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Manufacturing Quality Assurance Checkpoints & Defect Logs:")
        lbl.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 14px;")
        layout.addWidget(lbl)

        self.table_quality = QTableWidget()
        self.table_quality.setColumnCount(7)
        self.table_quality.setHorizontalHeaderLabels([
            "Order #", "Product", "Quality Parameter", "Target Specification",
            "Measured Value", "Status", "Inspector Remarks"
        ])
        self.table_quality.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_quality.verticalHeader().setVisible(False)
        self.table_quality.setAlternatingRowColors(True)

        layout.addWidget(self.table_quality)

    def populate_quality_table(self):
        self.table_quality.setRowCount(0)
        row = 0
        for o in self.cached_orders:
            for q in o.get("inspections", []):
                self.table_quality.insertRow(row)
                self.table_quality.setItem(row, 0, QTableWidgetItem(o.get("order_number", "")))
                self.table_quality.setItem(row, 1, QTableWidgetItem(o.get("product_name", "")))
                self.table_quality.setItem(row, 2, QTableWidgetItem(q.get("parameter_name", "")))
                self.table_quality.setItem(row, 3, QTableWidgetItem(q.get("target_specification", "")))
                self.table_quality.setItem(row, 4, QTableWidgetItem(q.get("measured_value", "")))

                st = q.get("status", "PASSED").upper()
                item_st = QTableWidgetItem(st)
                item_st.setTextAlignment(Qt.AlignCenter)
                if st == "PASSED":
                    item_st.setForeground(Qt.darkGreen)
                else:
                    item_st.setForeground(Qt.red)
                self.table_quality.setItem(row, 5, item_st)

                self.table_quality.setItem(row, 6, QTableWidgetItem(q.get("remarks", "")))
                row += 1

    # =========================================================================
    # Tab 5: Manufacturing Telemetry & Cost Accounting
    # =========================================================================
    def setup_costing_tab(self):
        layout = QVBoxLayout(self.tab_costing)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        lbl = QLabel("Automated General Ledger Absorption Costing Architecture:")
        lbl.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 14px;")
        layout.addWidget(lbl)

        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        ib_layout = QVBoxLayout(info_box)
        ib_layout.setSpacing(10)

        lbl_desc = QLabel(
            "<b>Double-Entry Financial Cost Absorption Flow:</b><br>"
            "1. <b>Material Release:</b> DR 1220 (WIP Inventory) &nbsp;|&nbsp; CR 1210 (Raw Materials Inventory)<br>"
            "2. <b>Overhead & Labor Absorption:</b> DR 1220 (WIP Inventory) &nbsp;|&nbsp; CR 5030 (Manufacturing Direct Labor & Overhead)<br>"
            "3. <b>Finished Goods Receipting:</b> DR 1230 (Finished Goods Inventory) &nbsp;|&nbsp; CR 1220 (WIP Inventory)<br>"
            "4. <b>Integrated Ledger:</b> Real-time synchronization with Finance Module general ledger journals."
        )
        lbl_desc.setStyleSheet(f"font-size: 13px; line-height: 1.6; color: {ThemeColors.TEXT_MAIN};")
        ib_layout.addWidget(lbl_desc)
        layout.addWidget(info_box)

        self.lbl_telemetry_summary = QLabel("Loading telemetry...")
        self.lbl_telemetry_summary.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED}; padding: 8px;")
        layout.addWidget(self.lbl_telemetry_summary)
        layout.addStretch()

    def update_costing_summary(self):
        m = self.cached_metrics
        text = (
            f"<b>Active Manufacturing Metrics:</b><br>"
            f"• Total Orders: <b>{m.get('total_orders', 0)}</b> (Active: <b>{m.get('active_orders', 0)}</b>, Completed: <b>{m.get('completed_orders', 0)}</b>)<br>"
            f"• Produced Units: <b>{to_decimal(m.get('total_produced_units', 0)):.1f}</b> | Rejected Units: <b>{to_decimal(m.get('total_rejected_units', 0)):.1f}</b> (Scrap Rate: <b>{to_decimal(m.get('scrap_rate_percent', 0)):.2f}%</b>)<br>"
            f"• Current WIP Valuation: <b>₹{to_decimal(m.get('total_wip_valuation', 0)):,.2f}</b><br>"
            f"• Average Finished Unit Cost: <b>₹{to_decimal(m.get('average_unit_cost', 0)):,.2f}</b><br>"
            f"• Plant Capacity Utilization: <b>{to_decimal(m.get('capacity_utilization_percent', 0)):.1f}%</b> across {m.get('total_work_centers', 0)} work centers"
        )
        self.lbl_telemetry_summary.setText(text)

    # =========================================================================
    # Data Refresh & API Integration
    # =========================================================================
    def refresh_data(self):
        try:
            self.cached_work_centers = api_client.get_work_centers()
            self.cached_boms = api_client.get_boms()
            self.cached_orders = api_client.get_production_orders()
            self.cached_metrics = api_client.get_manufacturing_metrics()
        except Exception as e:
            # Silently fall back to cached
            pass

        # Update metric cards
        m = self.cached_metrics
        self.card_active_orders.value_label.setText(f"{m.get('active_orders', 0)} Orders")
        self.card_units_produced.value_label.setText(f"{to_decimal(m.get('total_produced_units', 0)):.0f} Units")
        self.card_scrap_rate.value_label.setText(f"{to_decimal(m.get('scrap_rate_percent', 0)):.1f}%")
        self.card_wip_val.value_label.setText(f"₹{to_decimal(m.get('total_wip_valuation', 0)):,.2f}")
        self.card_capacity_util.value_label.setText(f"{to_decimal(m.get('capacity_utilization_percent', 0)):.1f}%")

        # Update tables
        self.populate_orders_table(self.cached_orders)
        self.populate_boms_table()
        self.populate_work_centers_table()
        self.populate_quality_table()
        self.update_costing_summary()

    # =========================================================================
    # Action Dialogs
    # =========================================================================
    def start_order(self, order_id: str):
        try:
            api_client.start_production_order(order_id)
            QMessageBox.information(self, "Production Started", f"Order {order_id} transitioned to IN_PROGRESS.")
            self.refresh_data()
        except Exception as e:
            QMessageBox.warning(self, "Start Error", str(e))

    def open_complete_order_dialog(self, order_id: str):
        dialog = QDialog(self)
        dialog.setWindowTitle("Complete Production Order & Post GL")
        dialog.setMinimumWidth(450)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        spn_prod = QDoubleSpinBox()
        spn_prod.setRange(1, 10000)
        spn_prod.setValue(5)

        spn_rej = QDoubleSpinBox()
        spn_rej.setRange(0, 1000)
        spn_rej.setValue(0)

        spn_hours = QDoubleSpinBox()
        spn_hours.setRange(0.5, 500)
        spn_hours.setValue(8.0)

        spn_overhead = QDoubleSpinBox()
        spn_overhead.setRange(0, 100000)
        spn_overhead.setValue(1500.0)

        cb_qa = QComboBox()
        cb_qa.addItems(["PASSED", "CONDITIONAL", "FAILED"])

        txt_notes = QTextEdit()
        txt_notes.setMaximumHeight(60)
        txt_notes.setPlaceholderText("Inspection and completion remarks...")

        form.addRow("Produced Units:", spn_prod)
        form.addRow("Scrap / Rejected Units:", spn_rej)
        form.addRow("Actual Labor Hours:", spn_hours)
        form.addRow("Allocated Overhead (₹):", spn_overhead)
        form.addRow("Quality Inspection:", cb_qa)
        form.addRow("Remarks:", txt_notes)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Complete & Post to GL")
        btn_ok.setProperty("class", "btn_primary")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        def do_complete():
            payload = {
                "produced_quantity": str(spn_prod.value()),
                "rejected_quantity": str(spn_rej.value()),
                "actual_labor_hours": str(spn_hours.value()),
                "overhead_cost": str(spn_overhead.value()),
                "quality_status": cb_qa.currentText(),
                "notes": txt_notes.toPlainText()
            }
            try:
                res = api_client.complete_production_order(order_id, payload)
                QMessageBox.information(
                    dialog,
                    "Order Completed",
                    f"Production completed!\nTotal Cost: ₹{to_decimal(res.get('total_actual_cost', 0)):,.2f}\n"
                    f"Unit Cost: ₹{to_decimal(res.get('unit_actual_cost', 0)):,.2f}\n"
                    f"General Ledger Journal: {res.get('journal_entry_id', 'Posted')}"
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Completion Error", str(e))

        btn_ok.clicked.connect(do_complete)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

        dialog.exec()

    def open_create_production_order_dialog(self):
        if not self.cached_boms:
            QMessageBox.warning(self, "No BOM Available", "Please create a Bill of Materials before releasing an order.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Release New Production Order")
        dialog.setMinimumWidth(450)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        cb_bom = QComboBox()
        for b in self.cached_boms:
            cb_bom.addItem(f"{b['bom_code']} - {b['product_name']}", b["id"])

        spn_target = QDoubleSpinBox()
        spn_target.setRange(1, 10000)
        spn_target.setValue(10)

        cb_pri = QComboBox()
        cb_pri.addItems(["NORMAL", "HIGH", "URGENT", "LOW"])

        cb_wc = QComboBox()
        for wc in self.cached_work_centers:
            cb_wc.addItem(f"{wc['code']} - {wc['name']}", wc["id"])

        txt_sup = QLineEdit("Production Lead")
        txt_notes = QLineEdit("Banquet / Resort replenishment run")

        form.addRow("Bill of Materials:", cb_bom)
        form.addRow("Target Quantity:", spn_target)
        form.addRow("Priority:", cb_pri)
        form.addRow("Work Center:", cb_wc)
        form.addRow("Supervisor:", txt_sup)
        form.addRow("Notes:", txt_notes)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Create Order")
        btn_ok.setProperty("class", "btn_primary")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        def do_create():
            bom_id = cb_bom.currentData()
            wc_id = cb_wc.currentData() if cb_wc.count() > 0 else None
            now = datetime.now()
            payload = {
                "bom_id": bom_id,
                "target_quantity": str(spn_target.value()),
                "planned_start_date": now.isoformat(),
                "planned_end_date": (now + timedelta(days=7)).isoformat(),
                "priority": cb_pri.currentText(),
                "work_center_id": wc_id,
                "supervisor_name": txt_sup.text(),
                "notes": txt_notes.text()
            }
            try:
                res = api_client.create_production_order(payload)
                QMessageBox.information(dialog, "Order Created", f"Released Production Order {res.get('order_number')}.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Creation Error", str(e))

        btn_ok.clicked.connect(do_create)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

        dialog.exec()

    def open_create_bom_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Bill of Materials (BOM)")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        txt_code = QLineEdit("BOM-NEW-PRD-01")
        txt_name = QLineEdit("Artisan Heritage Teak Stool")
        txt_sku = QLineEdit("PRD-STL-HTG-01")
        spn_batch = QDoubleSpinBox()
        spn_batch.setRange(1, 1000)
        spn_batch.setValue(10)
        txt_uom = QLineEdit("Units")
        txt_notes = QLineEdit("Carved teak barstools for resort lounge.")

        form.addRow("BOM Code:", txt_code)
        form.addRow("Product Name:", txt_name)
        form.addRow("Product SKU:", txt_sku)
        form.addRow("Batch Quantity:", spn_batch)
        form.addRow("Unit of Measure:", txt_uom)
        form.addRow("Notes:", txt_notes)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Save BOM")
        btn_ok.setProperty("class", "btn_primary")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        def do_create_bom():
            payload = {
                "bom_code": txt_code.text(),
                "product_id": f"prd_{txt_code.text().lower()}",
                "product_name": txt_name.text(),
                "product_sku": txt_sku.text(),
                "version": "v1.0",
                "batch_quantity": str(spn_batch.value()),
                "uom": txt_uom.text(),
                "notes": txt_notes.text(),
                "components": [
                    {
                        "item_code": "RAW-TEAK-TIM",
                        "item_name": "Teak Timber Planks",
                        "quantity": "15.00",
                        "uom": "bd ft",
                        "unit_cost": "750.00",
                        "scrap_percent": "3.00"
                    }
                ],
                "operations": [
                    {
                        "sequence": 10,
                        "work_center_id": "wc_carp_01",
                        "work_center_name": "Colonial Teak Joinery & Carving Bay",
                        "operation_name": "Turnery & Joinery Assembly",
                        "setup_time_hours": "0.50",
                        "run_time_per_unit_hours": "0.80",
                        "hourly_rate": "550.00"
                    }
                ]
            }
            try:
                res = api_client.create_bom(payload)
                QMessageBox.information(dialog, "BOM Created", f"Successfully created BOM {res.get('bom_code')}.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Creation Error", str(e))

        btn_ok.clicked.connect(do_create_bom)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

        dialog.exec()

    def open_create_work_center_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register New Work Center")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        txt_code = QLineEdit("WC-NEW-01")
        txt_name = QLineEdit("Textile Loom & Embroidery Bay")
        cb_type = QComboBox()
        cb_type.addItems(["ASSEMBLY", "MACHINING", "BAKING", "PACKAGING", "LAB"])

        spn_lrate = QDoubleSpinBox()
        spn_lrate.setRange(50, 5000)
        spn_lrate.setValue(450.0)

        spn_mrate = QDoubleSpinBox()
        spn_mrate.setRange(0, 5000)
        spn_mrate.setValue(250.0)

        spn_cap = QDoubleSpinBox()
        spn_cap.setRange(1, 24)
        spn_cap.setValue(8.0)

        form.addRow("Code:", txt_code)
        form.addRow("Name:", txt_name)
        form.addRow("Type:", cb_type)
        form.addRow("Labor Rate (₹/hr):", spn_lrate)
        form.addRow("Machine Rate (₹/hr):", spn_mrate)
        form.addRow("Daily Capacity (hrs):", spn_cap)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Register Work Center")
        btn_ok.setProperty("class", "btn_primary")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        def do_create_wc():
            payload = {
                "code": txt_code.text(),
                "name": txt_name.text(),
                "work_center_type": cb_type.currentText(),
                "hourly_labor_rate": str(spn_lrate.value()),
                "hourly_machine_rate": str(spn_mrate.value()),
                "daily_capacity_hours": str(spn_cap.value()),
                "status": "AVAILABLE",
                "is_active": True
            }
            try:
                res = api_client.create_work_center(payload)
                QMessageBox.information(dialog, "Work Center Added", f"Registered Work Center {res.get('code')}.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", str(e))

        btn_ok.clicked.connect(do_create_wc)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

        dialog.exec()
