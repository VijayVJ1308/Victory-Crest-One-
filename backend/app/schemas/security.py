"""Victory Crest One - Zero-Trust Security & Compliance Auditor Schemas
Pydantic schemas for compliance controls, threat incident events, quarantine containment, and posture metrics.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from shared.enums import (
    ComplianceFramework,
    SecurityCheckStatus,
    SecurityThreatSeverity,
    SecurityEventType,
    SecurityRemediationAction,
)


class SecurityComplianceCheckBase(BaseModel):
    """Base attributes for compliance audit control."""
    control_code: str = Field(..., description="Unique compliance control code e.g. SOC2-CC6.1")
    title: str = Field(..., description="Control title")
    framework: ComplianceFramework = Field(..., description="Compliance framework (SOC2, ISO27001, GDPR, etc.)")
    category: str = Field(..., description="Control category e.g. Access Control, Data Encryption")
    status: SecurityCheckStatus = Field(default=SecurityCheckStatus.COMPLIANT, description="Audit check status")
    description: str = Field(..., description="Technical requirement description")
    remediation_guide: Optional[str] = Field(default=None, description="Steps to remediate non-compliance")
    is_automated: bool = Field(default=True, description="Whether verified automatically")
    property_id: Optional[str] = Field(default=None)


class SecurityComplianceCheckCreate(SecurityComplianceCheckBase):
    """Payload to register a new compliance control check."""
    pass


class SecurityComplianceCheckOut(SecurityComplianceCheckBase):
    """Compliance control check response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    last_scanned_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ComplianceScanRequest(BaseModel):
    """Trigger an on-demand zero-trust compliance posture audit."""
    framework: Optional[ComplianceFramework] = Field(default=None, description="Optional target framework filter")
    property_id: Optional[str] = Field(default=None)


class ComplianceScanResponse(BaseModel):
    """Result of automated compliance audit execution."""
    scanned_controls_count: int
    compliant_count: int
    warning_count: int
    non_compliant_count: int
    overall_compliance_percent: Decimal
    posture_rating: str
    timestamp: datetime


class SecurityIncidentBase(BaseModel):
    """Base attributes for security threat or anomaly incident."""
    event_code: str = Field(..., description="Unique incident identifier e.g. SEC-2026-001")
    event_type: SecurityEventType = Field(..., description="Classification of threat event")
    severity: SecurityThreatSeverity = Field(default=SecurityThreatSeverity.HIGH, description="Threat severity tier")
    source_ip: Optional[str] = Field(default=None, description="Originating IP address")
    actor_identity: Optional[str] = Field(default=None, description="Actor username, token, or service id")
    target_resource: str = Field(..., description="Target API endpoint, database, or resource")
    risk_score: Decimal = Field(default=Decimal("75.00"), description="Calculated threat risk score (0-100)")
    details: Optional[str] = Field(default=None, description="Diagnostic payload / raw log excerpt")
    recommended_action: SecurityRemediationAction = Field(default=SecurityRemediationAction.LOG_AND_FLAG)
    property_id: Optional[str] = Field(default=None)


class SecurityIncidentCreate(SecurityIncidentBase):
    """Payload to ingest or record a security incident."""
    pass


class IncidentResolutionRequest(BaseModel):
    """Payload to contain or resolve an active incident."""
    resolution_notes: str = Field(..., description="Remediation actions taken")
    remediation_action: Optional[SecurityRemediationAction] = Field(default=None)


class SecurityIncidentOut(SecurityIncidentBase):
    """Security incident response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    status: str
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: Optional[datetime] = None


class QuarantineRequest(BaseModel):
    """Payload to sandbox / quarantine a malicious entity or IP."""
    entity_id_or_ip: str = Field(..., description="IP address, user account id, or token to sandbox")
    entity_type: str = Field(default="IP_ADDRESS", description="Entity type (IP_ADDRESS, USER_ACCOUNT, API_KEY)")
    reason: str = Field(..., description="Reason for zero-trust quarantine isolation")
    incident_event_code: Optional[str] = Field(default=None)
    quarantined_by: Optional[str] = Field(default="SECURITY_OFFICER")


class QuarantinedEntityOut(BaseModel):
    """Quarantine sandbox containment schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    entity_id_or_ip: str
    entity_type: str
    reason: str
    incident_event_code: Optional[str] = None
    status: str
    is_active: bool
    quarantined_by: str
    expires_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ThreatEvaluationRequest(BaseModel):
    """Real-time payload to evaluate threat risk."""
    severity: SecurityThreatSeverity
    event_count: int = Field(default=1, ge=1)
    failed_attempts: int = Field(default=0, ge=0)
    is_privileged_account: bool = Field(default=False)


class ThreatEvaluationResponse(BaseModel):
    """Threat risk score response."""
    risk_score: Decimal
    risk_tier: str
    recommended_action: SecurityRemediationAction


class CredentialEntropyRequest(BaseModel):
    """Payload to evaluate password or secret key entropy."""
    password_length: int = Field(..., ge=1, description="Length of password/secret")
    has_symbols: bool = Field(default=True)
    has_numbers: bool = Field(default=True)
    has_mixed_case: bool = Field(default=True)


class CredentialEntropyResponse(BaseModel):
    """Entropy evaluation response."""
    password_length: int
    pool_size: int
    entropy_bits: Decimal
    strength_rating: str
    is_zero_trust_compliant: bool


class SecurityPostureMetricsOut(BaseModel):
    """Consolidated enterprise zero-trust security posture metrics."""
    enterprise_posture_score: Decimal
    posture_grade: str
    overall_compliance_percent: Decimal
    compliance_rating: str
    total_controls_audited: int
    failing_controls_count: int
    warning_controls_count: int
    open_incidents_count: int
    critical_threats_count: int
    quarantined_actors_count: int
    framework_scores: Dict[str, Decimal]
