"""Victory Crest One - Customer & Field Service Desktop View
Support Tickets, SLA Tracking, Field Work Orders, Technician Dispatch,
Spare Parts Requisitions, and Automated Finance GL Billing.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDoubleSpinBox, QTextEdit, QScrollArea,
    QSpinBox, QGroupBox
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from shared.calculations import to_decimal, calculate_work_order_totals, calculate_service_labor_cost


class ServiceManagementView(QWidget):
    """Central Customer & Field Service Management Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_tickets: List[Dict[str, Any]] = []
        self.cached_work_orders: List[Dict[str, Any]] = []
        self.cached_sla_policies: List[Dict[str, Any]] = []
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

        title = QLabel("Customer & Field Service Management")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Omnichannel incident ticketing, SLA countdowns, technician dispatch, inventory parts, and automated GL invoicing.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_new_ticket = QPushButton("➕ New Ticket")
        btn_new_ticket.setProperty("class", "btn_primary")
        btn_new_ticket.clicked.connect(self.open_create_ticket_dialog)

        btn_new_wo = QPushButton("🛠️ Create Work Order")
        btn_new_wo.setProperty("class", "btn_primary")
        btn_new_wo.clicked.connect(self.open_create_work_order_dialog)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_new_ticket)
        header_row.addWidget(btn_new_wo)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive Telemetry Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_active_tickets = self.create_metric_card("ACTIVE INCIDENTS", "0", "Open & In-Progress", ThemeColors.PRIMARY_LIGHT)
        self.card_sla_compliance = self.create_metric_card("SLA COMPLIANCE", "100.0%", "Target ≥ 95.0%", "#10B981")
        self.card_dispatched = self.create_metric_card("FIELD DISPATCHES", "0", "Technicians On-Site", "#F59E0B")
        self.card_completed_wo = self.create_metric_card("COMPLETED JOBS", "0", "Ready for Invoicing", "#6366F1")
        self.card_service_revenue = self.create_metric_card("BILLED REVENUE", "₹0.00", "GL AR Posted", "#EC4899")

        cards_row.addWidget(self.card_active_tickets)
        cards_row.addWidget(self.card_sla_compliance)
        cards_row.addWidget(self.card_dispatched)
        cards_row.addWidget(self.card_completed_wo)
        cards_row.addWidget(self.card_service_revenue)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Tabbed Multi-Function Workspace
        # -----------------------------------------------------
        self.tabs = QTabWidget()
        self.tabs.setObjectName("service_tabs")

        self.tab_tickets = QWidget()
        self.tab_work_orders = QWidget()
        self.tab_parts = QWidget()
        self.tab_invoicing = QWidget()
        self.tab_sla_policies = QWidget()

        self.setup_tickets_tab()
        self.setup_work_orders_tab()
        self.setup_parts_tab()
        self.setup_invoicing_tab()
        self.setup_sla_policies_tab()

        self.tabs.addTab(self.tab_tickets, "🎫  Support Tickets Desk")
        self.tabs.addTab(self.tab_work_orders, "🛠️  Field Work Orders")
        self.tabs.addTab(self.tab_parts, "📦  Parts Requisitions")
        self.tabs.addTab(self.tab_invoicing, "📑  Completed Jobs & Billing")
        self.tabs.addTab(self.tab_sla_policies, "⏱️  SLA Policy Tiers")

        main_layout.addWidget(self.tabs)

    def create_metric_card(self, title: str, value: str, subtext: str, color: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "metric_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {ThemeColors.TEXT_MUTED}; text-transform: uppercase;")
        lbl_value = QLabel(value)
        lbl_value.setObjectName("metric_value")
        lbl_value.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {color};")
        lbl_sub = QLabel(subtext)
        lbl_sub.setObjectName("metric_sub")
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.addWidget(lbl_sub)
        return card

    # -------------------------------------------------------------------------
    # TAB 1: Support Tickets Desk
    # -------------------------------------------------------------------------
    def setup_tickets_tab(self):
        layout = QVBoxLayout(self.tab_tickets)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        self.combo_ticket_status = QComboBox()
        self.combo_ticket_status.addItems(["ALL", "OPEN", "IN_PROGRESS", "PENDING_PARTS", "RESOLVED", "CLOSED"])
        self.combo_ticket_status.currentTextChanged.connect(self.filter_tickets)

        lbl_prio = QLabel("Priority:")
        lbl_prio.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        self.combo_ticket_priority = QComboBox()
        self.combo_ticket_priority.addItems(["ALL", "CRITICAL", "URGENT", "HIGH", "MEDIUM", "LOW"])
        self.combo_ticket_priority.currentTextChanged.connect(self.filter_tickets)

        self.txt_ticket_search = QLineEdit()
        self.txt_ticket_search.setPlaceholderText("🔍 Search ticket #, customer, or subject...")
        self.txt_ticket_search.textChanged.connect(self.filter_tickets)

        filter_bar.addWidget(lbl_status)
        filter_bar.addWidget(self.combo_ticket_status)
        filter_bar.addWidget(lbl_prio)
        filter_bar.addWidget(self.combo_ticket_priority)
        filter_bar.addWidget(self.txt_ticket_search)
        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # Tickets Table
        self.table_tickets = QTableWidget(0, 8)
        self.table_tickets.setHorizontalHeaderLabels([
            "Ticket #", "Customer Name", "Subject", "Category", "Priority", "Status", "SLA Timer", "Assigned Tech"
        ])
        header = self.table_tickets.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table_tickets.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_tickets.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_tickets.doubleClicked.connect(self.on_ticket_double_clicked)
        layout.addWidget(self.table_tickets)

    # -------------------------------------------------------------------------
    # TAB 2: Field Work Orders & Dispatch
    # -------------------------------------------------------------------------
    def setup_work_orders_tab(self):
        layout = QVBoxLayout(self.tab_work_orders)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        self.combo_wo_status = QComboBox()
        self.combo_wo_status.addItems(["ALL", "SCHEDULED", "DISPATCHED", "IN_PROGRESS", "COMPLETED"])
        self.combo_wo_status.currentTextChanged.connect(self.filter_work_orders)

        self.txt_wo_search = QLineEdit()
        self.txt_wo_search.setPlaceholderText("🔍 Search work order #, customer, or tech...")
        self.txt_wo_search.textChanged.connect(self.filter_work_orders)

        filter_bar.addWidget(lbl_status)
        filter_bar.addWidget(self.combo_wo_status)
        filter_bar.addWidget(self.txt_wo_search)
        filter_bar.addStretch()

        btn_dispatch = QPushButton("🚀 Dispatch Technician")
        btn_dispatch.setProperty("class", "btn_secondary")
        btn_dispatch.clicked.connect(self.open_dispatch_dialog)
        filter_bar.addWidget(btn_dispatch)

        layout.addLayout(filter_bar)

        # Work Orders Table
        self.table_work_orders = QTableWidget(0, 9)
        self.table_work_orders.setHorizontalHeaderLabels([
            "WO #", "Ticket Ref", "Customer Name", "Service Type", "Status",
            "Technician", "Site Address", "Grand Total", "Action"
        ])
        header = self.table_work_orders.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.table_work_orders.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_work_orders.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_work_orders)

    # -------------------------------------------------------------------------
    # TAB 3: Spare Parts Requisition
    # -------------------------------------------------------------------------
    def setup_parts_tab(self):
        layout = QVBoxLayout(self.tab_parts)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        lbl_info = QLabel("Warehouse Inventory Requisitions linked to active Field Work Orders:")
        lbl_info.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")
        top_row.addWidget(lbl_info)
        top_row.addStretch()

        btn_add_part = QPushButton("➕ Requisition Spare Part")
        btn_add_part.setProperty("class", "btn_secondary")
        btn_add_part.clicked.connect(self.open_add_part_dialog)
        top_row.addWidget(btn_add_part)
        layout.addLayout(top_row)

        self.table_parts = QTableWidget(0, 9)
        self.table_parts.setHorizontalHeaderLabels([
            "Work Order #", "Item Code", "Item Description", "Demanded",
            "Issued", "Unit Cost (₹)", "Total Cost (₹)", "Status", "Issue Action"
        ])
        header = self.table_parts.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.table_parts.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_parts.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_parts)

    # -------------------------------------------------------------------------
    # TAB 4: Invoicing & General Accounting Billing
    # -------------------------------------------------------------------------
    def setup_invoicing_tab(self):
        layout = QVBoxLayout(self.tab_invoicing)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl_desc = QLabel("Field Work Orders Completed & Invoiced with Automated General Ledger Double-Entry Postings:")
        lbl_desc.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")
        layout.addWidget(lbl_desc)

        self.table_invoicing = QTableWidget(0, 9)
        self.table_invoicing.setHorizontalHeaderLabels([
            "WO #", "Customer Name", "Labor (₹)", "Parts (₹)", "Tax 18% (₹)",
            "Grand Total (₹)", "Invoiced?", "GL Ref (AR / Revenue)", "Action"
        ])
        header = self.table_invoicing.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.table_invoicing.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_invoicing.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_invoicing)

    # -------------------------------------------------------------------------
    # TAB 5: SLA Policy Tiers
    # -------------------------------------------------------------------------
    def setup_sla_policies_tab(self):
        layout = QVBoxLayout(self.tab_sla_policies)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl_title = QLabel("Service Level Agreement (SLA) Matrix & Commitment Tiers:")
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(lbl_title)

        self.table_sla = QTableWidget(0, 5)
        self.table_sla.setHorizontalHeaderLabels([
            "SLA Tier", "Priority", "Target Response Time", "Target Resolution Time", "Operational Policy & Scope"
        ])
        header = self.table_sla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_sla.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_sla.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_sla)

    # -------------------------------------------------------------------------
    # Data Refresh & Rendering
    # -------------------------------------------------------------------------
    def refresh_data(self):
        """Fetch latest service tickets, work orders, parts, SLA rules, and metrics."""
        self.cached_tickets = api_client.get_service_tickets()
        self.cached_work_orders = api_client.get_field_work_orders()
        self.cached_sla_policies = api_client.get_service_sla_policies()
        self.cached_metrics = api_client.get_service_metrics()

        # Update Telemetry Metrics
        m = self.cached_metrics
        self.card_active_tickets.findChild(QLabel, "metric_value").setText(str(m.get("active_tickets", 0)))
        self.card_sla_compliance.findChild(QLabel, "metric_value").setText(f"{m.get('sla_compliance_rate', 100):.1f}%")
        self.card_dispatched.findChild(QLabel, "metric_value").setText(str(m.get("dispatched_work_orders", 0)))
        self.card_completed_wo.findChild(QLabel, "metric_value").setText(str(m.get("completed_work_orders", 0)))
        self.card_service_revenue.findChild(QLabel, "metric_value").setText(f"₹{to_decimal(m.get('total_service_revenue', 0)):,.2f}")

        # Render Tables
        self.filter_tickets()
        self.filter_work_orders()
        self.render_parts_table()
        self.render_invoicing_table()
        self.render_sla_policies_table()

    def filter_tickets(self):
        status_flt = self.combo_ticket_status.currentText().upper()
        prio_flt = self.combo_ticket_priority.currentText().upper()
        q = self.txt_ticket_search.text().strip().lower()

        filtered = []
        for t in self.cached_tickets:
            if status_flt != "ALL" and t.get("status", "").upper() != status_flt:
                continue
            if prio_flt != "ALL" and t.get("priority", "").upper() != prio_flt:
                continue
            if q:
                matched = (
                    q in t.get("ticket_number", "").lower() or
                    q in t.get("customer_name", "").lower() or
                    q in t.get("subject", "").lower() or
                    q in (t.get("assigned_to_name") or "").lower()
                )
                if not matched:
                    continue
            filtered.append(t)

        self.table_tickets.setRowCount(len(filtered))
        for row, t in enumerate(filtered):
            self.table_tickets.setItem(row, 0, QTableWidgetItem(t.get("ticket_number", "")))
            self.table_tickets.setItem(row, 1, QTableWidgetItem(t.get("customer_name", "")))
            self.table_tickets.setItem(row, 2, QTableWidgetItem(t.get("subject", "")))
            self.table_tickets.setItem(row, 3, QTableWidgetItem(t.get("category", "")))

            # Priority Pill
            prio = t.get("priority", "MEDIUM")
            prio_item = QTableWidgetItem(prio)
            if prio == "CRITICAL":
                prio_item.setForeground(Qt.red)
            elif prio in ("URGENT", "HIGH"):
                prio_item.setForeground(Qt.darkYellow)
            self.table_tickets.setItem(row, 4, prio_item)

            # Status Capsule
            st = t.get("status", "OPEN")
            st_item = QTableWidgetItem(st)
            if st in ("RESOLVED", "CLOSED"):
                st_item.setForeground(Qt.green)
            self.table_tickets.setItem(row, 5, st_item)

            # SLA Timer
            rem_hrs = t.get("sla_remaining_hours")
            is_breached = t.get("sla_breached", False)
            if is_breached:
                timer_str = "⚠️ BREACHED"
                timer_item = QTableWidgetItem(timer_str)
                timer_item.setForeground(Qt.red)
            elif rem_hrs is not None:
                timer_str = f"⏱️ {float(rem_hrs):.1f}h remaining"
                timer_item = QTableWidgetItem(timer_str)
                timer_item.setForeground(Qt.green)
            else:
                timer_item = QTableWidgetItem("N/A")
            self.table_tickets.setItem(row, 6, timer_item)

            self.table_tickets.setItem(row, 7, QTableWidgetItem(t.get("assigned_to_name") or "Unassigned"))

    def filter_work_orders(self):
        status_flt = self.combo_wo_status.currentText().upper()
        q = self.txt_wo_search.text().strip().lower()

        filtered = []
        for wo in self.cached_work_orders:
            if status_flt != "ALL" and wo.get("status", "").upper() != status_flt:
                continue
            if q:
                matched = (
                    q in wo.get("work_order_number", "").lower() or
                    q in wo.get("customer_name", "").lower() or
                    q in (wo.get("technician_name") or "").lower() or
                    q in (wo.get("ticket_number") or "").lower()
                )
                if not matched:
                    continue
            filtered.append(wo)

        self.table_work_orders.setRowCount(len(filtered))
        for row, wo in enumerate(filtered):
            self.table_work_orders.setItem(row, 0, QTableWidgetItem(wo.get("work_order_number", "")))
            self.table_work_orders.setItem(row, 1, QTableWidgetItem(wo.get("ticket_number") or "Direct"))
            self.table_work_orders.setItem(row, 2, QTableWidgetItem(wo.get("customer_name", "")))
            self.table_work_orders.setItem(row, 3, QTableWidgetItem(wo.get("service_type", "")))

            # Status
            st = wo.get("status", "SCHEDULED")
            st_item = QTableWidgetItem(st)
            if st == "COMPLETED":
                st_item.setForeground(Qt.green)
            elif st == "DISPATCHED":
                st_item.setForeground(Qt.cyan)
            self.table_work_orders.setItem(row, 4, st_item)

            self.table_work_orders.setItem(row, 5, QTableWidgetItem(wo.get("technician_name") or "Unassigned"))
            self.table_work_orders.setItem(row, 6, QTableWidgetItem(wo.get("site_address", "")))
            self.table_work_orders.setItem(row, 7, QTableWidgetItem(f"₹{to_decimal(wo.get('grand_total', 0)):,.2f}"))

            # Action button
            if st != "COMPLETED":
                btn_action = QPushButton("Complete & Bill")
                btn_action.setProperty("class", "btn_secondary")
                btn_action.setStyleSheet("padding: 2px 6px; font-size: 11px;")
                btn_action.clicked.connect(lambda _, w=wo: self.open_complete_billing_dialog(w))
                self.table_work_orders.setCellWidget(row, 8, btn_action)
            else:
                lbl_done = QLabel("✅ Invoiced")
                lbl_done.setStyleSheet("color: #10B981; font-weight: 600; font-size: 11px; padding: 2px;")
                self.table_work_orders.setCellWidget(row, 8, lbl_done)

    def render_parts_table(self):
        parts_list = []
        for wo in self.cached_work_orders:
            for p in wo.get("parts", []):
                p_copy = dict(p)
                p_copy["work_order_number"] = wo.get("work_order_number", "")
                parts_list.append(p_copy)

        self.table_parts.setRowCount(len(parts_list))
        for row, p in enumerate(parts_list):
            self.table_parts.setItem(row, 0, QTableWidgetItem(p.get("work_order_number", "")))
            self.table_parts.setItem(row, 1, QTableWidgetItem(p.get("item_code", "")))
            self.table_parts.setItem(row, 2, QTableWidgetItem(p.get("item_name", "")))
            self.table_parts.setItem(row, 3, QTableWidgetItem(str(p.get("quantity_demanded", 1))))
            self.table_parts.setItem(row, 4, QTableWidgetItem(str(p.get("quantity_issued", 0))))
            self.table_parts.setItem(row, 5, QTableWidgetItem(f"{to_decimal(p.get('unit_cost', 0)):,.2f}"))
            self.table_parts.setItem(row, 6, QTableWidgetItem(f"{to_decimal(p.get('total_cost', 0)):,.2f}"))

            # Status
            st = p.get("status", "REQUESTED")
            st_item = QTableWidgetItem(st)
            if st == "ISSUED":
                st_item.setForeground(Qt.cyan)
            elif st == "CONSUMED":
                st_item.setForeground(Qt.green)
            self.table_parts.setItem(row, 7, st_item)

            if st == "REQUESTED":
                btn_issue = QPushButton("Issue Part")
                btn_issue.setProperty("class", "btn_primary")
                btn_issue.setStyleSheet("padding: 2px 6px; font-size: 11px;")
                btn_issue.clicked.connect(lambda _, w_id=p.get("work_order_id"), p_id=p.get("id"): self.issue_part(w_id, p_id))
                self.table_parts.setCellWidget(row, 8, btn_issue)
            else:
                lbl_ok = QLabel("Dispatched" if st == "ISSUED" else "Consumed")
                lbl_ok.setStyleSheet("color: #10B981; font-size: 11px;")
                self.table_parts.setCellWidget(row, 8, lbl_ok)

    def render_invoicing_table(self):
        self.table_invoicing.setRowCount(len(self.cached_work_orders))
        for row, wo in enumerate(self.cached_work_orders):
            self.table_invoicing.setItem(row, 0, QTableWidgetItem(wo.get("work_order_number", "")))
            self.table_invoicing.setItem(row, 1, QTableWidgetItem(wo.get("customer_name", "")))
            self.table_invoicing.setItem(row, 2, QTableWidgetItem(f"₹{to_decimal(wo.get('labor_total', 0)):,.2f}"))
            self.table_invoicing.setItem(row, 3, QTableWidgetItem(f"₹{to_decimal(wo.get('parts_total', 0)):,.2f}"))
            self.table_invoicing.setItem(row, 4, QTableWidgetItem(f"₹{to_decimal(wo.get('tax_amount', 0)):,.2f}"))
            self.table_invoicing.setItem(row, 5, QTableWidgetItem(f"₹{to_decimal(wo.get('grand_total', 0)):,.2f}"))

            invoiced = wo.get("is_invoiced", False)
            inv_item = QTableWidgetItem("YES" if invoiced else "PENDING")
            if invoiced:
                inv_item.setForeground(Qt.green)
            self.table_invoicing.setItem(row, 6, inv_item)

            gl_ref = wo.get("journal_entry_id") or "Pending Billing"
            self.table_invoicing.setItem(row, 7, QTableWidgetItem(gl_ref))

            if not invoiced:
                btn_bill = QPushButton("⚡ Invoicing (GL)")
                btn_bill.setProperty("class", "btn_primary")
                btn_bill.setStyleSheet("padding: 2px 6px; font-size: 11px;")
                btn_bill.clicked.connect(lambda _, w=wo: self.open_complete_billing_dialog(w))
                self.table_invoicing.setCellWidget(row, 8, btn_bill)
            else:
                lbl_done = QLabel("✅ GL Posted")
                lbl_done.setStyleSheet("color: #10B981; font-weight: 600; font-size: 11px;")
                self.table_invoicing.setCellWidget(row, 8, lbl_done)

    def render_sla_policies_table(self):
        self.table_sla.setRowCount(len(self.cached_sla_policies))
        for row, p in enumerate(self.cached_sla_policies):
            self.table_sla.setItem(row, 0, QTableWidgetItem(p.get("name", "")))
            self.table_sla.setItem(row, 1, QTableWidgetItem(p.get("priority", "")))
            self.table_sla.setItem(row, 2, QTableWidgetItem(f"{float(p.get('response_target_hours', 0)):.1f} hours"))
            self.table_sla.setItem(row, 3, QTableWidgetItem(f"{float(p.get('resolution_target_hours', 0)):.1f} hours"))
            self.table_sla.setItem(row, 4, QTableWidgetItem(p.get("description", "")))

    # -------------------------------------------------------------------------
    # Dialogs & Modal Actions
    # -------------------------------------------------------------------------
    def open_create_ticket_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Log New Support Incident / Maintenance Ticket")
        dialog.resize(500, 480)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        txt_cust = QLineEdit()
        txt_cust.setPlaceholderText("Customer or Facility Name")
        txt_email = QLineEdit()
        txt_email.setPlaceholderText("customer@domain.com")
        txt_subj = QLineEdit()
        txt_subj.setPlaceholderText("Brief description of issue")
        txt_desc = QTextEdit()
        txt_desc.setPlaceholderText("Detailed symptoms, error codes, and impacted units...")
        txt_desc.setMaximumHeight(80)

        combo_cat = QComboBox()
        combo_cat.addItems(["HVAC_REPAIR", "KITCHEN_EQUIPMENT", "SECURITY_ACCESS", "PREVENTIVE_MAINTENANCE", "ELECTRICAL", "PLUMBING"])

        combo_prio = QComboBox()
        combo_prio.addItems(["MEDIUM", "HIGH", "URGENT", "CRITICAL", "LOW"])

        combo_chan = QComboBox()
        combo_chan.addItems(["PORTAL", "PHONE", "EMAIL", "ON_SITE", "IOT_ALARM"])

        form.addRow("Customer Name*:", txt_cust)
        form.addRow("Customer Email:", txt_email)
        form.addRow("Subject*:", txt_subj)
        form.addRow("Category*:", combo_cat)
        form.addRow("Priority*:", combo_prio)
        form.addRow("Intake Channel*:", combo_chan)
        form.addRow("Details*:", txt_desc)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Log Incident")
        btn_save.setProperty("class", "btn_primary")

        def submit():
            cname = txt_cust.text().strip()
            subj = txt_subj.text().strip()
            desc = txt_desc.toPlainText().strip()
            if not cname or not subj or not desc:
                QMessageBox.warning(dialog, "Validation Error", "Customer name, subject, and details are required.")
                return

            payload = {
                "customer_name": cname,
                "customer_email": txt_email.text().strip() or None,
                "subject": subj,
                "description": desc,
                "category": combo_cat.currentText(),
                "priority": combo_prio.currentText(),
                "channel": combo_chan.currentText()
            }
            try:
                api_client.create_service_ticket(payload)
                QMessageBox.information(dialog, "Incident Created", f"Support Ticket successfully logged for '{cname}'.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to log incident: {str(e)}")

        btn_save.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        form.addRow(btn_row)

        dialog.exec()

    def open_create_work_order_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Field Work Order")
        dialog.resize(520, 480)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        txt_cust = QLineEdit()
        txt_cust.setPlaceholderText("Customer Name")
        txt_site = QLineEdit()
        txt_site.setPlaceholderText("Building, Floor, Room, or Site Address")

        combo_type = QComboBox()
        combo_type.addItems(["EMERGENCY_REPAIR", "PREVENTIVE_MAINTENANCE", "WARRANTY", "INSTALLATION", "AMC"])

        combo_prio = QComboBox()
        combo_prio.addItems(["MEDIUM", "HIGH", "CRITICAL", "LOW"])

        txt_tech = QLineEdit()
        txt_tech.setText("Rajesh Kumar (Senior Facilities Engineer)")

        spin_hours = QDoubleSpinBox()
        spin_hours.setRange(0.5, 100.0)
        spin_hours.setValue(3.0)
        spin_hours.setSuffix(" hrs")

        spin_rate = QDoubleSpinBox()
        spin_rate.setRange(100.0, 5000.0)
        spin_rate.setValue(850.0)
        spin_rate.setPrefix("₹")

        form.addRow("Customer Name*:", txt_cust)
        form.addRow("Site Location*:", txt_site)
        form.addRow("Service Type*:", combo_type)
        form.addRow("Priority*:", combo_prio)
        form.addRow("Assigned Tech:", txt_tech)
        form.addRow("Estimated Labor Hours:", spin_hours)
        form.addRow("Labor Rate / Hour:", spin_rate)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Schedule Order")
        btn_save.setProperty("class", "btn_primary")

        def submit():
            cname = txt_cust.text().strip()
            site = txt_site.text().strip()
            if not cname or not site:
                QMessageBox.warning(dialog, "Validation Error", "Customer name and site location are required.")
                return

            payload = {
                "customer_name": cname,
                "site_address": site,
                "service_type": combo_type.currentText(),
                "priority": combo_prio.currentText(),
                "technician_name": txt_tech.text().strip(),
                "labor_hours": spin_hours.value(),
                "labor_rate_per_hour": spin_rate.value()
            }
            try:
                api_client.create_field_work_order(payload)
                QMessageBox.information(dialog, "Work Order Created", f"Field Work Order scheduled for {cname}.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to create work order: {str(e)}")

        btn_save.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        form.addRow(btn_row)

        dialog.exec()

    def open_dispatch_dialog(self):
        if not self.cached_work_orders:
            QMessageBox.information(self, "No Orders", "No work orders available to dispatch.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Dispatch Technician to Field Work Order")
        dialog.resize(460, 260)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        combo_wo = QComboBox()
        for wo in self.cached_work_orders:
            combo_wo.addItem(f"{wo['work_order_number']} - {wo['customer_name']} ({wo['status']})", wo["id"])

        txt_tech = QLineEdit()
        txt_tech.setText("Priya Nair (Kitchen Systems Specialist)")

        form.addRow("Select Work Order*:", combo_wo)
        form.addRow("Technician Name*:", txt_tech)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_dispatch = QPushButton("Confirm Dispatch")
        btn_dispatch.setProperty("class", "btn_primary")

        def submit():
            wo_id = combo_wo.currentData()
            tech = txt_tech.text().strip()
            if not tech:
                QMessageBox.warning(dialog, "Validation Error", "Technician name is required.")
                return

            payload = {
                "technician_id": f"tech_{tech.split()[0].lower()}",
                "technician_name": tech
            }
            try:
                api_client.dispatch_work_order(wo_id, payload)
                QMessageBox.information(dialog, "Dispatched", f"Dispatched {tech} to the selected work order.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to dispatch: {str(e)}")

        btn_dispatch.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_dispatch)
        form.addRow(btn_row)

        dialog.exec()

    def open_add_part_dialog(self):
        if not self.cached_work_orders:
            QMessageBox.information(self, "No Orders", "No work orders available.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Requisition Spare Parts from Warehouse")
        dialog.resize(480, 320)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        combo_wo = QComboBox()
        for wo in self.cached_work_orders:
            combo_wo.addItem(f"{wo['work_order_number']} - {wo['customer_name']}", wo["id"])

        txt_code = QLineEdit()
        txt_code.setText("PRT-HVC-12")
        txt_name = QLineEdit()
        txt_name.setText("High Performance Compressor Capacitor 70uF")

        spin_qty = QDoubleSpinBox()
        spin_qty.setRange(1.0, 100.0)
        spin_qty.setValue(1.0)

        spin_cost = QDoubleSpinBox()
        spin_cost.setRange(10.0, 50000.0)
        spin_cost.setValue(1650.0)
        spin_cost.setPrefix("₹")

        form.addRow("Work Order*:", combo_wo)
        form.addRow("Item Code*:", txt_code)
        form.addRow("Item Description*:", txt_name)
        form.addRow("Quantity Demanded*:", spin_qty)
        form.addRow("Unit Cost (₹)*:", spin_cost)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Request Part")
        btn_save.setProperty("class", "btn_primary")

        def submit():
            wo_id = combo_wo.currentData()
            code = txt_code.text().strip()
            name = txt_name.text().strip()
            if not code or not name:
                QMessageBox.warning(dialog, "Validation Error", "Item code and name are required.")
                return

            payload = {
                "item_code": code,
                "item_name": name,
                "quantity_demanded": spin_qty.value(),
                "unit_cost": spin_cost.value()
            }
            try:
                api_client.add_work_order_part(wo_id, payload)
                QMessageBox.information(dialog, "Part Requisitioned", f"Requisitioned {name} from warehouse inventory.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to requisition part: {str(e)}")

        btn_save.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        form.addRow(btn_row)

        dialog.exec()

    def issue_part(self, wo_id: str, part_id: str):
        try:
            api_client.issue_work_order_part(wo_id, part_id)
            QMessageBox.information(self, "Part Issued", "Part successfully issued from warehouse inventory to work order.")
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to issue part: {str(e)}")

    def open_complete_billing_dialog(self, wo: Dict[str, Any]):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Complete & Bill Work Order — {wo['work_order_number']}")
        dialog.resize(520, 380)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        lbl_cust = QLabel(f"<b>Customer:</b> {wo['customer_name']} | <b>Type:</b> {wo['service_type']}")
        form.addRow(lbl_cust)

        spin_hours = QDoubleSpinBox()
        spin_hours.setRange(0.5, 100.0)
        spin_hours.setValue(float(wo.get("labor_hours", 2.0)))
        spin_hours.setSuffix(" hrs")

        spin_rate = QDoubleSpinBox()
        spin_rate.setRange(100.0, 5000.0)
        spin_rate.setValue(float(wo.get("labor_rate_per_hour", 800.0)))
        spin_rate.setPrefix("₹")

        txt_summary = QTextEdit()
        txt_summary.setPlaceholderText("Detailed resolution notes: root cause, parts replaced, and verification test...")
        txt_summary.setText("Repaired damaged contacts, replaced worn capacitors, tested compressor under full load.")
        txt_summary.setMaximumHeight(80)

        lbl_totals = QLabel()
        lbl_totals.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {ThemeColors.PRIMARY_LIGHT};")

        def update_calculation_display():
            tot_labor = calculate_service_labor_cost(spin_hours.value(), spin_rate.value())
            parts_tot = to_decimal(wo.get("parts_total", 0))
            totals = calculate_work_order_totals(tot_labor, parts_tot, 18.0)
            lbl_totals.setText(
                f"Labor: ₹{totals['labor_total']:,.2f} | Parts: ₹{totals['parts_total']:,.2f} | "
                f"GST 18%: ₹{totals['tax_amount']:,.2f} | <b>Grand Total: ₹{totals['grand_total']:,.2f}</b>"
            )

        spin_hours.valueChanged.connect(update_calculation_display)
        spin_rate.valueChanged.connect(update_calculation_display)
        update_calculation_display()

        form.addRow("Actual Labor Hours*:", spin_hours)
        form.addRow("Labor Rate / Hour*:", spin_rate)
        form.addRow("Billing Breakdown:", lbl_totals)
        form.addRow("Resolution Summary*:", txt_summary)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_bill = QPushButton("⚡ Generate Invoice & GL Posting")
        btn_bill.setProperty("class", "btn_primary")

        def submit():
            summary = txt_summary.toPlainText().strip()
            if not summary:
                QMessageBox.warning(dialog, "Validation Error", "Resolution summary is required.")
                return

            payload = {
                "actual_labor_hours": spin_hours.value(),
                "labor_rate_per_hour": spin_rate.value(),
                "resolution_summary": summary,
                "mark_ticket_resolved": True
            }
            try:
                res = api_client.complete_and_bill_work_order(wo["id"], payload)
                je_ref = res.get("journal_entry_id", "Posted")
                QMessageBox.information(
                    dialog,
                    "Invoicing & GL Complete",
                    f"Work Order {wo['work_order_number']} successfully completed and invoiced!\n\n"
                    f"Grand Total: ₹{to_decimal(res.get('grand_total', 0)):,.2f}\n"
                    f"Finance GL Posting: {je_ref}\n"
                    f"• DR 1020 Accounts Receivable\n"
                    f"• CR 4040 Service Fee Revenue\n"
                    f"• CR 2020 GST Payable"
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to complete & bill: {str(e)}")

        btn_bill.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_bill)
        form.addRow(btn_row)

        dialog.exec()

    def on_ticket_double_clicked(self, index):
        row = index.row()
        if row < 0 or row >= len(self.cached_tickets):
            return
        t = self.cached_tickets[row]
        QMessageBox.information(
            self,
            f"Ticket {t.get('ticket_number')}",
            f"Customer: {t.get('customer_name')}\n"
            f"Subject: {t.get('subject')}\n"
            f"Category: {t.get('category')}\n"
            f"Priority: {t.get('priority')} | Status: {t.get('status')}\n"
            f"Assigned Tech: {t.get('assigned_to_name') or 'Unassigned'}\n\n"
            f"Description:\n{t.get('description')}\n\n"
            f"Resolution Notes:\n{t.get('resolution_notes') or 'Pending resolution'}"
        )
