"""Victory Crest One - Enterprise Design System & Styling
Cohesive dark theme palette, typography rules, component styling, and Qt Style Sheet (QSS).
"""


class ThemeColors:
    BG_BASE = "#090D16"
    BG_SURFACE = "#111827"
    BG_SECONDARY = "#161F30"
    BG_CARD = "#161F30"
    BG_CARD_HOVER = "#1D283D"
    BG_INPUT = "#0F172A"
    
    BORDER_LIGHT = "#1F293D"
    BORDER_SUBTLE = "#283548"
    BORDER_ACTIVE = "#3B82F6"
    
    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    PRIMARY_LIGHT = "#3B82F6"
    ACCENT_PRIMARY = "#3B82F6"
    
    TEXT_MAIN = "#F8FAFC"
    TEXT_MUTED = "#94A3B8"
    TEXT_DIM = "#64748B"
    
    STATUS_ACTIVE = "#10B981"
    STATUS_SUCCESS = "#10B981"
    STATUS_INFO = "#3B82F6"
    STATUS_PLANNED = "#8B5CF6"
    STATUS_WARNING = "#F59E0B"
    STATUS_ERROR = "#EF4444"
    STATUS_OFFLINE = "#6B7280"



ENTERPRISE_STYLE_SHEET = f"""
QMainWindow {{
    background-color: {ThemeColors.BG_BASE};
    color: {ThemeColors.TEXT_MAIN};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}}

QWidget {{
    background-color: transparent;
    color: {ThemeColors.TEXT_MAIN};
    font-size: 13px;
}}

/* Top Navigation Bar */
#top_toolbar {{
    background-color: {ThemeColors.BG_SURFACE};
    border-bottom: 1px solid {ThemeColors.BORDER_LIGHT};
    min-height: 56px;
    max-height: 56px;
    padding: 0 16px;
}}

/* Sidebar */
#sidebar {{
    background-color: {ThemeColors.BG_SURFACE};
    border-right: 1px solid {ThemeColors.BORDER_LIGHT};
    min-width: 250px;
    max-width: 250px;
}}

/* Sidebar Brand Header */
#sidebar_header {{
    padding: 18px 16px 14px 16px;
    border-bottom: 1px solid {ThemeColors.BORDER_LIGHT};
}}

#brand_title {{
    font-size: 16px;
    font-weight: 700;
    color: {ThemeColors.TEXT_MAIN};
    letter-spacing: 0.5px;
}}

#brand_tagline {{
    font-size: 11px;
    color: {ThemeColors.TEXT_MUTED};
    font-weight: 400;
}}

/* Navigation Category Headers */
.nav_category_label {{
    font-size: 10px;
    font-weight: 700;
    color: {ThemeColors.TEXT_DIM};
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 12px 16px 4px 16px;
}}

/* Navigation Items */
QPushButton.nav_item {{
    text-align: left;
    padding: 8px 16px;
    border-radius: 6px;
    margin: 2px 8px;
    background-color: transparent;
    color: {ThemeColors.TEXT_MUTED};
    font-weight: 500;
    border: none;
}}

QPushButton.nav_item:hover {{
    background-color: {ThemeColors.BG_CARD_HOVER};
    color: {ThemeColors.TEXT_MAIN};
}}

QPushButton.nav_item:checked, QPushButton.nav_item[active="true"] {{
    background-color: #1E3A8A;
    color: #93C5FD;
    font-weight: 600;
    border-left: 3px solid {ThemeColors.PRIMARY_LIGHT};
}}

/* Cards */
QFrame.metric_card, QFrame.content_card {{
    background-color: {ThemeColors.BG_CARD};
    border: 1px solid {ThemeColors.BORDER_LIGHT};
    border-radius: 8px;
    padding: 14px;
}}

QFrame.metric_card:hover {{
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    background-color: {ThemeColors.BG_CARD_HOVER};
}}

/* Buttons */
QPushButton.btn_primary {{
    background-color: {ThemeColors.PRIMARY};
    color: #FFFFFF;
    font-weight: 600;
    padding: 7px 16px;
    border-radius: 6px;
    border: none;
}}

QPushButton.btn_primary:hover {{
    background-color: {ThemeColors.PRIMARY_HOVER};
}}

QPushButton.btn_secondary {{
    background-color: {ThemeColors.BG_CARD};
    color: {ThemeColors.TEXT_MAIN};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    font-weight: 500;
    padding: 7px 14px;
    border-radius: 6px;
}}

QPushButton.btn_secondary:hover {{
    background-color: {ThemeColors.BG_CARD_HOVER};
    border-color: {ThemeColors.TEXT_DIM};
}}

/* Dropdowns / ComboBox */
QComboBox {{
    background-color: {ThemeColors.BG_INPUT};
    color: {ThemeColors.TEXT_MAIN};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-radius: 6px;
    padding: 5px 12px;
    min-width: 180px;
    font-weight: 500;
}}

QComboBox:hover {{
    border-color: {ThemeColors.BORDER_ACTIVE};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {ThemeColors.BG_SURFACE};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    color: {ThemeColors.TEXT_MAIN};
    selection-background-color: {ThemeColors.PRIMARY};
    selection-color: #FFFFFF;
    border-radius: 4px;
    padding: 4px;
}}

/* Search Input */
QLineEdit {{
    background-color: {ThemeColors.BG_INPUT};
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-radius: 6px;
    padding: 6px 12px;
    color: {ThemeColors.TEXT_MAIN};
}}

QLineEdit:focus {{
    border-color: {ThemeColors.BORDER_ACTIVE};
}}

/* Scroll Areas */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: {ThemeColors.BG_BASE};
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {ThemeColors.BORDER_SUBTLE};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {ThemeColors.TEXT_DIM};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* Status Bar */
QStatusBar {{
    background-color: {ThemeColors.BG_SURFACE};
    border-top: 1px solid {ThemeColors.BORDER_LIGHT};
    color: {ThemeColors.TEXT_MUTED};
    font-size: 11px;
    padding: 4px 12px;
}}
"""
