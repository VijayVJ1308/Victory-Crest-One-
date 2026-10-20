"""Victory Crest One - Module Catalog View
Searchable catalog displaying all 18+ enterprise modules, categorised by domain,
with implementation status, phase indicators, and capability descriptions.
"""

from typing import Callable, Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QScrollArea, QFrame, QPushButton
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client
from desktop.ui.components.module_card import ModuleCard
from shared.constants import (
    CATEGORY_CORE,
    CATEGORY_REVENUE,
    CATEGORY_OPERATIONS,
    CATEGORY_HOSPITALITY,
    CATEGORY_PEOPLE
)


class ModuleCatalogView(QWidget):
    """View presenting the complete modular enterprise operating system catalog."""

    def __init__(self, on_select_module: Optional[Callable[[str], None]] = None, parent=None):
        super().__init__(parent)
        self.on_select_module = on_select_module
        self.modules: List[Dict[str, Any]] = api_client.get_modules()
        self.cards: List[ModuleCard] = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # Header Section
        header_row = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel("Enterprise Business Modules")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {ThemeColors.TEXT_MAIN};
        """)

        subtitle = QLabel("One Platform. Every Business. Complete Control. (18 Modules Across 5 Domains)")
        subtitle.setStyleSheet(f"""
            font-size: 13px;
            color: {ThemeColors.TEXT_MUTED};
        """)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_row.addLayout(title_layout)
        header_row.addStretch()

        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter modules by name, keyword, or domain...")
        self.search_input.setMinimumWidth(320)
        self.search_input.textChanged.connect(self.filter_modules)
        header_row.addWidget(self.search_input)

        main_layout.addLayout(header_row)

        # Category Filter Buttons
        cat_row = QHBoxLayout()
        cat_row.setSpacing(8)

        categories = ["All Modules", CATEGORY_CORE, CATEGORY_REVENUE, CATEGORY_OPERATIONS, CATEGORY_HOSPITALITY, CATEGORY_PEOPLE]
        self.cat_buttons = []

        for cat in categories:
            btn = QPushButton(cat)
            btn.setProperty("class", "btn_secondary")
            btn.setCheckable(True)
            if cat == "All Modules":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, c=cat: self.on_category_clicked(c))
            cat_row.addWidget(btn)
            self.cat_buttons.append(btn)

        cat_row.addStretch()
        main_layout.addLayout(cat_row)

        # Scrollable Grid of Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)
        self.grid_layout.setSpacing(14)

        self.populate_grid(self.modules)

        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll)

    def populate_grid(self, modules_list: List[Dict[str, Any]]):
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards.clear()

        # Layout in 3 columns
        cols = 3
        for idx, mod in enumerate(modules_list):
            card = ModuleCard(
                module_id=mod["id"],
                name=mod["name"],
                category=mod["category"],
                icon=mod["icon"],
                description=mod["description"],
                phase=mod.get("phase", 1),
                status=mod.get("status", "planned"),
                on_click=self.on_select_module
            )
            self.cards.append(card)
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(card, row, col)

    def on_category_clicked(self, selected_category: str):
        for btn in self.cat_buttons:
            btn.setChecked(btn.text() == selected_category)

        if selected_category == "All Modules":
            filtered = self.modules
        else:
            filtered = [m for m in self.modules if m["category"] == selected_category]
        self.populate_grid(filtered)

    def filter_modules(self, query: str):
        q = query.lower().strip()
        if not q:
            self.populate_grid(self.modules)
            return
        filtered = [
            m for m in self.modules
            if q in m["name"].lower() or q in m["description"].lower() or q in m["category"].lower()
        ]
        self.populate_grid(filtered)
