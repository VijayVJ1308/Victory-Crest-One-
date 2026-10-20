"""Victory Crest One - Integration Tests for Master Data & Shared Business Services
"""

from fastapi.testclient import TestClient


def _get_admin_token(api_client: TestClient) -> str:
    res = api_client.post("/api/v1/auth/login", json={"username_or_email": "admin", "password": "AdminPassword123!"})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_customers_crud_and_deduplication(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List customers
    res = api_client.get("/api/v1/customers", headers=headers)
    assert res.status_code == 200
    customers = res.json()
    assert len(customers) >= 2
    codes = [c["code"] for c in customers]
    assert "CUST-CORP-001" in codes

    # 2. Create customer
    new_cust = {
        "code": "CUST-HOTEL-999",
        "name": "Rajeshwari Varma",
        "customer_type": "INDIVIDUAL",
        "email": "rajeshwari@varma.in",
        "phone": "+91 99887 76655",
        "credit_limit": "25000.00"
    }
    create_res = api_client.post("/api/v1/customers", json=new_cust, headers=headers)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["code"] == "CUST-HOTEL-999"
    assert created["name"] == "Rajeshwari Varma"

    # 3. Deduplication rejection on duplicate email
    dup_res = api_client.post("/api/v1/customers", json={
        "code": "CUST-DUP-001",
        "name": "Duplicate Attempt",
        "email": "rajeshwari@varma.in",
        "phone": "+91 11111 22222"
    }, headers=headers)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]


def test_suppliers_endpoints(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # List suppliers
    res = api_client.get("/api/v1/suppliers", headers=headers)
    assert res.status_code == 200
    suppliers = res.json()
    assert len(suppliers) >= 2

    # Create supplier
    new_supp = {
        "code": "SUPP-TECH-888",
        "name": "Apex Enterprise Network Solutions",
        "contact_person": "K. Venkatesh",
        "email": "support@apexnet.in",
        "payment_terms_days": 45,
        "lead_time_days": 7
    }
    create_res = api_client.post("/api/v1/suppliers", json=new_supp, headers=headers)
    assert create_res.status_code == 201
    assert create_res.json()["code"] == "SUPP-TECH-888"


def test_products_endpoints(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # List products
    res = api_client.get("/api/v1/products", headers=headers)
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 4

    # Create product
    new_prod = {
        "sku": "ITEM-RETAIL-COFFEE-01",
        "name": "Madurai Peaberry Roast (500g)",
        "category": "Retail Merchandise",
        "item_type": "PHYSICAL",
        "unit_of_measure": "UNIT",
        "unit_price": "650.00",
        "cost_price": "280.00",
        "tax_rate_percent": "5.00"
    }
    create_res = api_client.post("/api/v1/products", json=new_prod, headers=headers)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["sku"] == "ITEM-RETAIL-COFFEE-01"


def test_documents_vault_endpoints(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # List documents
    res = api_client.get("/api/v1/documents", headers=headers)
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 1

    # Register document
    reg_res = api_client.post("/api/v1/documents/register", json={
        "file_name": "executive_board_minutes_2026.pdf",
        "category": "REPORT",
        "linked_entity_type": "Organization",
        "linked_entity_id": "org_victory_crest_group"
    }, headers=headers)
    assert reg_res.status_code == 201
    assert reg_res.json()["file_name"] == "executive_board_minutes_2026.pdf"


def test_notifications_endpoints(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # Check unread count
    cnt_res = api_client.get("/api/v1/notifications/unread-count", headers=headers)
    assert cnt_res.status_code == 200
    initial_unread = cnt_res.json()["unread_count"]
    assert initial_unread >= 1

    # List notifications
    res = api_client.get("/api/v1/notifications", headers=headers)
    assert res.status_code == 200
    notifs = res.json()
    assert len(notifs) >= 2

    # Mark first notification as read
    target_id = notifs[0]["id"]
    read_res = api_client.post(f"/api/v1/notifications/{target_id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["success"] is True
