"""Victory Crest One - Zero-Trust Security & Compliance Auditor Service
Continuous compliance audit checks, automated posture scanning, threat detection,
active quarantine sandbox containment, and credential entropy analytics.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.security import (
    SecurityComplianceCheckCreate,
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
    SecurityCheckStatus,
    SecurityThreatSeverity,
    SecurityEventType,
    SecurityRemediationAction,
)
from shared.calculations import (
    calculate_compliance_score,
    evaluate_threat_risk_score,
    evaluate_credential_entropy,
    calculate_security_posture_metrics,
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory stores
_CHECKS_STORE: Dict[str, Dict[str, Any]] = {}
_INCIDENTS_STORE: Dict[str, Dict[str, Any]] = {}
_QUARANTINE_STORE: Dict[str, Dict[str, Any]] = {}
_INCIDENT_COUNTER = 1004
_QUARANTINE_COUNTER = 1003


def _seed_security_data():
    """Seed baseline compliance controls, threat incidents, and active quarantine sandboxes."""
    global _INCIDENT_COUNTER, _QUARANTINE_COUNTER
    if _CHECKS_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]
    now = datetime.now(timezone.utc)

    # 1. Baseline Compliance Audit Controls
    seed_checks = [
        {
            "id": "chk_sec_1001",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "control_code": "SOC2-CC6.1",
            "title": "Logical Access Controls & Multi-Factor Authentication",
            "framework": ComplianceFramework.SOC2_TYPE_II.value,
            "category": "Access Control",
            "status": SecurityCheckStatus.COMPLIANT.value,
            "description": "Enforce MFA for all staff roles and biometric Zero-Trust keys on privileged accounts.",
            "remediation_guide": "Ensure all Active Directory accounts have TOTP or WebAuthn enrolled.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        },
        {
            "id": "chk_sec_1002",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "control_code": "SOC2-CC6.6",
            "title": "Perimeter Boundary Protection & Zero-Trust Segmentation",
            "framework": ComplianceFramework.SOC2_TYPE_II.value,
            "category": "Network Security",
            "status": SecurityCheckStatus.COMPLIANT.value,
            "description": "Virtual network segregation isolating guest Wi-Fi, POS transactions, and IoT telemetry.",
            "remediation_guide": "Verify egress ACLs and VLAN isolation rules on core gateway switches.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        },
        {
            "id": "chk_sec_1003",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "control_code": "SOC2-CC7.1",
            "title": "Continuous Vulnerability Scanning & Patch Management",
            "framework": ComplianceFramework.SOC2_TYPE_II.value,
            "category": "Vulnerability Management",
            "status": SecurityCheckStatus.COMPLIANT.value,
            "description": "Daily automated vulnerability scanning of microservices, containers, and server kernels.",
            "remediation_guide": "Execute unattended OS security updates weekly across container clusters.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        },
        {
            "id": "chk_sec_1004",
            "organization_id": org_id,
            "property_id": prop_kod,
            "control_code": "ISO27001-A12.1",
            "title": "Operational Procedures & Responsibilities",
            "framework": ComplianceFramework.ISO_27001.value,
            "category": "Operations Security",
            "status": SecurityCheckStatus.COMPLIANT.value,
            "description": "Documented and cryptographically verified change management audit trails.",
            "remediation_guide": "Require two-person sign-off for critical production configuration shifts.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        },
        {
            "id": "chk_sec_1005",
            "organization_id": org_id,
            "property_id": prop_kod,
            "control_code": "ISO27001-A13.1",
            "title": "Network Security Management & IoT Subnet Isolation",
            "framework": ComplianceFramework.ISO_27001.value,
            "category": "Network Security",
            "status": SecurityCheckStatus.WARNING.value,
            "description": "Enforce micro-segmentation for high-density smart sensor and HVAC gateway subnets.",
            "remediation_guide": "Reconfigure gateway switch port 24 to block non-MQTT broadcast packets.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        },
        {
            "id": "chk_sec_1006",
            "organization_id": org_id,
            "property_id": prop_maa,
            "control_code": "GDPR-ART32",
            "title": "Security of Processing & PII Cryptographic Pseudonymization",
            "framework": ComplianceFramework.GDPR_PRIVACY.value,
            "category": "Data Protection",
            "status": SecurityCheckStatus.COMPLIANT.value,
            "description": "AES-256 GCM encryption at rest and TLS 1.3 in transit for all guest and employee PII.",
            "remediation_guide": "Rotate data-at-rest master keys every 90 days via AWS KMS or HashiCorp Vault.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        },
        {
            "id": "chk_sec_1007",
            "organization_id": org_id,
            "property_id": prop_maa,
            "control_code": "GDPR-ART33",
            "title": "72-Hour Breach Notification & Anomaly Detection",
            "framework": ComplianceFramework.GDPR_PRIVACY.value,
            "category": "Incident Governance",
            "status": SecurityCheckStatus.COMPLIANT.value,
            "description": "Automated incident correlation and SLA alerting within 15 minutes of suspected exfiltration.",
            "remediation_guide": "Test webhook escalation paths to Data Protection Officer (DPO) quarterly.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        },
        {
            "id": "chk_sec_1008",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "control_code": "PCI-REQ3",
            "title": "Protect Stored Account Data & Primary Account Number Masking",
            "framework": ComplianceFramework.PCI_DSS_V4.value,
            "category": "Cardholder Security",
            "status": SecurityCheckStatus.COMPLIANT.value,
            "description": "Point-to-point encryption (P2PE) and truncation of cardholder data across all POS terminals.",
            "remediation_guide": "Ensure tokenized credit card references are purged upon folio settlement.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        },
        {
            "id": "chk_sec_1009",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "control_code": "PCI-REQ8",
            "title": "Multi-Factor Authentication for Cardholder Data Environment",
            "framework": ComplianceFramework.PCI_DSS_V4.value,
            "category": "Identity & Access",
            "status": SecurityCheckStatus.COMPLIANT.value,
            "description": "MFA mandatory for all administrative access into the PCI cardholder environment.",
            "remediation_guide": "Enforce 15-minute inactivity screen locks across cashier terminals.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        },
        {
            "id": "chk_sec_1010",
            "organization_id": org_id,
            "property_id": None,
            "control_code": "HIPAA-164.312",
            "title": "Technical Safeguards & Tamper-Evident Audit Logging",
            "framework": ComplianceFramework.HIPAA_SECURITY.value,
            "category": "Audit Verification",
            "status": SecurityCheckStatus.COMPLIANT.value,
            "description": "Cryptographically hashed SHA-256 audit trails for all employee health and wellness records.",
            "remediation_guide": "Verify immutable WORM write policy on audit log storage buckets.",
            "last_scanned_at": now,
            "is_automated": True,
            "created_at": now
        }
    ]
    for chk in seed_checks:
        _CHECKS_STORE[chk["id"]] = chk

    # 2. Baseline Security Threat & Anomaly Incidents
    seed_incidents = [
        {
            "id": "inc_sec_1001",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "event_code": "SEC-2026-001",
            "event_type": SecurityEventType.BRUTE_FORCE_BURST.value,
            "severity": SecurityThreatSeverity.HIGH.value,
            "source_ip": "198.51.100.24",
            "actor_identity": "unknown_external",
            "target_resource": "/api/v1/auth/token",
            "risk_score": Decimal("78.00"),
            "details": "24 failed login bursts within 60 seconds from unclassified offshore ASN.",
            "status": "CONTAINED",
            "is_resolved": False,
            "recommended_action": SecurityRemediationAction.QUARANTINE_IP.value,
            "resolved_at": None,
            "resolution_notes": None,
            "created_at": now
        },
        {
            "id": "inc_sec_1002",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "event_code": "SEC-2026-002",
            "event_type": SecurityEventType.PRIVILEGE_ESCALATION_ATTEMPT.value,
            "severity": SecurityThreatSeverity.CRITICAL.value,
            "source_ip": "10.0.14.88",
            "actor_identity": "temp_contractor_12",
            "target_resource": "/api/v1/settings/organization",
            "risk_score": Decimal("88.50"),
            "details": "Unauthorized role escalation API invocation intercepted by zero-trust auth guard.",
            "status": "INVESTIGATING",
            "is_resolved": False,
            "recommended_action": SecurityRemediationAction.REVOKE_USER_SESSION.value,
            "resolved_at": None,
            "resolution_notes": None,
            "created_at": now
        },
        {
            "id": "inc_sec_1003",
            "organization_id": org_id,
            "property_id": prop_kod,
            "event_code": "SEC-2026-003",
            "event_type": SecurityEventType.SESSION_ANOMALY.value,
            "severity": SecurityThreatSeverity.MEDIUM.value,
            "source_ip": "203.0.113.45",
            "actor_identity": "frontdesk_user_02",
            "target_resource": "/api/v1/hospitality/reservations",
            "risk_score": Decimal("45.00"),
            "details": "Concurrent active browser sessions detected across two distinct geographical regions.",
            "status": "RESOLVED",
            "is_resolved": True,
            "recommended_action": SecurityRemediationAction.FORCE_MFA_CHALLENGE.value,
            "resolved_at": now,
            "resolution_notes": "Employee authenticated via biometric push token; prior session evicted.",
            "created_at": now
        }
    ]
    for inc in seed_incidents:
        _INCIDENTS_STORE[inc["id"]] = inc

    # 3. Active Quarantine Sandbox Records
    seed_quarantine = [
        {
            "id": "quar_sec_1001",
            "organization_id": org_id,
            "entity_id_or_ip": "198.51.100.24",
            "entity_type": "IP_ADDRESS",
            "reason": "Brute force attack burst threshold exceeded on auth endpoint.",
            "incident_event_code": "SEC-2026-001",
            "status": "ACTIVE",
            "is_active": True,
            "quarantined_by": "ZERO_TRUST_ENGINE",
            "expires_at": None,
            "released_at": None,
            "created_at": now
        },
        {
            "id": "quar_sec_1002",
            "organization_id": org_id,
            "entity_id_or_ip": "temp_contractor_12",
            "entity_type": "USER_ACCOUNT",
            "reason": "Privilege escalation policy violation detected.",
            "incident_event_code": "SEC-2026-002",
            "status": "ACTIVE",
            "is_active": True,
            "quarantined_by": "ZERO_TRUST_ENGINE",
            "expires_at": None,
            "released_at": None,
            "created_at": now
        }
    ]
    for q in seed_quarantine:
        _QUARANTINE_STORE[q["id"]] = q


_seed_security_data()


class SecurityService:
    """Enterprise Zero-Trust Security & Compliance Auditor orchestration service."""

    def __init__(self):
        _seed_security_data()

    def get_compliance_checks(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        framework: Optional[ComplianceFramework] = None
    ) -> List[SecurityComplianceCheckOut]:
        """Fetch registered compliance controls filtered by property and framework."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        checks = []
        for chk in _CHECKS_STORE.values():
            if chk.get("organization_id") != org_id:
                continue
            if property_id and chk.get("property_id") and chk.get("property_id") != property_id:
                continue
            if framework:
                fw_val = framework.value if hasattr(framework, "value") else str(framework)
                if chk.get("framework") != fw_val:
                    continue
            checks.append(SecurityComplianceCheckOut(**chk))
        return sorted(checks, key=lambda x: x.control_code)

    def run_compliance_scan(
        self,
        request: ComplianceScanRequest,
        organization_id: Optional[str] = None
    ) -> ComplianceScanResponse:
        """Execute on-demand zero-trust compliance scan across target framework controls."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        now = datetime.now(timezone.utc)
        target_checks = []

        for chk in _CHECKS_STORE.values():
            if chk.get("organization_id") != org_id:
                continue
            if request.property_id and chk.get("property_id") and chk.get("property_id") != request.property_id:
                continue
            if request.framework:
                fw_val = request.framework.value if hasattr(request.framework, "value") else str(request.framework)
                if chk.get("framework") != fw_val:
                    continue
            # Update last scanned timestamp
            chk["last_scanned_at"] = now
            target_checks.append(chk)

        score_res = calculate_compliance_score(target_checks)
        return ComplianceScanResponse(
            scanned_controls_count=score_res["total_checks"],
            compliant_count=score_res["compliant_count"],
            warning_count=score_res["warning_count"],
            non_compliant_count=score_res["non_compliant_count"],
            overall_compliance_percent=score_res["overall_compliance_percent"],
            posture_rating=score_res["posture_rating"],
            timestamp=now
        )

    def get_incidents(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        severity: Optional[SecurityThreatSeverity] = None
    ) -> List[SecurityIncidentOut]:
        """Retrieve threat events and anomalies."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        incidents = []
        for inc in _INCIDENTS_STORE.values():
            if inc.get("organization_id") != org_id:
                continue
            if property_id and inc.get("property_id") and inc.get("property_id") != property_id:
                continue
            if status_filter and inc.get("status") != status_filter:
                continue
            if severity:
                sev_val = severity.value if hasattr(severity, "value") else str(severity)
                if inc.get("severity") != sev_val:
                    continue
            incidents.append(SecurityIncidentOut(**inc))
        return sorted(incidents, key=lambda x: str(x.created_at or ""), reverse=True)

    def create_incident(
        self,
        payload: SecurityIncidentCreate,
        organization_id: Optional[str] = None
    ) -> SecurityIncidentOut:
        """Record a new security incident event and auto-evaluate threat risk score."""
        global _INCIDENT_COUNTER
        _INCIDENT_COUNTER += 1
        inc_id = f"inc_sec_{_INCIDENT_COUNTER}"
        now = datetime.now(timezone.utc)
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]

        # Evaluate risk score if default or low
        score, _ = evaluate_threat_risk_score(
            severity=payload.severity.value if hasattr(payload.severity, "value") else str(payload.severity),
            event_count=1,
            failed_attempts=1,
            is_privileged_account=("admin" in (payload.actor_identity or "").lower())
        )

        inc_data = {
            "id": inc_id,
            "organization_id": org_id,
            "property_id": payload.property_id,
            "event_code": payload.event_code,
            "event_type": payload.event_type.value if hasattr(payload.event_type, "value") else str(payload.event_type),
            "severity": payload.severity.value if hasattr(payload.severity, "value") else str(payload.severity),
            "source_ip": payload.source_ip,
            "actor_identity": payload.actor_identity,
            "target_resource": payload.target_resource,
            "risk_score": score,
            "details": payload.details,
            "recommended_action": payload.recommended_action.value if hasattr(payload.recommended_action, "value") else str(payload.recommended_action),
            "status": "INVESTIGATING",
            "is_resolved": False,
            "resolved_at": None,
            "resolution_notes": None,
            "created_at": now
        }
        _INCIDENTS_STORE[inc_id] = inc_data
        return SecurityIncidentOut(**inc_data)

    def resolve_incident(
        self,
        incident_id: str,
        payload: IncidentResolutionRequest,
        organization_id: Optional[str] = None
    ) -> SecurityIncidentOut:
        """Resolve an active security threat incident."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        inc = _INCIDENTS_STORE.get(incident_id)
        if not inc or inc.get("organization_id") != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")

        inc["status"] = "RESOLVED"
        inc["is_resolved"] = True
        inc["resolved_at"] = datetime.now(timezone.utc)
        inc["resolution_notes"] = payload.resolution_notes
        if payload.remediation_action:
            action_val = payload.remediation_action.value if hasattr(payload.remediation_action, "value") else str(payload.remediation_action)
            inc["recommended_action"] = action_val

        return SecurityIncidentOut(**inc)

    def get_quarantined_entities(
        self,
        organization_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[QuarantinedEntityOut]:
        """List entities in active quarantine sandbox or release history."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        entities = []
        for q in _QUARANTINE_STORE.values():
            if q.get("organization_id") != org_id:
                continue
            if is_active is not None and q.get("is_active") != is_active:
                continue
            entities.append(QuarantinedEntityOut(**q))
        return sorted(entities, key=lambda x: str(x.created_at or ""), reverse=True)

    def quarantine_entity(
        self,
        payload: QuarantineRequest,
        organization_id: Optional[str] = None
    ) -> QuarantinedEntityOut:
        """Isolate an IP address, user account, or compromised actor into quarantine sandbox."""
        global _QUARANTINE_COUNTER
        _QUARANTINE_COUNTER += 1
        q_id = f"quar_sec_{_QUARANTINE_COUNTER}"
        now = datetime.now(timezone.utc)
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]

        q_data = {
            "id": q_id,
            "organization_id": org_id,
            "entity_id_or_ip": payload.entity_id_or_ip,
            "entity_type": payload.entity_type,
            "reason": payload.reason,
            "incident_event_code": payload.incident_event_code,
            "status": "ACTIVE",
            "is_active": True,
            "quarantined_by": payload.quarantined_by or "SECURITY_OFFICER",
            "expires_at": None,
            "released_at": None,
            "created_at": now
        }
        _QUARANTINE_STORE[q_id] = q_data
        return QuarantinedEntityOut(**q_data)

    def release_quarantined_entity(
        self,
        quarantine_id: str,
        organization_id: Optional[str] = None
    ) -> QuarantinedEntityOut:
        """Release an entity from quarantine sandbox."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        q = _QUARANTINE_STORE.get(quarantine_id)
        if not q or q.get("organization_id") != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quarantined entity {quarantine_id} not found")

        q["status"] = "RELEASED"
        q["is_active"] = False
        q["released_at"] = datetime.now(timezone.utc)
        return QuarantinedEntityOut(**q)

    def evaluate_threat(
        self,
        request: ThreatEvaluationRequest
    ) -> ThreatEvaluationResponse:
        """Evaluate real-time threat risk and recommend zero-trust remediation action."""
        sev_val = request.severity.value if hasattr(request.severity, "value") else str(request.severity)
        risk_score, risk_tier = evaluate_threat_risk_score(
            severity=sev_val,
            event_count=request.event_count,
            failed_attempts=request.failed_attempts,
            is_privileged_account=request.is_privileged_account
        )

        if risk_tier == "CRITICAL":
            action = SecurityRemediationAction.QUARANTINE_IP
        elif risk_tier == "HIGH":
            action = SecurityRemediationAction.REVOKE_USER_SESSION
        elif risk_tier == "ELEVATED":
            action = SecurityRemediationAction.FORCE_MFA_CHALLENGE
        else:
            action = SecurityRemediationAction.LOG_AND_FLAG

        return ThreatEvaluationResponse(
            risk_score=risk_score,
            risk_tier=risk_tier,
            recommended_action=action
        )

    def evaluate_entropy(
        self,
        request: CredentialEntropyRequest
    ) -> CredentialEntropyResponse:
        """Calculate Shannon entropy and Zero-Trust credential compliance."""
        res = evaluate_credential_entropy(
            password_length=request.password_length,
            has_symbols=request.has_symbols,
            has_numbers=request.has_numbers,
            has_mixed_case=request.has_mixed_case
        )
        return CredentialEntropyResponse(
            password_length=res["password_length"],
            pool_size=res["pool_size"],
            entropy_bits=res["entropy_bits"],
            strength_rating=res["strength_rating"],
            is_zero_trust_compliant=res["is_zero_trust_compliant"]
        )

    def get_posture_metrics(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> SecurityPostureMetricsOut:
        """Calculate consolidated enterprise posture metrics across compliance and incidents."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        checks = [
            c for c in _CHECKS_STORE.values()
            if c.get("organization_id") == org_id and (
                property_id is None or c.get("property_id") is None or c.get("property_id") == property_id
            )
        ]
        incidents = [
            i for i in _INCIDENTS_STORE.values()
            if i.get("organization_id") == org_id and (
                property_id is None or i.get("property_id") is None or i.get("property_id") == property_id
            )
        ]
        quarantined = [
            q for q in _QUARANTINE_STORE.values()
            if q.get("organization_id") == org_id
        ]

        metrics = calculate_security_posture_metrics(checks, incidents, quarantined)
        return SecurityPostureMetricsOut(**metrics)


security_service = SecurityService()
