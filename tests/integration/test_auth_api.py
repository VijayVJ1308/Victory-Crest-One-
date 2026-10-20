"""Victory Crest One - Integration Tests for Authentication & User Endpoints
"""

from fastapi.testclient import TestClient


def test_login_success(api_client: TestClient):
    payload = {
        "username_or_email": "admin",
        "password": "AdminPassword123!"
    }
    response = api_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "System Administrator"


def test_login_invalid_password(api_client: TestClient):
    payload = {
        "username_or_email": "admin",
        "password": "WrongPassword!"
    }
    response = api_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_get_me_authenticated(api_client: TestClient):
    # 1. Login
    login_res = api_client.post("/api/v1/auth/login", json={"username_or_email": "hotel_gm", "password": "HotelPassword123!"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 2. Query /me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = api_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "hotel_gm"
    assert me_data["role"] == "Hotel Manager"


def test_get_me_unauthorized(api_client: TestClient):
    response = api_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_users_list_with_admin_token(api_client: TestClient):
    # Login as admin
    login_res = api_client.post("/api/v1/auth/login", json={"username_or_email": "admin", "password": "AdminPassword123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    users_res = api_client.get("/api/v1/users", headers=headers)
    assert users_res.status_code == 200
    users = users_res.json()
    assert len(users) >= 4
    usernames = [u["username"] for u in users]
    assert "admin" in usernames
    assert "hotel_gm" in usernames


def test_provision_user_with_admin_token(api_client: TestClient):
    login_res = api_client.post("/api/v1/auth/login", json={"username_or_email": "admin", "password": "AdminPassword123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    new_user = {
        "email": "sarah.finance@victorycrest.internal",
        "username": "sarah_finance",
        "password": "SarahPassword2026!",
        "full_name": "Sarah Jenkins",
        "role": "Finance Manager"
    }
    create_res = api_client.post("/api/v1/users", json=new_user, headers=headers)
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["username"] == "sarah_finance"
    assert created["role"] == "Finance Manager"

    # Authenticate as new user
    auth_check = api_client.post("/api/v1/auth/login", json={"username_or_email": "sarah_finance", "password": "SarahPassword2026!"})
    assert auth_check.status_code == 200


def test_audit_logs_endpoint(api_client: TestClient):
    login_res = api_client.post("/api/v1/auth/login", json={"username_or_email": "admin", "password": "AdminPassword123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    audit_res = api_client.get("/api/v1/audit/logs", headers=headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1
    actions = [l["action"] for l in logs]
    assert "LOGIN_SUCCESS" in actions or "USER_CREATED" in actions


def test_roles_endpoint(api_client: TestClient):
    roles_res = api_client.get("/api/v1/roles")
    assert roles_res.status_code == 200
    roles = roles_res.json()
    assert len(roles) >= 30
