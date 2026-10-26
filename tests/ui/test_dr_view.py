"""Victory Crest One - Desktop UI Tests for Multi-Cloud Resiliency & Autonomous DR View
Verifies initialization, metric cards, replica nodes table, chaos drills log,
cross-cloud replication stream diagnostics, failover simulation, and MainWindow navigation at index 22.
"""

import pytest
from PySide6.QtWidgets import QMessageBox
from desktop.ui.views.dr_view import MultiCloudDrView
from desktop.ui.main_window import MainWindow
from shared.enums import CloudProvider, NodeRole, FailoverDrillStatus


def test_dr_view_initialization(qapp):
    view = MultiCloudDrView()
    assert view is not None

    # Check 4 KPI metric cards
    assert view.card_resiliency is not None
    assert view.card_availability is not None
    assert view.card_lag is not None
    assert view.card_rto is not None

    # Check 3 tabs
    assert view.tab_widget.count() == 3
    assert "Multi-Cloud Standby Cluster" in view.tab_widget.tabText(0)
    assert "Autonomous Chaos Drills" in view.tab_widget.tabText(1)
    assert "DR Simulator" in view.tab_widget.tabText(2)

    # Check nodes table (Madurai scoped: AWS Mumbai, Azure Central India, On-Prem Madurai + GCP Org-wide)
    assert view.table_nodes.rowCount() >= 4
    assert len(view.cached_nodes) >= 4

    # Check drills table
    assert view.table_drills.rowCount() >= 2
    assert len(view.cached_drills) >= 2

    # Check node selection updates detail text
    view.table_nodes.selectRow(0)
    details = view.txt_node_details.toPlainText()
    assert "Node Identifier:" in details
    assert "Cloud Provider:" in details

    # Check drill selection updates execution log
    view.table_drills.selectRow(0)
    log_text = view.txt_drill_log.toPlainText()
    assert len(log_text) > 0


def test_dr_view_filtering(qapp):
    view = MultiCloudDrView()

    # Filter by provider: AWS
    aws_idx = view.combo_prov_filter.findData("AWS")
    if aws_idx >= 0:
        view.combo_prov_filter.setCurrentIndex(aws_idx)
        assert view.table_nodes.rowCount() >= 1
        for row in range(view.table_nodes.rowCount()):
            assert view.table_nodes.item(row, 1).text() == "AWS"

    # Reset provider filter
    view.combo_prov_filter.setCurrentIndex(0)
    assert view.table_nodes.rowCount() >= 4

    # Filter by role: PRIMARY
    pri_idx = view.combo_role_filter.findData("PRIMARY")
    if pri_idx >= 0:
        view.combo_role_filter.setCurrentIndex(pri_idx)
        assert view.table_nodes.rowCount() == 1
        assert view.table_nodes.item(0, 3).text() == "PRIMARY"

    # Reset role filter
    view.combo_role_filter.setCurrentIndex(0)
    assert view.table_nodes.rowCount() >= 4

    # Search filter
    view.txt_node_search.setText("aws")
    assert view.table_nodes.rowCount() >= 1
    view.txt_node_search.setText("")
    assert view.table_nodes.rowCount() >= 4

    # Filter drills table by status
    succeeded_idx = view.combo_drill_status.findData("SUCCEEDED")
    if succeeded_idx >= 0:
        view.combo_drill_status.setCurrentIndex(succeeded_idx)
        assert view.table_drills.rowCount() >= 1


def test_dr_view_simulators(qapp, monkeypatch):
    view = MultiCloudDrView()

    # Test live replication lag diagnostics
    view.sim_lag_node.setCurrentIndex(0)
    view.sim_bytes_behind.setValue(100)
    view.sim_packet_loss.setValue(0.0)
    view.run_simulated_lag_test()

    lag_text = view.lbl_lag_diag.text()
    assert "Lag:" in lag_text
    assert "Tier:" in lag_text
    assert "Zero-RPO:" in lag_text
    assert "Quorum:" in lag_text

    # Test instant chaos failover drill simulation with QMessageBox suppressed
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    view.sim_scenario.setCurrentIndex(0)
    view.run_simulated_failover()

    failover_text = view.lbl_failover_out.text()
    assert "RTO:" in failover_text
    assert "RPO:" in failover_text
    assert "Status: SUCCEEDED" in failover_text


def test_main_window_dr_navigation(qapp):
    window = MainWindow()
    assert "multi_cloud_dr" in window.nav_buttons

    window.navigate_to("multi_cloud_dr")
    assert window.view_stack.currentIndex() == 22
    assert window.current_nav_key == "multi_cloud_dr"
    assert window.dr_view is not None
