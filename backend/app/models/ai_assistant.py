"""Victory Crest One - AI Business Assistant Models
Persistent Conversation Threads, Messages, Intent Tags, and Query Logs.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, Integer
from backend.app.models.base import Base, BaseModelMixin


class AiConversationThread(Base, BaseModelMixin):
    """Conversational thread or executive inquiry session."""
    __tablename__ = "ai_conversation_threads"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    user_id = Column(String(36), nullable=False, index=True)
    user_name = Column(String(255), nullable=False)
    user_role = Column(String(100), nullable=False)

    title = Column(String(255), nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    last_message_at = Column(DateTime, nullable=True)


class AiMessageLog(Base, BaseModelMixin):
    """Historical record of an individual prompt or AI response in a thread."""
    __tablename__ = "ai_message_logs"

    thread_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)                         # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)                       # AiQueryIntent enum
    safety_rating = Column(String(50), default="SAFE", nullable=False) # AiSafetyRating enum

    structured_data_json = Column(Text, nullable=True)
    latency_ms = Column(Numeric(10, 2), default=0.00, nullable=False)
    tokens_estimated = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
