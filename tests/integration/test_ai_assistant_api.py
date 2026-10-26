"""Victory Crest One - Integration Tests for AI Business Assistant REST API
Verifies natural language inquiry endpoint, semantic synthesis, RBAC masking,
conversation thread retrieval, and operational telemetry.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_ai_query_occupancy(client: TestClient):
    payload = {
        "prompt": "What is our current hotel room occupancy rate and ADR?",
        "user_role": "General Manager"
    }
    response = client.post("/api/v1/ai/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["intent"] == "OCCUPANCY_STATUS"
    assert data["safety_rating"] == "SAFE"
    assert "78.4%" in data["response_text"]
    assert "structured_data" in data
    assert data["structured_data"] is not None
    assert "metric_cards" in data["structured_data"]
    assert len(data["suggested_followups"]) >= 1


def test_ai_query_financial_executive(client: TestClient):
    payload = {
        "prompt": "Summarize our quarterly EBITDA, GOP margin, and liquid cash balance.",
        "user_role": "General Manager"
    }
    response = client.post("/api/v1/ai/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["intent"] == "FINANCIAL_HEALTH"
    assert data["safety_rating"] == "SAFE"
    assert "₹9,850,000.00" in data["response_text"]


def test_ai_query_financial_operational_masked(client: TestClient):
    payload = {
        "prompt": "What is our operating EBITDA and cash balance?",
        "user_role": "POS Cashier"
    }
    response = client.post("/api/v1/ai/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["intent"] == "FINANCIAL_HEALTH"
    assert data["safety_rating"] == "CONFIDENTIAL_RESTRICTED"
    assert "restricted for role `POS Cashier`" in data["response_text"]
    masked = data["structured_data"]["masked_fields"]
    assert "[CONFIDENTIAL" in masked["ebitda"]
    assert "[CONFIDENTIAL" in masked["cash_balance"]


def test_list_conversation_threads_and_messages(client: TestClient):
    threads_res = client.get("/api/v1/ai/threads")
    assert threads_res.status_code == 200
    threads = threads_res.json()
    assert isinstance(threads, list)
    assert len(threads) >= 1

    t_id = threads[0]["id"]
    msgs_res = client.get(f"/api/v1/ai/threads/{t_id}/messages")
    assert msgs_res.status_code == 200
    msgs = msgs_res.json()
    assert isinstance(msgs, list)
    assert len(msgs) >= 1
    assert "role" in msgs[0]
    assert "content" in msgs[0]


def test_ai_telemetry_and_reset(client: TestClient):
    telem_res = client.get("/api/v1/ai/telemetry")
    assert telem_res.status_code == 200
    telem = telem_res.json()
    assert telem["total_queries"] >= 1
    assert "intent_distribution" in telem
    assert float(telem["safe_queries_percent"]) >= 0.0

    reset_res = client.post("/api/v1/ai/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"
