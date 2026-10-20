"""Victory Crest One - Desktop Application Entry Point
Initializes Qt application, loads enterprise design system stylesheet, and displays MainWindow.
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from desktop.core.config import desktop_config
from desktop.ui.main_window import MainWindow


def parse_arguments():
    parser = argparse.ArgumentParser(description=f"{desktop_config.APP_NAME} Desktop Application")
    parser.add_argument("--api-url", type=str, default=desktop_config.API_BASE_URL, help="Base URL of central FastAPI backend")
    parser.add_argument("--offline", action="store_true", help="Launch in offline/local storage mode")
    parser.add_argument("--dev-mode", action="store_true", default=True, help="Enable development diagnostics")
    return parser.parse_args()


def main():
    args = parse_arguments()
    if args.api_url:
        desktop_config.API_BASE_URL = args.api_url

    # High-DPI support
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName(desktop_config.APP_NAME)
    app.setApplicationVersion(desktop_config.APP_VERSION)
    app.setOrganizationName("Victory Crest Enterprise Systems")
    app.setOrganizationDomain("victorycrest.internal")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
