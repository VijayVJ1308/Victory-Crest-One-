"""Victory Crest One - Desktop Session Manager
Tracks active organization, active property/branch, user profile, and connectivity state.
"""

from typing import Optional, Dict, Any, List
from shared.constants import DEMO_ORGANISATIONS


class SessionManager:
    """Singleton session controller for desktop user state."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.current_user = {
            "name": "Enterprise Administrator",
            "email": "admin@victorycrest.internal",
            "role": "System Administrator",
            "is_superuser": True
        }
        
        # Default Organisation and Property
        self.organizations: List[Dict[str, Any]] = DEMO_ORGANISATIONS
        self.active_organization: Dict[str, Any] = DEMO_ORGANISATIONS[0]
        self.active_property: Dict[str, Any] = DEMO_ORGANISATIONS[0]["properties"][0]
        
        # System & Connectivity
        self.is_connected: bool = False
        self.is_dev_mode: bool = False
        self.backend_health: Optional[Dict[str, Any]] = None

    def set_active_organization(self, org_id: str):
        for org in self.organizations:
            if org["id"] == org_id:
                self.active_organization = org
                if org.get("properties"):
                    self.active_property = org["properties"][0]
                break

    def set_active_property(self, property_id: str):
        for prop in self.active_organization.get("properties", []):
            if prop["id"] == property_id:
                self.active_property = prop
                break

    def get_context_title(self) -> str:
        org_code = self.active_organization.get("code", "VCG")
        prop_name = self.active_property.get("name", "All Properties")
        return f"[{org_code}] {prop_name}"


session_manager = SessionManager()
