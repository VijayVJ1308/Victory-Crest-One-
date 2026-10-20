"""Victory Crest One - Integration Tests for Sales CRM & Revenue Pipeline API
Tests Leads CRUD, Lead Conversion, Deal Pipeline Stages, Quote to Invoice Conversion, and Metrics.
"""

from decimal import Decimal
from fastapi.testclient import TestClient


def _get_admin_token(api_client: TestClient) -> str:
    res = api_client.post("/api/v1/auth/login", json={"username_or_email": "admin", "password": "AdminPassword123!"})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_list_and_create_leads(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List seeded leads
    res = api_client.get("/api/v1/crm/leads", headers=headers)
    assert res.status_code == 200
    leads = res.json()
    assert len(leads) >= 3

    # 2. Create lead
    new_lead = {
        "first_name": "Siddharth",
        "last_name": "Mehra",
        "company_name": "Mehra Global Exports",
        "email": "siddharth@mehraglobal.com",
        "phone": "+91 99112 33445",
        "lead_source": "WEBSITE",
        "lead_score": 80,
        "estimated_budget": "500000.00",
        "assigned_rep_name": "Vikram Sharma"
    }
    c_res = api_client.post("/api/v1/crm/leads", json=new_lead, headers=headers)
    assert c_res.status_code == 201
    created = c_res.json()
    assert created["first_name"] == "Siddharth"
    assert created["company_name"] == "Mehra Global Exports"
    assert created["status"] == "NEW"


def test_lead_conversion_workflow(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a qualified lead
    lead_data = {
        "first_name": "Sunita",
        "last_name": "Rao",
        "company_name": "Rao Biotech Innovations",
        "email": "sunita.rao@raobiotech.in",
        "lead_source": "REFERRAL",
        "lead_score": 90,
        "estimated_budget": "1200000.00"
    }
    lead_res = api_client.post("/api/v1/crm/leads", json=lead_data, headers=headers)
    assert lead_res.status_code == 201
    lead_id = lead_res.json()["id"]

    # 2. Convert lead to Deal & Customer
    conv_req = {
        "deal_name": "Rao Biotech Annual Conclave",
        "estimated_amount": "1200000.00"
    }
    conv_res = api_client.post(f"/api/v1/crm/leads/{lead_id}/convert", json=conv_req, headers=headers)
    assert conv_res.status_code == 200
    conv = conv_res.json()
    assert conv["status"] == "CONVERTED"
    assert conv["customer_id"] is not None
    assert conv["deal_id"] is not None

    # Verify deal exists in pipeline
    deal_res = api_client.get(f"/api/v1/crm/deals/{conv['deal_id']}", headers=headers)
    assert deal_res.status_code == 200
    deal = deal_res.json()
    assert deal["deal_name"] == "Rao Biotech Annual Conclave"
    assert deal["stage"] == "QUALIFICATION"
    assert Decimal(str(deal["amount"])) == Decimal("1200000.00")


def test_deal_stage_advancement_and_probability(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Deal
    deal_data = {
        "deal_name": "Titan Corporate Gala Night",
        "customer_id": "cust_reliance_corp",
        "customer_name": "Tata Global Technologies Ltd",
        "stage": "QUALIFICATION",
        "amount": "500000.00",
        "expected_close_date": "2026-11-30T00:00:00"
    }
    create_res = api_client.post("/api/v1/crm/deals", json=deal_data, headers=headers)
    assert create_res.status_code == 201
    deal = create_res.json()
    deal_id = deal["id"]
    assert deal["probability_percent"] == 10
    assert Decimal(str(deal["weighted_amount"])) == Decimal("50000.00")

    # 2. Advance to Proposal stage
    stage_res = api_client.patch(
        f"/api/v1/crm/deals/{deal_id}/stage",
        json={"stage": "PROPOSAL", "notes": "Sent customized banquet and suite proposal."},
        headers=headers
    )
    assert stage_res.status_code == 200
    updated = stage_res.json()
    assert updated["stage"] == "PROPOSAL"
    assert updated["probability_percent"] == 60
    assert Decimal(str(updated["weighted_amount"])) == Decimal("300000.00")

    # 3. Mark Closed Won
    won_res = api_client.patch(
        f"/api/v1/crm/deals/{deal_id}/stage",
        json={"stage": "CLOSED_WON"},
        headers=headers
    )
    assert won_res.status_code == 200
    won = won_res.json()
    assert won["stage"] == "CLOSED_WON"
    assert won["probability_percent"] == 100
    assert Decimal(str(won["weighted_amount"])) == Decimal("500000.00")
    assert won["closed_at"] is not None


def test_quote_creation_and_invoice_conversion(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Quote
    quote_data = {
        "customer_id": "cust_reliance_corp",
        "customer_name": "Tata Global Technologies Ltd",
        "valid_until": "2026-11-30T00:00:00",
        "tax_rate_percent": "18.00",
        "notes": "Exclusive resort retreat quote",
        "lines": [
            {"description": "Executive Suites (2 Nights)", "quantity": "2.00", "unit_price": "25000.00"}
        ]
    }
    q_res = api_client.post("/api/v1/crm/quotes", json=quote_data, headers=headers)
    assert q_res.status_code == 201
    quote = q_res.json()
    assert quote["status"] == "SENT"
    assert Decimal(str(quote["subtotal"])) == Decimal("50000.00")
    assert Decimal(str(quote["tax_amount"])) == Decimal("9000.00")
    assert Decimal(str(quote["total_amount"])) == Decimal("59000.00")
    quote_id = quote["id"]

    # 2. Convert Quote directly to Finance AR Customer Invoice!
    conv_res = api_client.post(f"/api/v1/crm/quotes/{quote_id}/convert-invoice", headers=headers)
    assert conv_res.status_code == 200
    conv = conv_res.json()
    assert conv["status"] == "CONVERTED"
    assert conv["invoice_id"] is not None
    assert "INV-" in conv["invoice_number"]

    # 3. Verify created invoice in Finance AR
    inv_res = api_client.get(f"/api/v1/finance/invoices/{conv['invoice_id']}", headers=headers)
    assert inv_res.status_code == 200
    inv = inv_res.json()
    assert inv["invoice_number"] == conv["invoice_number"]
    assert Decimal(str(inv["total_amount"])) == Decimal("59000.00")
    assert inv["journal_entry_id"] is not None


def test_pipeline_metrics_forecasting(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    res = api_client.get("/api/v1/crm/metrics", headers=headers)
    assert res.status_code == 200
    m = res.json()
    assert Decimal(str(m["total_active_pipeline_value"])) > Decimal("0.00")
    assert Decimal(str(m["weighted_forecast_value"])) > Decimal("0.00")
    assert "win_rate_percentage" in m
    assert len(m["stages"]) >= 6
