"""Victory Crest One - AI Business Assistant View
Permission-aware executive inquiry, multi-domain data synthesis,
chat history with rich metric cards, and interactive prompt suggestions.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QTabWidget, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QTextEdit, QGroupBox, QScrollArea, QSplitter,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from desktop.core.session import session_manager


class AiAssistantView(QWidget):
    """Conversational AI Business Assistant Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_threads: List[Dict[str, Any]] = []
        self.active_thread_id: Optional[str] = None
        self.cached_telemetry: Dict[str, Any] = {}

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(14)

        # -----------------------------------------------------
        # 1. Executive Header
        # -----------------------------------------------------
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("AI Business Assistant")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Role-based natural language executive inquiry, multi-domain telemetry synthesis, and permission-aware data masking.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setProperty("class", "btn_secondary")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_reset = QPushButton("🗑️ Reset Chat")
        btn_reset.setProperty("class", "btn_secondary")
        btn_reset.clicked.connect(self.reset_conversations)

        header_row.addWidget(btn_refresh)
        header_row.addWidget(btn_reset)
        main_layout.addLayout(header_row)

        # -----------------------------------------------------
        # 2. Executive Metric Cards
        # -----------------------------------------------------
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.card_queries = self.create_metric_card("QUERIES RESOLVED", "0", "Multi-Domain Telemetry", "#10B981")
        self.card_latency = self.create_metric_card("AVERAGE LATENCY", "0.0 ms", "Sub-Second In-Memory Engine", "#3B82F6")
        self.card_safety = self.create_metric_card("PERMISSION COMPLIANCE", "100.0%", "RBAC Masking Active", "#8B5CF6")
        self.card_threads = self.create_metric_card("ACTIVE THREADS", "0", "Conversational Sessions", "#F59E0B")

        cards_row.addWidget(self.card_queries)
        cards_row.addWidget(self.card_latency)
        cards_row.addWidget(self.card_safety)
        cards_row.addWidget(self.card_threads)
        main_layout.addLayout(cards_row)

        # -----------------------------------------------------
        # 3. Splitter: Left Sidebar (Threads + Suggestions), Right (Chat Area)
        # -----------------------------------------------------
        splitter = QSplitter(Qt.Horizontal)

        # Left Column
        left_panel = QFrame()
        left_panel.setStyleSheet(f"background-color: {ThemeColors.BG_SURFACE}; border-radius: 8px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        # New Thread Button
        btn_new_thread = QPushButton("➕ New Conversation")
        btn_new_thread.setProperty("class", "btn_primary")
        btn_new_thread.clicked.connect(self.start_new_thread)
        left_layout.addWidget(btn_new_thread)

        lbl_threads = QLabel("Inquiry Threads:")
        lbl_threads.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ThemeColors.TEXT_DIM}; letter-spacing: 0.5px;")
        left_layout.addWidget(lbl_threads)

        self.thread_list = QListWidget()
        self.thread_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                color: {ThemeColors.TEXT_MAIN};
                font-size: 12px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                border-bottom: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {ThemeColors.PRIMARY};
                color: #FFFFFF;
            }}
        """)
        self.thread_list.itemClicked.connect(self.on_thread_selected)
        left_layout.addWidget(self.thread_list, 1)

        # Sample Prompts Group
        lbl_prompts = QLabel("Sample Queries (Click to Ask):")
        lbl_prompts.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ThemeColors.TEXT_DIM}; letter-spacing: 0.5px;")
        left_layout.addWidget(lbl_prompts)

        sample_prompts = [
            ("🏨 Room Occupancy & ADR", "What is our current hotel room occupancy rate and ADR?"),
            ("💰 EBITDA & Cash Reserves", "Summarize our quarterly EBITDA, GOP, and liquid cash balance."),
            ("💼 Sales Pipeline & Deals", "What is our current sales revenue and pipeline forecast?"),
            ("📦 Low Warehouse Stock", "Are there any low warehouse stock alerts or reorders?"),
            ("📋 PSA Project Delivery", "How are the professional services project milestones progressing?"),
            ("🛠️ Service Tickets & SLAs", "Check open customer service support tickets and SLA breaches.")
        ]

        for label, text in sample_prompts:
            btn_prompt = QPushButton(label)
            btn_prompt.setProperty("class", "btn_secondary")
            btn_prompt.setStyleSheet("text-align: left; font-size: 11px; padding: 6px 10px;")
            btn_prompt.clicked.connect(lambda ch, q=text: self.send_prompt(q))
            left_layout.addWidget(btn_prompt)

        splitter.addWidget(left_panel)

        # Right Column (Chat Area)
        right_panel = QFrame()
        right_panel.setStyleSheet(f"background-color: {ThemeColors.BG_CARD}; border-radius: 8px; border: 1px solid {ThemeColors.BORDER_DEFAULT};")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        # Chat Scroll Area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background: transparent; border: none;")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(8, 8, 8, 8)
        self.chat_layout.setSpacing(14)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        right_layout.addWidget(self.chat_scroll, 1)

        # Bottom Input Controls
        input_container = QFrame()
        input_container.setStyleSheet(f"background-color: {ThemeColors.BG_SURFACE}; border-radius: 8px; padding: 8px;")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        # Role switcher bar
        role_bar = QHBoxLayout()
        lbl_role = QLabel("Active Operator Role:")
        lbl_role.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MUTED};")
        role_bar.addWidget(lbl_role)

        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "General Manager",
            "System Administrator",
            "Finance Manager",
            "Sales Manager",
            "POS Cashier",
            "Receptionist",
            "Inventory Manager"
        ])
        self.role_combo.setStyleSheet("font-size: 12px; min-width: 180px;")
        role_bar.addWidget(self.role_combo)

        role_bar.addStretch()
        self.status_pill = QLabel("🟢 AI Model Ready")
        self.status_pill.setStyleSheet(f"color: {ThemeColors.STATUS_ACTIVE}; font-size: 11px; font-weight: 600;")
        role_bar.addWidget(self.status_pill)
        input_layout.addLayout(role_bar)

        # Text Input Row
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Ask about revenue, room occupancy, cash reserves, project delivery, inventory deficits...")
        self.prompt_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ThemeColors.BG_INPUT};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 6px;
                color: {ThemeColors.TEXT_MAIN};
                font-size: 13px;
                padding: 10px 14px;
            }}
        """)
        self.prompt_input.returnPressed.connect(self.on_send_clicked)
        input_row.addWidget(self.prompt_input, 1)

        btn_send = QPushButton("Send 🚀")
        btn_send.setProperty("class", "btn_primary")
        btn_send.setFixedHeight(38)
        btn_send.clicked.connect(self.on_send_clicked)
        input_row.addWidget(btn_send)

        input_layout.addLayout(input_row)
        right_layout.addWidget(input_container)

        splitter.addWidget(right_panel)
        splitter.setSizes([260, 680])
        main_layout.addWidget(splitter, 1)

    def create_metric_card(self, title: str, value: str, subtext: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_CARD};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 14px 16px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ThemeColors.TEXT_DIM}; letter-spacing: 0.5px;")

        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {accent_color};")

        lbl_sub = QLabel(subtext)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)
        card.lbl_val = lbl_val
        card.lbl_sub = lbl_sub
        return card

    def start_new_thread(self):
        self.active_thread_id = None
        self.clear_chat_widgets()
        # Add greeting
        self.add_message_bubble(
            "assistant",
            "### 🤖 Victory Crest ONE Executive Business Assistant\n\n"
            "I am ready to synthesize real-time data across all 16 business modules. "
            "Ask about portfolio revenue, hotel occupancy, cash reserves, open service SLAs, or project delivery.",
            followups=[
                "What is our current hotel room occupancy and ADR?",
                "Summarize our quarterly EBITDA, GOP, and cash balance.",
                "Are there any low warehouse stock alerts or reorders?"
            ]
        )

    def on_thread_selected(self, item: QListWidgetItem):
        t_id = item.data(Qt.UserRole)
        if t_id:
            self.load_thread(t_id)

    def load_thread(self, thread_id: str):
        self.active_thread_id = thread_id
        self.clear_chat_widgets()
        messages = api_client.get_ai_thread_messages(thread_id)

        for m in messages:
            role = m.get("role", "assistant")
            content = m.get("content", "")
            data = m.get("structured_data")
            self.add_message_bubble(role, content, structured_data=data)

        self.scroll_to_bottom()

    def clear_chat_widgets(self):
        while self.chat_layout.count() > 1:
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def add_message_bubble(
        self,
        role: str,
        content: str,
        structured_data: Optional[Dict[str, Any]] = None,
        followups: Optional[List[str]] = None
    ):
        bubble = QFrame()
        is_user = (role == "user")

        bg_color = "#1E293B" if is_user else ThemeColors.BG_SURFACE
        border_color = ThemeColors.PRIMARY if is_user else ThemeColors.BORDER_LIGHT

        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 12px 16px;
            }}
        """)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        bubble_layout.setSpacing(8)

        # Header with role avatar
        header_text = "👤 You" if is_user else "🤖 Victory Crest ONE AI"
        header_color = "#60A5FA" if is_user else "#34D399"
        lbl_header = QLabel(header_text)
        lbl_header.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {header_color};")
        bubble_layout.addWidget(lbl_header)

        # Content text (rendered as markdown-styled HTML)
        html_content = content.replace("\n", "<br>").replace("### ", "<b>").replace("**", "<b>")
        lbl_content = QLabel()
        lbl_content.setText(content)
        lbl_content.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MAIN}; line-height: 1.4;")
        lbl_content.setWordWrap(True)
        lbl_content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble_layout.addWidget(lbl_content)

        # Embedded metric cards if present
        if structured_data and "metric_cards" in structured_data:
            cards_box = QHBoxLayout()
            cards_box.setSpacing(8)
            for mc in structured_data["metric_cards"][:4]:
                c_frame = QFrame()
                c_frame.setStyleSheet(f"background-color: {ThemeColors.BG_CARD}; border: 1px solid {ThemeColors.BORDER_LIGHT}; border-radius: 6px; padding: 6px 10px;")
                c_layout = QVBoxLayout(c_frame)
                c_layout.setContentsMargins(0, 0, 0, 0)
                c_layout.setSpacing(2)
                l1 = QLabel(mc.get("label", ""))
                l1.setStyleSheet(f"font-size: 10px; color: {ThemeColors.TEXT_MUTED}; font-weight: 600;")
                l2 = QLabel(mc.get("value", ""))
                l2.setStyleSheet(f"font-size: 14px; color: {ThemeColors.TEXT_MAIN}; font-weight: 700;")
                c_layout.addWidget(l1)
                c_layout.addWidget(l2)
                cards_box.addWidget(c_frame)
            bubble_layout.addLayout(cards_box)

        # Embedded table if present
        if structured_data and "table_headers" in structured_data and "table_rows" in structured_data:
            headers = structured_data["table_headers"]
            rows = structured_data["table_rows"]
            tbl = QTableWidget()
            tbl.setColumnCount(len(headers))
            tbl.setHorizontalHeaderLabels(headers)
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tbl.setRowCount(len(rows))
            for r_idx, row in enumerate(rows):
                for c_idx, val in enumerate(row):
                    tbl.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))
            tbl.setMaximumHeight(min(140, 36 + len(rows) * 28))
            tbl.setStyleSheet("font-size: 11px;")
            bubble_layout.addWidget(tbl)

        # Proactive follow-up suggestion chips
        if followups:
            f_label = QLabel("Suggested Follow-ups:")
            f_label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {ThemeColors.TEXT_DIM};")
            bubble_layout.addWidget(f_label)

            chips_layout = QHBoxLayout()
            chips_layout.setSpacing(6)
            for f in followups:
                chip_btn = QPushButton(f)
                chip_btn.setProperty("class", "btn_secondary")
                chip_btn.setStyleSheet("font-size: 11px; padding: 4px 10px; border-radius: 12px;")
                chip_btn.clicked.connect(lambda ch, text=f: self.send_prompt(text))
                chips_layout.addWidget(chip_btn)
            chips_layout.addStretch()
            bubble_layout.addLayout(chips_layout)

        # Insert before bottom stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

    def on_send_clicked(self):
        text = self.prompt_input.text().strip()
        if text:
            self.send_prompt(text)
            self.prompt_input.clear()

    def send_prompt(self, prompt: str):
        # Add user bubble immediately
        self.add_message_bubble("user", prompt)
        self.scroll_to_bottom()

        user_role = self.role_combo.currentText()
        property_id = session_manager.active_property.get("id") if session_manager.active_property else None

        # Query API
        resp = api_client.query_ai_assistant(
            prompt=prompt,
            thread_id=self.active_thread_id,
            property_id=property_id,
            user_role=user_role
        )

        if resp:
            self.active_thread_id = resp.get("thread_id")
            content = resp.get("response_text", "")
            data = resp.get("structured_data")
            followups = resp.get("suggested_followups", [])
            self.add_message_bubble("assistant", content, structured_data=data, followups=followups)
            self.refresh_threads_list()
            self.scroll_to_bottom()

    def scroll_to_bottom(self):
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )

    def refresh_threads_list(self):
        self.cached_threads = api_client.get_ai_threads()
        self.thread_list.clear()
        for t in self.cached_threads:
            t_id = t.get("id")
            title = t.get("title", "New Conversation")
            count = t.get("message_count", 0)
            item = QListWidgetItem(f"💬 {title}\n   ({count} messages)")
            item.setData(Qt.UserRole, t_id)
            self.thread_list.addItem(item)
            if t_id == self.active_thread_id:
                self.thread_list.setCurrentItem(item)

    def reset_conversations(self):
        api_client.reset_ai_conversations()
        self.refresh_data()
        self.start_new_thread()

    def refresh_data(self):
        """Fetch latest telemetry and threads."""
        self.cached_telemetry = api_client.get_ai_telemetry()
        self.refresh_threads_list()

        # Update cards
        queries_count = self.cached_telemetry.get("total_queries", 0)
        self.card_queries.lbl_val.setText(str(queries_count))

        avg_lat = self.cached_telemetry.get("avg_latency_ms", "0.00")
        self.card_latency.lbl_val.setText(f"{avg_lat} ms")

        safety_pct = self.cached_telemetry.get("safe_queries_percent", "100.00")
        self.card_safety.lbl_val.setText(f"{safety_pct}%")

        threads_count = len(self.cached_threads)
        self.card_threads.lbl_val.setText(str(threads_count))

        # If no active thread selected, load the first thread or start fresh
        if not self.active_thread_id and self.cached_threads:
            self.load_thread(self.cached_threads[0]["id"])
        elif not self.active_thread_id:
            self.start_new_thread()
