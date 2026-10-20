"""Victory Crest One - Module Card Component
Interactive grid card for viewing system modules, phase status, and functional capabilities.
"""

from typing import Callable, Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from desktop.core.theme import ThemeColors
from desktop.ui.components.status_badge import StatusBadge


class ModuleCard(QFrame):
    """Card widget representing an enterprise business module."""

    def __init__(
        self,
        module_id: str,
        name: str,
        category: str,
        icon: str,
        description: str,
        phase: int,
        status: str,
        on_click: Optional[Callable[[str], None]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.module_id = module_id
        self.on_click = on_click
        self.setProperty("class", "content_card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Top row: Icon + Name + Status Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        top_row.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {ThemeColors.TEXT_MAIN};
            font-size: 14px;
            font-weight: 700;
        """)
        title_layout.addWidget(name_label)

        cat_label = QLabel(category.upper())
        cat_label.setStyleSheet(f"""
            color: {ThemeColors.TEXT_DIM};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        title_layout.addWidget(cat_label)

        top_row.addLayout(title_layout)
        top_row.addStretch()

        # Status Badge
        badge_type = "active" if status == "active" else "planned"
        badge_text = "ACTIVE" if status == "active" else f"PHASE {phase}"
        self.badge = StatusBadge(badge_text, badge_type)
        top_row.addWidget(self.badge)

        layout.addLayout(top_row)

        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            color: {ThemeColors.TEXT_MUTED};
            font-size: 12px;
            line-height: 1.4;
        """)
        layout.addWidget(desc_label)

        layout.addStretch()

        # Bottom Action Row
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        btn_text = "Open Module" if status == "active" else "View Roadmap"
        btn = QPushButton(btn_text)
        btn.setProperty("class", "btn_primary" if status == "active" else "btn_secondary")
        if self.on_click:
            btn.clicked.connect(lambda: self.on_click(self.module_id))
        bottom_row.addWidget(btn)

        layout.addLayout(bottom_row)
