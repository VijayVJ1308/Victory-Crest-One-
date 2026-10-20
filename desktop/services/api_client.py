"""Victory Crest One - Desktop API Client Service
Handles network communication with the FastAPI backend, connection telemetry,
and resilient offline fallback without masking real connection status.
"""

from typing import Dict, Any, Tuple, List, Optional
import httpx
from desktop.core.config import desktop_config
from desktop.core.session import session_manager
from shared.constants import DEMO_ORGANISATIONS, MODULE_CATALOG


class ApiClient:
    """Client for central backend API interactions."""

    def __init__(self, base_url: str = desktop_config.API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.timeout = desktop_config.REQUEST_TIMEOUT_SECONDS

    def check_health(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check health endpoint of central backend.
        Returns: (is_online, response_dict_or_error_details)
        """
        url = f"{self.base_url}{desktop_config.API_V1_PREFIX}/health"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    session_manager.is_connected = True
                    session_manager.backend_health = data
                    return True, data
                else:
                    err_info = {
                        "status": "error",
                        "detail": f"Backend returned HTTP {res.status_code}",
                        "troubleshooting": "Check backend service logs."
                    }
                    session_manager.is_connected = False
                    return False, err_info
        except httpx.ConnectError:
            err_info = {
                "status": "offline",
                "detail": f"Could not connect to backend server at {self.base_url}",
                "troubleshooting": (
                    "Backend server is not running. "
                    "Start it with: `./.venv/bin/uvicorn backend.app.main:app --port 8000`"
                )
            }
            session_manager.is_connected = False
            return False, err_info
        except Exception as e:
            err_info = {
                "status": "error",
                "detail": str(e),
                "troubleshooting": "Verify network configuration and API_BASE_URL."
            }
            session_manager.is_connected = False
            return False, err_info

    def get_organizations(self) -> List[Dict[str, Any]]:
        """Fetch organizations list or return simulated baseline if offline."""
        url = f"{self.base_url}{desktop_config.API_V1_PREFIX}/organizations"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url)
                if res.status_code == 200:
                    return res.json()
        except Exception:
            pass
        return DEMO_ORGANISATIONS

    def get_modules(self) -> List[Dict[str, Any]]:
        """Fetch module catalog or return canonical baseline if offline."""
        url = f"{self.base_url}{desktop_config.API_V1_PREFIX}/modules"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url)
                if res.status_code == 200:
                    return res.json()
        except Exception:
            pass
        return MODULE_CATALOG


api_client = ApiClient()
