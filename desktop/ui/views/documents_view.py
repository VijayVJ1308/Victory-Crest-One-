"""Victory Crest One - Document Vault View
Browse, filter, and register enterprise documents, contracts, invoices, and compliance files.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors
from desktop.services.api_client import api_client


class DocumentsView(QWidget):
    """Secure document vault management view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("Enterprise Document Vault")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ThemeColors.TEXT_MAIN};")
        subtitle = QLabel("Central repository for contracts, invoices, compliance records, and attachments.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_MUTED};")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        # Category Filter
        cat_label = QLabel("Category:")
        cat_label.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-weight: 600; font-size: 11px;")
        header_row.addWidget(cat_label)

        self.cat_filter = QComboBox()
        self.cat_filter.addItems(["All Categories", "REPORT", "INVOICE", "CONTRACT", "ID_PROOF", "GENERAL"])
        self.cat_filter.currentIndexChanged.connect(self.on_filter_changed)
        header_row.addWidget(self.cat_filter)

        # Upload / Register Button
        btn_upload = QPushButton("📄 Register Document")
        btn_upload.setProperty("class", "btn_primary")
        btn_upload.clicked.connect(self.open_register_dialog)
        header_row.addWidget(btn_upload)

        main_layout.addLayout(header_row)

        # Documents Table
        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(6)
        self.doc_table.setHorizontalHeaderLabels([
            "File Name", "Category", "Linked Record", "Version", "Size", "Uploaded At"
        ])
        self.doc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.doc_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_SURFACE};
                gridline-color: {ThemeColors.BORDER_LIGHT};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_BASE};
                color: {ThemeColors.TEXT_MUTED};
                padding: 8px;
                border: none;
                font-weight: 700;
                font-size: 11px;
            }}
        """)
        main_layout.addWidget(self.doc_table)

    def on_filter_changed(self):
        self.refresh_data()

    def refresh_data(self):
        cat = self.cat_filter.currentText()
        category_param = None if cat == "All Categories" else cat
        docs = api_client.get_documents(category=category_param)

        self.doc_table.setRowCount(len(docs))
        for row, d in enumerate(docs):
            self.doc_table.setItem(row, 0, QTableWidgetItem(f"📄 {d.get('file_name', '')}"))
            self.doc_table.setItem(row, 1, QTableWidgetItem(d.get("category", "GENERAL")))
            linked = f"{d.get('linked_entity_type', '')} ({d.get('linked_entity_id', '')})" if d.get("linked_entity_type") else "None"
            self.doc_table.setItem(row, 2, QTableWidgetItem(linked))
            self.doc_table.setItem(row, 3, QTableWidgetItem(f"v{d.get('version', 1)}"))
            size_kb = round(d.get("file_size_bytes", 0) / 1024, 1)
            self.doc_table.setItem(row, 4, QTableWidgetItem(f"{size_kb} KB"))
            ts = str(d.get("created_at", ""))[:19]
            self.doc_table.setItem(row, 5, QTableWidgetItem(ts))

    def open_register_dialog(self):
        file_name, ok = QInputDialog.getText(self, "Register Document", "Enter document file name (e.g. vendor_agreement_2026.pdf):")
        if ok and file_name.strip():
            api_client.register_document(file_name=file_name.strip(), category=self.cat_filter.currentText() if self.cat_filter.currentText() != "All Categories" else "GENERAL")
            self.refresh_data()
