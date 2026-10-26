"""Victory Crest One - AI Business Assistant Pydantic Schemas
DTOs for Natural Language Query Requests, Permission-Aware AI Responses,
Conversation Threads, and Query Telemetry.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

from shared.enums import AiQueryIntent, AiResponseFormat, AiMessageRole, AiSafetyRating


class AiQueryRequest(BaseModel):
    """User inquiry prompt sent to the AI assistant."""
    prompt: str = Field(..., min_length=1, description="Natural language question or command")
    thread_id: Optional[str] = Field(default=None, description="Existing thread ID to continue, or null for new")
    property_id: Optional[str] = Field(default=None, description="Operating property scope")
    user_role: Optional[str] = Field(default="General Manager", description="Role of the querying user for RBAC masking")


class AiQueryResponse(BaseModel):
    """Complete synthesized response from the AI assistant."""
    message_id: str
    thread_id: str
    intent: str
    safety_rating: str
    response_text: str
    structured_data: Optional[Dict[str, Any]] = None
    suggested_followups: List[str] = Field(default_factory=list)
    latency_ms: Decimal = Field(default=Decimal("0.00"))
    created_at: datetime


class AiMessageOut(BaseModel):
    """Individual conversational message in a thread."""
    id: str
    thread_id: str
    role: str
    content: str
    intent: Optional[str] = None
    safety_rating: str = "SAFE"
    structured_data: Optional[Dict[str, Any]] = None
    latency_ms: Decimal = Field(default=Decimal("0.00"))
    created_at: datetime


class AiThreadOut(BaseModel):
    """Summary of a conversation thread."""
    id: str
    organization_id: str
    property_id: Optional[str] = None
    user_id: str
    user_name: str
    user_role: str
    title: str
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime


class AiAssistantTelemetryOut(BaseModel):
    """Usage telemetry and intent breakdown for executive operations."""
    total_queries: int
    avg_latency_ms: Decimal
    safe_queries_percent: Decimal
    intent_distribution: Dict[str, int] = Field(default_factory=dict)
    total_threads: int
    recent_queries: List[AiMessageOut] = Field(default_factory=list)
