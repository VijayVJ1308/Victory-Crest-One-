"""Victory Crest One - Integration Tests for POS & Commerce API
Endpoints for terminals, shifts, barcode scan lookup, order lifecycle,
multi-tender settlement, GL journal integration, and telemetry.
"""

from decimal import Decimal
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_pos_terminals_and_active_session():
    # 1. List terminals
    res = client.get("/api/v1/pos/terminals")
    assert res.status_code == 200
    terminals = res.json()
    assert len(terminals) >= 3
    codes = [t["terminal_code"] for t in terminals]
    assert "POS-MDU-LOBBY-01" in codes
    assert "POS-MDU-BTQ-02" in codes

    # 2. Get active session
    res_sess = client.get("/api/v1/pos/sessions/active")
    assert res_sess.status_code == 200
    active = res_sess.json()
    assert active is not None
    assert active["status"] == "OPEN"
    assert active["terminal_code"] == "POS-MDU-LOBBY-01"
    assert Decimal(str(active["opening_float"])) >= Decimal("5000.00")


def test_pos_products_and_barcode_lookup():
    # 1. List all POS products
    res = client.get("/api/v1/pos/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 8

    # 2. Barcode exact lookup
    res_bc = client.get("/api/v1/pos/products?barcode=890103000001")
    assert res_bc.status_code == 200
    matched = res_bc.json()
    assert len(matched) == 1
    assert "Coffee" in matched[0]["name"]
    assert matched[0]["sku"] == "FNB-COF-MADURAI"

    # 3. Category filter
    res_cat = client.get("/api/v1/pos/products?category=Beverages")
    assert res_cat.status_code == 200
    bev_items = res_cat.json()
    assert all(b["category"] == "Beverages" for b in bev_items)


def test_pos_create_order_and_hold_recall():
    # 1. Create a new POS cart ticket
    order_payload = {
        "customer_name": "Dr. V. Sundaram",
        "table_or_room": "Table 8",
        "discount_percent": 5.00,
        "tax_rate_percent": 12.00,
        "lines": [
            {
                "sku": "FNB-COF-MADURAI",
                "barcode": "890103000001",
                "name": "Madurai Filter Degree Coffee",
                "category": "Beverages",
                "quantity": 2.0,
                "unit_price": 180.0,
                "discount_amount": 0.0
            },
            {
                "sku": "BAK-CRST-BUTTER",
                "barcode": "890103000003",
                "name": "French Butter Croissant",
                "category": "Bakery",
                "quantity": 1.0,
                "unit_price": 240.0,
                "discount_amount": 0.0
            }
        ],
        "notes": "Courtyard patio seating"
    }
    res = client.post("/api/v1/pos/orders", json=order_payload)
    assert res.status_code == 200
    created = res.json()
    assert created["status"] == "OPEN"
    order_id = created["id"]
    assert "POS-2026-" in created["order_number"]

    # Gross subtotal: 360 + 240 = 600.00
    # 5% discount: 30.00 -> taxable: 570.00
    # 12% GST: 68.40 -> total: 638.40
    assert Decimal(str(created["subtotal"])) == Decimal("600.00")
    assert Decimal(str(created["discount_amount"])) == Decimal("30.00")
    assert Decimal(str(created["tax_amount"])) == Decimal("68.40")
    assert Decimal(str(created["total_amount"])) == Decimal("638.40")

    # 2. Park / Hold order
    res_hold = client.post(f"/api/v1/pos/orders/{order_id}/hold", json={"reason": "Customer browsing boutique"})
    assert res_hold.status_code == 200
    held = res_hold.json()
    assert held["status"] == "HELD"

    # 3. Recall order
    res_recall = client.post(f"/api/v1/pos/orders/{order_id}/recall")
    assert res_recall.status_code == 200
    recalled = res_recall.json()
    assert recalled["status"] == "OPEN"


def test_pos_order_tender_and_gl_journal_posting():
    # 1. Create order
    order_payload = {
        "customer_name": "Siddharth Malhotra",
        "table_or_room": "Room 205",
        "discount_percent": 0.00,
        "tax_rate_percent": 12.00,
        "lines": [
            {
                "sku": "RET-TEA-NILGIRI",
                "barcode": "890103000007",
                "name": "Nilgiri Estate Black Tea Vintage Tin 200g",
                "category": "Retail",
                "quantity": 1.0,
                "unit_price": 650.0,
                "discount_amount": 0.0
            }
        ]
    }
    res_create = client.post("/api/v1/pos/orders", json=order_payload)
    assert res_create.status_code == 200
    order = res_create.json()
    order_id = order["id"]
    total_due = Decimal(str(order["total_amount"]))  # 650 + 12% = 728.00

    # 2. Tender with CASH overpayment (₹1,000 paid for ₹728 due)
    tender_payload = {
        "payments": [
            {
                "tender_type": "CASH",
                "amount": 1000.00,
                "reference_number": "CASH-TEST-99"
            }
        ],
        "notes": "Cash settlement with change returned"
    }
    res_pay = client.post(f"/api/v1/pos/orders/{order_id}/tender", json=tender_payload)
    assert res_pay.status_code == 200
    completed = res_pay.json()
    assert completed["status"] == "COMPLETED"
    assert Decimal(str(completed["paid_amount"])) == Decimal("1000.00")
    assert Decimal(str(completed["change_returned"])) == Decimal("272.00")
    # Verified automatic Phase 4 GL Journal posting!
    assert completed["journal_entry_id"] is not None
    assert len(completed["journal_entry_id"]) > 0


def test_pos_receipt_endpoint():
    # Fetch receipt for an existing completed order
    res = client.get("/api/v1/pos/orders?status=COMPLETED&limit=1")
    assert res.status_code == 200
    orders = res.json()
    assert len(orders) >= 1
    order_id = orders[0]["id"]

    res_rc = client.get(f"/api/v1/pos/orders/{order_id}/receipt")
    assert res_rc.status_code == 200
    receipt = res_rc.json()
    assert receipt["receipt_title"] == "VICTORY CREST ONE"
    assert "GrandVista" in receipt["property_name"]
    assert len(receipt["lines"]) >= 1
    assert Decimal(str(receipt["total_amount"])) > Decimal("0.00")
    assert receipt["journal_entry_id"] is not None


def test_pos_session_close_and_cash_variance():
    # 1. Open a new shift session for Terminal 2
    open_req = {
        "terminal_id": "term_mdu_02",
        "opening_float": 3000.00,
        "notes": "Evening boutique shift test"
    }
    res_open = client.post("/api/v1/pos/sessions/open", json=open_req)
    assert res_open.status_code == 200
    sess = res_open.json()
    assert sess["status"] == "OPEN"
    sess_id = sess["id"]

    # 2. Close session with slight cash overage (+₹50.00)
    close_req = {
        "counted_cash": 3050.00,
        "notes": "Evening shift close, ₹50 overage"
    }
    res_close = client.post(f"/api/v1/pos/sessions/{sess_id}/close", json=close_req)
    assert res_close.status_code == 200
    closed = res_close.json()
    assert closed["status"] == "CLOSED"
    assert Decimal(str(closed["cash_variance"])) == Decimal("50.00")


def test_pos_metrics_telemetry():
    res = client.get("/api/v1/pos/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["total_orders_count"] >= 2
    assert Decimal(str(metrics["total_sales_amount"])) > Decimal("0.00")
    assert Decimal(str(metrics["average_ticket_size"])) > Decimal("0.00")
