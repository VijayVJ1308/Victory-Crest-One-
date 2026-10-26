"""Victory Crest One - Integration Tests for Zero-Trust Security & Compliance Auditor REST API
Verifies endpoints for compliance audits, threat incidents, active quarantine sandboxes,
credential entropy evaluation, and security posture metrics.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_compliance_checks(client: TestClient):
    response = client.get("/api/v1/security/compliance/checks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 10

    codes = [chk["control_code"] for chk in data]
    assert "SOC2-CC6.1" in codes
    assert "ISO27001-A12.1" in codes
    assert "GDPR-ART32" in codes
    assert "PCI-REQ3" in codes


def test_trigger_compliance_scan(client: TestClient):
    payload = {"framework": "SOC2_TYPE_II"}
    response = client.post("/api/v1/security/compliance/scan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scanned_controls_count"] >= 3
    assert data["compliant_count"] >= 3
    assert float(data["overall_compliance_percent"]) >= 90.0
    assert data["posture_rating"] == "AUDIT_READY_EXCELLENT"


def test_list_security_incidents(client: TestClient):
    response = client.get("/api/v1/security/incidents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    event_codes = [inc["event_code"] for inc in data]
    assert "SEC-2026-001" in event_codes
    assert "SEC-2026-002" in event_codes


def test_record_and_resolve_security_incident(client: TestClient):
    new_incident = {
        "event_code": "SEC-2026-TEST-99",
        "event_type": "DATA_EXFILTRATION_PATTERN",
        "severity": "CRITICAL",
        "source_ip": "192.0.2.144",
        "actor_identity": "admin_test_compromised",
        "target_resource": "/api/v1/finance/ledgers",
        "risk_score": 85.00,
        "details": "Abnormal volume of bulk export calls outside business hours.",
        "recommended_action": "QUARANTINE_IP"
    }
    create_res = client.post("/api/v1/security/incidents", json=new_incident)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["event_code"] == "SEC-2026-TEST-99"
    assert created["is_resolved"] is False
    inc_id = created["id"]

    # Resolve incident
    resolve_res = client.post(
        f"/api/v1/security/incidents/{inc_id}/resolve",
        json={
            "resolution_notes": "Host quarantined, token invalidated, and firewall rule pushed.",
            "remediation_action": "QUARANTINE_IP"
        }
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()
    assert resolved["is_resolved"] is True
    assert resolved["status"] == "RESOLVED"
    assert "Host quarantined" in resolved["resolution_notes"]


def test_quarantine_sandbox_workflow(client: TestClient):
    # 1. List active quarantine
    list_res = client.get("/api/v1/security/quarantine?is_active=true")
    assert list_res.status_code == 200
    initial_items = list_res.json()
    assert len(initial_items) >= 2

    # 2. Add entity to quarantine
    quar_req = {
        "entity_id_or_ip": "203.0.113.99",
        "entity_type": "IP_ADDRESS",
        "reason": "Repeated unauthorized probes on admin gateway.",
        "incident_event_code": "SEC-2026-TEST-99",
        "quarantined_by": "SECOPS_TEAM"
    }
    quar_res = client.post("/api/v1/security/quarantine", json=quar_req)
    assert quar_res.status_code == 201
    quar_created = quar_res.json()
    assert quar_created["entity_id_or_ip"] == "203.0.113.99"
    assert quar_created["is_active"] is True
    q_id = quar_created["id"]

    # 3. Release entity from quarantine
    rel_res = client.delete(f"/api/v1/security/quarantine/{q_id}")
    assert rel_res.status_code == 200
    quar_released = rel_res.json()
    assert quar_released["is_active"] is False
    assert quar_released["status"] == "RELEASED"


def test_threat_evaluation_endpoint(client: TestClient):
    req_body = {
        "severity": "CRITICAL",
        "event_count": 6,
        "failed_attempts": 4,
        "is_privileged_account": True
    }
    response = client.post("/api/v1/security/threat/evaluate", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert float(data["risk_score"]) >= 80.0
    assert data["risk_tier"] == "CRITICAL"
    assert data["recommended_action"] == "QUARANTINE_IP"


def test_credential_entropy_endpoint(client: TestClient):
    req_body = {
        "password_length": 16,
        "has_symbols": True,
        "has_numbers": True,
        "has_mixed_case": True
    }
    response = client.post("/api/v1/security/credentials/entropy", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert data["password_length"] == 16
    assert float(data["entropy_bits"]) > 80.0
    assert data["strength_rating"] == "MILITARY_GRADE"
    assert data["is_zero_trust_compliant"] is True


def test_get_security_posture_metrics(client: TestClient):
    response = client.get("/api/v1/security/metrics")
    assert response.status_code == 200
    data = response.json()
    assert float(data["enterprise_posture_score"]) > 0.0
    assert "posture_grade" in data
    assert data["total_controls_audited"] >= 10
    assert "framework_scores" in data
    assert "SOC2_TYPE_II" in data["framework_scores"]
