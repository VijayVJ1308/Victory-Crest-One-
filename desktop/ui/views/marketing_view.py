"""Victory Crest One - Marketing Automation Desktop View
Interactive console for multi-channel campaigns, dynamic audience segmentation,
automated customer journeys, creative templates, and conversion attribution ROI.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDoubleSpinBox, QDateEdit, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, QDate

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from shared.calculations import to_decimal


class MarketingView(QWidget):
    """Central Marketing Automation & Lifecycle Journeys Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
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

        title = QLabel("Marketing Automation & Growth")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Multi-channel campaigns, audience segmentation, automated customer journeys, and conversion attribution.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)
        header_row.addWidget(btn_refresh)

        btn_new_segment = QPushButton("👥 New Segment")
        btn_new_segment.setProperty("class", "btn_secondary")
        btn_new_segment.clicked.connect(self.open_new_segment_dialog)
        header_row.addWidget(btn_new_segment)

        btn_new_campaign = QPushButton("➕ New Campaign")
        btn_new_campaign.setProperty("class", "btn_primary")
        btn_new_campaign.clicked.connect(self.open_new_campaign_dialog)
        header_row.addWidget(btn_new_campaign)

        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive KPI Summary Cards
        # -----------------------------------------------------
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_active_campaigns = self.create_summary_card("Active Campaigns", "0", "Running Multi-Channel", ThemeColors.PRIMARY_LIGHT)
        self.kpi_total_spend = self.create_summary_card("Marketing Spend", "₹0.00", "Total Capital Deployed", ThemeColors.STATUS_WARNING)
        self.kpi_attributed_revenue = self.create_summary_card("Attributed Revenue", "₹0.00", "Direct Sales Pipeline & POS", ThemeColors.STATUS_SUCCESS)
        self.kpi_roas = self.create_summary_card("Overall ROAS", "0.00x", "Return on Ad Spend", ThemeColors.ACCENT_PRIMARY)

        kpi_row.addWidget(self.kpi_active_campaigns)
        kpi_row.addWidget(self.kpi_total_spend)
        kpi_row.addWidget(self.kpi_attributed_revenue)
        kpi_row.addWidget(self.kpi_roas)
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

        # Tab 1: Campaigns Console
        tab_campaigns = self.build_campaigns_tab()
        self.tabs.addTab(tab_campaigns, "📣 Multi-Channel Campaigns")

        # Tab 2: Audience Segments
        tab_segments = self.build_segments_tab()
        self.tabs.addTab(tab_segments, "🎯 Audience Segments")

        # Tab 3: Customer Journeys
        tab_journeys = self.build_journeys_tab()
        self.tabs.addTab(tab_journeys, "⚡ Customer Journeys")

        # Tab 4: Creative Templates
        tab_templates = self.build_templates_tab()
        self.tabs.addTab(tab_templates, "📝 Message Templates")

        # Tab 5: Attribution & ROI
        tab_attribution = self.build_attribution_tab()
        self.tabs.addTab(tab_attribution, "📈 Conversion Attribution")

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
        v_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color_accent};")
        layout.addWidget(v_lbl)

        s_lbl = QLabel(subtext)
        s_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        layout.addWidget(s_lbl)
        return card

    # ---------------------------------------------------------
    # TAB 1: Campaigns Console
    # ---------------------------------------------------------
    def build_campaigns_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters & Actions
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.combo_camp_status = QComboBox()
        self.combo_camp_status.addItems(["ALL", "RUNNING", "SCHEDULED", "COMPLETED", "DRAFT", "PAUSED"])
        self.combo_camp_status.currentTextChanged.connect(self.load_campaigns_table)
        ctrl_row.addWidget(QLabel("Status:"))
        ctrl_row.addWidget(self.combo_camp_status)

        self.combo_camp_channel = QComboBox()
        self.combo_camp_channel.addItems(["ALL", "EMAIL", "SMS", "WHATSAPP", "PUSH_NOTIFICATION"])
        self.combo_camp_channel.currentTextChanged.connect(self.load_campaigns_table)
        ctrl_row.addWidget(QLabel("Channel:"))
        ctrl_row.addWidget(self.combo_camp_channel)

        ctrl_row.addStretch()

        btn_launch = QPushButton("🚀 Launch Selected Campaign")
        btn_launch.setProperty("class", "btn_primary")
        btn_launch.clicked.connect(self.launch_selected_campaign)
        ctrl_row.addWidget(btn_launch)

        layout.addLayout(ctrl_row)

        # Campaigns Table
        self.campaigns_table = QTableWidget(0, 11)
        self.campaigns_table.setHorizontalHeaderLabels([
            "Code", "Campaign Name", "Channel", "Status", "Budget", "Spend", "Attributed Revenue",
            "Delivered", "Open Rate", "CTR", "ROAS"
        ])
        self.campaigns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.campaigns_table.verticalHeader().setVisible(False)
        self.campaigns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.campaigns_table.setStyleSheet(f"""
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
        layout.addWidget(self.campaigns_table)
        return container

    # ---------------------------------------------------------
    # TAB 2: Audience Segments
    # ---------------------------------------------------------
    def build_segments_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_lbl = QLabel("Target Audience Segments & Behavioural Filters")
        header_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header_lbl)

        self.segments_table = QTableWidget(0, 5)
        self.segments_table.setHorizontalHeaderLabels([
            "Segment Name", "Description", "Type", "Members Count", "Active"
        ])
        self.segments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.segments_table.verticalHeader().setVisible(False)
        self.segments_table.setStyleSheet(f"""
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
        layout.addWidget(self.segments_table)
        return container

    # ---------------------------------------------------------
    # TAB 3: Customer Journeys
    # ---------------------------------------------------------
    def build_journeys_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_lbl = QLabel("Automated Lifecycle Sequences & Drip Triggers")
        header_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.journey_container = QWidget()
        self.journey_layout = QVBoxLayout(self.journey_container)
        self.journey_layout.setContentsMargins(0, 0, 0, 0)
        self.journey_layout.setSpacing(12)
        scroll.setWidget(self.journey_container)
        layout.addWidget(scroll)

        return container

    # ---------------------------------------------------------
    # TAB 4: Creative Templates
    # ---------------------------------------------------------
    def build_templates_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_lbl = QLabel("Multi-Channel Message Content & Merge Tag Templates")
        header_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header_lbl)

        self.templates_table = QTableWidget(0, 5)
        self.templates_table.setHorizontalHeaderLabels([
            "Template Name", "Channel", "Subject Line", "Merge Variables", "Active"
        ])
        self.templates_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.templates_table.verticalHeader().setVisible(False)
        self.templates_table.setStyleSheet(f"""
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
        layout.addWidget(self.templates_table)
        return container

    # ---------------------------------------------------------
    # TAB 5: Conversion Attribution & ROI
    # ---------------------------------------------------------
    def build_attribution_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_lbl = QLabel("Multi-Touch Revenue Attribution & Campaign ROI Analysis")
        header_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header_lbl)

        self.attrib_table = QTableWidget(0, 5)
        self.attrib_table.setHorizontalHeaderLabels([
            "Campaign Name", "Customer / Account", "Attribution Model", "Attributed Revenue", "Date Attributed"
        ])
        self.attrib_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attrib_table.verticalHeader().setVisible(False)
        self.attrib_table.setStyleSheet(f"""
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
        layout.addWidget(self.attrib_table)
        return container

    # ---------------------------------------------------------
    # Data Refresh & Rendering
    # ---------------------------------------------------------
    def refresh_data(self):
        """Fetch marketing portfolio metrics and populate all tabs."""
        # 1. Metrics & KPIs
        metrics = api_client.get_marketing_metrics()
        self.kpi_active_campaigns.findChild(QLabel, "kpi_value").setText(f"{metrics.get('active_campaigns_count', 0)} Running")
        spend = to_decimal(metrics.get("total_spend", 0))
        self.kpi_total_spend.findChild(QLabel, "kpi_value").setText(f"₹{spend:,.2f}")
        rev = to_decimal(metrics.get("total_attributed_revenue", 0))
        self.kpi_attributed_revenue.findChild(QLabel, "kpi_value").setText(f"₹{rev:,.2f}")
        roas = to_decimal(metrics.get("overall_roas", 0))
        self.kpi_roas.findChild(QLabel, "kpi_value").setText(f"{roas:.2f}x")

        # 2. Campaigns Table
        self.load_campaigns_table()

        # 3. Segments Table
        self.load_segments_table()

        # 4. Customer Journeys
        self.load_journeys_display()

        # 5. Templates Table
        self.load_templates_table()

        # 6. Attributions Table
        self.load_attribution_table()

    def load_campaigns_table(self):
        st_filter = self.combo_camp_status.currentText()
        st = None if st_filter == "ALL" else st_filter

        ch_filter = self.combo_camp_channel.currentText()
        ch = None if ch_filter == "ALL" else ch_filter

        campaigns = api_client.get_marketing_campaigns(status=st, channel=ch)
        self.campaigns_table.setRowCount(len(campaigns))

        for row, c in enumerate(campaigns):
            self.campaigns_table.setItem(row, 0, QTableWidgetItem(c.get("campaign_code", "")))
            self.campaigns_table.setItem(row, 1, QTableWidgetItem(c.get("name", "")))

            # Channel icon
            ch_name = c.get("channel", "EMAIL")
            icon = "📧" if ch_name == "EMAIL" else "💬" if ch_name == "WHATSAPP" else "📱" if ch_name == "SMS" else "📢"
            self.campaigns_table.setItem(row, 2, QTableWidgetItem(f"{icon} {ch_name}"))

            self.campaigns_table.setItem(row, 3, QTableWidgetItem(c.get("status", "")))

            bud = to_decimal(c.get("budget", 0))
            self.campaigns_table.setItem(row, 4, QTableWidgetItem(f"₹{bud:,.2f}"))

            spd = to_decimal(c.get("actual_spend", 0))
            self.campaigns_table.setItem(row, 5, QTableWidgetItem(f"₹{spd:,.2f}"))

            rev = to_decimal(c.get("attributed_revenue", 0))
            self.campaigns_table.setItem(row, 6, QTableWidgetItem(f"₹{rev:,.2f}"))

            deliv = c.get("delivered_count", 0)
            self.campaigns_table.setItem(row, 7, QTableWidgetItem(f"{deliv:,}"))

            op_rate = to_decimal(c.get("open_rate_percent", 0))
            self.campaigns_table.setItem(row, 8, QTableWidgetItem(f"{op_rate:.1f}%"))

            ctr = to_decimal(c.get("ctr_percent", 0))
            self.campaigns_table.setItem(row, 9, QTableWidgetItem(f"{ctr:.1f}%"))

            roas = to_decimal(c.get("roas", 0))
            self.campaigns_table.setItem(row, 10, QTableWidgetItem(f"{roas:.2f}x"))

    def load_segments_table(self):
        segments = api_client.get_audience_segments()
        self.segments_table.setRowCount(len(segments))
        for row, s in enumerate(segments):
            self.segments_table.setItem(row, 0, QTableWidgetItem(s.get("name", "")))
            self.segments_table.setItem(row, 1, QTableWidgetItem(s.get("description", "")))
            self.segments_table.setItem(row, 2, QTableWidgetItem(s.get("segment_type", "")))
            cnt = s.get("member_count", 0)
            self.segments_table.setItem(row, 3, QTableWidgetItem(f"{cnt:,} members"))
            act = "YES" if s.get("is_active") else "NO"
            self.segments_table.setItem(row, 4, QTableWidgetItem(act))

    def load_journeys_display(self):
        # Clear existing cards
        while self.journey_layout.count():
            item = self.journey_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        journeys = api_client.get_customer_journeys()
        for j in journeys:
            card = self.create_journey_card(j)
            self.journey_layout.addWidget(card)
        self.journey_layout.addStretch()

    def create_journey_card(self, j: Dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 14px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # Header
        top_row = QHBoxLayout()
        name_lbl = QLabel(f"⚡ {j.get('name')}")
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        top_row.addWidget(name_lbl)

        status_lbl = QLabel(f"[{j.get('status')}]")
        status_lbl.setStyleSheet(f"font-weight: 700; color: {ThemeColors.STATUS_SUCCESS};")
        top_row.addWidget(status_lbl)
        top_row.addStretch()

        enrolled = j.get("enrolled_count", 0)
        completed = j.get("completed_count", 0)
        stat_lbl = QLabel(f"Enrolled: {enrolled} | Completed: {completed}")
        stat_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        top_row.addWidget(stat_lbl)

        layout.addLayout(top_row)

        desc_lbl = QLabel(j.get("description", ""))
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MUTED};")
        layout.addWidget(desc_lbl)

        trigger_lbl = QLabel(f"Trigger Event: 🎯 {j.get('trigger_event')}")
        trigger_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ThemeColors.PRIMARY_LIGHT};")
        layout.addWidget(trigger_lbl)

        # Steps Row
        steps_row = QHBoxLayout()
        steps_row.setSpacing(6)
        for s in j.get("steps", []):
            step_box = QLabel(f"Step {s.get('step_number')}: {s.get('action_type')}\n(+{s.get('delay_hours')}h)")
            step_box.setStyleSheet(f"""
                background: {ThemeColors.BG_SURFACE};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
                color: {ThemeColors.TEXT_MAIN};
            """)
            steps_row.addWidget(step_box)
            arrow = QLabel("➔")
            arrow.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
            steps_row.addWidget(arrow)

        if steps_row.count() > 0:
            # Remove trailing arrow
            last_item = steps_row.takeAt(steps_row.count() - 1)
            if last_item.widget():
                last_item.widget().deleteLater()

        steps_row.addStretch()
        layout.addLayout(steps_row)
        return card

    def load_templates_table(self):
        templates = api_client.get_campaign_templates()
        self.templates_table.setRowCount(len(templates))
        for row, t in enumerate(templates):
            self.templates_table.setItem(row, 0, QTableWidgetItem(t.get("name", "")))
            self.templates_table.setItem(row, 1, QTableWidgetItem(t.get("channel", "")))
            self.templates_table.setItem(row, 2, QTableWidgetItem(t.get("subject") or "—"))
            self.templates_table.setItem(row, 3, QTableWidgetItem(t.get("merge_tags", "")))
            act = "YES" if t.get("is_active") else "NO"
            self.templates_table.setItem(row, 4, QTableWidgetItem(act))

    def load_attribution_table(self):
        attributions = api_client.get_marketing_attributions()
        self.attrib_table.setRowCount(len(attributions))
        for row, a in enumerate(attributions):
            self.attrib_table.setItem(row, 0, QTableWidgetItem(a.get("campaign_name", "")))
            self.attrib_table.setItem(row, 1, QTableWidgetItem(a.get("customer_name", "")))
            self.attrib_table.setItem(row, 2, QTableWidgetItem(a.get("attribution_model", "")))
            rev = to_decimal(a.get("attributed_revenue", 0))
            self.attrib_table.setItem(row, 3, QTableWidgetItem(f"₹{rev:,.2f}"))
            dt = str(a.get("attributed_at", ""))[:19]
            self.attrib_table.setItem(row, 4, QTableWidgetItem(dt))

    # ---------------------------------------------------------
    # Dialogs & Actions
    # ---------------------------------------------------------
    def launch_selected_campaign(self):
        curr_row = self.campaigns_table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Select Campaign", "Please click on a campaign row to launch.")
            return

        code = self.campaigns_table.item(curr_row, 0).text()
        campaigns = api_client.get_marketing_campaigns()
        selected = next((c for c in campaigns if c.get("campaign_code") == code), None)

        if selected:
            res = api_client.launch_marketing_campaign(selected["id"])
            QMessageBox.information(
                self,
                "Campaign Launched",
                f"Dispatched {res.get('messages_dispatched', 0)} messages!\n{res.get('message', '')}"
            )
            self.refresh_data()

    def open_new_campaign_dialog(self):
        dialog = NewCampaignDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            payload = dialog.get_payload()
            api_client.create_marketing_campaign(payload)
            QMessageBox.information(self, "Campaign Created", f"Marketing campaign '{payload['name']}' created successfully.")
            self.refresh_data()

    def open_new_segment_dialog(self):
        dialog = NewSegmentDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            payload = dialog.get_payload()
            api_client.create_audience_segment(payload)
            QMessageBox.information(self, "Segment Created", f"Audience segment '{payload['name']}' defined successfully.")
            self.refresh_data()


# =============================================================
# MODALS & DIALOGS
# =============================================================
class NewCampaignDialog(QDialog):
    """Modal to author a new multi-channel marketing campaign."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Marketing Campaign — Victory Crest ONE")
        self.resize(480, 420)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("New Growth & Marketing Campaign")
        header.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Q4 Executive Retreat Outreach")
        form.addRow("Campaign Name:", self.input_name)

        self.combo_channel = QComboBox()
        self.combo_channel.addItems(["EMAIL", "SMS", "WHATSAPP", "PUSH_NOTIFICATION", "SOCIAL_MEDIA"])
        form.addRow("Channel:", self.combo_channel)

        self.spin_budget = QDoubleSpinBox()
        self.spin_budget.setRange(0, 10000000)
        self.spin_budget.setDecimals(2)
        self.spin_budget.setValue(100000.0)
        self.spin_budget.setPrefix("₹ ")
        form.addRow("Campaign Budget:", self.spin_budget)

        self.combo_segment = QComboBox()
        segments = api_client.get_audience_segments()
        for s in segments:
            self.combo_segment.addItem(s["name"], s["id"])
        form.addRow("Target Segment:", self.combo_segment)

        self.input_notes = QTextEdit()
        self.input_notes.setPlaceholderText("Campaign objectives, promotional offers, and conversion targets")
        self.input_notes.setMaximumHeight(80)
        form.addRow("Notes:", self.input_notes)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("Create Campaign")
        btn_submit.setProperty("class", "btn_primary")
        btn_submit.clicked.connect(self.validate_and_accept)
        btn_row.addWidget(btn_submit)

        layout.addLayout(btn_row)

    def validate_and_accept(self):
        if not self.input_name.text().strip():
            QMessageBox.warning(self, "Required Field", "Please enter a campaign name.")
            return
        self.accept()

    def get_payload(self) -> Dict[str, Any]:
        return {
            "name": self.input_name.text().strip(),
            "channel": self.combo_channel.currentText(),
            "budget": self.spin_budget.value(),
            "segment_id": self.combo_segment.currentData(),
            "notes": self.input_notes.toPlainText().strip() or None
        }


class NewSegmentDialog(QDialog):
    """Modal to define an audience segment."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Define Audience Segment — Victory Crest ONE")
        self.resize(460, 340)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("New Audience Segment")
        header.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Wedding & Banqueting Prospects")
        form.addRow("Segment Name:", self.input_name)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["DYNAMIC", "STATIC"])
        form.addRow("Segment Type:", self.combo_type)

        self.input_desc = QTextEdit()
        self.input_desc.setPlaceholderText("Demographic and behavioural characteristics")
        self.input_desc.setMaximumHeight(80)
        form.addRow("Description:", self.input_desc)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_submit = QPushButton("Save Segment")
        btn_submit.setProperty("class", "btn_primary")
        btn_submit.clicked.connect(self.validate_and_accept)
        btn_row.addWidget(btn_submit)

        layout.addLayout(btn_row)

    def validate_and_accept(self):
        if not self.input_name.text().strip():
            QMessageBox.warning(self, "Required Field", "Please enter a segment name.")
            return
        self.accept()

    def get_payload(self) -> Dict[str, Any]:
        return {
            "name": self.input_name.text().strip(),
            "segment_type": self.combo_type.currentText(),
            "description": self.input_desc.toPlainText().strip() or None
        }
