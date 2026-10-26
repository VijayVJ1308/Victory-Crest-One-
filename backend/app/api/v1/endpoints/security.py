"""Victory Crest One - Zero-Trust Security & Compliance Auditor REST API Endpoints
Continuous automated compliance audits, real-time threat detection,
active quarantine sandboxes, and enterprise security posture analytics.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status

from backend.app.schemas.security import (
    SecurityComplianceCheckOut,
    ComplianceScanRequest,
    ComplianceScanResponse,
    SecurityIncidentCreate,
    SecurityIncidentOut,
    IncidentResolutionRequest,
    QuarantineRequest,
    QuarantinedEntityOut,
    ThreatEvaluationRequest,
    ThreatEvaluationResponse,
    CredentialEntropyRequest,
    CredentialEntropyResponse,
    SecurityPostureMetricsOut,
)
from shared.enums import (
    ComplianceFramework,
    SecurityThreatSeverity,
)
from backend.app.services.security_service import security_service

router = APIRouter()


@router.get("/compliance/checks", response_model=List[SecurityComplianceCheckOut])
def list_compliance_checks(
    property_id: Optional[str] = Query(None, description="Filter compliance controls by property"),
    framework: Optional[ComplianceFramework] = Query(None, description="Filter by compliance framework (SOC2, ISO27001, etc.)")
):
    """Retrieve all compliance controls, status, and remediation guidance."""
    return security_service.get_compliance_checks(property_id=property_id, framework=framework)


@router.post("/compliance/scan", response_model=ComplianceScanResponse)
def trigger_compliance_scan(request: ComplianceScanRequest):
    """Trigger an on-demand zero-trust compliance posture audit scan."""
    return security_service.run_compliance_scan(request)


@router.get("/incidents", response_model=List[SecurityIncidentOut])
def list_security_incidents(
    property_id: Optional[str] = Query(None, description="Filter incidents by property"),
    status: Optional[str] = Query(None, description="Filter by status (INVESTIGATING, CONTAINED, RESOLVED)"),
    severity: Optional[SecurityThreatSeverity] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)")
):
    """Retrieve real-time security threat log and anomaly stream."""
    return security_service.get_incidents(property_id=property_id, status_filter=status, severity=severity)


@router.post("/incidents", response_model=SecurityIncidentOut, status_code=status.HTTP_201_CREATED)
def record_security_incident(payload: SecurityIncidentCreate):
    """Log a newly detected threat event or zero-trust violation."""
    return security_service.create_incident(payload)


@router.post("/incidents/{incident_id}/resolve", response_model=SecurityIncidentOut)
def resolve_security_incident(incident_id: str, payload: IncidentResolutionRequest):
    """Resolve and mark an active security threat incident as contained or remediated."""
    return security_service.resolve_incident(incident_id=incident_id, payload=payload)


@router.get("/quarantine", response_model=List[QuarantinedEntityOut])
def list_quarantined_entities(
    is_active: Optional[bool] = Query(None, description="Filter by active quarantine status")
):
    """Retrieve entities (IPs, users, devices) currently or previously in quarantine sandbox."""
    return security_service.get_quarantined_entities(is_active=is_active)


@router.post("/quarantine", response_model=QuarantinedEntityOut, status_code=status.HTTP_201_CREATED)
def quarantine_entity(payload: QuarantineRequest):
    """Isolate and place a suspicious IP address or actor into active quarantine sandbox."""
    return security_service.quarantine_entity(payload)


@router.delete("/quarantine/{quarantine_id}", response_model=QuarantinedEntityOut)
def release_quarantined_entity(quarantine_id: str):
    """Release an isolated entity from quarantine sandbox."""
    return security_service.release_quarantined_entity(quarantine_id)


@router.post("/threat/evaluate", response_model=ThreatEvaluationResponse)
def evaluate_threat(request: ThreatEvaluationRequest):
    """Calculate multi-factor threat risk score and recommended zero-trust action."""
    return security_service.evaluate_threat(request)


@router.post("/credentials/entropy", response_model=CredentialEntropyResponse)
def evaluate_credential_entropy(request: CredentialEntropyRequest):
    """Calculate Shannon entropy bits and evaluate Zero-Trust credential compliance."""
    return security_service.evaluate_entropy(request)


@router.get("/metrics", response_model=SecurityPostureMetricsOut)
def get_security_posture_metrics(
    property_id: Optional[str] = Query(None, description="Filter posture metrics by property")
):
    """Retrieve executive zero-trust posture score, compliance readiness %, and active threats."""
    return security_service.get_posture_metrics(property_id=property_id)
