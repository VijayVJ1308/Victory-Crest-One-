"""Victory Crest One - Status Badge Component
Visual status indicator for modules, database connectivity, and operational states.
"""

from PySide6.QtWidgets import QLabel
from desktop.core.theme import ThemeColors


class StatusBadge(QLabel):
    """Clean capsule badge widget displaying state with appropriate styling."""

    STYLE_MAP = {
        "active": {"bg": "rgba(16, 185, 129, 0.15)", "text": "#34D399", "border": "#10B981"},
        "connected": {"bg": "rgba(16, 185, 129, 0.15)", "text": "#34D399", "border": "#10B981"},
        "planned": {"bg": "rgba(139, 92, 246, 0.15)", "text": "#C4B5FD", "border": "#8B5CF6"},
        "offline": {"bg": "rgba(107, 114, 128, 0.15)", "text": "#9CA3AF", "border": "#6B7280"},
        "degraded": {"bg": "rgba(245, 158, 11, 0.15)", "text": "#FCD34D", "border": "#F59E0B"},
        "simulated": {"bg": "rgba(59, 130, 246, 0.15)", "text": "#93C5FD", "border": "#3B82F6"},
        "error": {"bg": "rgba(239, 68, 68, 0.15)", "text": "#FCA5A5", "border": "#EF4444"},
    }

    def __init__(self, text: str, status_type: str = "active", parent=None):
        super().__init__(text.upper(), parent)
        self.status_type = status_type.lower()
        self.apply_style()

    def set_status(self, text: str, status_type: str):
        self.setText(text.upper())
        self.status_type = status_type.lower()
        self.apply_style()

    def apply_style(self):
        style = self.STYLE_MAP.get(self.status_type, self.STYLE_MAP["active"])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {style['bg']};
                color: {style['text']};
                border: 1px solid {style['border']};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
        """)
