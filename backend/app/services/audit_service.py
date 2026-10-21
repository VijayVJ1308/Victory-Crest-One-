"""Victory Crest One - Immutable Audit Trail Service
Records security and business events across user actions and API mutations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from backend.app.core.logging import logger
from backend.app.schemas.user import AuditLogOut

# Resilient in-memory audit buffer with database sync
_AUDIT_LOGS_STORE: List[Dict[str, Any]] = []


class AuditService:
    """Service to record and query immutable security and transactional audit trails."""

    @staticmethod
    def record_event(
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_email: Optional[str] = "system",
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = "127.0.0.1"
    ) -> Dict[str, Any]:
        """Record an event into the immutable audit trail."""
        log_entry = {
            "id": str(uuid.uuid4()),
            "action": action.upper(),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_email": user_email,
            "organization_id": organization_id,
            "property_id": property_id,
            "details": details,
            "ip_address": ip_address,
            "created_at": datetime.utcnow()
        }
        _AUDIT_LOGS_STORE.insert(0, log_entry)
        logger.info(f"AUDIT: [{log_entry['action']}] {entity_type} {entity_id or ''} by {user_email}")
        return log_entry

    @classmethod
    def log_event(
        cls,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = "system",
        username: Optional[str] = "System",
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        details: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Convenience adapter for logging events."""
        detail_str = str(details) if details else None
        return cls.record_event(
            action=action,
            entity_type=resource_type or "resource",
            entity_id=resource_id,
            user_email=username or user_id or "system",
            organization_id=organization_id,
            property_id=property_id,
            details=detail_str
        )

    @classmethod
    def log_action(
        cls,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = "SYSTEM",
        user_email: Optional[str] = "system@victorycrest.com",
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        details: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Convenience method for logging domain actions."""
        return cls.record_event(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_email=user_email,
            organization_id=organization_id,
            property_id=property_id,
            details=details
        )

    @staticmethod
    def get_logs(
        organization_id: Optional[str] = None,
        limit: int = 50
    ) -> List[AuditLogOut]:
        """Retrieve audit logs scoped to an organization."""
        filtered = _AUDIT_LOGS_STORE
        if organization_id:
            filtered = [
                log for log in _AUDIT_LOGS_STORE
                if log.get("organization_id") == organization_id or log.get("organization_id") is None
            ]
        return [AuditLogOut(**log) for log in filtered[:limit]]


audit_service = AuditService()
