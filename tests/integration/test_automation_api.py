"""Victory Crest One - Integration Tests for Workflow Automation REST API
Verifies endpoints for listing rules, creating/updating workflows, status toggling,
cross-module event dispatching, execution logs, and performance telemetry.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)



def test_list_workflow_rules(client: TestClient):
    response = client.get("/api/v1/automation/rules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5

    rule_codes = [r["code"] for r in data]
    assert "WF-1001" in rule_codes
    assert "WF-1002" in rule_codes
    assert "WF-1003" in rule_codes


def test_get_workflow_rule_by_id_and_not_found(client: TestClient):
    response = client.get("/api/v1/automation/rules/wf_rule_1001")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "WF-1001"
    assert data["trigger_event"] == "inventory.stock_level_low"
    assert len(data["actions"]) >= 1

    # 404 for non-existent
    bad_res = client.get("/api/v1/automation/rules/non_existent_wf")
    assert bad_res.status_code == 404


def test_create_and_update_workflow_rule(client: TestClient):
    payload = {
        "name": "High Value Dining Table Folio Alert",
        "description": "Alert restaurant manager when restaurant dining table order exceeds ₹10,000.",
        "trigger_type": "THRESHOLD",
        "trigger_event": "restaurant.order_created",
        "conditions": [
            {"field": "bill_amount", "operator": "GREATER_THAN", "value": 10000}
        ],
        "actions": [
            {"action_type": "SEND_NOTIFICATION", "parameters": {"title": "VIP Dining Bill", "recipient_role": "Restaurant Manager"}}
        ],
        "status": "ACTIVE"
    }
    create_res = client.post("/api/v1/automation/rules", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["name"] == payload["name"]
    rule_id = created_data["id"]

    # Update rule
    update_res = client.put(f"/api/v1/automation/rules/{rule_id}", json={
        "name": "Updated High Value Dining Alert",
        "status": "PAUSED"
    })
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["name"] == "Updated High Value Dining Alert"
    assert updated_data["status"] == "PAUSED"
    assert updated_data["is_active"] is False


def test_toggle_workflow_rule(client: TestClient):
    # Toggle WF-1006 which is initially PAUSED
    response = client.post("/api/v1/automation/rules/wf_rule_1006/toggle")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"
    assert data["is_active"] is True

    # Toggle back to PAUSED
    response2 = client.post("/api/v1/automation/rules/wf_rule_1006/toggle")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["status"] == "PAUSED"
    assert data2["is_active"] is False


def test_dispatch_event_condition_matched(client: TestClient):
    # WF-1001 listens to inventory.stock_level_low with condition current_stock <= 15
    dispatch_payload = {
        "event": "inventory.stock_level_low",
        "payload": {
            "item_code": "SKU-TEST-01",
            "current_stock": 5,
            "reorder_point": 15
        }
    }
    response = client.post("/api/v1/automation/dispatch", json=dispatch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == "inventory.stock_level_low"
    assert data["matched_rules_count"] >= 1
    assert data["executed_rules_count"] >= 1

    success_results = [r for r in data["results"] if r["status"] == "SUCCESS"]
    assert len(success_results) >= 1
    assert len(success_results[0]["actions_executed"]) >= 1


def test_dispatch_event_condition_skipped(client: TestClient):
    # Stock level 50 does NOT trigger reorder condition (<= 15)
    dispatch_payload = {
        "event": "inventory.stock_level_low",
        "payload": {
            "item_code": "SKU-SURPLUS-01",
            "current_stock": 50,
            "reorder_point": 15
        }
    }
    response = client.post("/api/v1/automation/dispatch", json=dispatch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["matched_rules_count"] >= 1
    skipped_results = [r for r in data["results"] if r["status"] == "SKIPPED"]
    assert len(skipped_results) >= 1


def test_get_execution_logs_and_telemetry(client: TestClient):
    logs_res = client.get("/api/v1/automation/logs?limit=10")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1
    assert "status" in logs[0]
    assert "duration_ms" in logs[0]

    telemetry_res = client.get("/api/v1/automation/telemetry")
    assert telemetry_res.status_code == 200
    telem = telemetry_res.json()
    assert telem["total_rules"] >= 5
    assert telem["active_rules"] >= 4
    assert telem["total_executions"] >= 1
    assert "success_rate_percent" in telem
    assert float(telem["success_rate_percent"]) >= 0.0
