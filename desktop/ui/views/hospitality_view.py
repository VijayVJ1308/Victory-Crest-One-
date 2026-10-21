"""Victory Crest One - Hospitality & Resort PMS / Restaurant Dining View
Multi-Property Room Rack, Reservations Engine, Housekeeping, Guest Folios,
Dining Tables, Kitchen Display System (KDS), and Automated GL Night Audits.
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
from shared.calculations import to_decimal, calculate_reservation_totals, calculate_dining_bill_totals


class HospitalityView(QWidget):
    """Central Hospitality PMS & Restaurant Dining Operations Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_rooms: List[Dict[str, Any]] = []
        self.cached_reservations: List[Dict[str, Any]] = []
        self.cached_folios: List[Dict[str, Any]] = []
        self.cached_tables: List[Dict[str, Any]] = []
        self.cached_dining_orders: List[Dict[str, Any]] = []
        self.cached_room_types: List[Dict[str, Any]] = []
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

        title = QLabel("Hospitality & Resort PMS / Restaurant Dining")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Room rack, reservation engine, guest folios, housekeeping, table dining, KDS tickets, and automated GL night audits.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_new_res = QPushButton("➕ New Reservation")
        btn_new_res.setProperty("class", "btn_primary")
        btn_new_res.clicked.connect(self.open_create_reservation_dialog)

        btn_new_order = QPushButton("🍽️ New Dining Order")
        btn_new_order.setProperty("class", "btn_primary")
        btn_new_order.clicked.connect(self.open_create_dining_order_dialog)

        btn_night_audit = QPushButton("🌙 Run Night Audit")
        btn_night_audit.setProperty("class", "btn_secondary")
        btn_night_audit.setStyleSheet("border-color: #8B5CF6; color: #A78BFA; font-weight: 600;")
        btn_night_audit.clicked.connect(self.run_night_audit)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_new_res)
        header_row.addWidget(btn_new_order)
        header_row.addWidget(btn_night_audit)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive Hospitality Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_occupancy = self.create_metric_card("ROOM OCCUPANCY", "0.0%", "Target ≥ 75.0%", "#10B981")
        self.card_adr = self.create_metric_card("AVERAGE DAILY RATE", "₹0.00", "ADR / Sold Room", ThemeColors.PRIMARY_LIGHT)
        self.card_revpar = self.create_metric_card("RevPAR", "₹0.00", "Revenue Per Available Rm", "#F59E0B")
        self.card_folios = self.create_metric_card("GUEST RECEIVABLES", "₹0.00", "In-House Folio Balance", "#EC4899")
        self.card_fnb_rev = self.create_metric_card("F&B DINING REVENUE", "₹0.00", "Restaurant & KDS Sales", "#6366F1")

        cards_row.addWidget(self.card_occupancy)
        cards_row.addWidget(self.card_adr)
        cards_row.addWidget(self.card_revpar)
        cards_row.addWidget(self.card_folios)
        cards_row.addWidget(self.card_fnb_rev)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Tabbed Multi-Function Workspace
        # -----------------------------------------------------
        self.tabs = QTabWidget()
        self.tabs.setObjectName("hospitality_tabs")

        self.tab_reservations = QWidget()
        self.tab_room_rack = QWidget()
        self.tab_folios = QWidget()
        self.tab_dining = QWidget()
        self.tab_night_audit = QWidget()

        self.setup_reservations_tab()
        self.setup_room_rack_tab()
        self.setup_folios_tab()
        self.setup_dining_tab()
        self.setup_night_audit_tab()

        self.tabs.addTab(self.tab_reservations, "📅  Reservations & Check-In")
        self.tabs.addTab(self.tab_room_rack, "🏨  Room Rack & Housekeeping")
        self.tabs.addTab(self.tab_folios, "💼  Guest Folios & Incidentals")
        self.tabs.addTab(self.tab_dining, "🍽️  Restaurant & KDS Tickets")
        self.tabs.addTab(self.tab_night_audit, "🌙  Night Audit & Daily GL")

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
    # TAB 1: Reservations & Check-In
    # -------------------------------------------------------------------------
    def setup_reservations_tab(self):
        layout = QVBoxLayout(self.tab_reservations)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        lbl_st = QLabel("Status:")
        lbl_st.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        self.combo_res_status = QComboBox()
        self.combo_res_status.addItems(["ALL", "CONFIRMED", "CHECKED_IN", "CHECKED_OUT", "CANCELLED"])
        self.combo_res_status.currentTextChanged.connect(self.filter_reservations)

        self.txt_res_search = QLineEdit()
        self.txt_res_search.setPlaceholderText("🔍 Search guest name, confirmation #, or room...")
        self.txt_res_search.textChanged.connect(self.filter_reservations)

        filter_bar.addWidget(lbl_st)
        filter_bar.addWidget(self.combo_res_status)
        filter_bar.addWidget(self.txt_res_search)
        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        self.table_reservations = QTableWidget(0, 10)
        self.table_reservations.setHorizontalHeaderLabels([
            "Conf #", "Guest Name", "Room Type", "Room #", "Check-In",
            "Check-Out", "Nights", "Status", "Grand Total (₹)", "Action"
        ])
        header = self.table_reservations.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.Stretch)
        self.table_reservations.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_reservations.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_reservations)

    # -------------------------------------------------------------------------
    # TAB 2: Room Rack & Housekeeping
    # -------------------------------------------------------------------------
    def setup_room_rack_tab(self):
        layout = QVBoxLayout(self.tab_room_rack)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        lbl_st = QLabel("Housekeeping Status:")
        lbl_st.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        self.combo_room_status = QComboBox()
        self.combo_room_status.addItems(["ALL", "AVAILABLE_CLEAN", "DIRTY", "INSPECTED", "OCCUPIED", "MAINTENANCE"])
        self.combo_room_status.currentTextChanged.connect(self.filter_rooms)

        btn_add_room = QPushButton("➕ Add Room")
        btn_add_room.setProperty("class", "btn_secondary")
        btn_add_room.clicked.connect(self.open_add_room_dialog)

        filter_bar.addWidget(lbl_st)
        filter_bar.addWidget(self.combo_room_status)
        filter_bar.addStretch()
        filter_bar.addWidget(btn_add_room)
        layout.addLayout(filter_bar)

        self.table_rooms = QTableWidget(0, 7)
        self.table_rooms.setHorizontalHeaderLabels([
            "Room #", "Room Type", "Wing / Building", "Floor", "Status", "Key Code", "Housekeeping Action"
        ])
        header = self.table_rooms.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        self.table_rooms.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_rooms.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_rooms)

    # -------------------------------------------------------------------------
    # TAB 3: Guest Folios & Incidentals
    # -------------------------------------------------------------------------
    def setup_folios_tab(self):
        layout = QVBoxLayout(self.tab_folios)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        lbl_st = QLabel("Folio Status:")
        lbl_st.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        self.combo_folio_status = QComboBox()
        self.combo_folio_status.addItems(["ALL", "OPEN", "SETTLED"])
        self.combo_folio_status.currentTextChanged.connect(self.filter_folios)

        filter_bar.addWidget(lbl_st)
        filter_bar.addWidget(self.combo_folio_status)
        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        self.table_folios = QTableWidget(0, 8)
        self.table_folios.setHorizontalHeaderLabels([
            "Folio #", "Guest Name", "Room #", "Charges (₹)", "Payments (₹)", "Balance Due (₹)", "Status", "Actions"
        ])
        header = self.table_folios.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        self.table_folios.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_folios.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_folios)

    # -------------------------------------------------------------------------
    # TAB 4: Restaurant & KDS Tickets
    # -------------------------------------------------------------------------
    def setup_dining_tab(self):
        layout = QVBoxLayout(self.tab_dining)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        lbl_info = QLabel("Live Restaurant Tables & Kitchen Display System (KDS) Active Tickets:")
        lbl_info.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")
        top_row.addWidget(lbl_info)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.table_dining = QTableWidget(0, 8)
        self.table_dining.setHorizontalHeaderLabels([
            "KDS Ticket #", "Table #", "Server", "Guests", "Ordered Items", "Status", "Total (₹)", "Billing Action"
        ])
        header = self.table_dining.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table_dining.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_dining.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_dining)

    # -------------------------------------------------------------------------
    # TAB 5: Night Audit & Daily GL
    # -------------------------------------------------------------------------
    def setup_night_audit_tab(self):
        layout = QVBoxLayout(self.tab_night_audit)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        audit_card = QFrame()
        audit_card.setProperty("class", "metric_card")
        c_layout = QVBoxLayout(audit_card)
        c_layout.setContentsMargins(20, 20, 20, 20)
        c_layout.setSpacing(10)

        lbl_na_title = QLabel("🌙 Automated End-of-Day Night Audit & Revenue Recognition Engine")
        lbl_na_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #A78BFA;")
        lbl_na_desc = QLabel(
            "The Night Audit process closes the daily hospitality operating ledger, posts nightly room rate charges "
            "to each active in-house guest folio, recalculates Occupancy Rate, ADR, and RevPAR metrics, and generates "
            "a balanced Double-Entry General Ledger journal entry directly in the Finance Engine."
        )
        lbl_na_desc.setWordWrap(True)
        lbl_na_desc.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MAIN}; line-height: 1.4;")

        btn_run = QPushButton("⚡ Execute Night Audit Now (GL Posting)")
        btn_run.setProperty("class", "btn_primary")
        btn_run.setStyleSheet("padding: 8px 18px; font-size: 13px; background-color: #7C3AED; border-color: #6D28D9;")
        btn_run.clicked.connect(self.run_night_audit)

        c_layout.addWidget(lbl_na_title)
        c_layout.addWidget(lbl_na_desc)
        c_layout.addWidget(btn_run, 0, Qt.AlignLeft)
        layout.addWidget(audit_card)

        # Audit History / Log text
        self.txt_audit_log = QTextEdit()
        self.txt_audit_log.setReadOnly(True)
        self.txt_audit_log.setStyleSheet(f"background-color: {ThemeColors.BG_SURFACE}; color: {ThemeColors.TEXT_MUTED}; font-family: monospace; font-size: 12px;")
        self.txt_audit_log.setText("Ready for End-of-Day Night Audit execution.\nSelect 'Execute Night Audit' above to post daily room charges.")
        layout.addWidget(self.txt_audit_log)

    # -------------------------------------------------------------------------
    # Data Refresh & Rendering
    # -------------------------------------------------------------------------
    def refresh_data(self):
        """Fetch latest rooms, reservations, folios, dining tables, orders, and telemetry."""
        self.cached_rooms = api_client.get_rooms()
        self.cached_reservations = api_client.get_reservations()
        self.cached_folios = api_client.get_guest_folios()
        self.cached_tables = api_client.get_dining_tables()
        self.cached_dining_orders = api_client.get_dining_orders()
        self.cached_room_types = api_client.get_room_types()
        self.cached_metrics = api_client.get_hospitality_metrics()

        # Update Telemetry Metric Cards
        m = self.cached_metrics
        self.card_occupancy.findChild(QLabel, "metric_value").setText(f"{float(m.get('occupancy_rate', 0)):.1f}%")
        self.card_adr.findChild(QLabel, "metric_value").setText(f"₹{to_decimal(m.get('average_daily_rate', 0)):,.2f}")
        self.card_revpar.findChild(QLabel, "metric_value").setText(f"₹{to_decimal(m.get('revpar', 0)):,.2f}")
        self.card_folios.findChild(QLabel, "metric_value").setText(f"₹{to_decimal(m.get('total_folio_receivables', 0)):,.2f}")
        self.card_fnb_rev.findChild(QLabel, "metric_value").setText(f"₹{to_decimal(m.get('today_fnb_revenue', 0)):,.2f}")

        # Render Tables
        self.filter_reservations()
        self.filter_rooms()
        self.filter_folios()
        self.render_dining_table()

    def filter_reservations(self):
        st_flt = self.combo_res_status.currentText().upper()
        q = self.txt_res_search.text().strip().lower()

        filtered = []
        for r in self.cached_reservations:
            if st_flt != "ALL" and r.get("status", "").upper() != st_flt:
                continue
            if q:
                matched = (
                    q in r.get("confirmation_code", "").lower() or
                    q in r.get("guest_name", "").lower() or
                    q in (r.get("room_number") or "").lower()
                )
                if not matched:
                    continue
            filtered.append(r)

        self.table_reservations.setRowCount(len(filtered))
        for row, r in enumerate(filtered):
            self.table_reservations.setItem(row, 0, QTableWidgetItem(r.get("confirmation_code", "")))
            self.table_reservations.setItem(row, 1, QTableWidgetItem(r.get("guest_name", "")))
            self.table_reservations.setItem(row, 2, QTableWidgetItem(r.get("room_type_name", "")))
            self.table_reservations.setItem(row, 3, QTableWidgetItem(r.get("room_number") or "Unassigned"))
            self.table_reservations.setItem(row, 4, QTableWidgetItem(str(r.get("check_in_date", ""))))
            self.table_reservations.setItem(row, 5, QTableWidgetItem(str(r.get("check_out_date", ""))))
            self.table_reservations.setItem(row, 6, QTableWidgetItem(str(r.get("nights", 1))))

            st = r.get("status", "CONFIRMED")
            st_item = QTableWidgetItem(st)
            if st == "CHECKED_IN":
                st_item.setForeground(Qt.cyan)
            elif st == "CHECKED_OUT":
                st_item.setForeground(Qt.green)
            self.table_reservations.setItem(row, 7, st_item)

            self.table_reservations.setItem(row, 8, QTableWidgetItem(f"₹{to_decimal(r.get('grand_total', 0)):,.2f}"))

            if st == "CONFIRMED":
                btn_cin = QPushButton("Check In Guest")
                btn_cin.setProperty("class", "btn_primary")
                btn_cin.setStyleSheet("padding: 2px 6px; font-size: 11px;")
                btn_cin.clicked.connect(lambda _, res=r: self.open_checkin_dialog(res))
                self.table_reservations.setCellWidget(row, 9, btn_cin)
            elif st == "CHECKED_IN":
                lbl_in = QLabel("In-House (Room " + str(r.get("room_number", "")) + ")")
                lbl_in.setStyleSheet("color: #06B6D4; font-size: 11px; font-weight: 600;")
                self.table_reservations.setCellWidget(row, 9, lbl_in)
            else:
                lbl_done = QLabel("Departed")
                lbl_done.setStyleSheet("color: #10B981; font-size: 11px;")
                self.table_reservations.setCellWidget(row, 9, lbl_done)

    def filter_rooms(self):
        st_flt = self.combo_room_status.currentText().upper()
        filtered = [
            r for r in self.cached_rooms
            if st_flt == "ALL" or r.get("status", "").upper() == st_flt
        ]

        self.table_rooms.setRowCount(len(filtered))
        for row, rm in enumerate(filtered):
            self.table_rooms.setItem(row, 0, QTableWidgetItem(rm.get("room_number", "")))
            self.table_rooms.setItem(row, 1, QTableWidgetItem(rm.get("room_type_name", "")))
            self.table_rooms.setItem(row, 2, QTableWidgetItem(rm.get("building_wing", "")))
            self.table_rooms.setItem(row, 3, QTableWidgetItem(rm.get("floor", "")))

            st = rm.get("status", "AVAILABLE_CLEAN")
            st_item = QTableWidgetItem(st)
            if st == "AVAILABLE_CLEAN":
                st_item.setForeground(Qt.green)
            elif st == "OCCUPIED":
                st_item.setForeground(Qt.cyan)
            elif st == "DIRTY":
                st_item.setForeground(Qt.red)
            elif st == "MAINTENANCE":
                st_item.setForeground(Qt.darkYellow)
            self.table_rooms.setItem(row, 4, st_item)

            self.table_rooms.setItem(row, 5, QTableWidgetItem(rm.get("key_card_code") or "None"))

            if st == "DIRTY":
                btn_clean = QPushButton("Mark Clean")
                btn_clean.setProperty("class", "btn_primary")
                btn_clean.setStyleSheet("padding: 2px 6px; font-size: 11px;")
                btn_clean.clicked.connect(lambda _, r_id=rm["id"]: self.set_room_clean(r_id))
                self.table_rooms.setCellWidget(row, 6, btn_clean)
            elif st == "AVAILABLE_CLEAN":
                lbl_ok = QLabel("Ready for Guest")
                lbl_ok.setStyleSheet("color: #10B981; font-size: 11px;")
                self.table_rooms.setCellWidget(row, 6, lbl_ok)
            else:
                lbl_other = QLabel(rm.get("notes") or st)
                lbl_other.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
                self.table_rooms.setCellWidget(row, 6, lbl_other)

    def filter_folios(self):
        st_flt = self.combo_folio_status.currentText().upper()
        filtered = [
            f for f in self.cached_folios
            if st_flt == "ALL" or f.get("status", "").upper() == st_flt
        ]

        self.table_folios.setRowCount(len(filtered))
        for row, fol in enumerate(filtered):
            self.table_folios.setItem(row, 0, QTableWidgetItem(fol.get("folio_number", "")))
            self.table_folios.setItem(row, 1, QTableWidgetItem(fol.get("guest_name", "")))
            self.table_folios.setItem(row, 2, QTableWidgetItem(fol.get("room_number", "")))
            self.table_folios.setItem(row, 3, QTableWidgetItem(f"₹{to_decimal(fol.get('total_charges', 0)):,.2f}"))
            self.table_folios.setItem(row, 4, QTableWidgetItem(f"₹{to_decimal(fol.get('total_payments', 0)):,.2f}"))
            self.table_folios.setItem(row, 5, QTableWidgetItem(f"₹{to_decimal(fol.get('balance_due', 0)):,.2f}"))

            st = fol.get("status", "OPEN")
            st_item = QTableWidgetItem(st)
            if st == "SETTLED":
                st_item.setForeground(Qt.green)
            else:
                st_item.setForeground(Qt.cyan)
            self.table_folios.setItem(row, 6, st_item)

            if st == "OPEN":
                btn_box = QWidget()
                b_layout = QHBoxLayout(btn_box)
                b_layout.setContentsMargins(0, 0, 0, 0)
                b_layout.setSpacing(4)

                btn_add = QPushButton("➕ Incidental")
                btn_add.setProperty("class", "btn_secondary")
                btn_add.setStyleSheet("padding: 2px 6px; font-size: 11px;")
                btn_add.clicked.connect(lambda _, f=fol: self.open_add_charge_dialog(f))

                btn_settle = QPushButton("⚡ Settle & Check Out")
                btn_settle.setProperty("class", "btn_primary")
                btn_settle.setStyleSheet("padding: 2px 6px; font-size: 11px;")
                btn_settle.clicked.connect(lambda _, f=fol: self.open_settle_folio_dialog(f))

                b_layout.addWidget(btn_add)
                b_layout.addWidget(btn_settle)
                self.table_folios.setCellWidget(row, 7, btn_box)
            else:
                lbl_done = QLabel("✅ Settled & Archived")
                lbl_done.setStyleSheet("color: #10B981; font-weight: 600; font-size: 11px;")
                self.table_folios.setCellWidget(row, 7, lbl_done)

    def render_dining_table(self):
        self.table_dining.setRowCount(len(self.cached_dining_orders))
        for row, ord_rec in enumerate(self.cached_dining_orders):
            self.table_dining.setItem(row, 0, QTableWidgetItem(ord_rec.get("order_number", "")))
            self.table_dining.setItem(row, 1, QTableWidgetItem(ord_rec.get("table_number", "")))
            self.table_dining.setItem(row, 2, QTableWidgetItem(ord_rec.get("server_name", "")))
            self.table_dining.setItem(row, 3, QTableWidgetItem(str(ord_rec.get("guest_count", 2))))

            item_names = ", ".join([f"{i.get('quantity', 1)}x {i.get('item_name')}" for i in ord_rec.get("items", [])])
            self.table_dining.setItem(row, 4, QTableWidgetItem(item_names))

            st = ord_rec.get("status", "PENDING")
            st_item = QTableWidgetItem(st)
            if st == "SERVED":
                st_item.setForeground(Qt.green)
            elif st == "PREPARING":
                st_item.setForeground(Qt.darkYellow)
            self.table_dining.setItem(row, 5, st_item)

            self.table_dining.setItem(row, 6, QTableWidgetItem(f"₹{to_decimal(ord_rec.get('grand_total', 0)):,.2f}"))

            if not ord_rec.get("is_paid", False):
                btn_bill = QPushButton("Settle Bill")
                btn_bill.setProperty("class", "btn_primary")
                btn_bill.setStyleSheet("padding: 2px 6px; font-size: 11px;")
                btn_bill.clicked.connect(lambda _, o=ord_rec: self.open_settle_dining_dialog(o))
                self.table_dining.setCellWidget(row, 7, btn_bill)
            else:
                lbl_paid = QLabel("Paid (" + str(ord_rec.get("payment_method")) + ")")
                lbl_paid.setStyleSheet("color: #10B981; font-weight: 600; font-size: 11px;")
                self.table_dining.setCellWidget(row, 7, lbl_paid)

    # -------------------------------------------------------------------------
    # Dialogs & Modal Actions
    # -------------------------------------------------------------------------
    def open_create_reservation_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Book Guest Reservation")
        dialog.resize(500, 460)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        txt_name = QLineEdit()
        txt_name.setPlaceholderText("Guest Full Name")
        txt_email = QLineEdit()
        txt_email.setPlaceholderText("guest@domain.com")
        txt_phone = QLineEdit()
        txt_phone.setPlaceholderText("+91 98401 00000")

        combo_rt = QComboBox()
        for rt in self.cached_room_types:
            combo_rt.addItem(f"{rt['name']} (₹{to_decimal(rt['base_rate_per_night']):,.2f}/night)", rt["id"])

        date_in = QDateEdit()
        date_in.setCalendarPopup(True)
        date_in.setDate(QDate.currentDate())

        date_out = QDateEdit()
        date_out.setCalendarPopup(True)
        date_out.setDate(QDate.currentDate().addDays(2))

        combo_meal = QComboBox()
        combo_meal.addItems(["CP - Bed & Breakfast", "EP - Room Only", "MAP - Half Board", "AP - Full Board"])

        spin_deposit = QDoubleSpinBox()
        spin_deposit.setRange(0.0, 500000.0)
        spin_deposit.setValue(5000.0)
        spin_deposit.setPrefix("₹")

        txt_req = QLineEdit()
        txt_req.setPlaceholderText("Dietary preference, floor preference, or airport pickup")

        form.addRow("Guest Name*:", txt_name)
        form.addRow("Email*:", txt_email)
        form.addRow("Phone*:", txt_phone)
        form.addRow("Room Type*:", combo_rt)
        form.addRow("Check-In Date*:", date_in)
        form.addRow("Check-Out Date*:", date_out)
        form.addRow("Meal Plan*:", combo_meal)
        form.addRow("Advance Deposit:", spin_deposit)
        form.addRow("Special Requests:", txt_req)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_book = QPushButton("Confirm Booking")
        btn_book.setProperty("class", "btn_primary")

        def submit():
            gname = txt_name.text().strip()
            gemail = txt_email.text().strip()
            gphone = txt_phone.text().strip()
            if not gname or not gemail or not gphone:
                QMessageBox.warning(dialog, "Validation Error", "Guest name, email, and phone are required.")
                return

            payload = {
                "guest_name": gname,
                "guest_email": gemail,
                "guest_phone": gphone,
                "check_in_date": date_in.date().toString("yyyy-MM-dd"),
                "check_out_date": date_out.date().toString("yyyy-MM-dd"),
                "room_type_id": combo_rt.currentData(),
                "meal_plan": combo_meal.currentText().split(" - ")[0],
                "advance_deposit_paid": spin_deposit.value(),
                "special_requests": txt_req.text().strip() or None
            }
            try:
                res = api_client.create_reservation(payload)
                QMessageBox.information(dialog, "Booking Confirmed", f"Reservation {res['confirmation_code']} booked successfully for {gname}.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to book reservation: {str(e)}")

        btn_book.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_book)
        form.addRow(btn_row)

        dialog.exec()

    def open_checkin_dialog(self, res: Dict[str, Any]):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Check In Guest — {res['confirmation_code']}")
        dialog.resize(460, 260)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        lbl_info = QLabel(f"<b>Guest:</b> {res['guest_name']}<br><b>Room Type:</b> {res['room_type_name']}")
        form.addRow(lbl_info)

        combo_rooms = QComboBox()
        # Find clean rooms of this type
        clean_rooms = [
            rm for rm in self.cached_rooms
            if rm["room_type_id"] == res["room_type_id"] and rm["status"] in ("AVAILABLE_CLEAN", "INSPECTED")
        ]
        if not clean_rooms:
            # Fallback to any clean room
            clean_rooms = [rm for rm in self.cached_rooms if rm["status"] in ("AVAILABLE_CLEAN", "INSPECTED")]

        for rm in clean_rooms:
            combo_rooms.addItem(f"Room {rm['room_number']} ({rm['floor']}, {rm['building_wing']})", rm["id"])

        txt_key = QLineEdit()
        txt_key.setText(f"KEY-{clean_rooms[0]['room_number'] if clean_rooms else '101'}-A")

        form.addRow("Assign Room*:", combo_rooms)
        form.addRow("Key Card Encode:", txt_key)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_cin = QPushButton("Check In & Open Folio")
        btn_cin.setProperty("class", "btn_primary")

        def submit():
            if not combo_rooms.count():
                QMessageBox.warning(dialog, "No Clean Rooms", "No clean rooms available for assignment.")
                return

            payload = {
                "room_id": combo_rooms.currentData(),
                "key_card_code": txt_key.text().strip()
            }
            try:
                api_client.check_in_guest(res["id"], payload)
                QMessageBox.information(dialog, "Guest Checked In", f"Guest {res['guest_name']} checked in. Active folio opened.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to check in: {str(e)}")

        btn_cin.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_cin)
        form.addRow(btn_row)

        dialog.exec()

    def set_room_clean(self, room_id: str):
        try:
            api_client.update_room_status(room_id, "AVAILABLE_CLEAN")
            QMessageBox.information(self, "Housekeeping", "Room marked AVAILABLE_CLEAN and ready for inspection.")
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update room: {str(e)}")

    def open_add_room_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Room to Rack")
        dialog.resize(420, 280)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        txt_num = QLineEdit()
        txt_num.setPlaceholderText("e.g. 104, 208, Villa-3")
        combo_rt = QComboBox()
        for rt in self.cached_room_types:
            combo_rt.addItem(rt["name"], rt["id"])

        txt_floor = QLineEdit()
        txt_floor.setText("Floor 1")
        txt_wing = QLineEdit()
        txt_wing.setText("Main Wing")

        form.addRow("Room Number*:", txt_num)
        form.addRow("Room Type*:", combo_rt)
        form.addRow("Floor:", txt_floor)
        form.addRow("Wing / Building:", txt_wing)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Save Room")
        btn_save.setProperty("class", "btn_primary")

        def submit():
            num = txt_num.text().strip()
            if not num:
                QMessageBox.warning(dialog, "Validation Error", "Room number is required.")
                return

            payload = {
                "room_number": num,
                "room_type_id": combo_rt.currentData(),
                "floor": txt_floor.text().strip(),
                "building_wing": txt_wing.text().strip()
            }
            try:
                api_client.create_room(payload)
                QMessageBox.information(dialog, "Room Created", f"Room {num} added to room rack.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to add room: {str(e)}")

        btn_save.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        form.addRow(btn_row)

        dialog.exec()

    def open_add_charge_dialog(self, fol: Dict[str, Any]):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Post Incidental Charge — {fol['folio_number']}")
        dialog.resize(450, 260)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        combo_type = QComboBox()
        combo_type.addItems(["FOOD_BEVERAGE", "SPA", "LAUNDRY", "MISC"])

        txt_desc = QLineEdit()
        txt_desc.setText("Restaurant Dining Charge - Aura Fine Dining")

        spin_amt = QDoubleSpinBox()
        spin_amt.setRange(10.0, 100000.0)
        spin_amt.setValue(2500.0)
        spin_amt.setPrefix("₹")

        txt_ref = QLineEdit()
        txt_ref.setText("BILL-9901")

        form.addRow("Charge Type*:", combo_type)
        form.addRow("Description*:", txt_desc)
        form.addRow("Amount (₹)*:", spin_amt)
        form.addRow("Reference #:", txt_ref)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_post = QPushButton("Post to Folio")
        btn_post.setProperty("class", "btn_primary")

        def submit():
            desc = txt_desc.text().strip()
            if not desc:
                QMessageBox.warning(dialog, "Validation Error", "Description is required.")
                return

            payload = {
                "line_type": combo_type.currentText(),
                "description": desc,
                "amount": spin_amt.value(),
                "reference": txt_ref.text().strip() or None
            }
            try:
                api_client.add_folio_charge(fol["id"], payload)
                QMessageBox.information(dialog, "Charge Posted", f"Posted ₹{spin_amt.value():,.2f} to {fol['folio_number']}.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to post charge: {str(e)}")

        btn_post.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_post)
        form.addRow(btn_row)

        dialog.exec()

    def open_settle_folio_dialog(self, fol: Dict[str, Any]):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Settle Folio & Check Out — {fol['folio_number']}")
        dialog.resize(460, 280)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        lbl_summary = QLabel(
            f"<b>Guest:</b> {fol['guest_name']} | <b>Room:</b> {fol['room_number']}<br>"
            f"<b>Total Charges:</b> ₹{to_decimal(fol.get('total_charges', 0)):,.2f}<br>"
            f"<b>Payments:</b> ₹{to_decimal(fol.get('total_payments', 0)):,.2f}<br>"
            f"<b style='color:#10B981; font-size:14px;'>Remaining Balance Due: ₹{to_decimal(fol.get('balance_due', 0)):,.2f}</b>"
        )
        form.addRow(lbl_summary)

        combo_pay = QComboBox()
        combo_pay.addItems(["CREDIT_CARD", "UPI_QR", "CASH", "BANK_TRANSFER"])
        form.addRow("Settlement Tender*:", combo_pay)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_settle = QPushButton("⚡ Final Settle & Post GL")
        btn_settle.setProperty("class", "btn_primary")

        def submit():
            try:
                res = api_client.check_out_and_settle_folio(fol["id"], combo_pay.currentText())
                je_id = res.get("journal_entry_id", "Posted")
                QMessageBox.information(
                    dialog,
                    "Check-Out Complete",
                    f"Folio {fol['folio_number']} settled successfully!\n\n"
                    f"• Revenue recognized & posted to General Ledger: {je_id}\n"
                    f"• Room {fol['room_number']} marked DIRTY for Housekeeping."
                )
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to settle folio: {str(e)}")

        btn_settle.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_settle)
        form.addRow(btn_row)

        dialog.exec()

    def open_create_dining_order_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Send New Dining Order to Kitchen (KDS)")
        dialog.resize(500, 420)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        combo_table = QComboBox()
        for t in self.cached_tables:
            combo_table.addItem(f"{t['table_number']} ({t['area_section']})", t["id"])

        txt_server = QLineEdit()
        txt_server.setText("Ramesh Swaminathan")

        spin_guests = QSpinBox()
        spin_guests.setRange(1, 20)
        spin_guests.setValue(2)

        txt_item1 = QLineEdit()
        txt_item1.setText("Tandoori Lobster Tail")
        spin_price1 = QDoubleSpinBox()
        spin_price1.setRange(50.0, 10000.0)
        spin_price1.setValue(1250.0)
        spin_price1.setPrefix("₹")

        txt_item2 = QLineEdit()
        txt_item2.setText("Cardamom Kulfi Falooda")
        spin_price2 = QDoubleSpinBox()
        spin_price2.setRange(50.0, 10000.0)
        spin_price2.setValue(350.0)
        spin_price2.setPrefix("₹")

        form.addRow("Dining Table*:", combo_table)
        form.addRow("Server Name*:", txt_server)
        form.addRow("Guest Count*:", spin_guests)
        form.addRow("Main Dish 1*:", txt_item1)
        form.addRow("Dish 1 Price:", spin_price1)
        form.addRow("Dessert 2:", txt_item2)
        form.addRow("Dish 2 Price:", spin_price2)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_send = QPushButton("Send to Kitchen (KDS)")
        btn_send.setProperty("class", "btn_primary")

        def submit():
            t_num = combo_table.currentText().split()[0]
            items = [
                {"item_name": txt_item1.text().strip(), "quantity": 1, "unit_price": spin_price1.value()},
                {"item_name": txt_item2.text().strip(), "quantity": 1, "unit_price": spin_price2.value()}
            ]
            payload = {
                "table_id": combo_table.currentData(),
                "table_number": t_num,
                "server_name": txt_server.text().strip(),
                "guest_count": spin_guests.value(),
                "items": items
            }
            try:
                res = api_client.create_dining_order(payload)
                QMessageBox.information(dialog, "KDS Order Created", f"Ticket {res['order_number']} sent to kitchen for Table {t_num}.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to send order: {str(e)}")

        btn_send.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_send)
        form.addRow(btn_row)

        dialog.exec()

    def open_settle_dining_dialog(self, ord_rec: Dict[str, Any]):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Settle Dining Bill — {ord_rec['order_number']}")
        dialog.resize(460, 300)
        form = QFormLayout(dialog)
        form.setSpacing(12)

        lbl_tot = QLabel(f"<b>Table:</b> {ord_rec['table_number']} | <b>Grand Total:</b> ₹{to_decimal(ord_rec.get('grand_total', 0)):,.2f}")
        form.addRow(lbl_tot)

        combo_method = QComboBox()
        combo_method.addItems(["CARD", "UPI", "CASH", "ROOM_FOLIO"])

        combo_folio = QComboBox()
        # List open guest folios
        for f in self.cached_folios:
            if f.get("status") == "OPEN":
                combo_folio.addItem(f"Room {f['room_number']} - {f['guest_name']} ({f['folio_number']})", f["id"])

        form.addRow("Payment Tender*:", combo_method)
        form.addRow("Transfer to Room Folio:", combo_folio)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_pay = QPushButton("Settle Dining Bill")
        btn_pay.setProperty("class", "btn_primary")

        def submit():
            payload = {
                "payment_method": combo_method.currentText(),
                "room_folio_id": combo_folio.currentData() if combo_method.currentText() == "ROOM_FOLIO" else None
            }
            try:
                api_client.settle_dining_order(ord_rec["id"], payload)
                QMessageBox.information(dialog, "Bill Settled", f"Dining order {ord_rec['order_number']} settled via {combo_method.currentText()}.")
                dialog.accept()
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to settle bill: {str(e)}")

        btn_pay.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_pay)
        form.addRow(btn_row)

        dialog.exec()

    def run_night_audit(self):
        confirm = QMessageBox.question(
            self,
            "Confirm Night Audit",
            "Are you sure you want to execute the End-of-Day Night Audit?\n\n"
            "This will post nightly room charges across all in-house guest folios "
            "and create a consolidated revenue journal entry in the General Ledger.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            res = api_client.run_night_audit()
            je_ref = res.get("journal_entry_id", "Posted")
            count = res.get("folios_processed", 0)
            tot = to_decimal(res.get("total_room_charges_posted", 0))

            log_msg = (
                f"[{datetime.now().strftime('%H:%M:%S')}] NIGHT AUDIT EXECUTED SUCCESSFULLY:\n"
                f"• Processed {count} in-house guest folios\n"
                f"• Posted daily room charges totaling ₹{tot:,.2f}\n"
                f"• General Ledger Revenue Posting Ref: {je_ref}\n"
                f"• Hospitality Occupancy KPIs updated.\n"
            )
            self.txt_audit_log.append(log_msg)
            QMessageBox.information(
                self,
                "Night Audit Complete",
                f"Night Audit Completed!\n\n"
                f"Folios Processed: {count}\n"
                f"Total Room Charges Posted: ₹{tot:,.2f}\n"
                f"Finance GL Journal Reference: {je_ref}"
            )
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run night audit: {str(e)}")
