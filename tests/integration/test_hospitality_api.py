"""Victory Crest One - Hospitality PMS & Restaurant Dining REST API Integration Test Suite
Validates endpoints for room inventory, reservations, guest check-in/out,
guest folios, dining orders, KDS tickets, and automated GL night audits.
"""

from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_list_room_types_and_rooms_rack():
    # 1. Room types
    res_types = client.get("/api/v1/hospitality/room-types")
    assert res_types.status_code == 200
    types = res_types.json()
    assert len(types) >= 4
    codes = [t["code"] for t in types]
    assert "DKG" in codes
    assert "EXS" in codes

    # 2. Rooms rack
    res_rooms = client.get("/api/v1/hospitality/rooms")
    assert res_rooms.status_code == 200
    rooms = res_rooms.json()
    assert len(rooms) >= 6
    room_numbers = [r["room_number"] for r in rooms]
    assert "101" in room_numbers
    assert "201" in room_numbers


def test_create_reservation_and_guest_check_in():
    today = date.today()
    # 1. Create reservation
    res_payload = {
        "guest_name": "Justice N. Radhakrishnan",
        "guest_email": "radhakrishnan@judiciary.internal",
        "guest_phone": "+91 98409 11223",
        "check_in_date": today.isoformat(),
        "check_out_date": (today + timedelta(days=2)).isoformat(),
        "room_type_id": "rt_dkg",
        "meal_plan": "CP",
        "advance_deposit_paid": 6000.0,
        "special_requests": "Ground floor room near gardens."
    }
    response = client.post("/api/v1/hospitality/reservations", json=res_payload)
    assert response.status_code == 200
    res_data = response.json()
    res_id = res_data["id"]
    assert res_data["confirmation_code"].startswith("RES-2026-")
    assert res_data["status"] == "CONFIRMED"
    assert res_data["nights"] == 2

    # 2. Check in guest into Room 101
    checkin_payload = {
        "room_id": "rm_101",
        "key_card_code": "KEY-101-GOLD"
    }
    res_cin = client.post(f"/api/v1/hospitality/reservations/{res_id}/check-in", json=checkin_payload)
    assert res_cin.status_code == 200
    cin_data = res_cin.json()
    assert cin_data["status"] == "CHECKED_IN"
    assert cin_data["room_number"] == "101"

    # Verify room is now OCCUPIED
    rm = client.get("/api/v1/hospitality/rooms?status=OCCUPIED").json()
    occ_numbers = [r["room_number"] for r in rm]
    assert "101" in occ_numbers


def test_guest_folio_incidental_and_settlement():
    # 1. Get open folios
    res_fol = client.get("/api/v1/hospitality/folios?status=OPEN")
    assert res_fol.status_code == 200
    folios = res_fol.json()
    assert len(folios) >= 1
    target_folio = folios[0]
    folio_id = target_folio["id"]

    # 2. Post incidental charge (e.g. Minibar / Laundry)
    charge_payload = {
        "line_type": "MISC",
        "description": "Executive Minibar & Dry Cleaning",
        "amount": 1650.0,
        "reference": "MINIBAR-01"
    }
    res_charge = client.post(f"/api/v1/hospitality/folios/{folio_id}/charges", json=charge_payload)
    assert res_charge.status_code == 200
    updated_folio = res_charge.json()
    assert float(updated_folio["total_charges"]) >= 1650.0

    # 3. Check-out and settle folio with automated GL posting
    settle_res = client.post(f"/api/v1/hospitality/folios/{folio_id}/settle", json={"payment_method": "CREDIT_CARD"})
    assert settle_res.status_code == 200
    settled_folio = settle_res.json()
    assert settled_folio["status"] == "SETTLED"
    assert settled_folio["is_settled"] is True
    assert float(settled_folio["balance_due"]) == 0.00
    assert settled_folio["journal_entry_id"] is not None


def test_restaurant_dining_order_and_kds_settlement():
    # 1. Create restaurant dining order
    order_payload = {
        "table_number": "T-02",
        "server_name": "Ramesh Swaminathan",
        "guest_count": 2,
        "items": [
            {"item_name": "Paneer Tikka Badami", "quantity": 1, "unit_price": 420.0},
            {"item_name": "Garlic Butter Naan Basket", "quantity": 2, "unit_price": 120.0}
        ]
    }
    res_order = client.post("/api/v1/hospitality/dining/orders", json=order_payload)
    assert res_order.status_code == 200
    order_data = res_order.json()
    order_id = order_data["id"]
    assert order_data["order_number"].startswith("KDS-2026-")
    assert order_data["status"] == "PENDING"
    assert float(order_data["subtotal"]) == 660.00

    # 2. Settle bill via UPI
    settle_payload = {
        "payment_method": "UPI"
    }
    res_settle = client.post(f"/api/v1/hospitality/dining/orders/{order_id}/settle", json=settle_payload)
    assert res_settle.status_code == 200
    settled_order = res_settle.json()
    assert settled_order["is_paid"] is True
    assert settled_order["status"] == "SERVED"
    assert settled_order["journal_entry_id"] is not None


def test_night_audit_execution_and_gl_posting():
    response = client.post("/api/v1/hospitality/night-audit")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "COMPLETED"
    assert "folios_processed" in result
    assert "total_room_charges_posted" in result
    assert result["journal_entry_id"] is not None


def test_hospitality_metrics_telemetry():
    response = client.get("/api/v1/hospitality/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["total_rooms"] >= 6
    assert "occupancy_rate" in metrics
    assert "average_daily_rate" in metrics
    assert "revpar" in metrics
    assert metrics["open_folios_count"] >= 1
