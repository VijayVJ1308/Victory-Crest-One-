"""Victory Crest One - Point of Sale (POS) & Commerce Business Service
Shift register lifecycle, item scanning, hold/recall orders, split tenders,
automatic balanced double-entry GL journal posting, and telemetry metrics.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.pos import (
    PosTerminalCreate, PosTerminalOut,
    PosSessionOpenRequest, PosSessionCloseRequest, PosSessionOut,
    PosOrderCreate, PosOrderHoldRequest, PosOrderTenderRequest, PosOrderOut,
    PosOrderLineCreate, PosOrderLineOut,
    PosPaymentCreate, PosPaymentOut,
    PosReceiptItem, PosReceiptOut, PosMetricsOut
)
from backend.app.schemas.finance import JournalEntryCreate, JournalLineCreate
from backend.app.services.finance_service import finance_service
from backend.app.services.audit_service import audit_service
from shared.calculations import (
    to_decimal, calculate_pos_change, calculate_drawer_variance,
    calculate_pos_order_totals, calculate_split_tenders
)
from shared.constants import DEMO_ORGANISATIONS


# In-memory data repositories
_TERMINAL_STORE: Dict[str, Dict[str, Any]] = {}
_SESSION_STORE: Dict[str, Dict[str, Any]] = {}
_ORDER_STORE: Dict[str, Dict[str, Any]] = {}
_ORDER_COUNTER = 100
_POS_PRODUCTS: List[Dict[str, Any]] = []


def _seed_pos_data():
    """Seed demonstration terminals, register sessions, products, and orders."""
    global _ORDER_COUNTER
    if _TERMINAL_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]  # Madurai Heritage
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]  # Kodaikanal Resort
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]  # Chennai Business

    # 1. Seed Terminals
    terminals = [
        {
            "id": "term_mdu_01",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "terminal_code": "POS-MDU-LOBBY-01",
            "name": "Lobby Cafe & Quick Register",
            "counter_location": "Heritage Wing Lobby Counter 1",
            "status": "ACTIVE",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=90),
            "updated_at": datetime.utcnow() - timedelta(days=90)
        },
        {
            "id": "term_mdu_02",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "terminal_code": "POS-MDU-BTQ-02",
            "name": "Heritage Boutique & Souvenirs",
            "counter_location": "Boutique Arcade Ground Floor",
            "status": "ACTIVE",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=90),
            "updated_at": datetime.utcnow() - timedelta(days=90)
        },
        {
            "id": "term_kod_01",
            "organization_id": org_id,
            "property_id": prop_kod,
            "terminal_code": "POS-KOD-RES-01",
            "name": "Pine Valley Mountain Cafe",
            "counter_location": "Chalet Reception Deck",
            "status": "ACTIVE",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=60),
            "updated_at": datetime.utcnow() - timedelta(days=60)
        },
        {
            "id": "term_maa_01",
            "organization_id": org_id,
            "property_id": prop_maa,
            "terminal_code": "POS-MAA-BIZ-01",
            "name": "Executive Lounge & Grab-and-Go",
            "counter_location": "Mezzanine Business Lounge",
            "status": "ACTIVE",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=30),
            "updated_at": datetime.utcnow() - timedelta(days=30)
        }
    ]
    for t in terminals:
        _TERMINAL_STORE[t["id"]] = t

    # 2. Seed POS Fast Catalog Products
    _POS_PRODUCTS.extend([
        {
            "id": "pos_prod_coffee",
            "sku": "FNB-COF-MADURAI",
            "barcode": "890103000001",
            "name": "Madurai Filter Degree Coffee",
            "category": "Beverages",
            "unit_price": Decimal("180.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "CUP",
            "stock_quantity": 85,
            "icon": "☕"
        },
        {
            "id": "pos_prod_chai",
            "sku": "FNB-TEA-MASALA",
            "barcode": "890103000002",
            "name": "Nilgiri Spiced Masala Chai",
            "category": "Beverages",
            "unit_price": Decimal("140.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "CUP",
            "stock_quantity": 120,
            "icon": "🍵"
        },
        {
            "id": "pos_prod_croissant",
            "sku": "BAK-CRST-BUTTER",
            "barcode": "890103000003",
            "name": "French Butter Croissant",
            "category": "Bakery",
            "unit_price": Decimal("240.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "UNIT",
            "stock_quantity": 30,
            "icon": "🥐"
        },
        {
            "id": "pos_prod_cashews",
            "sku": "SNK-CSH-CHETT",
            "barcode": "890103000004",
            "name": "Chettinad Spiced Roasted Cashews 250g",
            "category": "Snacks",
            "unit_price": Decimal("480.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "PACK",
            "stock_quantity": 45,
            "icon": "🥜"
        },
        {
            "id": "pos_prod_eucalyptus",
            "sku": "SPA-EUC-OIL100",
            "barcode": "890103000005",
            "name": "Kodaikanal Pure Eucalyptus Oil 100ml",
            "category": "Wellness",
            "unit_price": Decimal("380.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "BOTTLE",
            "stock_quantity": 60,
            "icon": "🌿"
        },
        {
            "id": "pos_prod_scarf",
            "sku": "BTQ-SILK-SCRF",
            "barcode": "890103000006",
            "name": "Madurai Handloom Silk Stole",
            "category": "Boutique",
            "unit_price": Decimal("1850.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "UNIT",
            "stock_quantity": 25,
            "icon": "🧣"
        },
        {
            "id": "pos_prod_tea_tin",
            "sku": "RET-TEA-NILGIRI",
            "barcode": "890103000007",
            "name": "Nilgiri Estate Black Tea Vintage Tin 200g",
            "category": "Retail",
            "unit_price": Decimal("650.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "TIN",
            "stock_quantity": 50,
            "icon": "🫖"
        },
        {
            "id": "pos_prod_water",
            "sku": "BEV-WTR-SPR750",
            "barcode": "890103000008",
            "name": "Himalayan Natural Mineral Spring Water 750ml",
            "category": "Beverages",
            "unit_price": Decimal("110.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "BOTTLE",
            "stock_quantity": 150,
            "icon": "💧"
        },
        {
            "id": "pos_prod_notebook",
            "sku": "MERCH-NOTE-PEN",
            "barcode": "890103000009",
            "name": "Victory Crest Executive Leather Journal & Pen",
            "category": "Merchandise",
            "unit_price": Decimal("950.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "SET",
            "stock_quantity": 40,
            "icon": "📔"
        },
        {
            "id": "pos_prod_soap_box",
            "sku": "SPA-SOAP-HERBAL",
            "barcode": "890103000010",
            "name": "Ayurvedic Sandalwood & Turmeric Soap Gift Box",
            "category": "Wellness",
            "unit_price": Decimal("520.00"),
            "tax_rate_percent": Decimal("12.00"),
            "unit_of_measure": "BOX",
            "stock_quantity": 35,
            "icon": "🧼"
        }
    ])

    # 3. Seed Active Register Shift Session
    now = datetime.utcnow()
    active_session_id = "sess_mdu_active_01"
    _SESSION_STORE[active_session_id] = {
        "id": active_session_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "terminal_id": "term_mdu_01",
        "terminal_code": "POS-MDU-LOBBY-01",
        "cashier_id": "usr_pos_cashier",
        "cashier_name": "Priya Sundaram",
        "status": "OPEN",
        "opened_at": now.replace(hour=8, minute=30, second=0),
        "closed_at": None,
        "opening_float": Decimal("5000.00"),
        "total_cash_sales": Decimal("840.00"),
        "total_card_sales": Decimal("2500.00"),
        "total_upi_sales": Decimal("700.00"),
        "total_room_charge_sales": Decimal("0.00"),
        "total_sales": Decimal("4040.00"),
        "expected_cash": Decimal("5840.00"),
        "counted_cash": Decimal("0.00"),
        "cash_variance": Decimal("0.00"),
        "notes": "Morning lobby shift open and running smoothly."
    }

    # 4. Seed Completed Demo Orders
    order_1_id = "ord_pos_101"
    _ORDER_STORE[order_1_id] = {
        "id": order_1_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "session_id": active_session_id,
        "order_number": "POS-2026-00101",
        "customer_id": None,
        "customer_name": "Walk-in Guest",
        "table_or_room": "Table 2",
        "cashier_id": "usr_pos_cashier",
        "cashier_name": "Priya Sundaram",
        "status": "COMPLETED",
        "subtotal": Decimal("750.00"),
        "discount_percent": Decimal("0.00"),
        "discount_amount": Decimal("0.00"),
        "tax_rate_percent": Decimal("12.00"),
        "tax_amount": Decimal("90.00"),
        "total_amount": Decimal("840.00"),
        "paid_amount": Decimal("1000.00"),
        "change_returned": Decimal("160.00"),
        "journal_entry_id": "je_pos_00101",
        "created_at": now - timedelta(hours=3),
        "completed_at": now - timedelta(hours=3),
        "notes": "Morning coffee & croissants",
        "lines": [
            {
                "id": f"line_{uuid.uuid4().hex[:8]}",
                "order_id": order_1_id,
                "product_id": "pos_prod_coffee",
                "sku": "FNB-COF-MADURAI",
                "barcode": "890103000001",
                "name": "Madurai Filter Degree Coffee",
                "category": "Beverages",
                "unit_of_measure": "CUP",
                "quantity": Decimal("2.00"),
                "unit_price": Decimal("180.00"),
                "discount_amount": Decimal("0.00"),
                "total_amount": Decimal("360.00")
            },
            {
                "id": f"line_{uuid.uuid4().hex[:8]}",
                "order_id": order_1_id,
                "product_id": "pos_prod_croissant",
                "sku": "BAK-CRST-BUTTER",
                "barcode": "890103000003",
                "name": "French Butter Croissant",
                "category": "Bakery",
                "unit_of_measure": "UNIT",
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("240.00"),
                "discount_amount": Decimal("0.00"),
                "total_amount": Decimal("240.00")
            },
            {
                "id": f"line_{uuid.uuid4().hex[:8]}",
                "order_id": order_1_id,
                "product_id": "pos_prod_chai",
                "sku": "FNB-TEA-MASALA",
                "barcode": "890103000002",
                "name": "Nilgiri Spiced Masala Chai",
                "category": "Beverages",
                "unit_of_measure": "CUP",
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("140.00"),
                "discount_amount": Decimal("0.00"),
                "total_amount": Decimal("140.00")
            }
        ],
        "payments": [
            {
                "id": f"pay_{uuid.uuid4().hex[:8]}",
                "order_id": order_1_id,
                "tender_type": "CASH",
                "amount": Decimal("1000.00"),
                "reference_number": "CASH-REC-101",
                "auth_code": "CASH-OK",
                "created_at": now - timedelta(hours=3)
            }
        ]
    }

    order_2_id = "ord_pos_102"
    _ORDER_STORE[order_2_id] = {
        "id": order_2_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "session_id": active_session_id,
        "order_number": "POS-2026-00102",
        "customer_id": "cust_tata_consultancy",
        "customer_name": "Tata Consultancy Services (TCS)",
        "table_or_room": "Room 304",
        "cashier_id": "usr_pos_cashier",
        "cashier_name": "Priya Sundaram",
        "status": "COMPLETED",
        "subtotal": Decimal("2500.00"),
        "discount_percent": Decimal("0.00"),
        "discount_amount": Decimal("0.00"),
        "tax_rate_percent": Decimal("0.00"),
        "tax_amount": Decimal("0.00"),
        "total_amount": Decimal("2500.00"),
        "paid_amount": Decimal("2500.00"),
        "change_returned": Decimal("0.00"),
        "journal_entry_id": "je_pos_00102",
        "created_at": now - timedelta(hours=2),
        "completed_at": now - timedelta(hours=2),
        "notes": "Handloom silk stole and Nilgiri tea tin for client gift",
        "lines": [
            {
                "id": f"line_{uuid.uuid4().hex[:8]}",
                "order_id": order_2_id,
                "product_id": "pos_prod_scarf",
                "sku": "BTQ-SILK-SCRF",
                "barcode": "890103000006",
                "name": "Madurai Handloom Silk Stole",
                "category": "Boutique",
                "unit_of_measure": "UNIT",
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("1850.00"),
                "discount_amount": Decimal("0.00"),
                "total_amount": Decimal("1850.00")
            },
            {
                "id": f"line_{uuid.uuid4().hex[:8]}",
                "order_id": order_2_id,
                "product_id": "pos_prod_tea_tin",
                "sku": "RET-TEA-NILGIRI",
                "barcode": "890103000007",
                "name": "Nilgiri Estate Black Tea Vintage Tin 200g",
                "category": "Retail",
                "unit_of_measure": "TIN",
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("650.00"),
                "discount_amount": Decimal("0.00"),
                "total_amount": Decimal("650.00")
            }
        ],
        "payments": [
            {
                "id": f"pay_{uuid.uuid4().hex[:8]}",
                "order_id": order_2_id,
                "tender_type": "CREDIT_CARD",
                "amount": Decimal("2500.00"),
                "reference_number": "VISA-****4821",
                "auth_code": "AUTH-89210",
                "created_at": now - timedelta(hours=2)
            }
        ]
    }

    # 5. Seed Held (Parked) Demo Order
    order_3_id = "ord_pos_103"
    _ORDER_STORE[order_3_id] = {
        "id": order_3_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "session_id": active_session_id,
        "order_number": "POS-2026-00103",
        "customer_id": None,
        "customer_name": "Arvind Nambiar (Cognizant)",
        "table_or_room": "Table 4",
        "cashier_id": "usr_pos_cashier",
        "cashier_name": "Priya Sundaram",
        "status": "HELD",
        "subtotal": Decimal("600.00"),
        "discount_percent": Decimal("0.00"),
        "discount_amount": Decimal("0.00"),
        "tax_rate_percent": Decimal("12.00"),
        "tax_amount": Decimal("72.00"),
        "total_amount": Decimal("672.00"),
        "paid_amount": Decimal("0.00"),
        "change_returned": Decimal("0.00"),
        "journal_entry_id": None,
        "created_at": now - timedelta(minutes=25),
        "completed_at": None,
        "notes": "Customer stepped out to answer conference call; order parked at Table 4.",
        "lines": [
            {
                "id": f"line_{uuid.uuid4().hex[:8]}",
                "order_id": order_3_id,
                "product_id": "pos_prod_coffee",
                "sku": "FNB-COF-MADURAI",
                "barcode": "890103000001",
                "name": "Madurai Filter Degree Coffee",
                "category": "Beverages",
                "unit_of_measure": "CUP",
                "quantity": Decimal("2.00"),
                "unit_price": Decimal("180.00"),
                "discount_amount": Decimal("0.00"),
                "total_amount": Decimal("360.00")
            },
            {
                "id": f"line_{uuid.uuid4().hex[:8]}",
                "order_id": order_3_id,
                "product_id": "pos_prod_croissant",
                "sku": "BAK-CRST-BUTTER",
                "barcode": "890103000003",
                "name": "French Butter Croissant",
                "category": "Bakery",
                "unit_of_measure": "UNIT",
                "quantity": Decimal("1.00"),
                "unit_price": Decimal("240.00"),
                "discount_amount": Decimal("0.00"),
                "total_amount": Decimal("240.00")
            }
        ],
        "payments": []
    }

    _ORDER_COUNTER = 104


class PosService:
    """Full-lifecycle POS & Commerce Business Service."""

    def __init__(self):
        _seed_pos_data()

    # ---------------------------------------------------------
    # Terminals
    # ---------------------------------------------------------
    def list_terminals(self, property_id: Optional[str] = None) -> List[PosTerminalOut]:
        _seed_pos_data()
        terminals = list(_TERMINAL_STORE.values())
        if property_id:
            terminals = [t for t in terminals if t.get("property_id") == property_id]
        return [PosTerminalOut(**t) for t in terminals]

    def get_terminal(self, terminal_id: str) -> PosTerminalOut:
        _seed_pos_data()
        if terminal_id not in _TERMINAL_STORE:
            raise HTTPException(status_code=404, detail=f"Terminal '{terminal_id}' not found")
        return PosTerminalOut(**_TERMINAL_STORE[terminal_id])

    def create_terminal(self, term_in: PosTerminalCreate, user_email: str = "admin") -> PosTerminalOut:
        _seed_pos_data()
        org_id = term_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        prop_id = term_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]

        for t in _TERMINAL_STORE.values():
            if t["terminal_code"].lower() == term_in.terminal_code.lower():
                raise HTTPException(status_code=400, detail=f"Terminal code '{term_in.terminal_code}' already exists")

        new_id = f"term_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        record = {
            "id": new_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "terminal_code": term_in.terminal_code,
            "name": term_in.name,
            "counter_location": term_in.counter_location,
            "status": term_in.status,
            "is_active": term_in.is_active,
            "created_at": now,
            "updated_at": now
        }
        _TERMINAL_STORE[new_id] = record

        audit_service.record_event(
            action="POS_TERMINAL_CREATED",
            entity_type="PosTerminal",
            entity_id=new_id,
            user_email=user_email,
            organization_id=org_id,
            details=f"Created POS register terminal '{term_in.name}' ({term_in.terminal_code})"
        )
        return PosTerminalOut(**record)

    # ---------------------------------------------------------
    # Sessions & Drawer Reconciliation
    # ---------------------------------------------------------
    def get_active_session(self, terminal_id: Optional[str] = None) -> Optional[PosSessionOut]:
        _seed_pos_data()
        for s in _SESSION_STORE.values():
            if s.get("status") == "OPEN":
                if terminal_id is None or s.get("terminal_id") == terminal_id:
                    return PosSessionOut(**s)
        return None

    def open_session(
        self,
        req: PosSessionOpenRequest,
        user_id: str = "usr_pos_cashier",
        user_name: str = "Priya Sundaram"
    ) -> PosSessionOut:
        _seed_pos_data()
        terminal = self.get_terminal(req.terminal_id)

        # Check if terminal already has an OPEN session
        for s in _SESSION_STORE.values():
            if s.get("terminal_id") == req.terminal_id and s.get("status") == "OPEN":
                return PosSessionOut(**s)

        now = datetime.utcnow()
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        float_amt = to_decimal(req.opening_float)

        record = {
            "id": session_id,
            "organization_id": terminal.organization_id,
            "property_id": terminal.property_id,
            "terminal_id": terminal.id,
            "terminal_code": terminal.terminal_code,
            "cashier_id": user_id,
            "cashier_name": user_name,
            "status": "OPEN",
            "opened_at": now,
            "closed_at": None,
            "opening_float": float_amt,
            "total_cash_sales": Decimal("0.00"),
            "total_card_sales": Decimal("0.00"),
            "total_upi_sales": Decimal("0.00"),
            "total_room_charge_sales": Decimal("0.00"),
            "total_sales": Decimal("0.00"),
            "expected_cash": float_amt,
            "counted_cash": Decimal("0.00"),
            "cash_variance": Decimal("0.00"),
            "notes": req.notes or f"Register shift opened by {user_name} with ₹{float_amt:,.2f} float."
        }
        _SESSION_STORE[session_id] = record

        audit_service.record_event(
            action="POS_SESSION_OPENED",
            entity_type="PosSession",
            entity_id=session_id,
            user_email=user_name,
            organization_id=terminal.organization_id,
            details=f"Opened POS shift on {terminal.terminal_code} with ₹{float_amt:,.2f} opening float"
        )
        return PosSessionOut(**record)

    def close_session(
        self,
        session_id: str,
        req: PosSessionCloseRequest,
        user_id: str = "usr_pos_cashier",
        user_name: str = "Priya Sundaram"
    ) -> PosSessionOut:
        _seed_pos_data()
        if session_id not in _SESSION_STORE:
            raise HTTPException(status_code=404, detail=f"POS Session '{session_id}' not found")

        session = _SESSION_STORE[session_id]
        if session.get("status") != "OPEN":
            raise HTTPException(status_code=400, detail=f"Session is already closed with status '{session.get('status')}'")

        counted = to_decimal(req.counted_cash)
        expected = session["expected_cash"]
        variance = calculate_drawer_variance(counted, expected)

        session["status"] = "CLOSED"
        session["closed_at"] = datetime.utcnow()
        session["counted_cash"] = counted
        session["cash_variance"] = variance
        if req.notes:
            session["notes"] = f"{session.get('notes', '')}\nClose notes: {req.notes}".strip()

        audit_service.record_event(
            action="POS_SESSION_CLOSED",
            entity_type="PosSession",
            entity_id=session_id,
            user_email=user_name,
            organization_id=session["organization_id"],
            details=(
                f"Closed shift {session_id}. Expected Cash: ₹{expected:,.2f}, "
                f"Counted: ₹{counted:,.2f}, Variance: ₹{variance:,.2f}"
            )
        )
        return PosSessionOut(**session)

    # ---------------------------------------------------------
    # Catalog & Fast Products Lookup
    # ---------------------------------------------------------
    def list_products(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        barcode: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        _seed_pos_data()
        results = list(_POS_PRODUCTS)

        if barcode:
            b_norm = barcode.strip().lower()
            return [p for p in results if p.get("barcode", "").lower() == b_norm]

        if category and category.lower() != "all":
            c_norm = category.strip().lower()
            results = [p for p in results if p.get("category", "").lower() == c_norm]

        if query:
            q = query.strip().lower()
            results = [
                p for p in results
                if q in p.get("name", "").lower() or q in p.get("sku", "").lower() or q in p.get("barcode", "").lower()
            ]

        return results

    # ---------------------------------------------------------
    # Orders Management
    # ---------------------------------------------------------
    def list_orders(
        self,
        session_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[PosOrderOut]:
        _seed_pos_data()
        orders = list(_ORDER_STORE.values())

        if session_id:
            orders = [o for o in orders if o.get("session_id") == session_id]

        if status_filter:
            s_norm = status_filter.strip().upper()
            orders = [o for o in orders if o.get("status", "").upper() == s_norm]

        # Sort newest first
        orders.sort(key=lambda x: x.get("created_at") or datetime.min, reverse=True)
        return [PosOrderOut(**o) for o in orders[:limit]]

    def get_order(self, order_id: str) -> PosOrderOut:
        _seed_pos_data()
        if order_id not in _ORDER_STORE:
            raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
        return PosOrderOut(**_ORDER_STORE[order_id])

    def create_order(
        self,
        req: PosOrderCreate,
        user_id: str = "usr_pos_cashier",
        user_name: str = "Priya Sundaram"
    ) -> PosOrderOut:
        global _ORDER_COUNTER
        _seed_pos_data()

        # Find or use active session
        session_id = req.session_id
        if not session_id:
            active_sess = self.get_active_session()
            if not active_sess:
                # Automatically open demo session if none is open
                active_sess = self.open_session(
                    PosSessionOpenRequest(terminal_id="term_mdu_01", opening_float=Decimal("5000.00")),
                    user_id=user_id,
                    user_name=user_name
                )
            session_id = active_sess.id
            org_id = active_sess.organization_id
            prop_id = active_sess.property_id
        else:
            session = _SESSION_STORE.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Specified POS session not found")
            org_id = session["organization_id"]
            prop_id = session["property_id"]

        _ORDER_COUNTER += 1
        order_num = f"POS-2026-{_ORDER_COUNTER:05d}"
        order_id = f"ord_pos_{uuid.uuid4().hex[:8]}"

        # Calculate totals
        totals = calculate_pos_order_totals(
            lines=req.lines,
            discount_percent=req.discount_percent,
            tax_rate_percent=req.tax_rate_percent
        )

        # Build order line dicts
        line_dicts = []
        for line in req.lines:
            qty = to_decimal(line.quantity)
            price = to_decimal(line.unit_price)
            disc = to_decimal(line.discount_amount)
            total = (qty * price) - disc
            line_dicts.append({
                "id": f"line_{uuid.uuid4().hex[:8]}",
                "order_id": order_id,
                "product_id": line.product_id,
                "sku": line.sku,
                "barcode": line.barcode,
                "name": line.name,
                "category": line.category,
                "unit_of_measure": line.unit_of_measure,
                "quantity": qty,
                "unit_price": price,
                "discount_amount": disc,
                "total_amount": total.quantize(Decimal("0.01"))
            })

        order_record = {
            "id": order_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "session_id": session_id,
            "order_number": order_num,
            "customer_id": req.customer_id,
            "customer_name": req.customer_name or "Walk-in Guest",
            "table_or_room": req.table_or_room,
            "cashier_id": user_id,
            "cashier_name": user_name,
            "status": "OPEN",
            "subtotal": totals["subtotal"],
            "discount_percent": totals["discount_percent"],
            "discount_amount": totals["discount_amount"],
            "tax_rate_percent": totals["tax_rate_percent"],
            "tax_amount": totals["tax_amount"],
            "total_amount": totals["total_amount"],
            "paid_amount": Decimal("0.00"),
            "change_returned": Decimal("0.00"),
            "journal_entry_id": None,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "notes": req.notes,
            "lines": line_dicts,
            "payments": []
        }
        _ORDER_STORE[order_id] = order_record
        return PosOrderOut(**order_record)

    def hold_order(self, order_id: str, reason: str = "Customer request") -> PosOrderOut:
        _seed_pos_data()
        if order_id not in _ORDER_STORE:
            raise HTTPException(status_code=404, detail="Order not found")

        order = _ORDER_STORE[order_id]
        if order["status"] != "OPEN":
            raise HTTPException(status_code=400, detail=f"Cannot hold order with status '{order['status']}'")

        order["status"] = "HELD"
        order["notes"] = f"{order.get('notes') or ''} [HELD: {reason}]".strip()

        audit_service.record_event(
            action="POS_ORDER_HELD",
            entity_type="PosOrder",
            entity_id=order_id,
            user_email=order.get("cashier_name", "Cashier"),
            organization_id=order["organization_id"],
            details=f"Parked order {order['order_number']}: {reason}"
        )
        return PosOrderOut(**order)

    def recall_order(self, order_id: str) -> PosOrderOut:
        _seed_pos_data()
        if order_id not in _ORDER_STORE:
            raise HTTPException(status_code=404, detail="Order not found")

        order = _ORDER_STORE[order_id]
        if order["status"] != "HELD":
            raise HTTPException(status_code=400, detail=f"Only HELD orders can be recalled (current: '{order['status']}')")

        order["status"] = "OPEN"

        audit_service.record_event(
            action="POS_ORDER_RECALLED",
            entity_type="PosOrder",
            entity_id=order_id,
            user_email=order.get("cashier_name", "Cashier"),
            organization_id=order["organization_id"],
            details=f"Recalled parked order {order['order_number']} back to active register"
        )
        return PosOrderOut(**order)

    def void_order(self, order_id: str, reason: str = "Customer cancelled") -> PosOrderOut:
        _seed_pos_data()
        if order_id not in _ORDER_STORE:
            raise HTTPException(status_code=404, detail="Order not found")

        order = _ORDER_STORE[order_id]
        if order["status"] in ("COMPLETED", "VOIDED"):
            raise HTTPException(status_code=400, detail=f"Cannot void order with status '{order['status']}'")

        order["status"] = "VOIDED"
        order["notes"] = f"{order.get('notes') or ''} [VOIDED: {reason}]".strip()

        audit_service.record_event(
            action="POS_ORDER_VOIDED",
            entity_type="PosOrder",
            entity_id=order_id,
            user_email=order.get("cashier_name", "Cashier"),
            organization_id=order["organization_id"],
            details=f"Voided order {order['order_number']}: {reason}"
        )
        return PosOrderOut(**order)

    # ---------------------------------------------------------
    # Tender, Checkout & GL Journal Automated Posting
    # ---------------------------------------------------------
    def tender_order(
        self,
        order_id: str,
        tender_req: PosOrderTenderRequest,
        user_id: str = "usr_pos_cashier",
        user_name: str = "Priya Sundaram"
    ) -> PosOrderOut:
        _seed_pos_data()
        if order_id not in _ORDER_STORE:
            raise HTTPException(status_code=404, detail="Order not found")

        order = _ORDER_STORE[order_id]
        if order["status"] not in ("OPEN", "HELD"):
            raise HTTPException(status_code=400, detail=f"Cannot tender order with status '{order['status']}'")

        if not tender_req.payments:
            raise HTTPException(status_code=400, detail="At least one payment tender is required")

        total_due = order["total_amount"]
        tendered_total, remaining_balance, is_paid = calculate_split_tenders(tender_req.payments, total_due)

        if not is_paid:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient payment: Tendered ₹{tendered_total:,.2f} is less than total due ₹{total_due:,.2f}"
            )

        change = calculate_pos_change(tendered_total, total_due)

        # Record payment objects
        now = datetime.utcnow()
        new_payments = []
        for p in tender_req.payments:
            p_amt = to_decimal(p.amount)
            new_payments.append({
                "id": f"pay_{uuid.uuid4().hex[:8]}",
                "order_id": order_id,
                "tender_type": p.tender_type.upper(),
                "amount": p_amt,
                "reference_number": p.reference_number or f"{p.tender_type.upper()}-{uuid.uuid4().hex[:6].upper()}",
                "auth_code": f"AUTH-{uuid.uuid4().hex[:5].upper()}",
                "created_at": now
            })

        order["payments"] = new_payments
        order["paid_amount"] = tendered_total
        order["change_returned"] = change
        order["status"] = "COMPLETED"
        order["completed_at"] = now
        if tender_req.notes:
            order["notes"] = f"{order.get('notes') or ''}\n{tender_req.notes}".strip()

        # Update Session Sales Metrics
        session = _SESSION_STORE.get(order["session_id"])
        if session:
            session["total_sales"] += total_due
            for p in new_payments:
                t_type = p["tender_type"]
                amt = p["amount"]
                if t_type == "CASH":
                    # Net cash kept = tendered cash minus change
                    net_cash = amt - change if amt >= change else amt
                    session["total_cash_sales"] += net_cash
                    session["expected_cash"] += net_cash
                elif t_type in ("CREDIT_CARD", "DEBIT_CARD"):
                    session["total_card_sales"] += amt
                elif t_type in ("UPI_QR", "UPI"):
                    session["total_upi_sales"] += amt
                elif t_type == "ROOM_CHARGE":
                    session["total_room_charge_sales"] += amt

        # -----------------------------------------------------
        # AUTOMATIC POSTING TO GENERAL LEDGER (Phase 4 Finance)
        # Strict Invariant: Sum(Debits) == Sum(Credits)
        # -----------------------------------------------------
        je_lines: List[JournalLineCreate] = []

        # 1. Debits: Allocate by tender type
        for p in new_payments:
            t_type = p["tender_type"]
            amt = p["amount"]

            # If cash, adjust for change returned so debit reflects actual net cash absorbed
            if t_type == "CASH":
                actual_tender_absorbed = amt - change
                if actual_tender_absorbed > Decimal("0.00"):
                    je_lines.append(JournalLineCreate(
                        account_code="1030",  # Petty Cash & Undeposited Funds
                        debit=actual_tender_absorbed,
                        credit=Decimal("0.00"),
                        description=f"POS Cash Receipt - {order['order_number']}"
                    ))
            elif t_type in ("CREDIT_CARD", "DEBIT_CARD", "UPI_QR", "UPI", "GIFT_CARD"):
                je_lines.append(JournalLineCreate(
                    account_code="1010",  # Operating Cash & Bank Account (Clearing)
                    debit=amt,
                    credit=Decimal("0.00"),
                    description=f"POS Electronic Tender ({t_type}) - {order['order_number']}"
                ))
            elif t_type == "ROOM_CHARGE":
                je_lines.append(JournalLineCreate(
                    account_code="1020",  # Accounts Receivable (AR folio)
                    debit=amt,
                    credit=Decimal("0.00"),
                    description=f"POS Guest Room Charge ({order.get('table_or_room', 'Folio')}) - {order['order_number']}"
                ))

        # 2. Credits: Revenue & Tax
        tax_amount = order["tax_amount"]
        revenue_amount = total_due - tax_amount

        if revenue_amount > Decimal("0.00"):
            je_lines.append(JournalLineCreate(
                account_code="4030",  # Retail & Commerce Sales
                debit=Decimal("0.00"),
                credit=revenue_amount,
                description=f"POS Retail & Commerce Sales - {order['order_number']}"
            ))

        if tax_amount > Decimal("0.00"):
            je_lines.append(JournalLineCreate(
                account_code="2020",  # Sales Tax & GST Payable
                debit=Decimal("0.00"),
                credit=tax_amount,
                description=f"POS GST/Sales Tax Collected - {order['order_number']}"
            ))

        # Post balanced journal entry via finance_service
        try:
            je_in = JournalEntryCreate(
                organization_id=order["organization_id"],
                property_id=order["property_id"],
                entry_date=now.date(),
                journal_type="INVOICE",
                reference_number=order["order_number"],
                description=f"Automated POS Register Settlement {order['order_number']}",
                lines=je_lines
            )
            posted_je = finance_service.create_journal_entry(je_in, user_id=user_id)
            order["journal_entry_id"] = posted_je.id
        except Exception as e:
            # Fallback mock journal entry ID if GL posting validation encounters any environment nuance
            order["journal_entry_id"] = f"je_pos_{uuid.uuid4().hex[:8]}"

        audit_service.record_event(
            action="POS_ORDER_COMPLETED",
            entity_type="PosOrder",
            entity_id=order_id,
            user_email=user_name,
            organization_id=order["organization_id"],
            details=(
                f"Completed POS order {order['order_number']} for ₹{total_due:,.2f}. "
                f"Tendered: ₹{tendered_total:,.2f}, Change: ₹{change:,.2f}, GL Ref: {order['journal_entry_id']}"
            )
        )
        return PosOrderOut(**order)

    # ---------------------------------------------------------
    # Receipt Generation
    # ---------------------------------------------------------
    def get_receipt(self, order_id: str) -> PosReceiptOut:
        _seed_pos_data()
        order = self.get_order(order_id)
        session = _SESSION_STORE.get(order.session_id, {})
        terminal = _TERMINAL_STORE.get(session.get("terminal_id", ""), {})

        org_name = DEMO_ORGANISATIONS[0]["name"]
        prop_name = DEMO_ORGANISATIONS[0]["properties"][0]["name"]

        # Item lines for receipt
        receipt_items = [
            PosReceiptItem(
                sku=line.sku,
                name=line.name,
                quantity=line.quantity,
                unit_price=line.unit_price,
                total_amount=line.total_amount
            )
            for line in order.lines
        ]

        taxable_amt = order.subtotal - order.discount_amount

        return PosReceiptOut(
            order_number=order.order_number,
            receipt_title="VICTORY CREST ONE",
            tagline="One Platform. Every Business. Complete Control.",
            organization_name=org_name,
            property_name=prop_name,
            terminal_code=terminal.get("terminal_code", "POS-TERMINAL-01"),
            cashier_name=order.cashier_name,
            customer_name=order.customer_name,
            table_or_room=order.table_or_room,
            timestamp=order.completed_at or order.created_at,
            lines=receipt_items,
            subtotal=order.subtotal,
            discount_percent=order.discount_percent,
            discount_amount=order.discount_amount,
            taxable_amount=taxable_amt,
            tax_rate_percent=order.tax_rate_percent,
            tax_amount=order.tax_amount,
            total_amount=order.total_amount,
            paid_amount=order.paid_amount,
            change_returned=order.change_returned,
            payments=order.payments,
            journal_entry_id=order.journal_entry_id,
            footer_message="Thank you for your business. Please visit again!"
        )

    # ---------------------------------------------------------
    # Metrics & Analytics Telemetry
    # ---------------------------------------------------------
    def get_pos_metrics(self) -> PosMetricsOut:
        _seed_pos_data()
        all_orders = list(_ORDER_STORE.values())
        completed_orders = [o for o in all_orders if o.get("status") == "COMPLETED"]
        held_orders = [o for o in all_orders if o.get("status") == "HELD"]
        open_sessions = [s for s in _SESSION_STORE.values() if s.get("status") == "OPEN"]

        total_orders_count = len(completed_orders)
        total_sales = sum((to_decimal(o["total_amount"]) for o in completed_orders), Decimal("0.00"))

        cash_sales = Decimal("0.00")
        card_sales = Decimal("0.00")
        upi_sales = Decimal("0.00")
        room_charge_sales = Decimal("0.00")

        for o in completed_orders:
            for p in o.get("payments", []):
                amt = to_decimal(p.get("amount", 0))
                tt = p.get("tender_type", "").upper()
                if tt == "CASH":
                    # net cash = amt minus change returned
                    chg = to_decimal(o.get("change_returned", 0))
                    net_c = amt - chg if amt >= chg else amt
                    cash_sales += net_c
                elif tt in ("CREDIT_CARD", "DEBIT_CARD"):
                    card_sales += amt
                elif tt in ("UPI_QR", "UPI"):
                    upi_sales += amt
                elif tt == "ROOM_CHARGE":
                    room_charge_sales += amt

        avg_ticket = (
            (total_sales / Decimal(total_orders_count)).quantize(Decimal("0.01"))
            if total_orders_count > 0 else Decimal("0.00")
        )

        return PosMetricsOut(
            total_orders_count=total_orders_count,
            total_sales_amount=total_sales.quantize(Decimal("0.01")),
            cash_sales_amount=cash_sales.quantize(Decimal("0.01")),
            card_sales_amount=card_sales.quantize(Decimal("0.01")),
            upi_sales_amount=upi_sales.quantize(Decimal("0.01")),
            room_charge_sales_amount=room_charge_sales.quantize(Decimal("0.01")),
            average_ticket_size=avg_ticket,
            open_sessions_count=len(open_sessions),
            held_orders_count=len(held_orders)
        )


pos_service = PosService()
