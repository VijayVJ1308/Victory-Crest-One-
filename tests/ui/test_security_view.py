"""Victory Crest One - Desktop UI Tests for Zero-Trust Security & Compliance Auditor View
Verifies initialization, metric cards, continuous compliance table,
threat anomaly stream, quarantine sandbox, and MainWindow stack navigation at index 21.
"""

import pytest
from desktop.ui.views.security_view import SecurityGovernanceView
from desktop.ui.main_window import MainWindow


def test_security_view_initialization(qapp):
    view = SecurityGovernanceView()
    assert view is not None

    # Check 4 metric cards
    assert view.card_posture is not None
    assert view.card_controls is not None
    assert view.card_threats is not None
    assert view.card_quarantine is not None

    # Check 3 tabs
    assert view.tab_widget.count() == 3

    # Check compliance controls table (active property Madurai has 6 controls, enterprise has >= 10)
    assert view.table_checks.rowCount() >= 6
    assert len(view.cached_checks) >= 6

    # Check threat incidents table (Madurai has 2 incidents, enterprise has >= 3)
    assert view.table_incidents.rowCount() >= 2

    # Check quarantine table
    assert view.table_quarantine.rowCount() >= 2


def test_security_view_simulators(qapp):
    view = SecurityGovernanceView()

    # Test threat simulation
    view.sim_sev.setCurrentText("CRITICAL")
    view.sim_events.setValue(5)
    view.sim_fails.setValue(3)
    view.sim_priv.setChecked(True)
    view.calculate_simulated_threat()

    threat_text = view.lbl_threat_res.text()
    assert "Risk:" in threat_text
    assert "Tier: CRITICAL" in threat_text
    assert "Action: QUARANTINE_IP" in threat_text

    # Test credential entropy evaluation
    view.ent_len.setValue(16)
    view.ent_symbols.setChecked(True)
    view.ent_numbers.setChecked(True)
    view.ent_mixed.setChecked(True)
    view.calculate_simulated_entropy()

    entropy_text = view.lbl_entropy_res.text()
    assert "Entropy:" in entropy_text
    assert "bits" in entropy_text
    assert "MILITARY_GRADE" in entropy_text
    assert "Zero-Trust" in entropy_text


def test_main_window_security_navigation(qapp):
    window = MainWindow()
    assert "cybersecurity_governance" in window.nav_buttons

    window.navigate_to("cybersecurity_governance")
    assert window.view_stack.currentIndex() == 21
    assert window.current_nav_key == "cybersecurity_governance"
    assert window.security_view is not None
