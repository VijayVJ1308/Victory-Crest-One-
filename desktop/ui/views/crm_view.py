"""Victory Crest One - Sales CRM & Revenue Pipeline Desktop View
Interactive console for Opportunity Deals, Lead Conversion, Commercial Quotations,
Pipeline Stage Progression, and Sales Forecasting.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDoubleSpinBox, QDateEdit, QSpinBox
)
from PySide6.QtCore import Qt, QDate

from desktop.core.theme import ThemeColors
from desktop.core.session import session_manager
from desktop.services.api_client import api_client
from shared.calculations import to_decimal


class SalesCrmView(QWidget):
    """Central Sales & CRM console."""

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

        title = QLabel("Sales CRM & Revenue Pipeline")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Lead qualification, deal pipeline stages, commercial quotations, and revenue forecast.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)
        header_row.addWidget(btn_refresh)

        btn_new_deal = QPushButton("➕ New Deal")
        btn_new_deal.setProperty("class", "btn_primary")
        btn_new_deal.clicked.connect(self.open_new_deal_dialog)
        header_row.addWidget(btn_new_deal)

        btn_new_lead = QPushButton("➕ Capture Lead")
        btn_new_lead.setProperty("class", "btn_secondary")
        btn_new_lead.clicked.connect(self.open_new_lead_dialog)
        header_row.addWidget(btn_new_lead)

        main_layout.addLayout(header_row)

        # 2. Executive KPI Summary Cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_pipeline = self.create_summary_card("Active Pipeline", "₹0.00", "Total Unclosed Opportunities", ThemeColors.PRIMARY_LIGHT)
        self.kpi_weighted = self.create_summary_card("Weighted Forecast", "₹0.00", "Probability Weighted Value", ThemeColors.STATUS_SUCCESS)
        self.kpi_deals_count = self.create_summary_card("Deals In Progress", "0", "Open Pipeline Deals", ThemeColors.STATUS_WARNING)
        self.kpi_win_rate = self.create_summary_card("Win Rate", "0%", "Closed Won / Total Closed", ThemeColors.ACCENT_PRIMARY)

        kpi_row.addWidget(self.kpi_pipeline)
        kpi_row.addWidget(self.kpi_weighted)
        kpi_row.addWidget(self.kpi_deals_count)
        kpi_row.addWidget(self.kpi_win_rate)
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
                border-bottom: 2px solid {ThemeColors.PRIMARY_LIGHT};
            }}
        """)

        self.deals_tab = self.build_deals_tab()
        self.leads_tab = self.build_leads_tab()
        self.quotes_tab = self.build_quotes_tab()
        self.activities_tab = self.build_activities_tab()

        self.tabs.addTab(self.deals_tab, "💼 Opportunity Deals")
        self.tabs.addTab(self.leads_tab, "🎯 Leads & Qualification")
        self.tabs.addTab(self.quotes_tab, "📄 Commercial Quotations")
        self.tabs.addTab(self.activities_tab, "📞 Sales Activities")

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

    # --- 1. Deals Tab ---
    def build_deals_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        lbl = QLabel("Stage:")
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-size: 12px; font-weight: 600;")
        bar.addWidget(lbl)

        self.deal_stage_filter = QComboBox()
        self.deal_stage_filter.addItems(["All Stages", "QUALIFICATION", "NEEDS_ANALYSIS", "PROPOSAL", "NEGOTIATION", "CLOSED_WON", "CLOSED_LOST"])
        self.deal_stage_filter.currentIndexChanged.connect(self.load_deals)
        bar.addWidget(self.deal_stage_filter)
        bar.addStretch()

        btn_advance = QPushButton("➡️ Advance Stage")
        btn_advance.setProperty("class", "btn_secondary")
        btn_advance.clicked.connect(self.advance_selected_deal)
        bar.addWidget(btn_advance)

        btn_won = QPushButton("🏆 Mark Won")
        btn_won.setProperty("class", "btn_secondary")
        btn_won.clicked.connect(lambda: self.set_selected_deal_status("CLOSED_WON"))
        bar.addWidget(btn_won)

        btn_lost = QPushButton("❌ Mark Lost")
        btn_lost.setProperty("class", "btn_secondary")
        btn_lost.clicked.connect(lambda: self.set_selected_deal_status("CLOSED_LOST"))
        bar.addWidget(btn_lost)

        layout.addLayout(bar)

        self.deals_table = QTableWidget()
        self.deals_table.setColumnCount(8)
        self.deals_table.setHorizontalHeaderLabels([
            "Deal #", "Deal Name", "Customer", "Stage", "Amount", "Probability", "Weighted Val", "Expected Close"
        ])
        self.deals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.deals_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.deals_table.setStyleSheet(self._table_style())
        layout.addWidget(self.deals_table)

        return widget

    # --- 2. Leads Tab ---
    def build_leads_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        lbl = QLabel("Status:")
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-size: 12px; font-weight: 600;")
        bar.addWidget(lbl)

        self.lead_status_filter = QComboBox()
        self.lead_status_filter.addItems(["All Leads", "NEW", "CONTACTED", "QUALIFIED", "UNQUALIFIED", "CONVERTED"])
        self.lead_status_filter.currentIndexChanged.connect(self.load_leads)
        bar.addWidget(self.lead_status_filter)
        bar.addStretch()

        btn_convert = QPushButton("🔄 Convert to Deal & Customer")
        btn_convert.setProperty("class", "btn_primary")
        btn_convert.clicked.connect(self.convert_selected_lead)
        bar.addWidget(btn_convert)

        layout.addLayout(bar)

        self.leads_table = QTableWidget()
        self.leads_table.setColumnCount(8)
        self.leads_table.setHorizontalHeaderLabels([
            "Name", "Company", "Email", "Phone", "Source", "Score", "Estimated Budget", "Status"
        ])
        self.leads_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.leads_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.leads_table.setStyleSheet(self._table_style())
        layout.addWidget(self.leads_table)

        return widget

    # --- 3. Quotations Tab ---
    def build_quotes_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        bar.addStretch()

        btn_new_q = QPushButton("➕ Create Quote")
        btn_new_q.setProperty("class", "btn_primary")
        btn_new_q.clicked.connect(self.open_new_quote_dialog)
        bar.addWidget(btn_new_q)

        btn_inv = QPushButton("📄 Convert to Invoice (Finance AR)")
        btn_inv.setProperty("class", "btn_secondary")
        btn_inv.clicked.connect(self.convert_selected_quote_to_invoice)
        bar.addWidget(btn_inv)

        layout.addLayout(bar)

        self.quotes_table = QTableWidget()
        self.quotes_table.setColumnCount(7)
        self.quotes_table.setHorizontalHeaderLabels([
            "Quote #", "Customer", "Valid Until", "Subtotal", "Tax", "Total Amount", "Status"
        ])
        self.quotes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.quotes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.quotes_table.setStyleSheet(self._table_style())
        layout.addWidget(self.quotes_table)

        return widget

    # --- 4. Activities Tab ---
    def build_activities_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        bar.addStretch()
        btn_log = QPushButton("📝 Log Activity")
        btn_log.setProperty("class", "btn_secondary")
        btn_log.clicked.connect(self.open_log_activity_dialog)
        bar.addWidget(btn_log)
        layout.addLayout(bar)

        self.activities_table = QTableWidget()
        self.activities_table.setColumnCount(5)
        self.activities_table.setHorizontalHeaderLabels(["Type", "Subject", "Details", "Rep", "Date"])
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.activities_table.setStyleSheet(self._table_style())
        layout.addWidget(self.activities_table)

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
                background-color: {ThemeColors.PRIMARY};
                color: #FFFFFF;
            }}
        """

    # --- Data Loading ---
    def refresh_data(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        self.load_kpis(org_id)
        self.load_deals()
        self.load_leads()
        self.load_quotes()
        self.load_activities()

    def load_kpis(self, org_id: Optional[str]):
        try:
            m = api_client.get_pipeline_metrics(org_id)
            pipe_val = Decimal(str(m.get("total_active_pipeline_value", 0)))
            weight_val = Decimal(str(m.get("weighted_forecast_value", 0)))
            deals_count = m.get("open_deals_count", 0)
            win_rate = Decimal(str(m.get("win_rate_percentage", 0)))

            self.kpi_pipeline.findChild(QLabel, "value_label").setText(f"₹{pipe_val:,.2f}")
            self.kpi_weighted.findChild(QLabel, "value_label").setText(f"₹{weight_val:,.2f}")
            self.kpi_deals_count.findChild(QLabel, "value_label").setText(str(deals_count))
            self.kpi_win_rate.findChild(QLabel, "value_label").setText(f"{win_rate:.1f}%")
        except Exception:
            pass

    def load_deals(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        st = self.deal_stage_filter.currentText()
        st_filter = None if st == "All Stages" else st

        deals = api_client.get_deals(org_id, stage=st_filter)
        self.deals_table.setRowCount(len(deals))

        for row, d in enumerate(deals):
            close_str = str(d.get("expected_close_date", ""))[:10]
            amt = Decimal(str(d.get("amount", 0)))
            w_amt = Decimal(str(d.get("weighted_amount", 0)))
            prob = d.get("probability_percent", 0)

            self.deals_table.setItem(row, 0, QTableWidgetItem(d.get("deal_number", "")))
            self.deals_table.setItem(row, 1, QTableWidgetItem(d.get("deal_name", "")))
            self.deals_table.setItem(row, 2, QTableWidgetItem(d.get("customer_name", "")))
            
            stage_item = QTableWidgetItem(d.get("stage", ""))
            if d.get("stage") == "CLOSED_WON":
                stage_item.setForeground(Qt.green)
            elif d.get("stage") == "CLOSED_LOST":
                stage_item.setForeground(Qt.red)
            self.deals_table.setItem(row, 3, stage_item)

            self.deals_table.setItem(row, 4, QTableWidgetItem(f"₹{amt:,.2f}"))
            self.deals_table.setItem(row, 5, QTableWidgetItem(f"{prob}%"))
            self.deals_table.setItem(row, 6, QTableWidgetItem(f"₹{w_amt:,.2f}"))
            self.deals_table.setItem(row, 7, QTableWidgetItem(close_str))

    def load_leads(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        st = self.lead_status_filter.currentText()
        st_filter = None if st == "All Leads" else st

        leads = api_client.get_leads(org_id, status_filter=st_filter)
        self.leads_table.setRowCount(len(leads))

        for row, lead in enumerate(leads):
            name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
            budget = Decimal(str(lead.get("estimated_budget", 0)))
            self.leads_table.setItem(row, 0, QTableWidgetItem(name))
            self.leads_table.setItem(row, 1, QTableWidgetItem(lead.get("company_name", "") or "-"))
            self.leads_table.setItem(row, 2, QTableWidgetItem(lead.get("email", "")))
            self.leads_table.setItem(row, 3, QTableWidgetItem(lead.get("phone", "") or "-"))
            self.leads_table.setItem(row, 4, QTableWidgetItem(lead.get("lead_source", "")))
            self.leads_table.setItem(row, 5, QTableWidgetItem(f"{lead.get('lead_score', 0)}/100"))
            self.leads_table.setItem(row, 6, QTableWidgetItem(f"₹{budget:,.2f}"))

            st_item = QTableWidgetItem(lead.get("status", ""))
            if lead.get("status") == "QUALIFIED":
                st_item.setForeground(Qt.cyan)
            elif lead.get("status") == "CONVERTED":
                st_item.setForeground(Qt.green)
            self.leads_table.setItem(row, 7, st_item)

    def load_quotes(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        quotes = api_client.get_quotes(org_id)
        self.quotes_table.setRowCount(len(quotes))

        for row, q in enumerate(quotes):
            val_str = str(q.get("valid_until", ""))[:10]
            sub = Decimal(str(q.get("subtotal", 0)))
            tax = Decimal(str(q.get("tax_amount", 0)))
            tot = Decimal(str(q.get("total_amount", 0)))

            self.quotes_table.setItem(row, 0, QTableWidgetItem(q.get("quote_number", "")))
            self.quotes_table.setItem(row, 1, QTableWidgetItem(q.get("customer_name", "")))
            self.quotes_table.setItem(row, 2, QTableWidgetItem(val_str))
            self.quotes_table.setItem(row, 3, QTableWidgetItem(f"₹{sub:,.2f}"))
            self.quotes_table.setItem(row, 4, QTableWidgetItem(f"₹{tax:,.2f}"))
            self.quotes_table.setItem(row, 5, QTableWidgetItem(f"₹{tot:,.2f}"))

            st_item = QTableWidgetItem(q.get("status", ""))
            if q.get("status") == "ACCEPTED":
                st_item.setForeground(Qt.green)
            elif q.get("status") == "SENT":
                st_item.setForeground(Qt.yellow)
            self.quotes_table.setItem(row, 6, st_item)

    def load_activities(self):
        org_id = session_manager.active_organization.get("id") if session_manager.active_organization else None
        activities = api_client.get_activities(org_id)
        self.activities_table.setRowCount(len(activities))

        for row, a in enumerate(activities):
            dt_str = str(a.get("created_at", ""))[:16].replace("T", " ")
            self.activities_table.setItem(row, 0, QTableWidgetItem(a.get("activity_type", "")))
            self.activities_table.setItem(row, 1, QTableWidgetItem(a.get("subject", "")))
            self.activities_table.setItem(row, 2, QTableWidgetItem(a.get("details", "") or "-"))
            self.activities_table.setItem(row, 3, QTableWidgetItem(a.get("assigned_rep_name", "") or "Rep"))
            self.activities_table.setItem(row, 4, QTableWidgetItem(dt_str))

    # --- Actions and Dialogs ---
    def advance_selected_deal(self):
        row = self.deals_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Deal", "Please select a deal in the table to advance.")
            return

        deal_num = self.deals_table.item(row, 0).text()
        deals = api_client.get_deals()
        target = next((d for d in deals if d.get("deal_number") == deal_num), None)
        if not target:
            return

        stages_flow = ["QUALIFICATION", "NEEDS_ANALYSIS", "PROPOSAL", "NEGOTIATION", "CLOSED_WON"]
        cur = target.get("stage", "QUALIFICATION")
        if cur in ("CLOSED_WON", "CLOSED_LOST"):
            QMessageBox.information(self, "Closed Deal", f"Deal is already in terminal stage {cur}.")
            return

        try:
            cur_idx = stages_flow.index(cur)
            next_stage = stages_flow[cur_idx + 1]
        except (ValueError, IndexError):
            next_stage = "PROPOSAL"

        res = api_client.update_deal_stage(target["id"], next_stage, notes="Stage advanced via CRM pipeline board.")
        if res:
            QMessageBox.information(self, "Stage Advanced", f"Deal {deal_num} advanced to stage {next_stage}!")
            self.refresh_data()

    def set_selected_deal_status(self, stage: str):
        row = self.deals_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Deal", "Please select a deal in the table first.")
            return

        deal_num = self.deals_table.item(row, 0).text()
        deals = api_client.get_deals()
        target = next((d for d in deals if d.get("deal_number") == deal_num), None)
        if not target:
            return

        res = api_client.update_deal_stage(target["id"], stage, notes=f"Marked as {stage}.")
        if res:
            QMessageBox.information(self, "Updated", f"Deal {deal_num} marked as {stage}!")
            self.refresh_data()

    def convert_selected_lead(self):
        row = self.leads_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Lead", "Please select a lead in the table to convert.")
            return

        leads = api_client.get_leads()
        if row >= len(leads):
            return
        target = leads[row]

        if target.get("status") == "CONVERTED":
            QMessageBox.warning(self, "Already Converted", "This lead has already been converted.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Convert Lead: {target.get('first_name')} {target.get('last_name')}")
        dialog.resize(460, 260)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        deal_name_edit = QLineEdit(f"{target.get('company_name') or target.get('first_name')} Opportunity")
        amt_spin = QDoubleSpinBox()
        amt_spin.setMaximum(100000000.0)
        amt_spin.setValue(float(target.get("estimated_budget", 500000.0)))

        form.addRow("Opportunity Name:", deal_name_edit)
        form.addRow("Estimated Amount (₹):", amt_spin)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_conv = QPushButton("Confirm Conversion")
        btn_conv.setProperty("class", "btn_primary")

        def submit():
            payload = {
                "deal_name": deal_name_edit.text(),
                "estimated_amount": Decimal(str(amt_spin.value()))
            }
            res = api_client.convert_lead(target["id"], payload)
            if res:
                QMessageBox.information(
                    dialog,
                    "Conversion Successful",
                    f"Lead converted!\nCustomer Code: {res.get('customer_code')}\nDeal Number: {res.get('deal_number')}"
                )
                dialog.accept()
                self.refresh_data()

        btn_conv.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_conv)
        layout.addLayout(btn_row)
        dialog.exec()

    def convert_selected_quote_to_invoice(self):
        row = self.quotes_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Quote", "Please select a quotation in the table to convert.")
            return

        q_num = self.quotes_table.item(row, 0).text()
        quotes = api_client.get_quotes()
        target = next((q for q in quotes if q.get("quote_number") == q_num), None)
        if not target:
            return

        if target.get("converted_invoice_id"):
            QMessageBox.warning(self, "Already Converted", f"Quote has already been converted to an invoice.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Conversion",
            f"Convert Quotation {q_num} to a Finance AR Customer Invoice?\nThis will post a balanced General Ledger journal entry automatically.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            res = api_client.convert_quote_to_invoice(target["id"])
            if res:
                QMessageBox.information(
                    self,
                    "Invoice Created",
                    f"Quotation converted successfully!\nGenerated AR Invoice: {res.get('invoice_number')}"
                )
                self.refresh_data()

    def open_new_deal_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Opportunity Deal — Victory Crest ONE")
        dialog.resize(480, 340)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        name_edit = QLineEdit("Corporate Retreat & Banqueting")
        cust_name_edit = QLineEdit("Tata Global Technologies Ltd")
        stage_combo = QComboBox()
        stage_combo.addItems(["QUALIFICATION", "NEEDS_ANALYSIS", "PROPOSAL", "NEGOTIATION"])
        amt_spin = QDoubleSpinBox()
        amt_spin.setMaximum(1000000000.0)
        amt_spin.setValue(750000.0)
        close_date = QDateEdit(QDate.currentDate().addDays(45))
        rep_edit = QLineEdit("Vikram Sharma")

        form.addRow("Deal Name:", name_edit)
        form.addRow("Customer Name:", cust_name_edit)
        form.addRow("Initial Stage:", stage_combo)
        form.addRow("Estimated Value (₹):", amt_spin)
        form.addRow("Target Close Date:", close_date)
        form.addRow("Assigned Rep:", rep_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Create Deal")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            dt_py = close_date.date().toPython()
            dt_full = datetime(dt_py.year, dt_py.month, dt_py.day, 23, 59, 59)
            payload = {
                "deal_name": name_edit.text(),
                "customer_id": "cust_reliance_corp",
                "customer_name": cust_name_edit.text(),
                "stage": stage_combo.currentText(),
                "amount": Decimal(str(amt_spin.value())),
                "expected_close_date": dt_full.isoformat(),
                "assigned_rep_name": rep_edit.text()
            }
            res = api_client.create_deal(payload)
            if res:
                QMessageBox.information(dialog, "Deal Created", f"Deal {res.get('deal_number')} created successfully!")
                dialog.accept()
                self.refresh_data()

        btn_submit.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)
        dialog.exec()

    def open_new_lead_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Capture Prospective Lead — Victory Crest ONE")
        dialog.resize(460, 360)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        fn_edit = QLineEdit()
        ln_edit = QLineEdit()
        comp_edit = QLineEdit()
        email_edit = QLineEdit()
        phone_edit = QLineEdit()
        src_combo = QComboBox()
        src_combo.addItems(["WEBSITE", "REFERRAL", "TRADE_SHOW", "COLD_OUTREACH", "PARTNER"])
        score_spin = QSpinBox()
        score_spin.setValue(65)
        budget_spin = QDoubleSpinBox()
        budget_spin.setMaximum(100000000.0)
        budget_spin.setValue(350000.0)

        form.addRow("First Name:", fn_edit)
        form.addRow("Last Name:", ln_edit)
        form.addRow("Company Name:", comp_edit)
        form.addRow("Email Address:", email_edit)
        form.addRow("Phone Number:", phone_edit)
        form.addRow("Lead Source:", src_combo)
        form.addRow("Lead Score (0-100):", score_spin)
        form.addRow("Est. Budget (₹):", budget_spin)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Save Lead")
        btn_save.setProperty("class", "btn_primary")

        def submit():
            if not fn_edit.text().strip() or not email_edit.text().strip():
                QMessageBox.warning(dialog, "Required", "First Name and Email are required.")
                return

            payload = {
                "first_name": fn_edit.text().strip(),
                "last_name": ln_edit.text().strip() or "Prospect",
                "company_name": comp_edit.text().strip(),
                "email": email_edit.text().strip(),
                "phone": phone_edit.text().strip(),
                "lead_source": src_combo.currentText(),
                "lead_score": score_spin.value(),
                "estimated_budget": Decimal(str(budget_spin.value()))
            }
            res = api_client.create_lead(payload)
            if res:
                QMessageBox.information(dialog, "Lead Saved", "Lead captured successfully!")
                dialog.accept()
                self.refresh_data()

        btn_save.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)
        dialog.exec()

    def open_new_quote_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Generate Commercial Quotation — Victory Crest ONE")
        dialog.resize(500, 360)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        cust_edit = QLineEdit("Tata Global Technologies Ltd")
        valid_date = QDateEdit(QDate.currentDate().addDays(30))
        item_edit = QLineEdit("Resort Villas Accommodation & Banqueting")
        qty_spin = QDoubleSpinBox()
        qty_spin.setValue(1.0)
        price_spin = QDoubleSpinBox()
        price_spin.setMaximum(100000000.0)
        price_spin.setValue(850000.0)
        tax_spin = QDoubleSpinBox()
        tax_spin.setValue(18.0)

        form.addRow("Customer Name:", cust_edit)
        form.addRow("Valid Until:", valid_date)
        form.addRow("Item Description:", item_edit)
        form.addRow("Quantity:", qty_spin)
        form.addRow("Unit Price (₹):", price_spin)
        form.addRow("Tax Rate (%):", tax_spin)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_submit = QPushButton("Generate Quote")
        btn_submit.setProperty("class", "btn_primary")

        def submit():
            dt_py = valid_date.date().toPython()
            dt_full = datetime(dt_py.year, dt_py.month, dt_py.day, 23, 59, 59)
            payload = {
                "customer_id": "cust_reliance_corp",
                "customer_name": cust_edit.text(),
                "valid_until": dt_full.isoformat(),
                "tax_rate_percent": Decimal(str(tax_spin.value())),
                "lines": [
                    {
                        "description": item_edit.text(),
                        "quantity": Decimal(str(qty_spin.value())),
                        "unit_price": Decimal(str(price_spin.value())),
                    }
                ]
            }
            res = api_client.create_quote(payload)
            if res:
                QMessageBox.information(dialog, "Quote Created", f"Quotation {res.get('quote_number')} generated!")
                dialog.accept()
                self.refresh_data()

        btn_submit.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)
        dialog.exec()

    def open_log_activity_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Log Sales Interaction — Victory Crest ONE")
        dialog.resize(440, 280)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        type_combo = QComboBox()
        type_combo.addItems(["CALL", "MEETING", "EMAIL", "NOTE", "TASK"])
        subj_edit = QLineEdit("Client strategy sync")
        det_edit = QLineEdit("Reviewed proposals and budget allocations.")
        rep_edit = QLineEdit("Vikram Sharma")

        form.addRow("Activity Type:", type_combo)
        form.addRow("Subject:", subj_edit)
        form.addRow("Notes / Details:", det_edit)
        form.addRow("Sales Rep:", rep_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Log Activity")
        btn_save.setProperty("class", "btn_primary")

        def submit():
            payload = {
                "entity_type": "DEAL",
                "entity_id": "deal_cognizant_conf",
                "activity_type": type_combo.currentText(),
                "subject": subj_edit.text(),
                "details": det_edit.text(),
                "assigned_rep_name": rep_edit.text()
            }
            res = api_client.log_activity(payload)
            if res:
                QMessageBox.information(dialog, "Activity Logged", "Interaction logged in sales timeline!")
                dialog.accept()
                self.refresh_data()

        btn_save.clicked.connect(submit)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)
        dialog.exec()
