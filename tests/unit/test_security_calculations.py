"""Victory Crest One - Unit Tests for Zero-Trust Security & Compliance Auditor Calculations
"""

from decimal import Decimal
import pytest

from shared.calculations import (
    calculate_compliance_score,
    evaluate_threat_risk_score,
    evaluate_credential_entropy,
    calculate_security_posture_metrics,
)


def test_calculate_compliance_score_empty():
    res = calculate_compliance_score([])
    assert res["total_checks"] == 0
    assert res["compliant_count"] == 0
    assert res["overall_compliance_percent"] == Decimal("100.00")
    assert res["posture_rating"] == "AUDIT_READY_EXCELLENT"


def test_calculate_compliance_score_mixed():
    checks = [
        {"framework": "SOC2_TYPE_II", "status": "COMPLIANT"},
        {"framework": "SOC2_TYPE_II", "status": "COMPLIANT"},
        {"framework": "ISO_27001", "status": "WARNING"},
        {"framework": "GDPR_PRIVACY", "status": "NON_COMPLIANT"},
    ]
    res = calculate_compliance_score(checks)
    assert res["total_checks"] == 4
    assert res["compliant_count"] == 2
    assert res["warning_count"] == 1
    assert res["non_compliant_count"] == 1
    # 2 compliant (2.0) + 1 warning (0.5) = 2.5 / 4 = 62.50%
    assert res["overall_compliance_percent"] == Decimal("62.50")
    assert res["posture_rating"] == "ELEVATED_RISK"
    assert res["framework_scores"]["SOC2_TYPE_II"] == Decimal("100.00")
    assert res["framework_scores"]["ISO_27001"] == Decimal("50.00")
    assert res["framework_scores"]["GDPR_PRIVACY"] == Decimal("0.00")


def test_evaluate_threat_risk_score_tiers():
    # Low severity, single event
    score_low, tier_low = evaluate_threat_risk_score(severity="LOW", event_count=1, failed_attempts=0)
    assert tier_low == "LOW"
    assert score_low < Decimal("35.00")

    # Critical severity + failed attempts + privileged account
    score_crit, tier_crit = evaluate_threat_risk_score(
        severity="CRITICAL",
        event_count=5,
        failed_attempts=4,
        is_privileged_account=True
    )
    # 50.0 + min(25.0, 12.5) + min(20.0, 16.0) + 15.0 = 50 + 12.5 + 16 + 15 = 93.50
    assert score_crit == Decimal("93.50")
    assert tier_crit == "CRITICAL"


def test_evaluate_credential_entropy():
    # Short / empty
    empty_res = evaluate_credential_entropy(0)
    assert empty_res["entropy_bits"] == Decimal("0.00")
    assert empty_res["is_zero_trust_compliant"] is False
    assert empty_res["strength_rating"] == "WEAK_VULNERABLE"

    # 8-char lowercase only: 8 * log2(26) = ~37.6 bits
    weak_res = evaluate_credential_entropy(8, has_symbols=False, has_numbers=False, has_mixed_case=False)
    assert weak_res["entropy_bits"] < Decimal("40.00")
    assert weak_res["strength_rating"] == "WEAK_VULNERABLE"
    assert weak_res["is_zero_trust_compliant"] is False

    # 16-char full zero-trust compliant: 52 + 10 + 32 = 94 pool size. 16 * log2(94) = ~104.87 bits
    strong_res = evaluate_credential_entropy(16, has_symbols=True, has_numbers=True, has_mixed_case=True)
    assert strong_res["entropy_bits"] > Decimal("80.00")
    assert strong_res["strength_rating"] == "MILITARY_GRADE"
    assert strong_res["is_zero_trust_compliant"] is True


def test_calculate_security_posture_metrics():
    compliance_checks = [
        {"framework": "SOC2_TYPE_II", "status": "COMPLIANT"},
        {"framework": "ISO_27001", "status": "COMPLIANT"},
        {"framework": "GDPR_PRIVACY", "status": "COMPLIANT"},
        {"framework": "PCI_DSS_V4", "status": "WARNING"},
    ]
    # Compliance = (3 + 0.5) / 4 = 87.50%
    incidents = [
        {"severity": "CRITICAL", "status": "INVESTIGATING", "is_resolved": False},
        {"severity": "HIGH", "status": "CONTAINED", "is_resolved": False},
        {"severity": "LOW", "status": "RESOLVED", "is_resolved": True},
    ]
    # Penalties: 1 critical (5.0) + 1 high (2.0) = 7.00
    quarantined = [
        {"status": "ACTIVE", "is_active": True},
        {"status": "RELEASED", "is_active": False},
    ]

    metrics = calculate_security_posture_metrics(compliance_checks, incidents, quarantined)
    assert metrics["total_controls_audited"] == 4
    assert metrics["overall_compliance_percent"] == Decimal("87.50")
    # Enterprise posture = 87.50 - 7.00 = 80.50
    assert metrics["enterprise_posture_score"] == Decimal("80.50")
    assert metrics["posture_grade"] == "B - COMPLIANT_STABLE"
    assert metrics["open_incidents_count"] == 2
    assert metrics["critical_threats_count"] == 1
    assert metrics["quarantined_actors_count"] == 1
