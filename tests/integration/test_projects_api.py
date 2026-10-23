"""Victory Crest One - Integration Tests for Project Management & PSA REST API
Tests Projects CRUD, Milestones, WBS Tasks, Timesheets, Expenses,
and automated milestone customer invoicing with GL revenue posting.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_list_projects():
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) >= 3
    codes = [p["project_code"] for p in projects]
    assert "PRJ-2026-001" in codes
    assert "PRJ-2026-002" in codes
    assert "PRJ-2026-003" in codes


def test_create_project_with_milestones_and_tasks():
    payload = {
        "project_code": "PRJ-TEST-001",
        "name": "Luxury Penthouse Interior Renovation",
        "description": "High-end bespoke cabinetry and smart lighting integration.",
        "customer_name": "Prestige Horizon Estates",
        "project_manager_name": "Meera Krishnan",
        "billing_type": "MILESTONE_BASED",
        "status": "ACTIVE",
        "priority": "HIGH",
        "start_date": "2026-11-01",
        "end_date": "2026-12-15",
        "budget_amount": "800000.00",
        "milestones": [
            {
                "title": "M1: Interior Architecture Signoff",
                "description": "3D renderings and material boards approved.",
                "milestone_amount": "300000.00",
                "due_date": "2026-11-15",
                "status": "PENDING"
            }
        ],
        "tasks": [
            {
                "task_code": "TSK-TEST-1",
                "title": "Draft CAD Joinery Plans",
                "description": "Teak closet joinery drawings.",
                "assigned_to_name": "Karthik Raja",
                "estimated_hours": "16.00",
                "actual_hours": "0.00",
                "status": "TODO",
                "priority": "NORMAL",
                "due_date": "2026-11-05"
            }
        ]
    }
    response = client.post("/api/v1/projects", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_code"] == "PRJ-TEST-001"
    assert len(data["milestones"]) == 1
    assert len(data["tasks"]) == 1
    assert Decimal(str(data["budget_amount"])) == Decimal("800000.00")


def test_mark_milestone_achieved_and_invoice_gl():
    # 1. Fetch project 1
    response = client.get("/api/v1/projects")
    p1 = next(p for p in response.json() if p["project_code"] == "PRJ-2026-001")
    p1_id = p1["id"]

    # 2. Add a new milestone
    ms_payload = {
        "title": "Test Milestone for Billing",
        "description": "Verification of milestone invoice generation",
        "milestone_amount": "100000.00",
        "due_date": "2026-11-10",
        "status": "PENDING"
    }
    ms_create_res = client.post(f"/api/v1/projects/{p1_id}/milestones", json=ms_payload)
    assert ms_create_res.status_code == 200
    ms_id = ms_create_res.json()["id"]

    # 3. Mark milestone achieved
    achieve_res = client.post(f"/api/v1/projects/{p1_id}/milestones/{ms_id}/achieve")
    assert achieve_res.status_code == 200
    assert achieve_res.json()["status"] == "ACHIEVED"

    # 4. Invoice milestone with 18% GST
    inv_payload = {
        "tax_percent": "18.00",
        "due_days": 30,
        "notes": "Milestone achieved on schedule."
    }
    inv_res = client.post(f"/api/v1/projects/{p1_id}/milestones/{ms_id}/invoice", json=inv_payload)
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert Decimal(str(inv_data["subtotal"])) == Decimal("100000.00")
    assert Decimal(str(inv_data["tax_amount"])) == Decimal("18000.00")
    assert Decimal(str(inv_data["grand_total"])) == Decimal("118000.00")
    assert inv_data["journal_entry_id"] is not None
    assert "INV-PRJ-" in inv_data["invoice_number"]


def test_log_timesheet_and_actual_cost():
    response = client.get("/api/v1/projects")
    p1 = next(p for p in response.json() if p["project_code"] == "PRJ-2026-001")
    p1_id = p1["id"]
    cost_before = Decimal(str(p1["actual_cost"]))

    ts_payload = {
        "work_date": "2026-10-22",
        "hours": "10.00",
        "employee_name": "Kavitha Ramanathan",
        "is_billable": True,
        "hourly_billing_rate": "2500.00",
        "hourly_cost_rate": "850.00",
        "description": "Final testing of Dante digital audio routing.",
        "status": "APPROVED"
    }
    ts_res = client.post(f"/api/v1/projects/{p1_id}/timesheets", json=ts_payload)
    assert ts_res.status_code == 200
    ts_data = ts_res.json()
    assert Decimal(str(ts_data["total_billing_amount"])) == Decimal("25000.00")
    assert Decimal(str(ts_data["total_cost_amount"])) == Decimal("8500.00")

    # Verify project actual cost increased
    p1_updated = client.get(f"/api/v1/projects/{p1_id}").json()
    assert Decimal(str(p1_updated["actual_cost"])) == cost_before + Decimal("8500.00")


def test_log_expense_and_actual_cost():
    response = client.get("/api/v1/projects")
    p2 = next(p for p in response.json() if p["project_code"] == "PRJ-2026-002")
    p2_id = p2["id"]
    cost_before = Decimal(str(p2["actual_cost"]))

    exp_payload = {
        "category": "TRAVEL",
        "amount": "15000.00",
        "expense_date": "2026-10-21",
        "description": "Onsite travel and accommodation for technical surveyor.",
        "is_billable": True
    }
    exp_res = client.post(f"/api/v1/projects/{p2_id}/expenses", json=exp_payload)
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert Decimal(str(exp_data["amount"])) == Decimal("15000.00")

    # Verify project actual cost increased
    p2_updated = client.get(f"/api/v1/projects/{p2_id}").json()
    assert Decimal(str(p2_updated["actual_cost"])) == cost_before + Decimal("15000.00")


def test_project_metrics_summary():
    response = client.get("/api/v1/projects/metrics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] >= 3
    assert data["active_projects"] >= 2
    assert Decimal(str(data["total_contract_value"])) > Decimal("0.00")
    assert Decimal(str(data["total_billed_revenue"])) > Decimal("0.00")
    assert Decimal(str(data["total_logged_hours"])) > Decimal("0.00")
    assert Decimal(str(data["billable_utilization_rate"])) > Decimal("0.00")
