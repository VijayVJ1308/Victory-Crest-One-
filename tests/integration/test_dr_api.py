"""Victory Crest One - Integration Tests for Multi-Cloud Resiliency & Autonomous DR REST API
Verifies endpoints for distributed standby nodes, node promotion, chaos failover drills,
replication lag evaluations, and disaster recovery telemetry.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_replica_nodes(client: TestClient):
    response = client.get("/api/v1/dr/nodes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4

    codes = [n["node_code"] for n in data]
    assert "NODE-AWS-MUMBAI" in codes
    assert "NODE-AZURE-CHENNAI" in codes
    assert "NODE-GCP-SINGAPORE" in codes
    assert "NODE-ONPREM-MADURAI" in codes


def test_register_replica_node(client: TestClient):
    new_node = {
        "node_code": "NODE-AWS-HYDERABAD",
        "name": "AWS South Asia Standby Zone 2",
        "provider": "AWS",
        "region": "ap-south-2 (Hyderabad)",
        "role": "HOT_STANDBY",
        "replication_mode": "SYNCHRONOUS",
        "health_status": "HEALTHY",
        "endpoint_url": "https://db-hyd.ap-south-2.aws.victorycrest.internal"
    }
    response = client.post("/api/v1/dr/nodes", json=new_node)
    assert response.status_code == 201
    created = response.json()
    assert created["node_code"] == "NODE-AWS-HYDERABAD"
    assert created["role"] == "HOT_STANDBY"


def test_promote_node_to_primary(client: TestClient):
    # Promote Azure node to primary
    response = client.post("/api/v1/dr/nodes/node_dr_1002/promote")
    assert response.status_code == 200
    promoted = response.json()
    assert promoted["id"] == "node_dr_1002"
    assert promoted["role"] == "PRIMARY"
    assert promoted["health_status"] == "HEALTHY"


def test_list_failover_drills(client: TestClient):
    response = client.get("/api/v1/dr/drills")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    codes = [d["drill_code"] for d in data]
    assert "DRILL-2026-001" in codes


def test_trigger_failover_drill(client: TestClient):
    payload = {
        "drill_type": "ZONE_OUTAGE",
        "target_primary_node": "NODE-AWS-MUMBAI",
        "promoted_standby_node": "NODE-AZURE-CHENNAI",
        "simulate_network_partition": True
    }
    response = client.post("/api/v1/dr/drills/trigger", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCEEDED"
    assert data["is_zero_rpo_achieved"] is True
    assert float(data["switchover_latency_seconds"]) > 0.0
    assert "succeeded" in data["summary"].lower()


def test_test_replication_lag(client: TestClient):
    payload = {
        "node_code": "NODE-AZURE-CHENNAI",
        "simulated_bytes_behind": 500,
        "packet_loss_percent": 0.0
    }
    response = client.post("/api/v1/dr/replication/test", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["node_code"] == "NODE-AZURE-CHENNAI"
    assert float(data["replication_lag_seconds"]) < 1.0
    assert data["lag_tier"] == "SYNCHRONIZED_ZERO_RPO"
    assert data["is_zero_rpo"] is True
    assert data["consensus_valid"] is True


def test_get_dr_resiliency_metrics(client: TestClient):
    response = client.get("/api/v1/dr/metrics")
    assert response.status_code == 200
    data = response.json()
    assert float(data["resiliency_score"]) >= 75.0
    assert "TIER_" in data["resiliency_tier"]
    assert data["total_nodes"] >= 4
    assert data["healthy_nodes"] >= 4
    assert data["is_zero_rpo_compliant"] is True
    assert "AWS" in data["providers_active"]
    assert "AZURE" in data["providers_active"]
