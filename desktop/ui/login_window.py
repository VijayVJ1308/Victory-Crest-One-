"""Victory Crest One - Enterprise Login Dialog
Provides credential authentication, Argon2 validation via backend, and quick-fill demo presets.
"""

from typing import Optional, Callable
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt

from desktop.core.theme import ThemeColors, ENTERPRISE_STYLE_SHEET
from desktop.core.session import session_manager
from desktop.services.api_client import api_client


class LoginDialog(QDialog):
    """Secure login dialog for user authentication and session establishment."""

    def __init__(self, on_success: Optional[Callable[[], None]] = None, parent=None):
        super().__init__(parent)
        self.on_success = on_success
        self.setWindowTitle("Sign In — Victory Crest ONE")
        self.setFixedSize(440, 520)
        self.setStyleSheet(ENTERPRISE_STYLE_SHEET)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Brand Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)
        header_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("👑")
        icon_label.setStyleSheet("font-size: 36px;")
        icon_label.setAlignment(Qt.AlignCenter)

        title = QLabel("VICTORY CREST ONE")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 800;
            color: {ThemeColors.TEXT_MAIN};
            letter-spacing: 0.8px;
        """)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Sign in to your enterprise account")
        subtitle.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 12px;")
        subtitle.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # Form Card
        form_frame = QFrame()
        form_frame.setProperty("class", "content_card")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(12)

        # Username / Email
        u_label = QLabel("Username or Email")
        u_label.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. admin or admin@victorycrest.internal")
        self.username_input.setText("admin")
        form_layout.addWidget(u_label)
        form_layout.addWidget(self.username_input)

        # Password
        p_label = QLabel("Password")
        p_label.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setText("AdminPassword123!")
        form_layout.addWidget(p_label)
        form_layout.addWidget(self.password_input)

        # Error Message
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #F87171; font-size: 11px;")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)

        # Sign In Button
        self.sign_in_btn = QPushButton("Sign In")
        self.sign_in_btn.setProperty("class", "btn_primary")
        self.sign_in_btn.setMinimumHeight(38)
        self.sign_in_btn.clicked.connect(self.handle_login)
        form_layout.addWidget(self.sign_in_btn)

        layout.addWidget(form_frame)

        # Demo Presets Section
        presets_label = QLabel("Quick-Fill Demonstration Profiles:")
        presets_label.setStyleSheet(f"color: {ThemeColors.TEXT_DIM}; font-size: 10px; font-weight: 600;")
        layout.addWidget(presets_label)

        presets_row = QHBoxLayout()
        presets_row.setSpacing(6)

        presets = [
            ("Admin", "admin", "AdminPassword123!"),
            ("Hotel GM", "hotel_gm", "HotelPassword123!"),
            ("Accountant", "accountant", "AccountantPass123!"),
            ("Auditor", "auditor", "AuditorPass123!")
        ]

        for name, user, pwd in presets:
            btn = QPushButton(name)
            btn.setProperty("class", "btn_secondary")
            btn.setStyleSheet("font-size: 11px; padding: 4px 8px;")
            btn.clicked.connect(lambda checked, u=user, p=pwd: self.fill_preset(u, p))
            presets_row.addWidget(btn)

        layout.addLayout(presets_row)

    def fill_preset(self, username: str, password: str):
        self.username_input.setText(username)
        self.password_input.setText(password)
        self.error_label.setVisible(False)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.error_label.setText("Please enter both username and password.")
            self.error_label.setVisible(True)
            return

        success, data_or_err = api_client.login(username, password)
        if success:
            session_manager.current_user = data_or_err.get("user", {})
            self.accept()
            if self.on_success:
                self.on_success()
        else:
            err_msg = data_or_err.get("detail", "Authentication failed. Check credentials.")
            self.error_label.setText(err_msg)
            self.error_label.setVisible(True)
