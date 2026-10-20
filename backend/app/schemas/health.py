"""Victory Crest One - Health Schemas
Pydantic schemas for health endpoint responses and database diagnostic telemetry.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DatabaseHealthSchema(BaseModel):
    status: str
    engine: str
    url_masked: str
    is_connected: bool
    latency_ms: Optional[float] = None
    detail: Optional[str] = None
    troubleshooting: Optional[str] = None


class SystemHealthSchema(BaseModel):
    app_name: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str
    database: DatabaseHealthSchema
    offline_sync_available: bool = True
    active_organization: Optional[str] = None
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
