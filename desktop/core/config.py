"""Victory Crest One - Desktop Configuration
Client-side settings, default connection endpoints, and offline mode parameters.
"""

import os
from pathlib import Path


class DesktopConfig:
    APP_NAME = "Victory Crest ONE"
    APP_VERSION = "0.1.0"
    TAGLINE = "One Platform. Every Business. Complete Control."
    
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    API_V1_PREFIX = "/api/v1"
    
    # Development and offline flags
    ALLOW_DEV_OFFLINE = True
    REQUEST_TIMEOUT_SECONDS = 3.0
    
    # Local Storage
    LOCAL_DATA_DIR = Path("local_data")
    LOCAL_DB_FILE = LOCAL_DATA_DIR / "victory_crest_local.db"
    
    # UI Dimensions
    DEFAULT_WINDOW_WIDTH = 1380
    DEFAULT_WINDOW_HEIGHT = 880
    MIN_WINDOW_WIDTH = 1080
    MIN_WINDOW_HEIGHT = 700


desktop_config = DesktopConfig()
