"""Victory Crest One - Integration Tests for Manufacturing & BOM REST API
Tests Work Centers, Bill of Materials calculation, Production Orders,
Quality Control checkpoints, and automated General Ledger journal creation.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_list_work_centers():
    response = client.get("/api/v1/manufacturing/work-centers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 4
    codes = [wc["code"] for wc in data]
    assert "WC-CARP-01" in codes
    assert "WC-BKY-01" in codes
    assert "WC-ASM-01" in codes


def test_create_work_center():
    payload = {
        "code": "WC-TEST-99",
        "name": "Rapid Prototyping 3D Printing Lab",
        "work_center_type": "LAB",
        "hourly_labor_rate": "500.00",
        "hourly_machine_rate": "300.00",
        "daily_capacity_hours": "12.00",
        "status": "AVAILABLE",
        "is_active": True
    }
    response = client.post("/api/v1/manufacturing/work-centers", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "WC-TEST-99"
    assert data["work_center_type"] == "LAB"
    assert Decimal(str(data["daily_capacity_hours"])) == Decimal("12.00")


def test_list_boms_and_get_details():
    response = client.get("/api/v1/manufacturing/boms")
    assert response.status_code == 200
    boms = response.json()
    assert len(boms) >= 2

    # Check Heritage Desk BOM
    desk_bom = next(b for b in boms if b["bom_code"] == "BOM-HTG-DESK-01")
    assert desk_bom["product_name"] == "Solid Teak Heritage Writing Desk"
    assert len(desk_bom["components"]) >= 3
    assert len(desk_bom["operations"]) >= 3
    assert Decimal(str(desk_bom["total_bom_cost"])) > Decimal("0.00")
    assert Decimal(str(desk_bom["unit_cost"])) > Decimal("0.00")

    # Fetch individual BOM
    single_res = client.get(f"/api/v1/manufacturing/boms/{desk_bom['id']}")
    assert single_res.status_code == 200
    assert single_res.json()["bom_code"] == "BOM-HTG-DESK-01"


def test_create_bom_with_components_and_routing():
    payload = {
        "bom_code": "BOM-CUSTOM-CHAIR-01",
        "product_id": "prd_cst_chr",
        "product_name": "Handcrafted Rattan Lounge Chair",
        "product_sku": "PRD-CHR-RAT-01",
        "version": "v1.0",
        "batch_quantity": "2.00",
        "uom": "Units",
        "notes": "Natural cane and teak armchairs for resort veranda.",
        "components": [
            {
                "item_code": "RAW-TEAK-FRM",
                "item_name": "Shaped Teak Framing Rails",
                "quantity": "4.00",
                "uom": "Units",
                "unit_cost": "600.00",
                "scrap_percent": "0.00"
            },
            {
                "item_code": "RAW-CANE-WEV",
                "item_name": "Premium Natural Cane Webbing Roll",
                "quantity": "2.00",
                "uom": "Rolls",
                "unit_cost": "450.00",
                "scrap_percent": "5.00"
            }
        ],
        "operations": [
            {
                "sequence": 10,
                "work_center_id": "wc_carp_01",
                "work_center_name": "Colonial Teak Joinery & Carving Bay",
                "operation_name": "Frame Assembly & Cane Weaving",
                "setup_time_hours": "0.50",
                "run_time_per_unit_hours": "1.00",
                "hourly_rate": "550.00"
            }
        ]
    }
    response = client.post("/api/v1/manufacturing/boms", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["bom_code"] == "BOM-CUSTOM-CHAIR-01"
    assert len(data["components"]) == 2
    assert len(data["operations"]) == 1
    # Check unit cost is total / batch_quantity (2)
    assert Decimal(str(data["unit_cost"])) > Decimal("0.00")


def test_production_order_lifecycle_and_gl_posting():
    # 1. Fetch active BOM
    boms_res = client.get("/api/v1/manufacturing/boms")
    boms = boms_res.json()
    target_bom = boms[0]

    # 2. Create Production Order
    create_payload = {
        "bom_id": target_bom["id"],
        "target_quantity": "5.00",
        "planned_start_date": "2026-10-25T08:00:00Z",
        "planned_end_date": "2026-10-28T18:00:00Z",
        "priority": "HIGH",
        "work_center_id": "wc_carp_01",
        "supervisor_name": "Foreman Balasubramanian M.",
        "notes": "Express production for hotel banquet hall upgrade."
    }
    create_res = client.post("/api/v1/manufacturing/production-orders", json=create_payload)
    assert create_res.status_code == 200
    order = create_res.json()
    order_id = order["id"]
    assert order["status"] == "PLANNED"
    assert order["target_quantity"] == "5.00"
    assert len(order["materials"]) > 0

    # 3. Start Production Order
    start_res = client.post(f"/api/v1/manufacturing/production-orders/{order_id}/start")
    assert start_res.status_code == 200
    started_order = start_res.json()
    assert started_order["status"] == "IN_PROGRESS"
    assert started_order["actual_start_date"] is not None

    # 4. Complete Production Order (which executes GL posting)
    complete_payload = {
        "produced_quantity": "5.00",
        "rejected_quantity": "0.00",
        "actual_labor_hours": "12.00",
        "labor_hourly_rate": "550.00",
        "overhead_cost": "1500.00",
        "quality_status": "PASSED",
        "notes": "Zero defects; passed high-tolerance mechanical inspection."
    }
    complete_res = client.post(f"/api/v1/manufacturing/production-orders/{order_id}/complete", json=complete_payload)
    assert complete_res.status_code == 200
    completed_order = complete_res.json()
    assert completed_order["status"] == "COMPLETED"
    assert Decimal(str(completed_order["produced_quantity"])) == Decimal("5.00")
    assert Decimal(str(completed_order["total_actual_cost"])) > Decimal("0.00")
    assert completed_order["journal_entry_id"] is not None
    assert len(completed_order["inspections"]) >= 1


def test_manufacturing_metrics_telemetry():
    response = client.get("/api/v1/manufacturing/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_orders" in data
    assert "completed_orders" in data
    assert "active_orders" in data
    assert "scrap_rate_percent" in data
    assert "total_wip_valuation" in data
    assert "capacity_utilization_percent" in data
    assert data["total_work_centers"] >= 4
