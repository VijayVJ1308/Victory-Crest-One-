"""Victory Crest One - Integration Tests for Supply Chain, ERP & Warehouse Inventory API
Warehouses, Stock Catalog, Purchase Orders, Receiving with automated GL/AP posting,
Inter-Warehouse Transfers, Cycle Counts, and Valuation Metrics.
"""

from decimal import Decimal
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_warehouses_list_and_create():
    # 1. List warehouses
    res = client.get("/api/v1/inventory/warehouses")
    assert res.status_code == 200
    warehouses = res.json()
    assert len(warehouses) >= 4
    codes = [w["warehouse_code"] for w in warehouses]
    assert "WH-MDU-OPS-01" in codes
    assert "WH-MDU-FNB-02" in codes

    # 2. Register new warehouse depot
    payload = {
        "warehouse_code": "WH-TEST-BLR-01",
        "name": "Bengaluru Regional Logistics Center",
        "warehouse_type": "CENTRAL",
        "location_address": "Whitefield Supply Park B-12",
        "manager_name": "R. Anand (Hub Manager)",
        "is_active": True
    }
    res_create = client.post("/api/v1/inventory/warehouses", json=payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["warehouse_code"] == "WH-TEST-BLR-01"
    assert created["name"] == "Bengaluru Regional Logistics Center"

    # 3. Get warehouse details by ID
    res_get = client.get(f"/api/v1/inventory/warehouses/{created['id']}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == created["id"]


def test_stock_catalog_and_filtering():
    # 1. List all stock items
    res = client.get("/api/v1/inventory/stock")
    assert res.status_code == 200
    stocks = res.json()
    assert len(stocks) >= 5

    # 2. Filter by status LOW_STOCK
    res_low = client.get("/api/v1/inventory/stock?stock_status=LOW_STOCK")
    assert res_low.status_code == 200
    low_stocks = res_low.json()
    assert len(low_stocks) >= 1
    for s in low_stocks:
        assert s["stock_status"] == "LOW_STOCK"

    # 3. Filter by warehouse
    res_wh = client.get("/api/v1/inventory/stock?warehouse_id=wh_mdu_fnb")
    assert res_wh.status_code == 200
    fnb_stocks = res_wh.json()
    assert len(fnb_stocks) >= 2
    for s in fnb_stocks:
        assert s["warehouse_id"] == "wh_mdu_fnb"

    # 4. Get specific stock item
    res_item = client.get("/api/v1/inventory/stock/wh_mdu_fnb/FNB-COF-MADURAI")
    assert res_item.status_code == 200
    item = res_item.json()
    assert item["sku"] == "FNB-COF-MADURAI"
    assert Decimal(str(item["quantity_on_hand"])) > 0


def test_update_stock_item():
    # Update quantity and unit cost of an existing stock item
    payload = {
        "product_name": "Premium Madurai Degree Filter Coffee",
        "quantity_on_hand": 180.0,
        "unit_cost": 70.0,
        "reorder_point": 40.0
    }
    res = client.put("/api/v1/inventory/stock/wh_mdu_fnb_FNB-COF-MADURAI", json=payload)
    assert res.status_code == 200
    updated = res.json()
    assert updated["product_name"] == "Premium Madurai Degree Filter Coffee"
    assert Decimal(str(updated["quantity_on_hand"])) == Decimal("180.0")
    assert Decimal(str(updated["unit_cost"])) == Decimal("70.0")
    assert Decimal(str(updated["total_value"])) == Decimal("12600.0")


def test_stock_replenishment_alerts():
    res = client.get("/api/v1/inventory/alerts/replenishment")
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) >= 1
    # Verify alert properties
    for a in alerts:
        assert Decimal(str(a["quantity_on_hand"])) <= Decimal(str(a["reorder_point"]))
        assert Decimal(str(a["shortage_quantity"])) >= 0
        assert Decimal(str(a["suggested_order_quantity"])) > 0


def test_purchase_order_lifecycle_and_automated_gl_ap_posting():
    # 1. List existing POs
    res_list = client.get("/api/v1/inventory/purchase-orders")
    assert res_list.status_code == 200
    pos = res_list.json()
    assert len(pos) >= 2

    # 2. Create a new Purchase Order
    po_payload = {
        "supplier_id": "supp_organic_foods",
        "supplier_name": "Nilgiri Organics & Gourmet Supplies",
        "warehouse_id": "wh_mdu_fnb",
        "payment_terms_days": 30,
        "tax_rate_percent": 18.0,
        "lines": [
            {
                "sku": "RAW-TEA-GREEN",
                "name": "Highland Organic Green Tea 1kg",
                "unit_of_measure": "PACK",
                "quantity_ordered": 20.0,
                "unit_price": 600.0
            }
        ],
        "notes": "Testing automated PO issue and receiving"
    }
    res_po = client.post("/api/v1/inventory/purchase-orders", json=po_payload)
    assert res_po.status_code == 200
    po = res_po.json()
    assert "PO-2026-" in po["po_number"]
    assert po["status"] == "ISSUED"
    # Subtotal: 20 * 600 = 12000.00, Tax (18%): 2160.00, Total: 14160.00
    assert Decimal(str(po["subtotal"])) == Decimal("12000.00")
    assert Decimal(str(po["tax_amount"])) == Decimal("2160.00")
    assert Decimal(str(po["total_amount"])) == Decimal("14160.00")

    # 3. Receive Goods against the PO (triggers automated GL journal DR 1200 / CR 2010 and AP Bill)
    po_id = po["id"]
    res_rec = client.post(
        f"/api/v1/inventory/purchase-orders/{po_id}/receive",
        json={"notes": "Received full shipment at loading bay"}
    )
    assert res_rec.status_code == 200
    received_po = res_rec.json()
    assert received_po["status"] == "RECEIVED"
    assert received_po["supplier_bill_id"] is not None

    # Verify stock now exists in target warehouse
    res_stock = client.get("/api/v1/inventory/stock/wh_mdu_fnb/RAW-TEA-GREEN")
    assert res_stock.status_code == 200
    st = res_stock.json()
    assert Decimal(str(st["quantity_on_hand"])) >= Decimal("20.00")


def test_inter_warehouse_stock_transfer():
    # Transfer Himalayan Mineral Water from Madurai Central to Madurai F&B
    transfer_payload = {
        "sku": "BEV-WTR-SPR750",
        "source_warehouse_id": "wh_mdu_central",
        "target_warehouse_id": "wh_mdu_fnb",
        "quantity": 10.0,
        "notes": "Transfer 10 bottles to Kitchen"
    }
    res_tr = client.post("/api/v1/inventory/transfers", json=transfer_payload)
    assert res_tr.status_code == 200
    movement = res_tr.json()
    assert movement["movement_type"] == "TRANSFER"
    assert Decimal(str(movement["quantity"])) == Decimal("10.00")
    assert "MOV-2026-" in movement["movement_number"]

    # Verify movement listed in movements endpoint
    res_movs = client.get("/api/v1/inventory/movements")
    assert res_movs.status_code == 200
    movs = res_movs.json()
    assert any(m["movement_number"] == movement["movement_number"] for m in movs)


def test_cycle_counts_and_reconciliation():
    # 1. Create a cycle count session
    cc_payload = {
        "warehouse_id": "wh_mdu_central",
        "notes": "End of Month stocktake"
    }
    res_cc = client.post("/api/v1/inventory/cycle-counts", json=cc_payload)
    assert res_cc.status_code == 200
    session = res_cc.json()
    assert session["status"] == "OPEN"
    assert "CC-2026-" in session["session_code"]

    # 2. Reconcile counted stock
    reconcile_payload = {
        "counts": [
            {
                "sku": "SNK-CSH-CHETT",
                "product_name": "Chettinad Spiced Roasted Cashews 250g",
                "book_quantity": 65.0,
                "counted_quantity": 64.0,  # 1 unit shrinkage
                "unit_cost": 210.0,
                "variance_quantity": -1.0,
                "variance_value": -210.0,
                "is_discrepant": True
            }
        ],
        "notes": "1 damaged tin written off"
    }
    session_id = session["id"]
    res_rec = client.post(
        f"/api/v1/inventory/cycle-counts/{session_id}/reconcile",
        json=reconcile_payload
    )
    assert res_rec.status_code == 200
    reconciled = res_rec.json()
    assert reconciled["status"] == "RECONCILED"
    assert reconciled["total_items_counted"] == 1
    assert Decimal(str(reconciled["total_variance_value"])) == Decimal("-210.00")


def test_inventory_metrics_telemetry():
    res = client.get("/api/v1/inventory/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["total_warehouses_count"] >= 4
    assert metrics["total_active_skus"] >= 5
    assert Decimal(str(metrics["total_stock_units"])) > 0
    assert Decimal(str(metrics["total_inventory_valuation"])) > 0
    assert metrics["active_purchase_orders_count"] >= 0
