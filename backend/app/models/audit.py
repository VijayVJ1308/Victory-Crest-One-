"""Victory Crest One - Audit Trail Models
Immutable record of security and administrative actions.
"""

from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
from backend.app.models.base import Base, BaseModelMixin


class AuditLog(Base, BaseModelMixin):
    """Audit log entry tracking user operations, resource changes, and system events."""
    __tablename__ = "audit_logs"

    organization_id = Column(String(36), nullable=True, index=True)
    property_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    
    action = Column(String(50), nullable=False, index=True)  # LOGIN, CREATE, UPDATE, DELETE, EXPORT, APPROVE
    entity_type = Column(String(50), nullable=False, index=True)  # Organization, User, Invoice, etc.
    entity_id = Column(String(36), nullable=True, index=True)
    
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
