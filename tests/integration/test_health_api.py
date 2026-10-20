"""Victory Crest One - Integration Tests for Health & Base Endpoints
"""

from fastapi.testclient import TestClient


def test_root_endpoint(api_client: TestClient):
    response = api_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Victory Crest" in data["product"]
    assert "api_docs" in data
    assert "health_endpoint" in data


def test_quick_health_endpoint(api_client: TestClient):
    response = api_client.get("/api/v1/health/quick")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["healthy"] is True


def test_full_health_endpoint(api_client: TestClient):
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "database" in data
    assert "offline_sync_available" in data
    assert "diagnostics" in data
    # Database object checks
    db = data["database"]
    assert "status" in db
    assert "engine" in db
    assert "is_connected" in db


def test_modules_catalog_endpoint(api_client: TestClient):
    response = api_client.get("/api/v1/modules")
    assert response.status_code == 200
    modules = response.json()
    assert isinstance(modules, list)
    assert len(modules) >= 15
    for m in modules:
        assert "id" in m
        assert "name" in m
        assert "category" in m
        assert "phase" in m


def test_organizations_endpoint(api_client: TestClient):
    response = api_client.get("/api/v1/organizations")
    assert response.status_code == 200
    orgs = response.json()
    assert isinstance(orgs, list)
    assert len(orgs) >= 1
    first_org = orgs[0]
    assert "id" in first_org
    assert "properties" in first_org
    assert len(first_org["properties"]) >= 3
