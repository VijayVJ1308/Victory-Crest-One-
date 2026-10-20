"""Victory Crest One - Metric Card Component
Displays executive KPI metrics with icon, title, main value, and contextual subtext.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from desktop.core.theme import ThemeColors


class MetricCard(QFrame):
    """Card widget for displaying key business metrics and indicators."""

    def __init__(
        self,
        title: str,
        value: str,
        icon: str = "📈",
        subtext: str = "",
        is_positive: bool = True,
        parent=None
    ):
        super().__init__(parent)
        self.setProperty("class", "metric_card")
        self.setObjectName("metric_card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Header Row: Icon + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        
        title_label = QLabel(title.upper())
        title_label.setStyleSheet(f"""
            color: {ThemeColors.TEXT_MUTED};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Value Label
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            color: {ThemeColors.TEXT_MAIN};
            font-size: 24px;
            font-weight: 700;
            margin-top: 4px;
        """)
        layout.addWidget(self.value_label)

        # Subtext / Context
        if subtext:
            sub_color = ThemeColors.STATUS_ACTIVE if is_positive else ThemeColors.TEXT_DIM
            sub_label = QLabel(subtext)
            sub_label.setStyleSheet(f"""
                color: {sub_color};
                font-size: 11px;
                font-weight: 500;
            """)
            layout.addWidget(sub_label)

    def update_value(self, new_value: str):
        self.value_label.setText(new_value)
