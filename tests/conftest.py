"""Victory Crest One - Test Suite Configuration & Fixtures
"""

import sys
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure workspace root is in python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.main import app


@pytest.fixture(scope="session")
def api_client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def qapp():
    """Headless PySide6 QApplication fixture for UI component testing."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtWidgets import QApplication
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication(sys.argv)
    yield app_instance
