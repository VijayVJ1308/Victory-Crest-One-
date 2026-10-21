"""Victory Crest One - Customer & Field Service REST API Integration Test Suite
Validates endpoints for SLA policies, Support Tickets, Field Work Orders,
Technician Dispatch, Parts Requisitions, and Invoiced GL Postings.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_list_sla_policies():
    response = client.get("/api/v1/service/sla-policies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 4
    priorities = [p["priority"] for p in data]
    assert "CRITICAL" in priorities
    assert "HIGH" in priorities
    assert "MEDIUM" in priorities
    assert "LOW" in priorities


def test_list_support_tickets_and_filtering():
    response = client.get("/api/v1/service/tickets")
    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) >= 3

    # Filter by priority
    res_crit = client.get("/api/v1/service/tickets?priority=CRITICAL")
    assert res_crit.status_code == 200
    crit_tickets = res_crit.json()
    assert all(t["priority"] == "CRITICAL" for t in crit_tickets)


def test_create_support_ticket_and_sla_targets():
    payload = {
        "customer_name": "Manipal Healthcare Hospital",
        "customer_email": "biomedical@manipal.internal",
        "subject": "Oxygen Concentration Manifold Sensor Alarm",
        "description": "Secondary line sensor throwing intermittent pressure telemetry warnings.",
        "category": "MEDICAL_EQUIPMENT",
        "priority": "CRITICAL",
        "channel": "PHONE"
    }
    response = client.post("/api/v1/service/tickets", json=payload)
    assert response.status_code == 200
    ticket = response.json()
    assert ticket["ticket_number"].startswith("TCK-2026-")
    assert ticket["priority"] == "CRITICAL"
    assert ticket["status"] == "OPEN"
    assert float(ticket["sla_target_response_hours"]) == 1.0
    assert float(ticket["sla_target_resolution_hours"]) == 4.0
    assert ticket["sla_breached"] is False


def test_create_work_order_dispatch_and_parts_requisition():
    # 1. Create work order
    wo_payload = {
        "customer_name": "Titan Corporate Watch Factory",
        "site_address": "Titan Plant 4, Assembly Floor 2, Hosur",
        "service_type": "EMERGENCY_REPAIR",
        "priority": "HIGH",
        "technician_name": "Rajesh Kumar (Senior Facilities Engineer)",
        "labor_hours": 3.0,
        "labor_rate_per_hour": 850.0
    }
    res_wo = client.post("/api/v1/service/work-orders", json=wo_payload)
    assert res_wo.status_code == 200
    wo = res_wo.json()
    wo_id = wo["id"]
    assert wo["work_order_number"].startswith("WO-2026-")
    assert wo["status"] == "SCHEDULED"

    # 2. Dispatch technician
    disp_payload = {
        "technician_id": "tech_rajesh_01",
        "technician_name": "Rajesh Kumar (Senior Facilities Engineer)"
    }
    res_disp = client.post(f"/api/v1/service/work-orders/{wo_id}/dispatch", json=disp_payload)
    assert res_disp.status_code == 200
    assert res_disp.json()["status"] == "DISPATCHED"

    # 3. Requisition spare part
    part_payload = {
        "item_code": "PRT-ELC-44",
        "item_name": "Optical Rotary Encoder 1024-PPR",
        "quantity_demanded": 1.0,
        "unit_cost": 4200.0
    }
    res_part = client.post(f"/api/v1/service/work-orders/{wo_id}/parts", json=part_payload)
    assert res_part.status_code == 200
    part = res_part.json()
    part_id = part["id"]
    assert part["status"] == "REQUESTED"

    # 4. Issue spare part
    res_issue = client.post(f"/api/v1/service/work-orders/{wo_id}/parts/{part_id}/issue")
    assert res_issue.status_code == 200
    assert res_issue.json()["status"] == "ISSUED"


def test_complete_work_order_and_automated_gl_invoicing():
    # 1. Create work order
    wo_payload = {
        "customer_name": "L&T Defense Systems",
        "site_address": "Hydraulic Testing Bay, Coimbatore",
        "service_type": "PREVENTIVE_MAINTENANCE",
        "priority": "MEDIUM",
        "technician_name": "Priya Nair",
        "labor_hours": 2.0,
        "labor_rate_per_hour": 800.0
    }
    wo = client.post("/api/v1/service/work-orders", json=wo_payload).json()
    wo_id = wo["id"]

    # 2. Add and issue part
    part_payload = {
        "item_code": "PRT-HYD-03",
        "item_name": "High-Pressure Seal Kit",
        "quantity_demanded": 1.0,
        "unit_cost": 2500.0
    }
    part = client.post(f"/api/v1/service/work-orders/{wo_id}/parts", json=part_payload).json()
    client.post(f"/api/v1/service/work-orders/{wo_id}/parts/{part['id']}/issue")

    # 3. Complete and bill work order
    complete_payload = {
        "actual_labor_hours": 3.0,
        "labor_rate_per_hour": 800.0,
        "resolution_summary": "Replaced worn high-pressure seals, bled hydraulic lines, validated pressure curve at 350 bar.",
        "mark_ticket_resolved": True
    }
    res_bill = client.post(f"/api/v1/service/work-orders/{wo_id}/complete-and-bill", json=complete_payload)
    assert res_bill.status_code == 200
    completed_wo = res_bill.json()

    assert completed_wo["status"] == "COMPLETED"
    assert completed_wo["is_invoiced"] is True
    assert completed_wo["journal_entry_id"] is not None
    # Labor: 3 * 800 = 2400.00
    # Parts: 2500.00
    # Subtotal: 4900.00
    # Tax 18%: 882.00
    # Grand Total: 5782.00
    assert float(completed_wo["labor_total"]) == 2400.00
    assert float(completed_wo["parts_total"]) == 2500.00
    assert float(completed_wo["tax_amount"]) == 882.00
    assert float(completed_wo["grand_total"]) == 5782.00


def test_service_metrics_telemetry():
    response = client.get("/api/v1/service/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["total_tickets"] >= 3
    assert "sla_compliance_rate" in metrics
    assert "first_contact_resolution_rate" in metrics
    assert metrics["active_work_orders"] >= 1
    assert float(metrics["total_service_revenue"]) > 0
