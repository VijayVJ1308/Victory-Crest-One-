"""Victory Crest One - AI Business Assistant REST API Endpoints
Endpoints for natural language inquiries, semantic data synthesis,
conversation threads, and query performance telemetry.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status

from backend.app.schemas.ai_assistant import (
    AiQueryRequest,
    AiQueryResponse,
    AiMessageOut,
    AiThreadOut,
    AiAssistantTelemetryOut
)
from backend.app.services.ai_assistant_service import ai_assistant_service

router = APIRouter()


@router.post("/query", response_model=AiQueryResponse)
def execute_ai_query(request: AiQueryRequest):
    """
    Process a natural language user query against consolidated enterprise data.
    Applies role-based access control (RBAC) permission masking.
    """
    return ai_assistant_service.query(request)


@router.get("/threads", response_model=List[AiThreadOut])
def list_conversation_threads(
    user_id: Optional[str] = Query(None, description="Filter threads by user ID")
):
    """Retrieve active AI conversation threads."""
    return ai_assistant_service.get_threads(user_id=user_id)


@router.get("/threads/{thread_id}/messages", response_model=List[AiMessageOut])
def get_thread_messages(thread_id: str):
    """Retrieve full chronological message history for a conversation thread."""
    messages = ai_assistant_service.get_thread_messages(thread_id)
    if not messages:
        # Return empty list or 404 if thread unknown
        thread = [t for t in ai_assistant_service.get_threads() if t["id"] == thread_id]
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation thread '{thread_id}' not found."
            )
    return messages


@router.get("/telemetry", response_model=AiAssistantTelemetryOut)
def get_ai_assistant_telemetry():
    """Retrieve AI assistant operational telemetry, intent distributions, and average latency."""
    return ai_assistant_service.get_telemetry()


@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_conversation_history():
    """Reset all conversation threads and telemetry to demo initial state."""
    ai_assistant_service.reset_threads()
    return {"status": "success", "message": "AI assistant conversations reset successfully."}
