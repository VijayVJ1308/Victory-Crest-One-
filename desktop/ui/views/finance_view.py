"""Victory Crest One - Finance and General Accounting Desktop View
Unified interface for Double-entry General Ledger, Chart of Accounts,
Accounts Receivable (Invoices), Accounts Payable (Bills), and Financial Statements.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDoubleSpinBox, QDateEdit, QTextEdit
)
from PySide6.QtCore import Qt, QDate

from desktop.core.theme import ThemeColors
from desktop.core.session import session_manager
from desktop.services.api_client import api_client
from shared.calculations import to_decimal


class FinanceView(QWidget):
    """Central Finance & General Accounting management console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # 1. Header Section
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("Finance & General Accounting")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Double-entry General Ledger, Chart of Accounts, Invoicing (AR), Payables (AP), and Financial Statements.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        # Action Buttons
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)
        header_row.addWidget(btn_refresh)

        btn_new_je = QPushButton("➕ New Journal")
        btn_new_je.setProperty("class", "btn_primary")
        btn_new_je.clicked.connect(self.open_new_journal_dialog)
        header_row.addWidget(btn_new_je)

        main_layout.addLayout(header_row)

        # 2. KPI Summary Cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_assets = self.create_summary_card("Total Assets", "₹0.00", "Balance Sheet", ThemeColors.ACCENT_PRIMARY)
        self.kpi_ar = self.create_summary_card("Accounts Receivable (AR)", "₹0.00", "Pending Customer Collections", ThemeColors.STATUS_INFO)
        self.kpi_ap = self.create_summary_card("Accounts Payable (AP)", "₹0.00", "Vendor Payables Due", ThemeColors.STATUS_WARNING)
        self.kpi_profit = self.create_summary_card("Net Profit (YTD)", "₹0.00", "Profit & Loss Net", ThemeColors.STATUS_SUCCESS)

        kpi_row.addWidget(self.kpi_assets)
        kpi_row.addWidget(self.kpi_ar)
        kpi_row.addWidget(self.kpi_ap)
        kpi_row.addWidget(self.kpi_profit)
        main_layout.addLayout(kpi_row)

        # 3. Main Navigation Tabs
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
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-weight: 600;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background: {ThemeColors.BG_SURFACE};
                color: {ThemeColors.TEXT_MAIN};
                border-bottom: 2px solid {ThemeColors.ACCENT_PRIMARY};
            }}
        """)

        # Tab Pages
        self.journals_tab = self.build_journals_tab()
        self.coa_tab = self.build_coa_tab()
        self.ar_tab = self.build_ar_tab()
        self.ap_tab = self.build_ap_tab()
        self.reports_tab = self.build_reports_tab()

        self.tabs.addTab(self.journals_tab, "📑 General Ledger & Journals")
        self.tabs.addTab(self.coa_tab, "🌳 Chart of Accounts")
        self.tabs.addTab(self.ar_tab, "📥 Accounts Receivable (Invoices)")
        self.tabs.addTab(self.ap_tab, "📤 Accounts Payable (Bills)")
        self.tabs.addTab(self.reports_tab, "📊 Financial Statements")

        main_layout.addWidget(self.tabs)

    def create_summary_card(self, title: str, value: str, sub: str, color_hex: str) -> QFrame:
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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ThemeColors.TEXT_MUTED}; text-transform: uppercase;")
        v_lbl = QLabel(value)
        v_lbl.setObjectName("value_label")
        v_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {color_hex};")
        s_lbl = QLabel(sub)
        s_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_DIM};")

        layout.addWidget(t_lbl)
        layout.addWidget(v_lbl)
        layout.addWidget(s_lbl)
        return card

    # --- 1. General Ledger Journals Tab ---
    def build_journals_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filter bar
        bar = QHBoxLayout()
        bar.setSpacing(10)
        lbl = QLabel("Filter:")
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-size: 12px; font-weight: 600;")
        bar.addWidget(lbl)

        self.journal_status_filter = QComboBox()
        self.journal_status_filter.addItems(["All Statuses", "POSTED", "REVERSED", "DRAFT"])
        self.journal_status_filter.currentIndexChanged.connect(self.load_journals)
        bar.addWidget(self.journal_status_filter)

        bar.addStretch()

        btn_reverse = QPushButton("🔄 Reverse Selected Journal")
        btn_reverse.setProperty("class", "btn_secondary")
        btn_reverse.clicked.connect(self.reverse_selected_journal)
        bar.addWidget(btn_reverse)
        layout.addLayout(bar)

        # Table
        self.journals_table = QTableWidget()
        self.journals_table.setColumnCount(8)
        self.journals_table.setHorizontalHeaderLabels([
            "Entry #", "Date", "Type", "Reference", "Description", "Debits", "Credits", "Status"
        ])
        self.journals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.journals_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.journals_table.setStyleSheet(self._table_style())
        layout.addWidget(self.journals_table)

        return widget

    # --- 2. Chart of Accounts Tab ---
    def build_coa_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        lbl = QLabel("Category:")
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-size: 12px; font-weight: 600;")
        bar.addWidget(lbl)

        self.coa_type_filter = QComboBox()
        self.coa_type_filter.addItems(["All Account Types", "ASSET", "LIABILITY", "EQUITY", "REVENUE", "COGS", "EXPENSE"])
        self.coa_type_filter.currentIndexChanged.connect(self.load_accounts)
        bar.addWidget(self.coa_type_filter)
        bar.addStretch()

        btn_add_acc = QPushButton("➕ Add Account")
        btn_add_acc.setProperty("class", "btn_secondary")
        btn_add_acc.clicked.connect(self.open_new_account_dialog)
        bar.addWidget(btn_add_acc)
        layout.addLayout(bar)

        self.coa_table = QTableWidget()
        self.coa_table.setColumnCount(7)
        self.coa_table.setHorizontalHeaderLabels([
            "Code", "Account Name", "Type", "Normal Balance", "Current Balance", "System", "Status"
        ])
        self.coa_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.coa_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.coa_table.setStyleSheet(self._table_style())
        layout.addWidget(self.coa_table)

        return widget

    # --- 3. Accounts Receivable (Invoices) Tab ---
    def build_ar_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        lbl = QLabel("Status:")
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-size: 12px; font-weight: 600;")
        bar.addWidget(lbl)

        self.ar_status_filter = QComboBox()
        self.ar_status_filter.addItems(["All Invoices", "ISSUED", "PARTIALLY_PAID", "PAID", "DRAFT"])
        self.ar_status_filter.currentIndexChanged.connect(self.load_invoices)
        bar.addWidget(self.ar_status_filter)
        bar.addStretch()

        btn_new_inv = QPushButton("➕ Create Invoice")
        btn_new_inv.setProperty("class", "btn_primary")
        btn_new_inv.clicked.connect(self.open_new_invoice_dialog)
        bar.addWidget(btn_new_inv)

        btn_pay_inv = QPushButton("💳 Record Payment")
        btn_pay_inv.setProperty("class", "btn_secondary")
        btn_pay_inv.clicked.connect(self.open_record_payment_dialog)
        bar.addWidget(btn_pay_inv)
        layout.addLayout(bar)

        self.ar_table = QTableWidget()
        self.ar_table.setColumnCount(8)
        self.ar_table.setHorizontalHeaderLabels([
            "Invoice #", "Customer", "Issue Date", "Due Date", "Total", "Paid", "Balance Due", "Status"
        ])
        self.ar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ar_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ar_table.setStyleSheet(self._table_style())
        layout.addWidget(self.ar_table)

        return widget

    # --- 4. Accounts Payable (Bills) Tab ---
    def build_ap_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        lbl = QLabel("Status:")
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-size: 12px; font-weight: 600;")
        bar.addWidget(lbl)

        self.ap_status_filter = QComboBox()
        self.ap_status_filter.addItems(["All Bills", "RECEIVED", "PARTIALLY_PAID", "PAID", "DRAFT"])
        self.ap_status_filter.currentIndexChanged.connect(self.load_bills)
        bar.addWidget(self.ap_status_filter)
        bar.addStretch()

        btn_new_bill = QPushButton("➕ Record Bill")
        btn_new_bill.setProperty("class", "btn_primary")
        btn_new_bill.clicked.connect(self.open_new_bill_dialog)
        bar.addWidget(btn_new_bill)

        btn_pay_bill = QPushButton("💸 Pay Bill")
        btn_pay_bill.setProperty("class", "btn_secondary")
        btn_pay_bill.clicked.connect(self.open_pay_bill_dialog)
        bar.addWidget(btn_pay_bill)
        layout.addLayout(bar)

        self.ap_table = QTableWidget()
        self.ap_table.setColumnCount(8)
        self.ap_table.setHorizontalHeaderLabels([
            "Bill #", "Supplier", "Vendor Ref", "Bill Date", "Due Date", "Total", "Paid", "Balance Due", "Status"
        ])
        self.ap_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ap_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ap_table.setStyleSheet(self._table_style())
        layout.addWidget(self.ap_table)

        return widget

    # --- 5. Financial Statements Tab ---
    def build_reports_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        lbl = QLabel("Statement:")
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-size: 12px; font-weight: 600;")
        bar.addWidget(lbl)

        self.report_selector = QComboBox()
        self.report_selector.addItems(["Trial Balance", "Profit & Loss (P&L)", "Balance Sheet"])
        self.report_selector.currentIndexChanged.connect(self.load_financial_reports)
        bar.addWidget(self.report_selector)

        self.report_status_tag = QLabel("Ledger: Balanced")
        self.report_status_tag.setStyleSheet(f"color: {ThemeColors.STATUS_SUCCESS}; font-weight: 700; font-size: 12px;")
        bar.addWidget(self.report_status_tag)
        bar.addStretch()

        layout.addLayout(bar)

        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(4)
        self.reports_table.setHorizontalHeaderLabels(["Account / Section", "Details", "Debit / Amount", "Credit / Subtotal"])
        self.reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reports_table.setStyleSheet(self._table_style())
        layout.addWidget(self.reports_table)

        return widget

    def _table_style(self) -> str:
        return f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                gridline-color: {ThemeColors.BORDER_LIGHT};
                color: {ThemeColors.TEXT_MAIN};
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_SECONDARY};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 600;
                padding: 6px;
                border: 1px solid {ThemeColors.BORDER_LIGHT};
            }}
            QTableWidget::item:selected {{
                background-color: {ThemeColors.ACCENT_PRIMARY};
                color: #FFFFFF;
            }}
        """

    # --- Data Loading Logic ---
    def refresh_data(self):
        """Reload all finance components from API."""
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        self.load_kpis(org_id)
        self.load_journals()
        self.load_accounts()
        self.load_invoices()
        self.load_bills()
        self.load_financial_reports()

    def load_kpis(self, org_id: Optional[str]):
        try:
            bs = api_client.get_balance_sheet(org_id)
            total_assets = bs.get("total_assets", 0.0)
            self.kpi_assets.findChild(QLabel, "value_label").setText(f"₹{Decimal(str(total_assets)):,.2f}")

            pnl = api_client.get_profit_and_loss(org_id)
            net_profit = pnl.get("net_profit", 0.0)
            self.kpi_profit.findChild(QLabel, "value_label").setText(f"₹{Decimal(str(net_profit)):,.2f}")

            invoices = api_client.get_invoices(org_id)
            total_ar = sum(to_decimal(i.get("balance_due", 0)) for i in invoices)
            self.kpi_ar.findChild(QLabel, "value_label").setText(f"₹{total_ar:,.2f}")

            bills = api_client.get_bills(org_id)
            total_ap = sum(to_decimal(b.get("balance_due", 0)) for b in bills)
            self.kpi_ap.findChild(QLabel, "value_label").setText(f"₹{total_ap:,.2f}")
        except Exception:
            pass

    def load_journals(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        st = self.journal_status_filter.currentText()
        st_filter = None if st == "All Statuses" else st

        journals = api_client.get_journals(org_id, status_filter=st_filter)
        self.journals_table.setRowCount(len(journals))

        for row, je in enumerate(journals):
            dt_str = str(je.get("entry_date", ""))[:10]
            self.journals_table.setItem(row, 0, QTableWidgetItem(je.get("entry_number", "")))
            self.journals_table.setItem(row, 1, QTableWidgetItem(dt_str))
            self.journals_table.setItem(row, 2, QTableWidgetItem(je.get("entry_type", "")))
            self.journals_table.setItem(row, 3, QTableWidgetItem(je.get("reference", "") or "-"))
            self.journals_table.setItem(row, 4, QTableWidgetItem(je.get("description", "")))
            self.journals_table.setItem(row, 5, QTableWidgetItem(f"₹{Decimal(str(je.get('total_debit', 0))):,.2f}"))
            self.journals_table.setItem(row, 6, QTableWidgetItem(f"₹{Decimal(str(je.get('total_credit', 0))):,.2f}"))
            
            st_item = QTableWidgetItem(je.get("status", ""))
            if je.get("status") == "POSTED":
                st_item.setForeground(Qt.green)
            elif je.get("status") == "REVERSED":
                st_item.setForeground(Qt.red)
            self.journals_table.setItem(row, 7, st_item)

    def load_accounts(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        cat = self.coa_type_filter.currentText()
        cat_filter = None if cat == "All Account Types" else cat

        accounts = api_client.get_accounts(org_id, account_type=cat_filter)
        self.coa_table.setRowCount(len(accounts))

        for row, acc in enumerate(accounts):
            bal = Decimal(str(acc.get("current_balance", 0)))
            self.coa_table.setItem(row, 0, QTableWidgetItem(acc.get("account_code", "")))
            self.coa_table.setItem(row, 1, QTableWidgetItem(acc.get("account_name", "")))
            self.coa_table.setItem(row, 2, QTableWidgetItem(acc.get("account_type", "")))
            self.coa_table.setItem(row, 3, QTableWidgetItem(acc.get("normal_balance", "")))
            self.coa_table.setItem(row, 4, QTableWidgetItem(f"₹{bal:,.2f}"))
            self.coa_table.setItem(row, 5, QTableWidgetItem("🔒 System" if acc.get("is_system") else "Custom"))
            self.coa_table.setItem(row, 6, QTableWidgetItem("Active" if acc.get("is_active") else "Inactive"))

    def load_invoices(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        st = self.ar_status_filter.currentText()
        st_filter = None if st == "All Invoices" else st

        invoices = api_client.get_invoices(org_id, status_filter=st_filter)
        self.ar_table.setRowCount(len(invoices))

        for row, inv in enumerate(invoices):
            iss_str = str(inv.get("issue_date", ""))[:10]
            due_str = str(inv.get("due_date", ""))[:10]
            self.ar_table.setItem(row, 0, QTableWidgetItem(inv.get("invoice_number", "")))
            self.ar_table.setItem(row, 1, QTableWidgetItem(inv.get("customer_name", "")))
            self.ar_table.setItem(row, 2, QTableWidgetItem(iss_str))
            self.ar_table.setItem(row, 3, QTableWidgetItem(due_str))
            self.ar_table.setItem(row, 4, QTableWidgetItem(f"₹{Decimal(str(inv.get('total_amount', 0))):,.2f}"))
            self.ar_table.setItem(row, 5, QTableWidgetItem(f"₹{Decimal(str(inv.get('paid_amount', 0))):,.2f}"))
            self.ar_table.setItem(row, 6, QTableWidgetItem(f"₹{Decimal(str(inv.get('balance_due', 0))):,.2f}"))
            
            st_item = QTableWidgetItem(inv.get("status", ""))
            if inv.get("status") == "PAID":
                st_item.setForeground(Qt.green)
            elif inv.get("status") == "PARTIALLY_PAID":
                st_item.setForeground(Qt.yellow)
            self.ar_table.setItem(row, 7, st_item)

    def load_bills(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        st = self.ap_status_filter.currentText()
        st_filter = None if st == "All Bills" else st

        bills = api_client.get_bills(org_id, status_filter=st_filter)
        self.ap_table.setRowCount(len(bills))

        for row, bill in enumerate(bills):
            b_str = str(bill.get("bill_date", ""))[:10]
            d_str = str(bill.get("due_date", ""))[:10]
            self.ap_table.setItem(row, 0, QTableWidgetItem(bill.get("bill_number", "")))
            self.ap_table.setItem(row, 1, QTableWidgetItem(bill.get("supplier_name", "")))
            self.ap_table.setItem(row, 2, QTableWidgetItem(bill.get("vendor_invoice_ref", "") or "-"))
            self.ap_table.setItem(row, 3, QTableWidgetItem(b_str))
            self.ap_table.setItem(row, 4, QTableWidgetItem(d_str))
            self.ap_table.setItem(row, 5, QTableWidgetItem(f"₹{Decimal(str(bill.get('total_amount', 0))):,.2f}"))
            self.ap_table.setItem(row, 6, QTableWidgetItem(f"₹{Decimal(str(bill.get('paid_amount', 0))):,.2f}"))
            self.ap_table.setItem(row, 7, QTableWidgetItem(f"₹{Decimal(str(bill.get('balance_due', 0))):,.2f}"))
            
            st_item = QTableWidgetItem(bill.get("status", ""))
            if bill.get("status") == "PAID":
                st_item.setForeground(Qt.green)
            elif bill.get("status") == "PARTIALLY_PAID":
                st_item.setForeground(Qt.yellow)
            self.ap_table.setItem(row, 8, st_item)

    def load_financial_reports(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        mode = self.report_selector.currentText()

        if mode == "Trial Balance":
            self.reports_table.setColumnCount(4)
            self.reports_table.setHorizontalHeaderLabels(["Account Code", "Account Name", "Ending Debit", "Ending Credit"])
            tb = api_client.get_trial_balance(org_id)
            rows = tb.get("rows", [])
            self.reports_table.setRowCount(len(rows) + 1)

            for i, r in enumerate(rows):
                self.reports_table.setItem(i, 0, QTableWidgetItem(r.get("account_code", "")))
                self.reports_table.setItem(i, 1, QTableWidgetItem(r.get("account_name", "")))
                deb = Decimal(str(r.get("ending_debit", 0)))
                crd = Decimal(str(r.get("ending_credit", 0)))
                self.reports_table.setItem(i, 2, QTableWidgetItem(f"₹{deb:,.2f}" if deb > 0 else "-"))
                self.reports_table.setItem(i, 3, QTableWidgetItem(f"₹{crd:,.2f}" if crd > 0 else "-"))

            # Total Summary Row
            t_row = len(rows)
            t_deb = Decimal(str(tb.get("total_debits", 0)))
            t_crd = Decimal(str(tb.get("total_credits", 0)))
            self.reports_table.setItem(t_row, 0, QTableWidgetItem("TOTAL"))
            self.reports_table.setItem(t_row, 1, QTableWidgetItem("Sum of Ledger Activity"))
            self.reports_table.setItem(t_row, 2, QTableWidgetItem(f"₹{t_deb:,.2f}"))
            self.reports_table.setItem(t_row, 3, QTableWidgetItem(f"₹{t_crd:,.2f}"))
            
            is_bal = tb.get("is_balanced", False)
            self.report_status_tag.setText("Ledger: Strictly Balanced (DR == CR)" if is_bal else "Unbalanced!")
            self.report_status_tag.setStyleSheet(f"color: {ThemeColors.STATUS_SUCCESS if is_bal else ThemeColors.STATUS_ERROR}; font-weight: 700;")

        elif mode == "Profit & Loss (P&L)":
            self.reports_table.setColumnCount(3)
            self.reports_table.setHorizontalHeaderLabels(["Category", "Section Details", "Amount"])
            pnl = api_client.get_profit_and_loss(org_id)
            
            pnl_rows = [
                ("1. REVENUE", "Total Operating Revenue", pnl.get("revenue", {}).get("total", 0)),
                ("2. COST OF SALES", "Cost of Goods Sold (COGS)", pnl.get("cogs", {}).get("total", 0)),
                ("GROSS PROFIT", "Revenue - COGS", pnl.get("gross_profit", 0)),
                ("3. OPERATING EXPENSES", "Facilities, Payroll, IT & Operations", pnl.get("operating_expenses", {}).get("total", 0)),
                ("NET PROFIT / (LOSS)", "Operating Income", pnl.get("net_profit", 0)),
            ]
            self.reports_table.setRowCount(len(pnl_rows))
            for i, (cat, desc, amt) in enumerate(pnl_rows):
                val = Decimal(str(amt))
                self.reports_table.setItem(i, 0, QTableWidgetItem(cat))
                self.reports_table.setItem(i, 1, QTableWidgetItem(desc))
                amt_item = QTableWidgetItem(f"₹{val:,.2f}")
                if "NET" in cat or "GROSS" in cat:
                    amt_item.setForeground(Qt.green if val >= 0 else Qt.red)
                self.reports_table.setItem(i, 2, amt_item)

            self.report_status_tag.setText("P&L: Up to Date")
            self.report_status_tag.setStyleSheet(f"color: {ThemeColors.STATUS_SUCCESS}; font-weight: 700;")

        elif mode == "Balance Sheet":
            self.reports_table.setColumnCount(3)
            self.reports_table.setHorizontalHeaderLabels(["Category", "Section Details", "Amount"])
            bs = api_client.get_balance_sheet(org_id)

            bs_rows = [
                ("ASSETS", "Cash, Receivables, Inventory, Equipment", bs.get("total_assets", 0)),
                ("LIABILITIES", "Accounts Payable, Sales Tax & GST", bs.get("liabilities", {}).get("total", 0)),
                ("EQUITY", "Share Capital & Retained Earnings", bs.get("equity", {}).get("total", 0)),
                ("CURRENT PERIOD EARNINGS", "Net Income from P&L", bs.get("current_earnings", 0)),
                ("TOTAL LIABILITIES & EQUITY", "Liabilities + Equity + Net Income", bs.get("total_liabilities_and_equity", 0)),
            ]
            self.reports_table.setRowCount(len(bs_rows))
            for i, (cat, desc, amt) in enumerate(bs_rows):
                val = Decimal(str(amt))
                self.reports_table.setItem(i, 0, QTableWidgetItem(cat))
                self.reports_table.setItem(i, 1, QTableWidgetItem(desc))
                self.reports_table.setItem(i, 2, QTableWidgetItem(f"₹{val:,.2f}"))

            is_bal = bs.get("is_balanced", False)
            self.report_status_tag.setText("Accounting Equation: Balanced (Assets == L + E)" if is_bal else "Equation Mismatch!")
            self.report_status_tag.setStyleSheet(f"color: {ThemeColors.STATUS_SUCCESS if is_bal else ThemeColors.STATUS_ERROR}; font-weight: 700;")

    # --- Dialogs and Actions ---
    def reverse_selected_journal(self):
        row = self.journals_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Entry", "Please select a posted journal entry to reverse.")
            return

        entry_num = self.journals_table.item(row, 0).text()
        journals = api_client.get_journals()
        selected = next((j for j in journals if j.get("entry_number") == entry_num), None)
        if not selected:
            return

        if selected.get("status") != "POSTED":
            QMessageBox.warning(self, "Invalid Status", f"Cannot reverse entry with status '{selected.get('status')}'.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Reversal",
            f"Are you sure you want to reverse journal entry {entry_num}?\nAn exact mirror reversal entry will be posted.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            res = api_client.reverse_journal(selected["id"], reason="User initiated reversal")
            if res:
                QMessageBox.information(self, "Reversed", f"Journal reversed successfully. Reversal entry: {res.get('entry_number')}")
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Error", "Failed to reverse journal entry.")

    def open_new_journal_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Post Balanced Journal Entry — Victory Crest ONE")
        dialog.resize(540, 420)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        form = QFormLayout()
        desc_edit = QLineEdit("Manual adjusting entry")
        ref_edit = QLineEdit("ADJ-001")
        form.addRow("Description:", desc_edit)
        form.addRow("Reference:", ref_edit)

        # Line items
        accounts = api_client.get_accounts()
        acc_choices = [f"{a['account_code']} - {a['account_name']}" for a in accounts]

        dr_combo = QComboBox()
        dr_combo.addItems(acc_choices)
        dr_amount = QDoubleSpinBox()
        dr_amount.setMaximum(1000000000.0)
        dr_amount.setValue(10000.0)
        form.addRow("Debit Account:", dr_combo)
        form.addRow("Debit Amount (₹):", dr_amount)

        cr_combo = QComboBox()
        cr_combo.addItems(acc_choices)
        if len(acc_choices) > 1:
            cr_combo.setCurrentIndex(1)
        cr_amount = QDoubleSpinBox()
        cr_amount.setMaximum(1000000000.0)
        cr_amount.setValue(10000.0)
        form.addRow("Credit Account:", cr_combo)
        form.addRow("Credit Amount (₹):", cr_amount)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Post Journal")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            dr_code = dr_combo.currentText().split(" - ")[0]
            cr_code = cr_combo.currentText().split(" - ")[0]
            dr_val = Decimal(str(dr_amount.value()))
            cr_val = Decimal(str(cr_amount.value()))

            if dr_val != cr_val:
                QMessageBox.warning(dialog, "Unbalanced Entry", f"Debits (₹{dr_val}) do not equal Credits (₹{cr_val}).")
                return

            payload = {
                "description": desc_edit.text(),
                "reference": ref_edit.text(),
                "entry_type": "GENERAL",
                "lines": [
                    {"account_code": dr_code, "debit": dr_val, "credit": Decimal("0.00"), "description": desc_edit.text()},
                    {"account_code": cr_code, "debit": Decimal("0.00"), "credit": cr_val, "description": desc_edit.text()},
                ]
            }
            res = api_client.create_journal(payload)
            if res:
                QMessageBox.information(dialog, "Success", f"Posted entry {res.get('entry_number')} successfully!")
                dialog.accept()
                self.refresh_data()
            else:
                QMessageBox.critical(dialog, "Error", "Failed to post journal entry.")

        btn_submit.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_new_account_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Account — Chart of Accounts")
        dialog.resize(450, 320)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        code_edit = QLineEdit()
        code_edit.setPlaceholderText("e.g. 6070")
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g. Legal & Professional Fees")
        
        type_combo = QComboBox()
        type_combo.addItems(["ASSET", "LIABILITY", "EQUITY", "REVENUE", "COGS", "EXPENSE"])
        
        bal_combo = QComboBox()
        bal_combo.addItems(["DEBIT", "CREDIT"])

        desc_edit = QLineEdit()

        form.addRow("Account Code:", code_edit)
        form.addRow("Account Name:", name_edit)
        form.addRow("Account Type:", type_combo)
        form.addRow("Normal Balance:", bal_combo)
        form.addRow("Description:", desc_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Create Account")
        btn_save.setProperty("class", "btn_primary")

        def submit():
            code = code_edit.text().strip()
            name = name_edit.text().strip()
            if not code or not name:
                QMessageBox.warning(dialog, "Required", "Account Code and Name are required.")
                return

            payload = {
                "account_code": code,
                "account_name": name,
                "account_type": type_combo.currentText(),
                "normal_balance": bal_combo.currentText(),
                "description": desc_edit.text()
            }
            res = api_client.create_account(payload)
            if res:
                QMessageBox.information(dialog, "Success", f"Account {code} created successfully.")
                dialog.accept()
                self.refresh_data()
            else:
                QMessageBox.critical(dialog, "Error", "Failed to create account.")

        btn_save.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)
        dialog.exec()

    def open_new_invoice_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Customer Invoice (AR) — Victory Crest ONE")
        dialog.resize(500, 380)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        cust_edit = QLineEdit("Tata Global Technologies Ltd")
        due_date = QDateEdit(QDate.currentDate().addDays(30))
        item_desc = QLineEdit("Executive Suite & Dining Package")
        qty_spin = QDoubleSpinBox()
        qty_spin.setValue(2.0)
        price_spin = QDoubleSpinBox()
        price_spin.setMaximum(10000000.0)
        price_spin.setValue(15000.0)
        tax_spin = QDoubleSpinBox()
        tax_spin.setValue(18.0)  # 18% GST

        form.addRow("Customer Name:", cust_edit)
        form.addRow("Payment Due Date:", due_date)
        form.addRow("Line Description:", item_desc)
        form.addRow("Quantity:", qty_spin)
        form.addRow("Unit Price (₹):", price_spin)
        form.addRow("GST / Tax Rate (%):", tax_spin)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Issue Invoice")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            dt_py = due_date.date().toPython()
            dt_full = datetime(dt_py.year, dt_py.month, dt_py.day, 23, 59, 59)
            payload = {
                "customer_id": "cust_reliance_corp",
                "customer_name": cust_edit.text(),
                "due_date": dt_full.isoformat(),
                "tax_rate_percent": Decimal(str(tax_spin.value())),
                "lines": [
                    {
                        "description": item_desc.text(),
                        "quantity": Decimal(str(qty_spin.value())),
                        "unit_price": Decimal(str(price_spin.value())),
                    }
                ]
            }
            res = api_client.create_invoice(payload)
            if res:
                QMessageBox.information(dialog, "Invoice Issued", f"Invoice {res.get('invoice_number')} issued and GL posted!")
                dialog.accept()
                self.refresh_data()
            else:
                QMessageBox.critical(dialog, "Error", "Failed to create invoice.")

        btn_submit.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)
        dialog.exec()

    def open_record_payment_dialog(self):
        row = self.ar_table.currentRow()
        inv_num = self.ar_table.item(row, 0).text() if row >= 0 else None

        invoices = api_client.get_invoices()
        target = next((i for i in invoices if i.get("invoice_number") == inv_num), None)
        if not target:
            target = next((i for i in invoices if Decimal(str(i.get("balance_due", 0))) > 0), None)

        if not target:
            QMessageBox.information(self, "No Unpaid Invoices", "There are no pending invoices to apply payment to.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Record Payment for {target.get('invoice_number')}")
        dialog.resize(440, 260)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        inv_info = QLabel(f"{target.get('invoice_number')} — Balance Due: ₹{Decimal(str(target.get('balance_due'))):,.2f}")
        inv_info.setStyleSheet("font-weight: 700; color: #58A6FF;")
        form.addRow("Invoice:", inv_info)

        amt_spin = QDoubleSpinBox()
        amt_spin.setMaximum(float(target.get("balance_due")))
        amt_spin.setValue(float(target.get("balance_due")))
        form.addRow("Payment Amount (₹):", amt_spin)

        method_combo = QComboBox()
        method_combo.addItems(["BANK_TRANSFER", "CREDIT_CARD", "CASH", "CHECK"])
        form.addRow("Method:", method_combo)

        ref_edit = QLineEdit("NEFT-REC-8899")
        form.addRow("Reference #:", ref_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_pay = QPushButton("Apply Payment")
        btn_pay.setProperty("class", "btn_primary")

        def submit():
            payload = {
                "invoice_id": target["id"],
                "amount": Decimal(str(amt_spin.value())),
                "payment_method": method_combo.currentText(),
                "reference": ref_edit.text()
            }
            res = api_client.record_customer_payment(payload)
            if res:
                QMessageBox.information(dialog, "Payment Recorded", f"Payment {res.get('payment_number')} recorded successfully!")
                dialog.accept()
                self.refresh_data()
            else:
                QMessageBox.critical(dialog, "Error", "Failed to record payment.")

        btn_pay.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_pay)
        layout.addLayout(btn_row)
        dialog.exec()

    def open_new_bill_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Record Supplier Bill (AP) — Victory Crest ONE")
        dialog.resize(500, 360)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        supp_edit = QLineEdit("Fresh Organic Farms & Produce")
        ref_edit = QLineEdit("FOF-INV-9922")
        due_date = QDateEdit(QDate.currentDate().addDays(30))
        item_desc = QLineEdit("Kitchen Produce & Dairy Supplies")
        amount_spin = QDoubleSpinBox()
        amount_spin.setMaximum(10000000.0)
        amount_spin.setValue(28000.0)

        form.addRow("Supplier Name:", supp_edit)
        form.addRow("Vendor Invoice #:", ref_edit)
        form.addRow("Due Date:", due_date)
        form.addRow("Description:", item_desc)
        form.addRow("Total Amount (₹):", amount_spin)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Record Bill")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            dt_py = due_date.date().toPython()
            dt_full = datetime(dt_py.year, dt_py.month, dt_py.day, 23, 59, 59)
            payload = {
                "supplier_id": "supp_fresh_farms",
                "supplier_name": supp_edit.text(),
                "vendor_invoice_ref": ref_edit.text(),
                "due_date": dt_full.isoformat(),
                "lines": [
                    {
                        "description": item_desc.text(),
                        "quantity": Decimal("1.00"),
                        "unit_price": Decimal(str(amount_spin.value())),
                    }
                ]
            }
            res = api_client.create_bill(payload)
            if res:
                QMessageBox.information(dialog, "Bill Recorded", f"Bill {res.get('bill_number')} recorded and GL posted!")
                dialog.accept()
                self.refresh_data()
            else:
                QMessageBox.critical(dialog, "Error", "Failed to create bill.")

        btn_submit.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)
        dialog.exec()

    def open_pay_bill_dialog(self):
        row = self.ap_table.currentRow()
        bill_num = self.ap_table.item(row, 0).text() if row >= 0 else None

        bills = api_client.get_bills()
        target = next((b for b in bills if b.get("bill_number") == bill_num), None)
        if not target:
            target = next((b for b in bills if Decimal(str(b.get("balance_due", 0))) > 0), None)

        if not target:
            QMessageBox.information(self, "No Unpaid Bills", "There are no pending vendor bills to pay.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Disburse Payment for {target.get('bill_number')}")
        dialog.resize(440, 260)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        b_info = QLabel(f"{target.get('bill_number')} ({target.get('supplier_name')}) — Balance: ₹{Decimal(str(target.get('balance_due'))):,.2f}")
        b_info.setStyleSheet("font-weight: 700; color: #58A6FF;")
        form.addRow("Vendor Bill:", b_info)

        amt_spin = QDoubleSpinBox()
        amt_spin.setMaximum(float(target.get("balance_due")))
        amt_spin.setValue(float(target.get("balance_due")))
        form.addRow("Payment Amount (₹):", amt_spin)

        method_combo = QComboBox()
        method_combo.addItems(["BANK_TRANSFER", "CHECK", "CREDIT_CARD", "ELECTRONIC"])
        form.addRow("Method:", method_combo)

        ref_edit = QLineEdit("BANK-TXN-4411")
        form.addRow("Reference / Cheque #:", ref_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_pay = QPushButton("Disburse Payment")
        btn_pay.setProperty("class", "btn_primary")

        def submit():
            payload = {
                "bill_id": target["id"],
                "amount": Decimal(str(amt_spin.value())),
                "payment_method": method_combo.currentText(),
                "reference": ref_edit.text()
            }
            res = api_client.record_bill_payment(payload)
            if res:
                QMessageBox.information(dialog, "Payment Disbursed", f"Payment {res.get('payment_number')} recorded successfully!")
                dialog.accept()
                self.refresh_data()
            else:
                QMessageBox.critical(dialog, "Error", "Failed to disburse bill payment.")

        btn_pay.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_pay)
        layout.addLayout(btn_row)
        dialog.exec()
