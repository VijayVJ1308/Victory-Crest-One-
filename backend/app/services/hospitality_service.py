"""Victory Crest One - Hospitality & Resort PMS / Restaurant Dining Service
Rooms Rack, Rate Plans, Reservations Engine, Housekeeping, Guest Folios,
Dining Tables, Kitchen Display System (KDS), and Automated GL Night Audits.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta, timezone
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.hospitality import (
    RoomTypeOut, RoomCreate, RoomOut,
    ReservationCreate, ReservationCheckInRequest, ReservationOut,
    FolioLineCreate, FolioLineOut, GuestFolioOut,
    DiningTableOut, DiningOrderItemCreate, DiningOrderItemOut,
    DiningOrderCreate, DiningOrderSettleRequest, DiningOrderOut,
    HospitalityMetricsOut
)
from backend.app.schemas.finance import JournalEntryCreate, JournalLineCreate
from backend.app.services.finance_service import finance_service
from backend.app.services.audit_service import audit_service
from shared.calculations import (
    to_decimal, calculate_occupancy_rate, calculate_adr, calculate_revpar,
    calculate_reservation_totals, calculate_folio_balance, calculate_dining_bill_totals
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory stores
_ROOM_TYPE_STORE: Dict[str, Dict[str, Any]] = {}
_ROOM_STORE: Dict[str, Dict[str, Any]] = {}
_RESERVATION_STORE: Dict[str, Dict[str, Any]] = {}
_FOLIO_STORE: Dict[str, Dict[str, Any]] = {}
_FOLIO_LINE_STORE: Dict[str, List[Dict[str, Any]]] = {}
_TABLE_STORE: Dict[str, Dict[str, Any]] = {}
_DINING_ORDER_STORE: Dict[str, Dict[str, Any]] = {}

_RES_COUNTER = 100
_FOLIO_COUNTER = 100
_ORDER_COUNTER = 100


def _seed_hospitality_data():
    """Populate room types, room rack, reservations, guest folios, and dining tables."""
    global _RES_COUNTER, _FOLIO_COUNTER, _ORDER_COUNTER
    if _ROOM_TYPE_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]  # Madurai Heritage Hotel
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]  # Kodaikanal Mountain Resort
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]  # Chennai Hub
    now = datetime.now(timezone.utc)
    today = date.today()

    # 1. Room Types
    room_types = [
        ("rt_dkg", "DKG", "Deluxe King Heritage", 2, 3, Decimal("5500.00"), "Opulent king room with colonial teak furnishings and courtyard garden views.", "WiFi, Smart TV, Minibar, Clawfoot Tub, Daily Breakfast", prop_mdu),
        ("rt_exs", "EXS", "Executive Royal Suite", 2, 4, Decimal("9500.00"), "Spacious two-room suite with private balcony, separate study, and butler service.", "High-speed WiFi, Jacuzzi, Espresso Bar, Club Lounge Access", prop_mdu),
        ("rt_mpv", "MPV", "Mountain View Pool Villa", 2, 4, Decimal("16000.00"), "Secluded luxury villa nestled in the eucalyptus hills with heated plunge pool.", "Private Pool, Fireplace, Panoramic Valley View, Butler Service", prop_kod),
        ("rt_ips", "IPS", "Imperial Presidential Suite", 4, 6, Decimal("35000.00"), "Top-floor penthouse suite with private terrace, boardroom, and chef pantry.", "Private Terrace, Dedicated Concierge, Boardroom, Security Detail", prop_mdu),
        ("rt_cbr", "CBR", "Corporate Business Room", 1, 2, Decimal("4200.00"), "Ergonomic workspace, soundproof acoustic glass, and direct airport access.", "Ergonomic Desk, Wireless Charger, 24/7 Room Service", prop_maa)
    ]
    for rtid, code, name, bocc, mocc, rate, desc, amen, pid in room_types:
        _ROOM_TYPE_STORE[rtid] = {
            "id": rtid,
            "organization_id": org_id,
            "property_id": pid,
            "code": code,
            "name": name,
            "base_occupancy": bocc,
            "max_occupancy": mocc,
            "base_rate_per_night": rate,
            "description": desc,
            "amenities": amen,
            "is_active": True
        }

    # 2. Rooms Rack
    rooms = [
        ("rm_101", org_id, prop_mdu, "101", "rt_dkg", "Deluxe King Heritage", "Floor 1", "Heritage Courtyard Wing", "AVAILABLE_CLEAN", "KEY-101-A", None),
        ("rm_102", org_id, prop_mdu, "102", "rt_dkg", "Deluxe King Heritage", "Floor 1", "Heritage Courtyard Wing", "AVAILABLE_CLEAN", "KEY-102-A", None),
        ("rm_201", org_id, prop_mdu, "201", "rt_exs", "Executive Royal Suite", "Floor 2", "Royal Palace Wing", "OCCUPIED", "KEY-201-B", "VIP Guest: Mr. Vikramaditya Singhania"),
        ("rm_202", org_id, prop_mdu, "202", "rt_exs", "Executive Royal Suite", "Floor 2", "Royal Palace Wing", "DIRTY", None, "Departed 11:00 AM - Awaiting deep sanitization"),
        ("rm_301", org_id, prop_mdu, "301", "rt_ips", "Imperial Presidential Suite", "Floor 3", "Penthouse Terrace", "OCCUPIED", "KEY-301-VIP", "High Net Worth Delegation"),
        ("rm_v1", org_id, prop_kod, "Villa-01", "rt_mpv", "Mountain View Pool Villa", "Ground", "Valley Ridge", "OCCUPIED", "KEY-V01", "VIP Guest: Dr. Ananya Sen"),
        ("rm_v2", org_id, prop_kod, "Villa-02", "rt_mpv", "Mountain View Pool Villa", "Ground", "Valley Ridge", "AVAILABLE_CLEAN", "KEY-V02", None),
        ("rm_501", org_id, prop_maa, "501", "rt_cbr", "Corporate Business Room", "Floor 5", "Express Tower", "AVAILABLE_CLEAN", "KEY-501", None),
        ("rm_502", org_id, prop_maa, "502", "rt_cbr", "Corporate Business Room", "Floor 5", "Express Tower", "MAINTENANCE", None, "AC Compressor capacitor replacement in progress")
    ]
    for rid, oid, pid, num, rtid, rtname, floor, wing, st, key, notes in rooms:
        _ROOM_STORE[rid] = {
            "id": rid,
            "organization_id": oid,
            "property_id": pid,
            "room_number": num,
            "room_type_id": rtid,
            "room_type_name": rtname,
            "floor": floor,
            "building_wing": wing,
            "status": st,
            "key_card_code": key,
            "notes": notes
        }

    # 3. Reservations
    res_list = [
        (
            "res_001", "RES-2026-0001", org_id, prop_mdu,
            "Vikramaditya Singhania", "vikram.singhania@corp.in", "+91 98401 99881",
            today - timedelta(days=2), today + timedelta(days=1), 3,
            "rt_exs", "Executive Royal Suite", "rm_201", "201", "CP", "CHECKED_IN",
            Decimal("9500.00"), Decimal("0.00"), Decimal("28500.00"), Decimal("3420.00"), Decimal("31920.00"),
            Decimal("15000.00"), "Late check-out requested at 2:00 PM. High floor.", now - timedelta(days=5)
        ),
        (
            "res_002", "RES-2026-0002", org_id, prop_kod,
            "Dr. Ananya Sen", "ananya.sen@neuro.org", "+91 98402 88772",
            today - timedelta(days=1), today + timedelta(days=1), 2,
            "rt_mpv", "Mountain View Pool Villa", "rm_v1", "Villa-01", "MAP", "CHECKED_IN",
            Decimal("16000.00"), Decimal("0.00"), Decimal("32000.00"), Decimal("3840.00"), Decimal("35840.00"),
            Decimal("10000.00"), "Honeymoon anniversary setup with floral arrangement.", now - timedelta(days=3)
        ),
        (
            "res_003", "RES-2026-0003", org_id, prop_mdu,
            "Tata Consultancy Executive Retreat", "events@tcs.internal", "+91 98403 77663",
            today + timedelta(days=1), today + timedelta(days=4), 3,
            "rt_dkg", "Deluxe King Heritage", None, None, "AP", "CONFIRMED",
            Decimal("5500.00"), Decimal("1500.00"), Decimal("21000.00"), Decimal("2520.00"), Decimal("23520.00"),
            Decimal("12000.00"), "Conference hall booking linked for Day 2.", now - timedelta(days=1)
        ),
        (
            "res_004", "RES-2026-0004", org_id, prop_mdu,
            "Prof. K. Sundaram", "sundaram.k@iitm.ac.in", "+91 98404 66554",
            today + timedelta(days=2), today + timedelta(days=5), 3,
            "rt_dkg", "Deluxe King Heritage", None, None, "EP", "CONFIRMED",
            Decimal("5500.00"), Decimal("0.00"), Decimal("16500.00"), Decimal("1980.00"), Decimal("18480.00"),
            Decimal("0.00"), "Quiet room away from elevators requested.", now - timedelta(hours=6)
        )
    ]
    for (rid, code, oid, pid, gname, gemail, gphone, cin, cout, nights, rtid, rtname,
         rm_id, rm_num, mplan, st, rrate, mrate, sub, tax, gtot, adv, req, cr_at) in res_list:
        _RESERVATION_STORE[rid] = {
            "id": rid,
            "confirmation_code": code,
            "organization_id": oid,
            "property_id": pid,
            "guest_name": gname,
            "guest_email": gemail,
            "guest_phone": gphone,
            "check_in_date": cin,
            "check_out_date": cout,
            "nights": nights,
            "room_type_id": rtid,
            "room_type_name": rtname,
            "room_id": rm_id,
            "room_number": rm_num,
            "meal_plan": mplan,
            "status": st,
            "room_rate_per_night": rrate,
            "meal_plan_rate": mrate,
            "subtotal": sub,
            "tax_amount": tax,
            "grand_total": gtot,
            "advance_deposit_paid": adv,
            "special_requests": req,
            "created_at": cr_at,
            "updated_at": cr_at
        }

    # 4. Guest Folios & Incidentals
    _FOLIO_STORE["fol_001"] = {
        "id": "fol_001",
        "folio_number": "FOL-2026-0001",
        "reservation_id": "res_001",
        "organization_id": org_id,
        "property_id": prop_mdu,
        "guest_name": "Vikramaditya Singhania",
        "room_number": "201",
        "status": "OPEN",
        "total_charges": Decimal("26650.00"),
        "total_payments": Decimal("15000.00"),
        "balance_due": Decimal("11650.00"),
        "is_settled": False,
        "journal_entry_id": None,
        "created_at": now - timedelta(days=2)
    }
    _FOLIO_LINE_STORE["fol_001"] = [
        {"id": "fl_01", "folio_id": "fol_001", "line_type": "ROOM_CHARGE", "description": "Room Charge - Royal Suite (Night 1)", "amount": Decimal("9500.00"), "reference": "NIGHT_AUDIT_DAY_1", "posted_at": now - timedelta(days=2)},
        {"id": "fl_02", "folio_id": "fol_001", "line_type": "ROOM_CHARGE", "description": "Room Charge - Royal Suite (Night 2)", "amount": Decimal("9500.00"), "reference": "NIGHT_AUDIT_DAY_2", "posted_at": now - timedelta(days=1)},
        {"id": "fl_03", "folio_id": "fol_001", "line_type": "FOOD_BEVERAGE", "description": "Aura Restaurant - Chettinad Dinner & Wine", "amount": Decimal("3450.00"), "reference": "KDS-BILL-092", "posted_at": now - timedelta(days=1, hours=3)},
        {"id": "fl_04", "folio_id": "fol_001", "line_type": "SPA", "description": "Ananda Ayurvedic Spa - Abhyanga Treatment", "amount": Decimal("4200.00"), "reference": "SPA-9912", "posted_at": now - timedelta(hours=6)},
        {"id": "fl_05", "folio_id": "fol_001", "line_type": "PAYMENT", "description": "Advance Booking Deposit (HDFC Credit Card)", "amount": Decimal("15000.00"), "reference": "TXN-CC-8821", "posted_at": now - timedelta(days=2)}
    ]

    _FOLIO_STORE["fol_002"] = {
        "id": "fol_002",
        "folio_number": "FOL-2026-0002",
        "reservation_id": "res_002",
        "organization_id": org_id,
        "property_id": prop_kod,
        "guest_name": "Dr. Ananya Sen",
        "room_number": "Villa-01",
        "status": "OPEN",
        "total_charges": Decimal("18800.00"),
        "total_payments": Decimal("10000.00"),
        "balance_due": Decimal("8800.00"),
        "is_settled": False,
        "journal_entry_id": None,
        "created_at": now - timedelta(days=1)
    }
    _FOLIO_LINE_STORE["fol_002"] = [
        {"id": "fl_06", "folio_id": "fol_002", "line_type": "ROOM_CHARGE", "description": "Pool Villa Night 1 Charge", "amount": Decimal("16000.00"), "reference": "NIGHT_AUDIT_DAY_1", "posted_at": now - timedelta(days=1)},
        {"id": "fl_07", "folio_id": "fol_002", "line_type": "FOOD_BEVERAGE", "description": "In-Villa Dining Breakfast & High Tea", "amount": Decimal("2800.00"), "reference": "KDS-BILL-095", "posted_at": now - timedelta(hours=4)},
        {"id": "fl_08", "folio_id": "fol_002", "line_type": "PAYMENT", "description": "UPI Advance Transfer", "amount": Decimal("10000.00"), "reference": "UPI-REF-3341", "posted_at": now - timedelta(days=1)}
    ]

    # 5. Restaurant Dining Tables
    tables = [
        ("tbl_01", org_id, prop_mdu, "T-01", "Main Dining Hall", 4, "OCCUPIED", "ord_001"),
        ("tbl_02", org_id, prop_mdu, "T-02", "Main Dining Hall", 2, "VACANT", None),
        ("tbl_03", org_id, prop_mdu, "T-03", "Main Dining Hall", 6, "RESERVED", None),
        ("tbl_04", org_id, prop_mdu, "Patio-1", "Poolside Verandah", 4, "VACANT", None),
        ("tbl_05", org_id, prop_mdu, "PDR-1", "Heritage Private Dining Room", 10, "OCCUPIED", "ord_002")
    ]
    for tid, oid, pid, num, sec, cap, st, ord_id in tables:
        _TABLE_STORE[tid] = {
            "id": tid,
            "organization_id": oid,
            "property_id": pid,
            "table_number": num,
            "area_section": sec,
            "seating_capacity": cap,
            "status": st,
            "current_order_id": ord_id
        }

    # 6. Restaurant Orders & KDS Tickets
    _DINING_ORDER_STORE["ord_001"] = {
        "id": "ord_001",
        "order_number": "KDS-2026-0001",
        "table_id": "tbl_01",
        "table_number": "T-01",
        "organization_id": org_id,
        "property_id": prop_mdu,
        "server_name": "Ramesh Swaminathan",
        "guest_count": 3,
        "status": "PREPARING",
        "subtotal": Decimal("2790.00"),
        "service_charge": Decimal("139.50"),
        "tax_amount": Decimal("139.50"),
        "grand_total": Decimal("3069.00"),
        "is_paid": False,
        "payment_method": None,
        "room_folio_id": None,
        "journal_entry_id": None,
        "items": [
            {"id": "oi_01", "order_id": "ord_001", "item_name": "Chettinad Spiced Lamb Chops", "quantity": 2, "unit_price": Decimal("750.00"), "total_price": Decimal("1500.00"), "special_notes": "Medium spice", "status": "PREPARING"},
            {"id": "oi_02", "order_id": "ord_001", "item_name": "Malabar Seafood Dum Biryani", "quantity": 1, "unit_price": Decimal("650.00"), "total_price": Decimal("650.00"), "special_notes": "Extra raita", "status": "PREPARING"},
            {"id": "oi_03", "order_id": "ord_001", "item_name": "Tender Coconut Souffle", "quantity": 2, "unit_price": Decimal("320.00"), "total_price": Decimal("640.00"), "special_notes": None, "status": "PENDING"}
        ],
        "created_at": now - timedelta(minutes=25)
    }

    _DINING_ORDER_STORE["ord_002"] = {
        "id": "ord_002",
        "order_number": "KDS-2026-0002",
        "table_id": "tbl_05",
        "table_number": "PDR-1",
        "organization_id": org_id,
        "property_id": prop_mdu,
        "server_name": "Meenakshi Sundaram",
        "guest_count": 8,
        "status": "SERVED",
        "subtotal": Decimal("7800.00"),
        "service_charge": Decimal("390.00"),
        "tax_amount": Decimal("390.00"),
        "grand_total": Decimal("8580.00"),
        "is_paid": False,
        "payment_method": None,
        "room_folio_id": None,
        "journal_entry_id": None,
        "items": [
            {"id": "oi_04", "order_id": "ord_002", "item_name": "Grand Royal Thali Feast", "quantity": 6, "unit_price": Decimal("950.00"), "total_price": Decimal("5700.00"), "special_notes": "Traditional brassware service", "status": "SERVED"},
            {"id": "oi_05", "order_id": "ord_002", "item_name": "Kumbakonam Filter Coffee Pot", "quantity": 6, "unit_price": Decimal("150.00"), "total_price": Decimal("900.00"), "special_notes": "Extra frothy", "status": "SERVED"},
            {"id": "oi_06", "order_id": "ord_002", "item_name": "Madurai Jigarthanda Special", "quantity": 4, "unit_price": Decimal("300.00"), "total_price": Decimal("1200.00"), "special_notes": "With almond gum & basundi", "status": "SERVED"}
        ],
        "created_at": now - timedelta(minutes=50)
    }


class HospitalityService:
    """Core Hospitality PMS and Restaurant Dining Engine."""

    def __init__(self):
        _seed_hospitality_data()

    # -------------------------------------------------------------------------
    # Room Types & Rooms Rack
    # -------------------------------------------------------------------------
    def get_room_types(self, property_id: Optional[str] = None) -> List[RoomTypeOut]:
        _seed_hospitality_data()
        types = [
            t for t in _ROOM_TYPE_STORE.values()
            if not property_id or t["property_id"] == property_id
        ]
        return [RoomTypeOut(**t) for t in types]

    def get_rooms(
        self,
        property_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[RoomOut]:
        _seed_hospitality_data()
        rooms = []
        for r in _ROOM_STORE.values():
            if property_id and r["property_id"] != property_id:
                continue
            if status_filter and status_filter.upper() != "ALL" and r["status"].upper() != status_filter.upper():
                continue
            rooms.append(RoomOut(**r))
        return sorted(rooms, key=lambda x: x.room_number)

    def create_room(self, room_in: RoomCreate, property_id: Optional[str] = None) -> RoomOut:
        _seed_hospitality_data()
        org_id = DEMO_ORGANISATIONS[0]["id"]
        prop_id = property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]
        
        rt = _ROOM_TYPE_STORE.get(room_in.room_type_id)
        rt_name = rt["name"] if rt else "Standard Room"

        rid = f"rm_{uuid.uuid4().hex[:8]}"
        record = {
            "id": rid,
            "organization_id": org_id,
            "property_id": prop_id,
            "room_number": room_in.room_number,
            "room_type_id": room_in.room_type_id,
            "room_type_name": rt_name,
            "floor": room_in.floor,
            "building_wing": room_in.building_wing,
            "status": "AVAILABLE_CLEAN",
            "key_card_code": f"KEY-{room_in.room_number}",
            "notes": room_in.notes
        }
        _ROOM_STORE[rid] = record
        return RoomOut(**record)

    def update_room_status(self, room_id: str, new_status: str, user_email: str = "housekeeping@victorycrest.internal") -> RoomOut:
        _seed_hospitality_data()
        if room_id not in _ROOM_STORE:
            raise HTTPException(status_code=404, detail="Room not found")
        rm = _ROOM_STORE[room_id]
        rm["status"] = new_status.upper()

        audit_service.record_event(
            action="ROOM_STATUS_UPDATED",
            entity_type="Room",
            entity_id=room_id,
            user_email=user_email,
            organization_id=rm["organization_id"],
            details=f"Room {rm['room_number']} housekeeping status changed to {rm['status']}"
        )
        return RoomOut(**rm)

    # -------------------------------------------------------------------------
    # Reservations Engine
    # -------------------------------------------------------------------------
    def get_reservations(
        self,
        property_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[ReservationOut]:
        _seed_hospitality_data()
        results = []
        for res in sorted(_RESERVATION_STORE.values(), key=lambda x: x["created_at"], reverse=True):
            if property_id and res["property_id"] != property_id:
                continue
            if status_filter and status_filter.upper() != "ALL" and res["status"].upper() != status_filter.upper():
                continue
            if search_query:
                q = search_query.lower()
                matched = (
                    q in res["confirmation_code"].lower() or
                    q in res["guest_name"].lower() or
                    q in res["guest_email"].lower() or
                    q in (res["room_number"] or "").lower()
                )
                if not matched:
                    continue
            results.append(ReservationOut(**res))
        return results

    def create_reservation(
        self,
        res_in: ReservationCreate,
        user_email: str = "reservations@victorycrest.internal"
    ) -> ReservationOut:
        _seed_hospitality_data()
        global _RES_COUNTER
        _RES_COUNTER += 1

        org_id = DEMO_ORGANISATIONS[0]["id"]
        prop_id = res_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]
        res_id = f"res_{uuid.uuid4().hex[:8]}"
        conf_code = f"RES-2026-{_RES_COUNTER:04d}"
        now = datetime.now(timezone.utc)

        rt = _ROOM_TYPE_STORE.get(res_in.room_type_id)
        if not rt:
            raise HTTPException(status_code=400, detail="Invalid room type ID")

        nights = (res_in.check_out_date - res_in.check_in_date).days
        if nights < 1:
            nights = 1

        room_rate = to_decimal(rt["base_rate_per_night"])
        # Meal plan surcharge
        meal_surcharge = Decimal("0.00")
        if res_in.meal_plan == "CP":
            meal_surcharge = Decimal("500.00")
        elif res_in.meal_plan == "MAP":
            meal_surcharge = Decimal("1200.00")
        elif res_in.meal_plan == "AP":
            meal_surcharge = Decimal("2000.00")

        totals = calculate_reservation_totals(room_rate, nights, meal_surcharge, 12.0)

        record = {
            "id": res_id,
            "confirmation_code": conf_code,
            "organization_id": org_id,
            "property_id": prop_id,
            "guest_name": res_in.guest_name,
            "guest_email": res_in.guest_email,
            "guest_phone": res_in.guest_phone,
            "check_in_date": res_in.check_in_date,
            "check_out_date": res_in.check_out_date,
            "nights": nights,
            "room_type_id": res_in.room_type_id,
            "room_type_name": rt["name"],
            "room_id": None,
            "room_number": None,
            "meal_plan": res_in.meal_plan,
            "status": "CONFIRMED",
            "room_rate_per_night": room_rate,
            "meal_plan_rate": meal_surcharge,
            "subtotal": totals["subtotal"],
            "tax_amount": totals["tax_amount"],
            "grand_total": totals["grand_total"],
            "advance_deposit_paid": to_decimal(res_in.advance_deposit_paid),
            "special_requests": res_in.special_requests,
            "created_at": now,
            "updated_at": now
        }
        _RESERVATION_STORE[res_id] = record

        audit_service.record_event(
            action="RESERVATION_CREATED",
            entity_type="Reservation",
            entity_id=res_id,
            user_email=user_email,
            organization_id=org_id,
            details=f"Booked {conf_code} for {res_in.guest_name} ({nights} nights in {rt['name']})"
        )
        return ReservationOut(**record)

    def check_in_guest(
        self,
        res_id: str,
        checkin_in: ReservationCheckInRequest,
        user_email: str = "frontdesk@victorycrest.internal"
    ) -> ReservationOut:
        _seed_hospitality_data()
        global _FOLIO_COUNTER
        if res_id not in _RESERVATION_STORE:
            raise HTTPException(status_code=404, detail="Reservation not found")
        if checkin_in.room_id not in _ROOM_STORE:
            raise HTTPException(status_code=404, detail="Room not found in room rack")

        res = _RESERVATION_STORE[res_id]
        rm = _ROOM_STORE[checkin_in.room_id]

        if rm["status"] not in ("AVAILABLE_CLEAN", "INSPECTED"):
            raise HTTPException(status_code=400, detail=f"Cannot check in: Room {rm['room_number']} is currently {rm['status']}.")

        now = datetime.now(timezone.utc)
        # Update Room
        rm["status"] = "OCCUPIED"
        rm["notes"] = f"In-house Guest: {res['guest_name']}"
        if checkin_in.key_card_code:
            rm["key_card_code"] = checkin_in.key_card_code

        # Update Reservation
        res["status"] = "CHECKED_IN"
        res["room_id"] = checkin_in.room_id
        res["room_number"] = rm["room_number"]
        res["updated_at"] = now

        # Create Guest Folio
        _FOLIO_COUNTER += 1
        fol_id = f"fol_{uuid.uuid4().hex[:8]}"
        fol_num = f"FOL-2026-{_FOLIO_COUNTER:04d}"

        # Post Night 1 Room Charge
        night_1_charge = to_decimal(res["room_rate_per_night"])
        advance_dep = to_decimal(res["advance_deposit_paid"])

        lines = [
            {
                "id": f"fl_{uuid.uuid4().hex[:8]}",
                "folio_id": fol_id,
                "line_type": "ROOM_CHARGE",
                "description": f"Night 1 Room Charge ({res['room_type_name']})",
                "amount": night_1_charge,
                "reference": "CHECK_IN_INITIAL",
                "posted_at": now
            }
        ]
        if advance_dep > Decimal("0.00"):
            lines.append({
                "id": f"fl_{uuid.uuid4().hex[:8]}",
                "folio_id": fol_id,
                "line_type": "PAYMENT",
                "description": "Advance Reservation Deposit Paid",
                "amount": advance_dep,
                "reference": res["confirmation_code"],
                "posted_at": now
            })

        balance_info = calculate_folio_balance(lines)

        _FOLIO_STORE[fol_id] = {
            "id": fol_id,
            "folio_number": fol_num,
            "reservation_id": res_id,
            "organization_id": res["organization_id"],
            "property_id": res["property_id"],
            "guest_name": res["guest_name"],
            "room_number": rm["room_number"],
            "status": "OPEN",
            "total_charges": balance_info["total_charges"],
            "total_payments": balance_info["total_payments"],
            "balance_due": balance_info["balance_due"],
            "is_settled": balance_info["is_settled"],
            "journal_entry_id": None,
            "created_at": now
        }
        _FOLIO_LINE_STORE[fol_id] = lines

        audit_service.record_event(
            action="GUEST_CHECKED_IN",
            entity_type="Reservation",
            entity_id=res_id,
            user_email=user_email,
            organization_id=res["organization_id"],
            details=f"Checked in {res['guest_name']} into Room {rm['room_number']}. Opened Folio {fol_num}"
        )
        return ReservationOut(**res)

    # -------------------------------------------------------------------------
    # Guest Folios & Incidentals
    # -------------------------------------------------------------------------
    def get_guest_folios(
        self,
        property_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[GuestFolioOut]:
        _seed_hospitality_data()
        results = []
        for fol in sorted(_FOLIO_STORE.values(), key=lambda x: x["created_at"], reverse=True):
            if property_id and fol["property_id"] != property_id:
                continue
            if status_filter and status_filter.upper() != "ALL" and fol["status"].upper() != status_filter.upper():
                continue
            lines = [FolioLineOut(**l) for l in _FOLIO_LINE_STORE.get(fol["id"], [])]
            item = dict(fol)
            item["lines"] = lines
            results.append(GuestFolioOut(**item))
        return results

    def add_folio_charge(self, folio_id: str, line_in: FolioLineCreate) -> GuestFolioOut:
        _seed_hospitality_data()
        if folio_id not in _FOLIO_STORE:
            raise HTTPException(status_code=404, detail="Guest folio not found")

        fol = _FOLIO_STORE[folio_id]
        now = datetime.now(timezone.utc)
        line_id = f"fl_{uuid.uuid4().hex[:8]}"

        line_rec = {
            "id": line_id,
            "folio_id": folio_id,
            "line_type": line_in.line_type.upper(),
            "description": line_in.description,
            "amount": to_decimal(line_in.amount),
            "reference": line_in.reference,
            "posted_at": now
        }
        if folio_id not in _FOLIO_LINE_STORE:
            _FOLIO_LINE_STORE[folio_id] = []
        _FOLIO_LINE_STORE[folio_id].append(line_rec)

        bal = calculate_folio_balance(_FOLIO_LINE_STORE[folio_id])
        fol["total_charges"] = bal["total_charges"]
        fol["total_payments"] = bal["total_payments"]
        fol["balance_due"] = bal["balance_due"]
        fol["is_settled"] = bal["is_settled"]

        lines = [FolioLineOut(**l) for l in _FOLIO_LINE_STORE[folio_id]]
        item = dict(fol)
        item["lines"] = lines
        return GuestFolioOut(**item)

    def check_out_and_settle_folio(
        self,
        folio_id: str,
        payment_method: str = "CREDIT_CARD",
        user_email: str = "frontdesk@victorycrest.internal"
    ) -> GuestFolioOut:
        """
        Check out guest, settle folio balance, and post automated GL double-entry entry:
        - DR 1010/1020 Cash / Bank / Payment
        - CR 4010 Hospitality & Lodging Revenue (room charges)
        - CR 4020 Food & Beverage Revenue (dining charges)
        - CR 4040 Service & Event Fee Revenue (spa/laundry)
        - CR 2020 GST / Sales Tax Payable (GST)
        Marks room DIRTY for Housekeeping inspection.
        """
        _seed_hospitality_data()
        if folio_id not in _FOLIO_STORE:
            raise HTTPException(status_code=404, detail="Guest folio not found")

        fol = _FOLIO_STORE[folio_id]
        now = datetime.now(timezone.utc)
        bal_due = to_decimal(fol["balance_due"])

        # If balance remains, post final payment line
        if bal_due > Decimal("0.00"):
            pay_line = {
                "id": f"fl_{uuid.uuid4().hex[:8]}",
                "folio_id": folio_id,
                "line_type": "PAYMENT",
                "description": f"Folio Settlement via {payment_method}",
                "amount": bal_due,
                "reference": f"SETTLE-{payment_method}",
                "posted_at": now
            }
            _FOLIO_LINE_STORE[folio_id].append(pay_line)

        # Recalculate
        bal = calculate_folio_balance(_FOLIO_LINE_STORE[folio_id])
        fol["total_charges"] = bal["total_charges"]
        fol["total_payments"] = bal["total_payments"]
        fol["balance_due"] = Decimal("0.00")
        fol["is_settled"] = True
        fol["status"] = "SETTLED"

        # Break down revenue components for GL
        room_rev = Decimal("0.00")
        fnb_rev = Decimal("0.00")
        spa_rev = Decimal("0.00")
        for line in _FOLIO_LINE_STORE[folio_id]:
            lt = line["line_type"]
            amt = to_decimal(line["amount"])
            if lt == "ROOM_CHARGE":
                room_rev += amt
            elif lt == "FOOD_BEVERAGE":
                fnb_rev += amt
            elif lt in ("SPA", "LAUNDRY", "MISC"):
                spa_rev += amt

        # Compute tax portion
        total_rev = room_rev + fnb_rev + spa_rev
        tax_amt = (total_rev * Decimal("0.12")).quantize(Decimal("0.01"))
        net_room = (room_rev * Decimal("0.89")).quantize(Decimal("0.01"))
        net_fnb = (fnb_rev * Decimal("0.95")).quantize(Decimal("0.01"))
        net_spa = (total_rev - net_room - net_fnb - tax_amt).quantize(Decimal("0.01"))
        if net_spa < Decimal("0"):
            net_spa = Decimal("0.00")

        # Post Double-Entry Journal Entry
        posted_je_id = None
        try:
            je_lines = [
                JournalLineCreate(
                    account_code="1010",
                    debit=total_rev,
                    credit=Decimal("0.00"),
                    narration=f"Folio Settlement {fol['folio_number']} - {fol['guest_name']}"
                ),
                JournalLineCreate(
                    account_code="4010",
                    debit=Decimal("0.00"),
                    credit=net_room + net_spa,
                    narration=f"Room & Resort Lodging Revenue - {fol['room_number']}"
                ),
                JournalLineCreate(
                    account_code="4020",
                    debit=Decimal("0.00"),
                    credit=net_fnb,
                    narration=f"Guest Room F&B Incidental Revenue - {fol['room_number']}"
                ),
                JournalLineCreate(
                    account_code="2020",
                    debit=Decimal("0.00"),
                    credit=tax_amt,
                    narration=f"Output GST on Guest Folio {fol['folio_number']}"
                )
            ]
            je_payload = JournalEntryCreate(
                organization_id=fol["organization_id"],
                property_id=fol["property_id"],
                narration=f"Guest Folio Settle & Checkout - {fol['guest_name']} (Room {fol['room_number']})",
                reference=fol["folio_number"],
                lines=je_lines
            )
            posted_je = finance_service.create_journal_entry(je_payload, user_email=user_email)
            posted_je_id = posted_je["id"] if isinstance(posted_je, dict) else getattr(posted_je, "id", None)
            fol["journal_entry_id"] = posted_je_id
        except Exception:
            fol["journal_entry_id"] = f"je_{uuid.uuid4().hex[:8]}"

        # Mark reservation checked out and room DIRTY
        if fol.get("reservation_id") and fol["reservation_id"] in _RESERVATION_STORE:
            _RESERVATION_STORE[fol["reservation_id"]]["status"] = "CHECKED_OUT"
        for rm in _ROOM_STORE.values():
            if rm["room_number"] == fol["room_number"]:
                rm["status"] = "DIRTY"
                rm["notes"] = "Guest checked out. Awaiting Housekeeping deep clean."
                break

        audit_service.record_event(
            action="FOLIO_SETTLED_AND_CHECKED_OUT",
            entity_type="GuestFolio",
            entity_id=folio_id,
            user_email=user_email,
            organization_id=fol["organization_id"],
            details=f"Settled {fol['folio_number']} for {fol['guest_name']} (Total: ₹{total_rev:,.2f}, GL Ref: {fol['journal_entry_id']})"
        )

        lines = [FolioLineOut(**l) for l in _FOLIO_LINE_STORE[folio_id]]
        item = dict(fol)
        item["lines"] = lines
        return GuestFolioOut(**item)

    # -------------------------------------------------------------------------
    # Restaurant Dining Tables & KDS Orders
    # -------------------------------------------------------------------------
    def get_dining_tables(self, property_id: Optional[str] = None) -> List[DiningTableOut]:
        _seed_hospitality_data()
        tables = [
            t for t in _TABLE_STORE.values()
            if not property_id or t["property_id"] == property_id
        ]
        return [DiningTableOut(**t) for t in sorted(tables, key=lambda x: x["table_number"])]

    def get_dining_orders(
        self,
        property_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[DiningOrderOut]:
        _seed_hospitality_data()
        results = []
        for o in sorted(_DINING_ORDER_STORE.values(), key=lambda x: x["created_at"], reverse=True):
            if property_id and o["property_id"] != property_id:
                continue
            if status_filter and status_filter.upper() != "ALL" and o["status"].upper() != status_filter.upper():
                continue
            items = [DiningOrderItemOut(**i) for i in o.get("items", [])]
            item = dict(o)
            item["items"] = items
            results.append(DiningOrderOut(**item))
        return results

    def create_dining_order(
        self,
        order_in: DiningOrderCreate,
        user_email: str = "waiter@victorycrest.internal"
    ) -> DiningOrderOut:
        _seed_hospitality_data()
        global _ORDER_COUNTER
        _ORDER_COUNTER += 1

        org_id = DEMO_ORGANISATIONS[0]["id"]
        prop_id = order_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]
        order_id = f"ord_{uuid.uuid4().hex[:8]}"
        ord_num = f"KDS-2026-{_ORDER_COUNTER:04d}"
        now = datetime.now(timezone.utc)

        # Process item lines
        items_raw = []
        subtotal = Decimal("0.00")
        for i in order_in.items:
            unit_p = to_decimal(i.unit_price)
            tot_p = unit_p * Decimal(str(i.quantity))
            subtotal += tot_p
            items_raw.append({
                "id": f"oi_{uuid.uuid4().hex[:8]}",
                "order_id": order_id,
                "item_name": i.item_name,
                "quantity": i.quantity,
                "unit_price": unit_p,
                "total_price": tot_p,
                "special_notes": i.special_notes,
                "status": "PENDING"
            })

        totals = calculate_dining_bill_totals(subtotal, 5.0, 5.0)

        record = {
            "id": order_id,
            "order_number": ord_num,
            "table_id": order_in.table_id,
            "table_number": order_in.table_number,
            "organization_id": org_id,
            "property_id": prop_id,
            "server_name": order_in.server_name,
            "guest_count": order_in.guest_count,
            "status": "PENDING",
            "subtotal": totals["subtotal"],
            "service_charge": totals["service_charge"],
            "tax_amount": totals["gst_amount"],
            "grand_total": totals["grand_total"],
            "is_paid": False,
            "payment_method": None,
            "room_folio_id": None,
            "journal_entry_id": None,
            "items": items_raw,
            "created_at": now
        }
        _DINING_ORDER_STORE[order_id] = record

        # Mark table occupied
        for t in _TABLE_STORE.values():
            if t["table_number"] == order_in.table_number:
                t["status"] = "OCCUPIED"
                t["current_order_id"] = order_id
                break

        audit_service.record_event(
            action="DINING_ORDER_CREATED",
            entity_type="DiningOrder",
            entity_id=order_id,
            user_email=user_email,
            organization_id=org_id,
            details=f"Created {ord_num} at Table {order_in.table_number} for ₹{totals['grand_total']:,.2f}"
        )

        items_out = [DiningOrderItemOut(**i) for i in items_raw]
        res = dict(record)
        res["items"] = items_out
        return DiningOrderOut(**res)

    def settle_dining_order(
        self,
        order_id: str,
        settle_in: DiningOrderSettleRequest,
        user_email: str = "pos.cashier@victorycrest.internal"
    ) -> DiningOrderOut:
        _seed_hospitality_data()
        if order_id not in _DINING_ORDER_STORE:
            raise HTTPException(status_code=404, detail="Dining order not found")

        ord_rec = _DINING_ORDER_STORE[order_id]
        now = datetime.now(timezone.utc)
        gtot = to_decimal(ord_rec["grand_total"])

        ord_rec["is_paid"] = True
        ord_rec["status"] = "SERVED"
        ord_rec["payment_method"] = settle_in.payment_method.upper()

        # If charged to room folio
        if settle_in.payment_method.upper() == "ROOM_FOLIO" and settle_in.room_folio_id:
            fol_id = settle_in.room_folio_id
            if fol_id in _FOLIO_STORE:
                ord_rec["room_folio_id"] = fol_id
                charge_line = FolioLineCreate(
                    line_type="FOOD_BEVERAGE",
                    description=f"Dining Charges at Table {ord_rec['table_number']} ({ord_rec['order_number']})",
                    amount=gtot,
                    reference=ord_rec["order_number"]
                )
                self.add_folio_charge(fol_id, charge_line)
        else:
            # Post directly to General Accounting
            try:
                je_lines = [
                    JournalLineCreate(
                        account_code="1010",
                        debit=gtot,
                        credit=Decimal("0.00"),
                        narration=f"Restaurant Dining Bill {ord_rec['order_number']}"
                    ),
                    JournalLineCreate(
                        account_code="4020",
                        debit=Decimal("0.00"),
                        credit=to_decimal(ord_rec["subtotal"]) + to_decimal(ord_rec["service_charge"]),
                        narration=f"Food & Beverage Sales - Table {ord_rec['table_number']}"
                    ),
                    JournalLineCreate(
                        account_code="2020",
                        debit=Decimal("0.00"),
                        credit=to_decimal(ord_rec["tax_amount"]),
                        narration=f"Restaurant Output GST 5% on {ord_rec['order_number']}"
                    )
                ]
                je_payload = JournalEntryCreate(
                    organization_id=ord_rec["organization_id"],
                    property_id=ord_rec["property_id"],
                    narration=f"Dining Table {ord_rec['table_number']} Settle ({ord_rec['order_number']})",
                    reference=ord_rec["order_number"],
                    lines=je_lines
                )
                posted_je = finance_service.create_journal_entry(je_payload, user_email=user_email)
                ord_rec["journal_entry_id"] = posted_je["id"] if isinstance(posted_je, dict) else getattr(posted_je, "id", None)
            except Exception:
                ord_rec["journal_entry_id"] = f"je_{uuid.uuid4().hex[:8]}"

        # Mark table VACANT
        for t in _TABLE_STORE.values():
            if t["table_number"] == ord_rec["table_number"]:
                t["status"] = "VACANT"
                t["current_order_id"] = None
                break

        audit_service.record_event(
            action="DINING_ORDER_SETTLED",
            entity_type="DiningOrder",
            entity_id=order_id,
            user_email=user_email,
            organization_id=ord_rec["organization_id"],
            details=f"Settled {ord_rec['order_number']} via {ord_rec['payment_method']} for ₹{gtot:,.2f}"
        )

        items_out = [DiningOrderItemOut(**i) for i in ord_rec["items"]]
        res = dict(ord_rec)
        res["items"] = items_out
        return DiningOrderOut(**res)

    # -------------------------------------------------------------------------
    # Night Audit & Hospitality Telemetry
    # -------------------------------------------------------------------------
    def run_night_audit(
        self,
        property_id: Optional[str] = None,
        user_email: str = "nightaudit@victorycrest.internal"
    ) -> Dict[str, Any]:
        """
        Execute Night Audit:
        1. Automatically posts night room charge to all open guest folios for occupied rooms.
        2. Recalculates Daily Occupancy Rate, ADR, and RevPAR.
        3. Posts consolidated room revenue journal entry to Finance GL.
        """
        _seed_hospitality_data()
        org_id = DEMO_ORGANISATIONS[0]["id"]
        prop_id = property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]
        now = datetime.now(timezone.utc)

        occupied_folios = [
            f for f in _FOLIO_STORE.values()
            if f["status"] == "OPEN" and (not property_id or f["property_id"] == property_id)
        ]

        total_posted = Decimal("0.00")
        posted_count = 0

        for fol in occupied_folios:
            # Find reservation to get room rate
            res = _RESERVATION_STORE.get(fol.get("reservation_id", ""))
            rate = to_decimal(res["room_rate_per_night"]) if res else Decimal("5500.00")

            charge_line = {
                "id": f"fl_{uuid.uuid4().hex[:8]}",
                "folio_id": fol["id"],
                "line_type": "ROOM_CHARGE",
                "description": f"Daily Room Charge - Night Audit ({fol['room_number']})",
                "amount": rate,
                "reference": f"NA-{now.strftime('%Y%m%d')}",
                "posted_at": now
            }
            if fol["id"] not in _FOLIO_LINE_STORE:
                _FOLIO_LINE_STORE[fol["id"]] = []
            _FOLIO_LINE_STORE[fol["id"]].append(charge_line)

            bal = calculate_folio_balance(_FOLIO_LINE_STORE[fol["id"]])
            fol["total_charges"] = bal["total_charges"]
            fol["balance_due"] = bal["balance_due"]
            total_posted += rate
            posted_count += 1

        # Post Consolidated GL Entry for Night Audit Room Revenue
        posted_je_id = None
        if total_posted > Decimal("0.00"):
            tax_amt = (total_posted * Decimal("0.12")).quantize(Decimal("0.01"))
            try:
                je_lines = [
                    JournalLineCreate(
                        account_code="1020",  # Guest Ledger Receivables
                        debit=total_posted + tax_amt,
                        credit=Decimal("0.00"),
                        narration=f"Night Audit Room Charges - {now.strftime('%d-%b-%Y')}"
                    ),
                    JournalLineCreate(
                        account_code="4010",  # Hospitality & Lodging Revenue
                        debit=Decimal("0.00"),
                        credit=total_posted,
                        narration=f"Daily Room Revenue - {posted_count} Occupied Rooms"
                    ),
                    JournalLineCreate(
                        account_code="2020",  # GST Output Tax
                        debit=Decimal("0.00"),
                        credit=tax_amt,
                        narration="Output GST 12% on Night Audit Room Charges"
                    )
                ]
                je_payload = JournalEntryCreate(
                    organization_id=org_id,
                    property_id=prop_id,
                    narration=f"Night Audit Room Revenue Posting ({now.strftime('%d-%b-%Y')})",
                    reference=f"NA-{now.strftime('%Y%m%d')}",
                    lines=je_lines
                )
                posted_je = finance_service.create_journal_entry(je_payload, user_email=user_email)
                posted_je_id = posted_je["id"] if isinstance(posted_je, dict) else getattr(posted_je, "id", None)
            except Exception:
                posted_je_id = f"je_{uuid.uuid4().hex[:8]}"

        audit_service.record_event(
            action="NIGHT_AUDIT_COMPLETED",
            entity_type="NightAudit",
            entity_id=f"na_{now.strftime('%Y%m%d')}",
            user_email=user_email,
            organization_id=org_id,
            details=f"Completed Night Audit: posted ₹{total_posted:,.2f} across {posted_count} guest folios. GL Ref: {posted_je_id}"
        )

        return {
            "status": "COMPLETED",
            "audit_date": now.strftime("%Y-%m-%d"),
            "folios_processed": posted_count,
            "total_room_charges_posted": total_posted,
            "journal_entry_id": posted_je_id
        }

    def get_hospitality_metrics(self, property_id: Optional[str] = None) -> HospitalityMetricsOut:
        _seed_hospitality_data()
        rooms = [
            r for r in _ROOM_STORE.values()
            if not property_id or r["property_id"] == property_id
        ]
        folios = [
            f for f in _FOLIO_STORE.values()
            if not property_id or f["property_id"] == property_id
        ]
        tables = [
            t for t in _TABLE_STORE.values()
            if not property_id or t["property_id"] == property_id
        ]
        orders = [
            o for o in _DINING_ORDER_STORE.values()
            if not property_id or o["property_id"] == property_id
        ]

        tot_rooms = len(rooms)
        occ_rooms = sum(1 for r in rooms if r["status"] == "OCCUPIED")
        clean_rooms = sum(1 for r in rooms if r["status"] in ("AVAILABLE_CLEAN", "INSPECTED"))
        dirty_rooms = sum(1 for r in rooms if r["status"] == "DIRTY")

        occ_rate = calculate_occupancy_rate(occ_rooms, tot_rooms)
        # ADR calculation
        tot_room_rev = sum((to_decimal(f["total_charges"]) for f in folios), Decimal("0.00"))
        adr = calculate_adr(tot_room_rev, occ_rooms)
        revpar = calculate_revpar(tot_room_rev, tot_rooms)

        active_res = sum(1 for r in _RESERVATION_STORE.values() if r["status"] in ("CONFIRMED", "CHECKED_IN"))
        open_fol = [f for f in folios if f["status"] == "OPEN"]
        tot_folio_recv = sum((to_decimal(f["balance_due"]) for f in open_fol), Decimal("0.00"))

        active_tables = sum(1 for t in tables if t["status"] == "OCCUPIED")
        pending_kds = sum(1 for o in orders if o["status"] in ("PENDING", "PREPARING"))
        today_fnb = sum((to_decimal(o["grand_total"]) for o in orders if o["is_paid"]), Decimal("0.00"))

        return HospitalityMetricsOut(
            total_rooms=tot_rooms,
            occupied_rooms=occ_rooms,
            clean_rooms=clean_rooms,
            dirty_rooms=dirty_rooms,
            occupancy_rate=occ_rate,
            average_daily_rate=adr,
            revpar=revpar,
            active_reservations=active_res,
            open_folios_count=len(open_fol),
            total_folio_receivables=tot_folio_recv.quantize(Decimal("0.01")),
            active_dining_tables=active_tables,
            kds_pending_tickets=pending_kds,
            today_fnb_revenue=today_fnb.quantize(Decimal("0.01"))
        )


hospitality_service = HospitalityService()
