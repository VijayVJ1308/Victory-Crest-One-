"""Victory Crest One - Zero-Trust Security & Compliance Auditor Models
Continuous compliance audit checks, real-time security incident events, and quarantined entities.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime
from backend.app.models.base import Base, BaseModelMixin


class SecurityComplianceCheck(Base, BaseModelMixin):
    """Continuous automated compliance audit framework control check."""
    __tablename__ = "security_compliance_checks"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    control_code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    framework = Column(String(50), nullable=False, index=True)  # ComplianceFramework
    category = Column(String(100), nullable=False)
    status = Column(String(30), default="COMPLIANT", nullable=False, index=True)  # SecurityCheckStatus

    description = Column(Text, nullable=False)
    remediation_guide = Column(Text, nullable=True)
    last_scanned_at = Column(DateTime, nullable=True)
    is_automated = Column(Boolean, default=True, nullable=False)


class SecurityIncidentEvent(Base, BaseModelMixin):
    """Real-time threat and anomaly incident event."""
    __tablename__ = "security_incident_events"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    event_code = Column(String(50), unique=True, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # SecurityEventType
    severity = Column(String(20), default="HIGH", nullable=False, index=True)  # SecurityThreatSeverity

    source_ip = Column(String(50), nullable=True)
    actor_identity = Column(String(100), nullable=True)
    target_resource = Column(String(255), nullable=False)
    risk_score = Column(Numeric(5, 2), default=75.00, nullable=False)
    details = Column(Text, nullable=True)

    status = Column(String(30), default="INVESTIGATING", nullable=False, index=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    recommended_action = Column(String(50), default="LOG_AND_FLAG", nullable=False)  # SecurityRemediationAction
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)


class QuarantinedEntity(Base, BaseModelMixin):
    """Active quarantine sandbox record and IP/actor containment."""
    __tablename__ = "security_quarantined_entities"

    organization_id = Column(String(36), nullable=False, index=True)
    entity_id_or_ip = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), default="IP_ADDRESS", nullable=False)
    reason = Column(Text, nullable=False)
    incident_event_code = Column(String(50), nullable=True, index=True)

    status = Column(String(30), default="ACTIVE", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    quarantined_by = Column(String(100), default="ZERO_TRUST_ENGINE", nullable=False)
    expires_at = Column(DateTime, nullable=True)
    released_at = Column(DateTime, nullable=True)
