"""Victory Crest One - Data Transfer Objects (DTO)
Pydantic schemas used across API endpoints, client services, and UI state models.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PropertyContext(BaseModel):
    id: str
    code: str
    name: str
    type: str
    city: str
    state: str
    country: str
    rooms_count: int = 0
    is_simulated: bool = True


class OrganisationContext(BaseModel):
    id: str
    code: str
    name: str
    legal_name: str
    currency: str = "INR"
    is_simulated: bool = True
    properties: List[PropertyContext] = Field(default_factory=list)


class DatabaseHealth(BaseModel):
    status: str
    engine: str
    url_masked: str
    is_connected: bool
    latency_ms: Optional[float] = None
    detail: Optional[str] = None
    troubleshooting: Optional[str] = None


class SystemHealthResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str  # healthy, degraded, critical
    database: DatabaseHealth
    offline_sync_available: bool = True
    active_organization: Optional[str] = None
    diagnostics: Dict[str, Any] = Field(default_factory=dict)


class ModuleInfo(BaseModel):
    id: str
    name: str
    category: str
    icon: str
    description: str
    phase: int
    status: str  # active, planned, maintenance
