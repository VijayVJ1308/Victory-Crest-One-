"""Victory Crest One - Business Intelligence & Executive Analytics View
Executive Dashboards, Gross Operating Profit (GOP), EBITDA, Cross-Property Benchmarks,
Departmental Contribution P&L, and Document Export Engine (Excel, PDF, CSV).
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QFileDialog, QTextEdit, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from shared.calculations import (
    to_decimal,
    calculate_financial_ratios,
    calculate_portfolio_kpis,
    calculate_department_contributions,
    calculate_linear_forecast
)


class BusinessIntelligenceView(QWidget):
    """Central Executive Business Intelligence & Analytics Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_dashboard: Optional[Dict[str, Any]] = None
        self.cached_reports: List[Dict[str, Any]] = []

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # -----------------------------------------------------
        # 1. Executive Header Section
        # -----------------------------------------------------
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("Business Intelligence & Executive Analytics")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Cross-property operating telemetry, Gross Operating Profit (GOP), EBITDA, departmental P&L, and high-fidelity PDF/Excel document exports.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_quick_pdf = QPushButton("📄 Quick PDF Dossier")
        btn_quick_pdf.setProperty("class", "btn_secondary")
        btn_quick_pdf.clicked.connect(lambda: self.quick_export("PDF"))

        btn_quick_excel = QPushButton("📑 Quick Excel Workbook")
        btn_quick_excel.setProperty("class", "btn_secondary")
        btn_quick_excel.clicked.connect(lambda: self.quick_export("EXCEL"))

        btn_compile = QPushButton("⚡ Compile Custom Report")
        btn_compile.setProperty("class", "btn_primary")
        btn_compile.clicked.connect(self.open_compile_report_dialog)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_quick_pdf)
        header_row.addWidget(btn_quick_excel)
        header_row.addWidget(btn_compile)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_total_rev = self.create_metric_card("CONSOLIDATED REVENUE", "₹0.00", "Enterprise YTD Run-Rate", "#10B981")
        self.card_gop = self.create_metric_card("GROSS OPERATING PROFIT", "₹0.00", "GOP Margin 0.0%", "#3B82F6")
        self.card_ebitda = self.create_metric_card("OPERATING EBITDA", "₹0.00", "Core Operating Earnings", "#8B5CF6")
        self.card_blended_occ = self.create_metric_card("BLENDED OCCUPANCY", "0.0%", "Portfolio ADR ₹0.00", "#F59E0B")
        self.card_net_margin = self.create_metric_card("NET PROFIT MARGIN", "0.0%", "After Tax & Overheads", "#06B6D4")

        cards_row.addWidget(self.card_total_rev)
        cards_row.addWidget(self.card_gop)
        cards_row.addWidget(self.card_ebitda)
        cards_row.addWidget(self.card_blended_occ)
        cards_row.addWidget(self.card_net_margin)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Main Analytical Tabs
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

        # Tab 1: Executive Portfolio Overview
        self.tab_overview = QWidget()
        self.setup_overview_tab()
        self.tab_widget.addTab(self.tab_overview, "📊 Executive Portfolio Overview")

        # Tab 2: Cross-Property Benchmarks
        self.tab_properties = QWidget()
        self.setup_properties_tab()
        self.tab_widget.addTab(self.tab_properties, "🏨 Cross-Property Benchmarks")

        # Tab 3: Departmental P&L & Cost Centers
        self.tab_departments = QWidget()
        self.setup_departments_tab()
        self.tab_widget.addTab(self.tab_departments, "📑 Departmental P&L")

        # Tab 4: Financial Ratios & Liquidity Health
        self.tab_ratios = QWidget()
        self.setup_ratios_tab()
        self.tab_widget.addTab(self.tab_ratios, "📈 Financial Ratios & Liquidity")

        # Tab 5: Document Export & Snapshot Dossier
        self.tab_exports = QWidget()
        self.setup_exports_tab()
        self.tab_widget.addTab(self.tab_exports, "🖨️ Document Artifacts & Exports")

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
        card.value_label = lbl_val

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        card.sub_label = lbl_sub

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)
        return card

    # =========================================================================
    # Tab 1: Executive Portfolio Overview & 12-Month Trend
    # =========================================================================
    def setup_overview_tab(self):
        layout = QVBoxLayout(self.tab_overview)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Forecast Callout Box
        self.forecast_box = QFrame()
        self.forecast_box.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        fb_layout = QVBoxLayout(self.forecast_box)
        fb_layout.setContentsMargins(4, 4, 4, 4)
        fb_layout.setSpacing(4)

        self.lbl_forecast_title = QLabel("🔮 3-Month Predictive Revenue Trajectory (Linear Regression Engine)")
        self.lbl_forecast_title.setStyleSheet(f"font-weight: 700; color: {ThemeColors.PRIMARY}; font-size: 13px;")
        self.lbl_forecast_desc = QLabel("Loading predictive telemetry...")
        self.lbl_forecast_desc.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MAIN}; line-height: 1.5;")
        fb_layout.addWidget(self.lbl_forecast_title)
        fb_layout.addWidget(self.lbl_forecast_desc)
        layout.addWidget(self.forecast_box)

        lbl_tbl = QLabel("12-Month Performance Run-Rate & Monthly Operating Income:")
        lbl_tbl.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")
        layout.addWidget(lbl_tbl)

        self.table_monthly = QTableWidget()
        self.table_monthly.setColumnCount(6)
        self.table_monthly.setHorizontalHeaderLabels([
            "Month Period", "Gross Revenue (₹)", "Operating Expenses (₹)",
            "Net Operating Profit (₹)", "Net Margin %", "Room Occupancy %"
        ])
        self.table_monthly.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_monthly.verticalHeader().setVisible(False)
        self.table_monthly.setAlternatingRowColors(True)
        layout.addWidget(self.table_monthly)

    def populate_monthly_table(self, trend: List[Dict[str, Any]]):
        self.table_monthly.setRowCount(0)
        hist_revenues = []

        for row, pt in enumerate(trend):
            self.table_monthly.insertRow(row)

            m_str = pt.get("month", "")
            item_m = QTableWidgetItem(m_str)
            item_m.setTextAlignment(Qt.AlignCenter)

            rev = to_decimal(pt.get("revenue", 0))
            hist_revenues.append(rev)
            item_rev = QTableWidgetItem(f"₹{rev:,.2f}")
            item_rev.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            exp = to_decimal(pt.get("expenses", 0))
            item_exp = QTableWidgetItem(f"₹{exp:,.2f}")
            item_exp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            net = to_decimal(pt.get("net_profit", 0))
            item_net = QTableWidgetItem(f"₹{net:,.2f}")
            item_net.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            mgn = ((net / rev) * Decimal("100.00")) if rev > Decimal("0") else Decimal("0")
            item_mgn = QTableWidgetItem(f"{mgn:.1f}%")
            item_mgn.setTextAlignment(Qt.AlignCenter)
            if mgn >= Decimal("30.0"):
                item_mgn.setForeground(Qt.darkGreen)
            else:
                item_mgn.setForeground(Qt.blue)

            occ = to_decimal(pt.get("occupancy_percent", 0))
            item_occ = QTableWidgetItem(f"{occ:.1f}%")
            item_occ.setTextAlignment(Qt.AlignCenter)

            self.table_monthly.setItem(row, 0, item_m)
            self.table_monthly.setItem(row, 1, item_rev)
            self.table_monthly.setItem(row, 2, item_exp)
            self.table_monthly.setItem(row, 3, item_net)
            self.table_monthly.setItem(row, 4, item_mgn)
            self.table_monthly.setItem(row, 5, item_occ)

        # Update forecast banner
        fc = calculate_linear_forecast(hist_revenues, periods_ahead=3)
        preds = fc["forecast_values"]
        f_text = (
            f"• Historical Monthly Mean: <b>₹{fc['historical_mean']:,.2f}</b> | Trajectory Growth: <b>+{fc['growth_rate_percent']:.1f}%</b><br>"
            f"• Projected Month +1: <b style='color: #10B981;'>₹{preds[0]:,.2f}</b> &nbsp;|&nbsp; "
            f"Month +2: <b style='color: #10B981;'>₹{preds[1]:,.2f}</b> &nbsp;|&nbsp; "
            f"Month +3: <b style='color: #10B981;'>₹{preds[2]:,.2f}</b>"
        )
        self.lbl_forecast_desc.setText(f_text)

    # =========================================================================
    # Tab 2: Cross-Property Benchmarks
    # =========================================================================
    def setup_properties_tab(self):
        layout = QVBoxLayout(self.tab_properties)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Multi-Property Operational & Profitability Benchmark Matrix:")
        lbl.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")
        layout.addWidget(lbl)

        self.table_properties = QTableWidget()
        self.table_properties.setColumnCount(12)
        self.table_properties.setHorizontalHeaderLabels([
            "Code", "Property Name", "Total Revenue", "GOP (₹)", "GOP %",
            "Rooms Rev", "Dining Rev", "Retail Rev", "Service Rev",
            "Occupancy %", "RevPAR", "Staff"
        ])
        self.table_properties.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_properties.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_properties.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_properties.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.table_properties.horizontalHeader().setSectionResizeMode(11, QHeaderView.ResizeToContents)
        self.table_properties.verticalHeader().setVisible(False)
        self.table_properties.setAlternatingRowColors(True)
        layout.addWidget(self.table_properties)

    def populate_properties_table(self, properties: List[Dict[str, Any]]):
        self.table_properties.setRowCount(0)
        for row, p in enumerate(properties):
            self.table_properties.insertRow(row)

            item_code = QTableWidgetItem(p.get("property_code", ""))
            item_code.setTextAlignment(Qt.AlignCenter)

            item_name = QTableWidgetItem(p.get("property_name", ""))

            rev = to_decimal(p.get("total_revenue", 0))
            item_rev = QTableWidgetItem(f"₹{rev:,.2f}")
            item_rev.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            gop = to_decimal(p.get("gop", 0))
            item_gop = QTableWidgetItem(f"₹{gop:,.2f}")
            item_gop.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            gop_m = to_decimal(p.get("gop_margin_percent", 0))
            item_gopm = QTableWidgetItem(f"{gop_m:.1f}%")
            item_gopm.setTextAlignment(Qt.AlignCenter)
            if gop_m >= Decimal("40.0"):
                item_gopm.setForeground(Qt.darkGreen)
            else:
                item_gopm.setForeground(Qt.blue)

            rr = to_decimal(p.get("rooms_revenue", 0))
            item_rr = QTableWidgetItem(f"₹{rr:,.2f}")
            item_rr.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            dr = to_decimal(p.get("dining_revenue", 0))
            item_dr = QTableWidgetItem(f"₹{dr:,.2f}")
            item_dr.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            rt = to_decimal(p.get("retail_revenue", 0))
            item_rt = QTableWidgetItem(f"₹{rt:,.2f}")
            item_rt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            sr = to_decimal(p.get("service_revenue", 0))
            item_sr = QTableWidgetItem(f"₹{sr:,.2f}")
            item_sr.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            occ = to_decimal(p.get("occupancy_percent", 0))
            item_occ = QTableWidgetItem(f"{occ:.1f}%")
            item_occ.setTextAlignment(Qt.AlignCenter)

            revpar = to_decimal(p.get("revpar", 0))
            item_revpar = QTableWidgetItem(f"₹{revpar:,.2f}")
            item_revpar.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            staff = p.get("staff_headcount", 0)
            item_staff = QTableWidgetItem(str(staff))
            item_staff.setTextAlignment(Qt.AlignCenter)

            self.table_properties.setItem(row, 0, item_code)
            self.table_properties.setItem(row, 1, item_name)
            self.table_properties.setItem(row, 2, item_rev)
            self.table_properties.setItem(row, 3, item_gop)
            self.table_properties.setItem(row, 4, item_gopm)
            self.table_properties.setItem(row, 5, item_rr)
            self.table_properties.setItem(row, 6, item_dr)
            self.table_properties.setItem(row, 7, item_rt)
            self.table_properties.setItem(row, 8, item_sr)
            self.table_properties.setItem(row, 9, item_occ)
            self.table_properties.setItem(row, 10, item_revpar)
            self.table_properties.setItem(row, 11, item_staff)

    # =========================================================================
    # Tab 3: Departmental P&L & Cost Centers
    # =========================================================================
    def setup_departments_tab(self):
        layout = QVBoxLayout(self.tab_departments)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Operational Division Margin Breakdown & Revenue Attribution:")
        lbl.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")
        layout.addWidget(lbl)

        self.table_departments = QTableWidget()
        self.table_departments.setColumnCount(6)
        self.table_departments.setHorizontalHeaderLabels([
            "Operational Business Division", "Gross Revenue (₹)",
            "Allocated Expenses (₹)", "Net Operating Contribution (₹)",
            "Operating Margin %", "Revenue Share %"
        ])
        self.table_departments.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_departments.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_departments.verticalHeader().setVisible(False)
        self.table_departments.setAlternatingRowColors(True)
        layout.addWidget(self.table_departments)

    def populate_departments_table(self, depts: List[Dict[str, Any]]):
        self.table_departments.setRowCount(0)
        for row, d in enumerate(depts):
            self.table_departments.insertRow(row)

            item_d = QTableWidgetItem(d.get("department", ""))
            rev = to_decimal(d.get("revenue", 0))
            item_rev = QTableWidgetItem(f"₹{rev:,.2f}")
            item_rev.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            exp = to_decimal(d.get("expenses", 0))
            item_exp = QTableWidgetItem(f"₹{exp:,.2f}")
            item_exp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            net = to_decimal(d.get("net_profit", 0))
            item_net = QTableWidgetItem(f"₹{net:,.2f}")
            item_net.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            mgn = to_decimal(d.get("profit_margin_percent", 0))
            item_mgn = QTableWidgetItem(f"{mgn:.1f}%")
            item_mgn.setTextAlignment(Qt.AlignCenter)
            if mgn >= Decimal("40.0"):
                item_mgn.setForeground(Qt.darkGreen)
            else:
                item_mgn.setForeground(Qt.blue)

            share = to_decimal(d.get("revenue_share_percent", 0))
            item_share = QTableWidgetItem(f"{share:.1f}%")
            item_share.setTextAlignment(Qt.AlignCenter)

            self.table_departments.setItem(row, 0, item_d)
            self.table_departments.setItem(row, 1, item_rev)
            self.table_departments.setItem(row, 2, item_exp)
            self.table_departments.setItem(row, 3, item_net)
            self.table_departments.setItem(row, 4, item_mgn)
            self.table_departments.setItem(row, 5, item_share)

    # =========================================================================
    # Tab 4: Financial Ratios & Liquidity Health
    # =========================================================================
    def setup_ratios_tab(self):
        layout = QVBoxLayout(self.tab_ratios)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(4, 4, 4, 4)
        c_layout.setSpacing(14)

        # 1. Profitability Group
        gb_prof = QGroupBox("Core Operating & Profitability Ratios")
        p_layout = QFormLayout(gb_prof)
        self.lbl_r_gross = QLabel("0.0%")
        self.lbl_r_gop = QLabel("0.0%")
        self.lbl_r_ebit = QLabel("0.0%")
        self.lbl_r_ebitda = QLabel("0.0%")
        self.lbl_r_net = QLabel("0.0%")
        p_layout.addRow("Gross Profit Margin (Revenue - COGS):", self.lbl_r_gross)
        p_layout.addRow("Gross Operating Profit (GOP Margin):", self.lbl_r_gop)
        p_layout.addRow("Operating Income (EBIT Margin):", self.lbl_r_ebit)
        p_layout.addRow("EBITDA Margin:", self.lbl_r_ebitda)
        p_layout.addRow("Bottom-Line Net Margin:", self.lbl_r_net)
        c_layout.addWidget(gb_prof)

        # 2. Return on Capital Group
        gb_ret = QGroupBox("Capital Return & Efficiency Ratios")
        r_layout = QFormLayout(gb_ret)
        self.lbl_r_roa = QLabel("0.0%")
        self.lbl_r_roe = QLabel("0.0%")
        r_layout.addRow("Return on Assets (ROA):", self.lbl_r_roa)
        r_layout.addRow("Return on Equity (ROE):", self.lbl_r_roe)
        c_layout.addWidget(gb_ret)

        # 3. Liquidity & Solvency Group
        gb_liq = QGroupBox("Working Capital & Balance Sheet Liquidity")
        l_layout = QFormLayout(gb_liq)
        self.lbl_r_current = QLabel("0.00x")
        self.lbl_r_cash = QLabel("₹0.00")
        self.lbl_r_ar = QLabel("₹0.00")
        self.lbl_r_ap = QLabel("₹0.00")
        l_layout.addRow("Current Ratio (Assets / Liabilities):", self.lbl_r_current)
        l_layout.addRow("Liquid Bank & Cash Balances (1010):", self.lbl_r_cash)
        l_layout.addRow("Accounts Receivable (1020):", self.lbl_r_ar)
        l_layout.addRow("Accounts Payable (2010):", self.lbl_r_ap)
        c_layout.addWidget(gb_liq)

        c_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def populate_ratios(self, r: Dict[str, Any], t: Dict[str, Any]):
        self.lbl_r_gross.setText(f"<b>{to_decimal(r.get('gross_margin_percent', 0)):.1f}%</b> (Gross Profit: ₹{to_decimal(r.get('gross_profit', 0)):,.2f})")
        self.lbl_r_gop.setText(f"<b>{to_decimal(r.get('gop_margin_percent', 0)):.1f}%</b> (GOP: ₹{to_decimal(r.get('gop', 0)):,.2f})")
        self.lbl_r_ebit.setText(f"<b>{to_decimal(r.get('operating_margin_percent', 0)):.1f}%</b> (EBIT: ₹{to_decimal(r.get('ebit', 0)):,.2f})")
        self.lbl_r_ebitda.setText(f"<b>{to_decimal(r.get('ebitda_margin_percent', 0)):.1f}%</b> (EBITDA: ₹{to_decimal(r.get('ebitda', 0)):,.2f})")
        self.lbl_r_net.setText(f"<b style='color: #10B981;'>{to_decimal(r.get('net_margin_percent', 0)):.1f}%</b> (Net Income: ₹{to_decimal(r.get('net_income', 0)):,.2f})")

        self.lbl_r_roa.setText(f"<b>{to_decimal(r.get('roa_percent', 0)):.1f}%</b> (Asset Utilization)")
        self.lbl_r_roe.setText(f"<b>{to_decimal(r.get('roe_percent', 0)):.1f}%</b> (Equity Yield)")

        self.lbl_r_current.setText(f"<b>{to_decimal(r.get('current_ratio', 0)):.2f}x</b> (Healthy Liquidity > 1.50x)")
        self.lbl_r_cash.setText(f"₹{to_decimal(t.get('cash_balance', 0)):,.2f}")
        self.lbl_r_ar.setText(f"₹{to_decimal(t.get('accounts_receivable', 0)):,.2f}")
        self.lbl_r_ap.setText(f"₹{to_decimal(t.get('accounts_payable', 0)):,.2f}")

    # =========================================================================
    # Tab 5: Document Export & Snapshot Dossier
    # =========================================================================
    def setup_exports_tab(self):
        layout = QVBoxLayout(self.tab_exports)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Export Action Bar
        act_card = QFrame()
        act_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        ac_layout = QHBoxLayout(act_card)
        ac_layout.setSpacing(12)

        lbl_prompt = QLabel("Export High-Fidelity Management Reports:")
        lbl_prompt.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")

        btn_pdf = QPushButton("📄 Generate PDF Dossier")
        btn_pdf.setStyleSheet("background-color: #EF4444; color: white; font-weight: 700; padding: 6px 14px;")
        btn_pdf.clicked.connect(lambda: self.quick_export("PDF"))

        btn_xls = QPushButton("📑 Generate Excel Workbook")
        btn_xls.setStyleSheet("background-color: #10B981; color: white; font-weight: 700; padding: 6px 14px;")
        btn_xls.clicked.connect(lambda: self.quick_export("EXCEL"))

        btn_csv = QPushButton("📊 Export Raw CSV Data")
        btn_csv.setProperty("class", "btn_secondary")
        btn_csv.clicked.connect(lambda: self.quick_export("CSV"))

        ac_layout.addWidget(lbl_prompt)
        ac_layout.addStretch()
        ac_layout.addWidget(btn_pdf)
        ac_layout.addWidget(btn_xls)
        ac_layout.addWidget(btn_csv)
        layout.addWidget(act_card)

        lbl_hist = QLabel("Previously Generated Report Snapshots & Artifact Archives:")
        lbl_hist.setStyleSheet(f"font-weight: 700; color: {ThemeColors.TEXT_MAIN}; font-size: 13px;")
        layout.addWidget(lbl_hist)

        self.table_reports = QTableWidget()
        self.table_reports.setColumnCount(6)
        self.table_reports.setHorizontalHeaderLabels([
            "Report Title", "Report Scope", "Period", "Format", "Compiled Date", "Action"
        ])
        self.table_reports.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_reports.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_reports.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_reports.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_reports.verticalHeader().setVisible(False)
        self.table_reports.setAlternatingRowColors(True)
        layout.addWidget(self.table_reports)

    def populate_reports_table(self, reports: List[Dict[str, Any]]):
        self.table_reports.setRowCount(0)
        for row, r in enumerate(reports):
            self.table_reports.insertRow(row)

            item_title = QTableWidgetItem(r.get("title", ""))
            item_type = QTableWidgetItem(r.get("report_type", ""))
            item_period = QTableWidgetItem(r.get("period", ""))
            item_period.setTextAlignment(Qt.AlignCenter)

            fmt = r.get("format", "").upper()
            item_fmt = QTableWidgetItem(fmt)
            item_fmt.setTextAlignment(Qt.AlignCenter)
            if fmt == "PDF":
                item_fmt.setForeground(Qt.darkRed)
            elif fmt in ("EXCEL", "XLSX"):
                item_fmt.setForeground(Qt.darkGreen)
            else:
                item_fmt.setForeground(Qt.blue)

            c_date = str(r.get("created_at", ""))[:19]
            item_date = QTableWidgetItem(c_date)
            item_date.setTextAlignment(Qt.AlignCenter)

            btn_dl = QPushButton("⬇️ Download")
            btn_dl.setStyleSheet("padding: 4px 10px; font-size: 11px;")
            rep_id = r.get("id", "")
            btn_dl.clicked.connect(lambda _, rid=rep_id: self.download_report_artifact(rid))

            self.table_reports.setItem(row, 0, item_title)
            self.table_reports.setItem(row, 1, item_type)
            self.table_reports.setItem(row, 2, item_period)
            self.table_reports.setItem(row, 3, item_fmt)
            self.table_reports.setItem(row, 4, item_date)
            self.table_reports.setCellWidget(row, 5, btn_dl)

    # =========================================================================
    # Data Refresh & API Integration
    # =========================================================================
    def refresh_data(self):
        try:
            self.cached_dashboard = api_client.get_bi_dashboard()
            self.cached_reports = api_client.get_bi_report_history()
        except Exception:
            pass

        if not self.cached_dashboard:
            return

        dash = self.cached_dashboard
        t = dash.get("telemetry", {})
        r = dash.get("financial_ratios", {})

        # 1. Update metric cards
        self.card_total_rev.value_label.setText(f"₹{to_decimal(t.get('total_revenue', 0)):,.2f}")
        self.card_gop.value_label.setText(f"₹{to_decimal(t.get('gop', 0)):,.2f}")
        self.card_gop.sub_label.setText(f"GOP Margin {to_decimal(t.get('gop_margin_percent', 0)):.1f}%")

        self.card_ebitda.value_label.setText(f"₹{to_decimal(t.get('ebitda', 0)):,.2f}")
        self.card_ebitda.sub_label.setText(f"EBITDA Margin {to_decimal(t.get('ebitda_margin_percent', 0)):.1f}%")

        self.card_blended_occ.value_label.setText(f"{to_decimal(t.get('blended_occupancy_percent', 0)):.1f}%")
        self.card_blended_occ.sub_label.setText(f"Portfolio ADR ₹{to_decimal(t.get('average_adr', 0)):,.2f}")

        self.card_net_margin.value_label.setText(f"{to_decimal(t.get('net_margin_percent', 0)):.1f}%")
        self.card_net_margin.sub_label.setText(f"Net Profit ₹{to_decimal(t.get('net_income', 0)):,.2f}")

        # 2. Update tabs
        self.populate_monthly_table(dash.get("monthly_trend", []))
        self.populate_properties_table(dash.get("properties_benchmark", []))
        self.populate_departments_table(dash.get("department_contributions", []))
        self.populate_ratios(r, t)
        self.populate_reports_table(self.cached_reports)

    # =========================================================================
    # Report Actions & Document Downloads
    # =========================================================================
    def quick_export(self, fmt: str):
        req_data = {
            "report_type": "EXECUTIVE_SUMMARY",
            "period": "YEAR_TO_DATE",
            "format": fmt,
            "notes": f"One-click quick {fmt} export from desktop BI view."
        }
        try:
            meta = api_client.generate_bi_report(req_data)
            rep_id = meta.get("id")
            self.download_report_artifact(rep_id)
            self.refresh_data()
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))

    def open_compile_report_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Compile Executive Analytical Report")
        dialog.setMinimumWidth(450)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        cb_type = QComboBox()
        cb_type.addItems([
            "EXECUTIVE_SUMMARY",
            "FINANCIAL_PERFORMANCE",
            "DEPARTMENTAL_P_AND_L",
            "OCCUPANCY_AND_REVPAR",
            "SALES_PIPELINE",
            "MANUFACTURING_EFFICIENCY",
            "PROJECT_PROFITABILITY"
        ])

        cb_period = QComboBox()
        cb_period.addItems(["YEAR_TO_DATE", "QUARTERLY", "MONTHLY", "WEEKLY"])

        cb_fmt = QComboBox()
        cb_fmt.addItems(["PDF", "EXCEL", "CSV", "JSON"])

        txt_notes = QTextEdit()
        txt_notes.setMaximumHeight(60)
        txt_notes.setPlaceholderText("Optional management notes / compilation memo...")

        form.addRow("Report Scope *:", cb_type)
        form.addRow("Time Period:", cb_period)
        form.addRow("Artifact Format *:", cb_fmt)
        form.addRow("Executive Notes:", txt_notes)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        btn_compile = QPushButton("🚀 Compile & Download")
        btn_compile.setProperty("class", "btn_primary")

        def compile_it():
            req_data = {
                "report_type": cb_type.currentText(),
                "period": cb_period.currentText(),
                "format": cb_fmt.currentText(),
                "notes": txt_notes.toPlainText().strip()
            }
            try:
                meta = api_client.generate_bi_report(req_data)
                dialog.accept()
                self.download_report_artifact(meta.get("id"))
                self.refresh_data()
            except Exception as e:
                QMessageBox.warning(dialog, "Compilation Error", str(e))

        btn_compile.clicked.connect(compile_it)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_compile)
        layout.addLayout(btn_row)

        dialog.exec()

    def download_report_artifact(self, report_id: str):
        res = api_client.download_bi_report(report_id)
        if not res:
            QMessageBox.warning(self, "Download Error", f"Report artifact '{report_id}' could not be retrieved.")
            return

        content, _, default_filename = res

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Executive Report Artifact",
            default_filename,
            "All Files (*.*)"
        )
        if save_path:
            try:
                with open(save_path, "wb") as f:
                    f.write(content)
                QMessageBox.information(
                    self,
                    "Report Saved",
                    f"Report successfully compiled and saved to:\n{save_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Write Error", f"Could not write file: {e}")
