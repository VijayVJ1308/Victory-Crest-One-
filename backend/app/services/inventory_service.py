"""Victory Crest One - Supply Chain, ERP & Warehouse Inventory Service
Procurement Purchase Orders, Goods Receipt Notes (GRN), Multi-Warehouse Stock,
AVCO Valuation, Inter-Warehouse Transfers, and Automated AP / GL Postings.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.inventory import (
    WarehouseCreate, WarehouseOut,
    PurchaseOrderLineCreate, PurchaseOrderLineOut,
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderOut, PurchaseOrderReceiveRequest,
    GoodsReceiptNoteOut,
    WarehouseStockOut, StockReplenishmentAlert,
    StockTransferRequest, StockMovementCreate, StockMovementOut,
    CycleCountCreate, CycleCountItemVariance, CycleCountReconcileRequest, CycleCountOut,
    InventoryMetricsOut
)
from backend.app.schemas.finance import JournalEntryCreate, JournalLineCreate, SupplierBillCreate, BillLineCreate
from backend.app.services.finance_service import finance_service
from backend.app.services.audit_service import audit_service
from shared.calculations import (
    to_decimal, calculate_po_totals, calculate_reorder_point,
    calculate_inventory_valuation, calculate_stock_variance,
    calculate_weighted_average_cost
)
from shared.constants import DEMO_ORGANISATIONS


# In-memory stores
_WAREHOUSE_STORE: Dict[str, Dict[str, Any]] = {}
_STOCK_STORE: Dict[str, Dict[str, Any]] = {}
_PO_STORE: Dict[str, Dict[str, Any]] = {}
_GRN_STORE: Dict[str, Dict[str, Any]] = {}
_MOVEMENT_STORE: List[Dict[str, Any]] = []
_CYCLE_COUNT_STORE: Dict[str, Dict[str, Any]] = {}

_PO_COUNTER = 400
_GRN_COUNTER = 300
_MOV_COUNTER = 500


def _seed_inventory_data():
    """Populate realistic multi-warehouse stock, suppliers, purchase orders, and audit trail."""
    global _PO_COUNTER, _GRN_COUNTER, _MOV_COUNTER
    if _WAREHOUSE_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]  # Madurai
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]  # Kodaikanal
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]  # Chennai
    now = datetime.utcnow()

    # 1. Seed Warehouses
    warehouses = [
        {
            "id": "wh_mdu_central",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "warehouse_code": "WH-MDU-OPS-01",
            "name": "Madurai Central Operations & Supply Depot",
            "warehouse_type": "CENTRAL",
            "location_address": "Heritage Wing Logistics Bay, West Gate",
            "manager_name": "K. Alagarsamy (Warehouse Mgr)",
            "is_active": True,
            "created_at": now - timedelta(days=120),
            "updated_at": now - timedelta(days=120)
        },
        {
            "id": "wh_mdu_fnb",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "warehouse_code": "WH-MDU-FNB-02",
            "name": "Madurai F&B Commissary & Cold Storage",
            "warehouse_type": "FNB_COMMISSARY",
            "location_address": "Main Kitchen Basement Level -1",
            "manager_name": "Chef S. Murugan (Exec Sous Chef)",
            "is_active": True,
            "created_at": now - timedelta(days=120),
            "updated_at": now - timedelta(days=120)
        },
        {
            "id": "wh_kod_main",
            "organization_id": org_id,
            "property_id": prop_kod,
            "warehouse_code": "WH-KOD-RES-01",
            "name": "Kodaikanal Mountain Stores & Linen Depot",
            "warehouse_type": "CENTRAL",
            "location_address": "Pine Valley Service Quarter A",
            "manager_name": "J. Thomas (Resort Stores In-Charge)",
            "is_active": True,
            "created_at": now - timedelta(days=90),
            "updated_at": now - timedelta(days=90)
        },
        {
            "id": "wh_maa_retail",
            "organization_id": org_id,
            "property_id": prop_maa,
            "warehouse_code": "WH-MAA-BIZ-01",
            "name": "Chennai Business Hub Retail & Consumables Store",
            "warehouse_type": "RETAIL_STORE",
            "location_address": "Mezzanine Floor Supply Annex",
            "manager_name": "P. Ramesh (Floor Logistics)",
            "is_active": True,
            "created_at": now - timedelta(days=60),
            "updated_at": now - timedelta(days=60)
        }
    ]
    for w in warehouses:
        _WAREHOUSE_STORE[w["id"]] = w

    # 2. Seed Warehouse Stock Items
    raw_stocks = [
        # Madurai Central / F&B
        ("wh_mdu_fnb", "FNB-COF-MADURAI", "Madurai Filter Degree Coffee", "Beverages", "CUP", 150.0, 10.0, 50.0, 65.0),
        ("wh_mdu_fnb", "FNB-TEA-MASALA", "Nilgiri Spiced Masala Chai", "Beverages", "CUP", 220.0, 15.0, 60.0, 40.0),
        ("wh_mdu_fnb", "BAK-CRST-BUTTER", "French Butter Croissant", "Bakery", "UNIT", 40.0, 5.0, 25.0, 80.0),
        ("wh_mdu_central", "SNK-CSH-CHETT", "Chettinad Spiced Roasted Cashews 250g", "Snacks", "PACK", 65.0, 0.0, 30.0, 210.0),
        ("wh_mdu_central", "BTQ-SILK-SCRF", "Madurai Handloom Silk Stole", "Boutique", "UNIT", 18.0, 2.0, 10.0, 750.0),
        ("wh_mdu_central", "BEV-WTR-SPR750", "Himalayan Natural Mineral Spring Water 750ml", "Beverages", "BOTTLE", 350.0, 20.0, 100.0, 35.0),
        ("wh_mdu_central", "MERCH-NOTE-PEN", "Victory Crest Executive Leather Journal & Pen", "Merchandise", "SET", 50.0, 5.0, 20.0, 320.0),
        # Low stock item -> triggers alert!
        ("wh_mdu_central", "SPA-SOAP-HERBAL", "Ayurvedic Sandalwood Soap Gift Box", "Wellness", "BOX", 8.0, 0.0, 20.0, 180.0),
        # Kodaikanal Mountain Stores
        ("wh_kod_main", "SPA-EUC-OIL100", "Kodaikanal Pure Eucalyptus Oil 100ml", "Wellness", "BOTTLE", 80.0, 5.0, 30.0, 130.0),
        ("wh_kod_main", "RET-TEA-NILGIRI", "Nilgiri Estate Black Tea Vintage Tin 200g", "Retail", "TIN", 45.0, 0.0, 20.0, 260.0),
        ("wh_kod_main", "BEV-WTR-SPR750", "Himalayan Natural Mineral Spring Water 750ml", "Beverages", "BOTTLE", 180.0, 10.0, 80.0, 35.0),
    ]

    for wh_id, sku, name, cat, uom, qoh, qres, rop, cost in raw_stocks:
        wh = _WAREHOUSE_STORE[wh_id]
        key = f"{wh_id}_{sku}"
        q_on_hand = Decimal(str(qoh))
        q_reserved = Decimal(str(qres))
        q_avail = q_on_hand - q_reserved
        reorder = Decimal(str(rop))
        u_cost = Decimal(str(cost))
        tot_val = q_on_hand * u_cost

        st_status = "LOW_STOCK" if q_on_hand <= reorder else "IN_STOCK"
        _STOCK_STORE[key] = {
            "id": f"stock_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "property_id": wh["property_id"],
            "warehouse_id": wh_id,
            "warehouse_name": wh["name"],
            "product_id": f"prod_{sku.lower().replace('-', '_')}",
            "sku": sku,
            "product_name": name,
            "category": cat,
            "unit_of_measure": uom,
            "quantity_on_hand": q_on_hand,
            "quantity_reserved": q_reserved,
            "quantity_available": q_avail,
            "reorder_point": reorder,
            "unit_cost": u_cost,
            "total_value": tot_val,
            "stock_status": st_status,
            "last_restocked_at": now - timedelta(days=8)
        }

    # 3. Seed Purchase Orders
    po_1_id = "po_2026_401"
    _PO_STORE[po_1_id] = {
        "id": po_1_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "po_number": "PO-2026-00401",
        "supplier_id": "supp_linen_textiles",
        "supplier_name": "Coimbatore Luxury Linens & Fabrics",
        "status": "RECEIVED",
        "issue_date": now - timedelta(days=20),
        "expected_delivery_date": now - timedelta(days=5),
        "payment_terms_days": 30,
        "warehouse_id": "wh_mdu_central",
        "warehouse_name": "Madurai Central Operations & Supply Depot",
        "subtotal": Decimal("237288.14"),
        "tax_rate_percent": Decimal("18.00"),
        "tax_amount": Decimal("42711.86"),
        "total_amount": Decimal("280000.00"),
        "supplier_bill_id": "bill_supp_linens_01",
        "notes": "Annual replenishment of 400TC Egyptian cotton palace suite linens.",
        "created_at": now - timedelta(days=20),
        "updated_at": now - timedelta(days=5),
        "lines": [
            {
                "id": f"poline_{uuid.uuid4().hex[:8]}",
                "purchase_order_id": po_1_id,
                "product_id": "prod_heritage_suite",
                "sku": "LIN-EGYPT-400TC",
                "name": "Egyptian Cotton Luxury Bedding Set (400TC)",
                "unit_of_measure": "SET",
                "quantity_ordered": Decimal("100.00"),
                "quantity_received": Decimal("100.00"),
                "unit_price": Decimal("1800.00"),
                "total_amount": Decimal("180000.00")
            },
            {
                "id": f"poline_{uuid.uuid4().hex[:8]}",
                "purchase_order_id": po_1_id,
                "product_id": None,
                "sku": "LIN-BATH-PLUSH",
                "name": "Plush Turkish Terry Cotton Bathrobe",
                "unit_of_measure": "UNIT",
                "quantity_ordered": Decimal("50.00"),
                "quantity_received": Decimal("50.00"),
                "unit_price": Decimal("1145.76"),
                "total_amount": Decimal("57288.14")
            }
        ]
    }

    po_2_id = "po_2026_402"
    _PO_STORE[po_2_id] = {
        "id": po_2_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "po_number": "PO-2026-00402",
        "supplier_id": "supp_organic_foods",
        "supplier_name": "Nilgiri Organics & Gourmet Supplies",
        "status": "ISSUED",
        "issue_date": now - timedelta(days=3),
        "expected_delivery_date": now + timedelta(days=2),
        "payment_terms_days": 15,
        "warehouse_id": "wh_mdu_fnb",
        "warehouse_name": "Madurai F&B Commissary & Cold Storage",
        "subtotal": Decimal("72033.90"),
        "tax_rate_percent": Decimal("18.00"),
        "tax_amount": Decimal("12966.10"),
        "total_amount": Decimal("85000.00"),
        "supplier_bill_id": None,
        "notes": "Bi-weekly organic Arabica plantation coffee beans and mountain spices.",
        "created_at": now - timedelta(days=3),
        "updated_at": now - timedelta(days=3),
        "lines": [
            {
                "id": f"poline_{uuid.uuid4().hex[:8]}",
                "purchase_order_id": po_2_id,
                "product_id": None,
                "sku": "RAW-COF-ARABICA",
                "name": "Estate Arabica Green & Roasted Coffee Beans 5kg",
                "unit_of_measure": "BAG",
                "quantity_ordered": Decimal("20.00"),
                "quantity_received": Decimal("0.00"),
                "unit_price": Decimal("2500.00"),
                "total_amount": Decimal("50000.00")
            },
            {
                "id": f"poline_{uuid.uuid4().hex[:8]}",
                "purchase_order_id": po_2_id,
                "product_id": None,
                "sku": "RAW-SPICE-CHETT",
                "name": "Artisanal Whole Chettinad Spices Assortment",
                "unit_of_measure": "PACK",
                "quantity_ordered": Decimal("25.00"),
                "quantity_received": Decimal("0.00"),
                "unit_price": Decimal("881.36"),
                "total_amount": Decimal("22033.90")
            }
        ]
    }

    # 4. Seed Goods Receipt Note (GRN) for PO 401
    grn_1_id = "grn_2026_301"
    _GRN_STORE[grn_1_id] = {
        "id": grn_1_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "grn_number": "GRN-2026-00301",
        "purchase_order_id": po_1_id,
        "supplier_id": "supp_linen_textiles",
        "supplier_name": "Coimbatore Luxury Linens & Fabrics",
        "warehouse_id": "wh_mdu_central",
        "received_date": now - timedelta(days=5),
        "total_items_received": 150,
        "journal_entry_id": "je_grn_00301",
        "notes": "All cartons inspected and verified against PO-2026-00401."
    }

    # 5. Seed Stock Movements
    _MOVEMENT_STORE.extend([
        {
            "id": f"mov_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "movement_number": "MOV-2026-00501",
            "movement_type": "RECEIPT",
            "product_id": "prod_linen_cotton",
            "sku": "LIN-EGYPT-400TC",
            "product_name": "Egyptian Cotton Luxury Bedding Set (400TC)",
            "source_warehouse_id": None,
            "target_warehouse_id": "wh_mdu_central",
            "quantity": Decimal("100.00"),
            "unit_cost": Decimal("1800.00"),
            "total_value": Decimal("180000.00"),
            "reference_doc": "PO-2026-00401",
            "notes": "Initial delivery received via GRN-2026-00301",
            "created_at": now - timedelta(days=5)
        },
        {
            "id": f"mov_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "movement_number": "MOV-2026-00502",
            "movement_type": "TRANSFER",
            "product_id": "prod_mineral_water",
            "sku": "BEV-WTR-SPR750",
            "product_name": "Himalayan Natural Mineral Spring Water 750ml",
            "source_warehouse_id": "wh_mdu_central",
            "target_warehouse_id": "wh_mdu_fnb",
            "quantity": Decimal("50.00"),
            "unit_cost": Decimal("35.00"),
            "total_value": Decimal("1750.00"),
            "reference_doc": "TRANSFER-MDU-01",
            "notes": "Inter-warehouse replenishment to Main Kitchen beverage storage",
            "created_at": now - timedelta(days=2)
        }
    ])

    _PO_COUNTER = 404
    _GRN_COUNTER = 302
    _MOV_COUNTER = 503


class InventoryService:
    """Full-lifecycle Supply Chain, ERP, and Warehouse Inventory Service."""

    def __init__(self):
        _seed_inventory_data()

    # ---------------------------------------------------------
    # Warehouses
    # ---------------------------------------------------------
    def list_warehouses(self, property_id: Optional[str] = None) -> List[WarehouseOut]:
        _seed_inventory_data()
        warehouses = list(_WAREHOUSE_STORE.values())
        if property_id:
            warehouses = [w for w in warehouses if w["property_id"] == property_id]
        return [WarehouseOut(**w) for w in warehouses]

    def get_warehouse(self, warehouse_id: str) -> WarehouseOut:
        _seed_inventory_data()
        if warehouse_id not in _WAREHOUSE_STORE:
            raise HTTPException(status_code=404, detail=f"Warehouse '{warehouse_id}' not found")
        return WarehouseOut(**_WAREHOUSE_STORE[warehouse_id])

    def create_warehouse(self, wh_in: WarehouseCreate) -> WarehouseOut:
        _seed_inventory_data()
        org_id = wh_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        prop_id = wh_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]

        for w in _WAREHOUSE_STORE.values():
            if w["warehouse_code"].lower() == wh_in.warehouse_code.lower():
                raise HTTPException(status_code=400, detail=f"Warehouse code '{wh_in.warehouse_code}' already exists")

        new_id = f"wh_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        record = {
            "id": new_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "warehouse_code": wh_in.warehouse_code,
            "name": wh_in.name,
            "warehouse_type": wh_in.warehouse_type.upper(),
            "location_address": wh_in.location_address,
            "manager_name": wh_in.manager_name,
            "is_active": wh_in.is_active,
            "created_at": now,
            "updated_at": now
        }
        _WAREHOUSE_STORE[new_id] = record
        return WarehouseOut(**record)

    # ---------------------------------------------------------
    # Stock Levels & Inventory Catalog
    # ---------------------------------------------------------
    def list_stock(
        self,
        warehouse_id: Optional[str] = None,
        category: Optional[str] = None,
        stock_status: Optional[str] = None
    ) -> List[WarehouseStockOut]:
        _seed_inventory_data()
        stocks = list(_STOCK_STORE.values())

        if warehouse_id:
            stocks = [s for s in stocks if s["warehouse_id"] == warehouse_id]
        if category and category.lower() != "all":
            c_norm = category.strip().lower()
            stocks = [s for s in stocks if s["category"].lower() == c_norm]
        if stock_status:
            st_norm = stock_status.strip().upper()
            stocks = [s for s in stocks if s["stock_status"].upper() == st_norm]

        stocks.sort(key=lambda s: s["sku"])
        return [WarehouseStockOut(**s) for s in stocks]

    def get_stock_item(self, warehouse_id: str, sku: str) -> WarehouseStockOut:
        _seed_inventory_data()
        key = f"{warehouse_id}_{sku}"
        if key not in _STOCK_STORE:
            raise HTTPException(status_code=404, detail=f"Stock for SKU '{sku}' not found in warehouse '{warehouse_id}'")
        return WarehouseStockOut(**_STOCK_STORE[key])

    def update_stock_item(self, stock_id: str, updates: Dict[str, Any]) -> WarehouseStockOut:
        _seed_inventory_data()
        item = _STOCK_STORE.get(stock_id)
        if not item:
            for k, s in _STOCK_STORE.items():
                if s.get("id") == stock_id or k == stock_id:
                    item = s
                    break
        if not item:
            raise HTTPException(status_code=404, detail=f"Stock item '{stock_id}' not found")

        if "product_name" in updates and updates["product_name"]:
            item["product_name"] = str(updates["product_name"]).strip()
        if "category" in updates and updates["category"]:
            item["category"] = str(updates["category"]).strip()
        if "quantity_on_hand" in updates and updates["quantity_on_hand"] is not None:
            qoh = to_decimal(updates["quantity_on_hand"])
            item["quantity_on_hand"] = qoh
            item["quantity_available"] = qoh - to_decimal(item.get("quantity_reserved", 0))
        if "reorder_point" in updates and updates["reorder_point"] is not None:
            item["reorder_point"] = to_decimal(updates["reorder_point"])
        if "unit_cost" in updates and updates["unit_cost"] is not None:
            item["unit_cost"] = to_decimal(updates["unit_cost"])

        item["total_value"] = item["quantity_on_hand"] * item["unit_cost"]
        if item["quantity_on_hand"] <= Decimal("0"):
            item["stock_status"] = "OUT_OF_STOCK"
        elif item["quantity_on_hand"] <= item["reorder_point"]:
            item["stock_status"] = "LOW_STOCK"
        else:
            item["stock_status"] = "IN_STOCK"
        return WarehouseStockOut(**item)

    def list_replenishment_alerts(self, warehouse_id: Optional[str] = None) -> List[StockReplenishmentAlert]:
        """Detect and return items where quantity_on_hand <= reorder_point."""
        _seed_inventory_data()
        stocks = list(_STOCK_STORE.values())
        if warehouse_id:
            stocks = [s for s in stocks if s["warehouse_id"] == warehouse_id]

        alerts = []
        for s in stocks:
            qoh = to_decimal(s["quantity_on_hand"])
            rop = to_decimal(s["reorder_point"])
            if qoh <= rop:
                shortage = rop - qoh
                suggested = shortage + (rop * Decimal("2.00"))  # standard EOQ buffer
                alerts.append(StockReplenishmentAlert(
                    warehouse_id=s["warehouse_id"],
                    warehouse_name=s["warehouse_name"],
                    product_id=s.get("product_id"),
                    sku=s["sku"],
                    product_name=s["product_name"],
                    category=s["category"],
                    quantity_on_hand=qoh,
                    reorder_point=rop,
                    shortage_quantity=shortage,
                    suggested_order_quantity=suggested.quantize(Decimal("1.00")),
                    recommended_supplier_name="Coimbatore Luxury Linens & Fabrics" if "LIN" in s["sku"] else "Nilgiri Organics & Gourmet Supplies"
                ))
        return alerts

    # ---------------------------------------------------------
    # Purchase Orders & Procurement
    # ---------------------------------------------------------
    def list_purchase_orders(
        self,
        supplier_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[PurchaseOrderOut]:
        _seed_inventory_data()
        pos = list(_PO_STORE.values())

        if supplier_id:
            pos = [p for p in pos if p["supplier_id"] == supplier_id]
        if status_filter:
            s_norm = status_filter.strip().upper()
            pos = [p for p in pos if p["status"].upper() == s_norm]

        pos.sort(key=lambda p: p.get("created_at") or datetime.min, reverse=True)
        return [PurchaseOrderOut(**p) for p in pos]

    def get_purchase_order(self, po_id: str) -> PurchaseOrderOut:
        _seed_inventory_data()
        if po_id not in _PO_STORE:
            raise HTTPException(status_code=404, detail=f"Purchase Order '{po_id}' not found")
        return PurchaseOrderOut(**_PO_STORE[po_id])

    def create_purchase_order(
        self,
        po_in: PurchaseOrderCreate,
        user_email: str = "procurement@victorycrest.internal"
    ) -> PurchaseOrderOut:
        global _PO_COUNTER
        _seed_inventory_data()
        org_id = DEMO_ORGANISATIONS[0]["id"]
        prop_id = DEMO_ORGANISATIONS[0]["properties"][0]["id"]

        warehouse = self.get_warehouse(po_in.warehouse_id)
        _PO_COUNTER += 1
        po_num = f"PO-2026-{_PO_COUNTER:05d}"
        po_id = f"po_2026_{uuid.uuid4().hex[:6]}"

        totals = calculate_po_totals(po_in.lines, tax_rate_percent=po_in.tax_rate_percent)

        line_dicts = []
        for l in po_in.lines:
            qty = to_decimal(l.quantity_ordered)
            price = to_decimal(l.unit_price)
            line_dicts.append({
                "id": f"poline_{uuid.uuid4().hex[:8]}",
                "purchase_order_id": po_id,
                "product_id": l.product_id,
                "sku": l.sku,
                "name": l.name,
                "unit_of_measure": l.unit_of_measure,
                "quantity_ordered": qty,
                "quantity_received": Decimal("0.00"),
                "unit_price": price,
                "total_amount": (qty * price).quantize(Decimal("0.01"))
            })

        now = datetime.utcnow()
        supp_name = po_in.supplier_name or ("Coimbatore Luxury Linens & Fabrics" if "linen" in po_in.supplier_id.lower() else "Nilgiri Organics & Gourmet Supplies")

        record = {
            "id": po_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "po_number": po_num,
            "supplier_id": po_in.supplier_id,
            "supplier_name": supp_name,
            "status": "ISSUED",
            "issue_date": now,
            "expected_delivery_date": po_in.expected_delivery_date or (now + timedelta(days=7)),
            "payment_terms_days": po_in.payment_terms_days,
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "subtotal": totals["subtotal"],
            "tax_rate_percent": totals["tax_rate_percent"],
            "tax_amount": totals["tax_amount"],
            "total_amount": totals["total_amount"],
            "supplier_bill_id": None,
            "notes": po_in.notes,
            "created_at": now,
            "updated_at": now,
            "lines": line_dicts
        }
        _PO_STORE[po_id] = record

        audit_service.record_event(
            action="PURCHASE_ORDER_ISSUED",
            entity_type="PurchaseOrder",
            entity_id=po_id,
            user_email=user_email,
            organization_id=org_id,
            details=f"Issued purchase order {po_num} to '{supp_name}' for ₹{totals['total_amount']:,.2f}"
        )
        return PurchaseOrderOut(**record)

    def receive_purchase_order(
        self,
        po_id: str,
        req: PurchaseOrderReceiveRequest,
        user_id: str = "usr_superadmin_01",
        user_email: str = "procurement@victorycrest.internal"
    ) -> PurchaseOrderOut:
        """
        Receive Goods against a Purchase Order:
        1. Increments stock on hand in designated warehouse.
        2. Recalculates Weighted Average Cost (AVCO).
        3. Creates Goods Receipt Note (GRN).
        4. AUTOMATIC FINANCE INTEGRATION:
           - Posts balanced double-entry GL journal (DR 1200 Inventory Asset, CR 2010 Accounts Payable).
           - Creates Accounts Payable Supplier Bill in Phase 4 Finance.
        """
        global _GRN_COUNTER, _MOV_COUNTER
        _seed_inventory_data()

        if po_id not in _PO_STORE:
            raise HTTPException(status_code=404, detail="Purchase Order not found")

        po = _PO_STORE[po_id]
        if po["status"] in ("RECEIVED", "CLOSED", "CANCELLED"):
            raise HTTPException(status_code=400, detail=f"Cannot receive PO with status '{po['status']}'")

        now = datetime.utcnow()
        wh_id = po["warehouse_id"]
        total_items_received = 0

        # Update lines and warehouse stocks
        for line in po.get("lines", []):
            qty = to_decimal(line["quantity_ordered"])
            line["quantity_received"] = qty
            price = to_decimal(line["unit_price"])
            sku = line["sku"]
            key = f"{wh_id}_{sku}"

            # Update or create stock entry
            if key in _STOCK_STORE:
                stock = _STOCK_STORE[key]
                old_qty = to_decimal(stock["quantity_on_hand"])
                old_cost = to_decimal(stock["unit_cost"])

                # Weighted Average Cost calculation
                new_avg_cost = calculate_weighted_average_cost(old_qty, old_cost, qty, price)
                new_qty = old_qty + qty

                stock["quantity_on_hand"] = new_qty
                stock["quantity_available"] = new_qty - to_decimal(stock["quantity_reserved"])
                stock["unit_cost"] = new_avg_cost
                stock["total_value"] = (new_qty * new_avg_cost).quantize(Decimal("0.01"))
                stock["stock_status"] = "IN_STOCK" if new_qty > to_decimal(stock["reorder_point"]) else "LOW_STOCK"
                stock["last_restocked_at"] = now
            else:
                # Add new stock item to warehouse
                tot_val = (qty * price).quantize(Decimal("0.01"))
                _STOCK_STORE[key] = {
                    "id": f"stock_{uuid.uuid4().hex[:8]}",
                    "organization_id": po["organization_id"],
                    "property_id": po["property_id"],
                    "warehouse_id": wh_id,
                    "warehouse_name": po["warehouse_name"],
                    "product_id": line.get("product_id"),
                    "sku": sku,
                    "product_name": line["name"],
                    "category": "General",
                    "unit_of_measure": line["unit_of_measure"],
                    "quantity_on_hand": qty,
                    "quantity_reserved": Decimal("0.00"),
                    "quantity_available": qty,
                    "reorder_point": Decimal("10.00"),
                    "unit_cost": price,
                    "total_value": tot_val,
                    "stock_status": "IN_STOCK",
                    "last_restocked_at": now
                }

            # Record Stock Movement
            _MOV_COUNTER += 1
            _MOVEMENT_STORE.append({
                "id": f"mov_{uuid.uuid4().hex[:8]}",
                "organization_id": po["organization_id"],
                "movement_number": f"MOV-2026-{_MOV_COUNTER:05d}",
                "movement_type": "RECEIPT",
                "product_id": line.get("product_id"),
                "sku": sku,
                "product_name": line["name"],
                "source_warehouse_id": None,
                "target_warehouse_id": wh_id,
                "quantity": qty,
                "unit_cost": price,
                "total_value": (qty * price).quantize(Decimal("0.01")),
                "reference_doc": po["po_number"],
                "notes": f"Delivered via {po['po_number']}",
                "created_at": now
            })
            total_items_received += int(qty)

        # -----------------------------------------------------
        # AUTOMATIC FINANCE POSTINGS (Phase 4 Finance & GL)
        # 1. Balanced GL Journal Entry:
        #    DR 1200 Inventory Asset
        #    CR 2010 Accounts Payable
        # -----------------------------------------------------
        po_total = to_decimal(po["total_amount"])
        je_lines = [
            JournalLineCreate(
                account_code="1200",  # Inventory Asset
                debit=po_total,
                credit=Decimal("0.00"),
                description=f"Inventory Receipt - {po['po_number']} from {po['supplier_name']}"
            ),
            JournalLineCreate(
                account_code="2010",  # Accounts Payable
                debit=Decimal("0.00"),
                credit=po_total,
                description=f"AP Trade Liability - {po['po_number']}"
            )
        ]
        je_in = JournalEntryCreate(
            organization_id=po["organization_id"],
            property_id=po["property_id"],
            entry_date=now.date(),
            journal_type="BILL",
            reference_number=po["po_number"],
            description=f"Automated GL post for PO Receiving {po['po_number']}",
            lines=je_lines
        )
        posted_je = finance_service.create_journal_entry(je_in, user_id=user_id)
        je_id_str = posted_je["id"] if isinstance(posted_je, dict) else getattr(posted_je, "id", "je_auto")

        # 2. Automated Supplier Bill in Accounts Payable
        bill_lines = [
            BillLineCreate(
                description=l["name"],
                quantity=to_decimal(l["quantity_ordered"]),
                unit_price=to_decimal(l["unit_price"]),
                amount=to_decimal(l["total_amount"]),
                account_id=None
            )
            for l in po.get("lines", [])
        ]
        bill_in = SupplierBillCreate(
            organization_id=po["organization_id"],
            property_id=po["property_id"],
            supplier_id=po["supplier_id"],
            supplier_name=po["supplier_name"],
            bill_date=now,
            due_date=now + timedelta(days=po["payment_terms_days"]),
            vendor_invoice_ref=po["po_number"],
            notes=f"Auto-generated AP bill from received purchase order {po['po_number']}",
            lines=bill_lines
        )
        created_bill = finance_service.create_bill(bill_in, user_id=user_id)
        po["supplier_bill_id"] = created_bill["id"] if isinstance(created_bill, dict) else created_bill.id
        bill_num_str = created_bill.get("bill_number") if isinstance(created_bill, dict) else getattr(created_bill, "bill_number", "BILL")

        # 3. Create Goods Receipt Note (GRN)
        _GRN_COUNTER += 1
        grn_num = f"GRN-2026-{_GRN_COUNTER:05d}"
        grn_id = f"grn_{uuid.uuid4().hex[:8]}"
        _GRN_STORE[grn_id] = {
            "id": grn_id,
            "organization_id": po["organization_id"],
            "property_id": po["property_id"],
            "grn_number": grn_num,
            "purchase_order_id": po_id,
            "supplier_id": po["supplier_id"],
            "supplier_name": po["supplier_name"],
            "warehouse_id": wh_id,
            "received_date": now,
            "total_items_received": total_items_received,
            "journal_entry_id": je_id_str,
            "notes": req.notes
        }

        # Finalize PO status
        po["status"] = "RECEIVED"
        po["updated_at"] = now
        po["notes"] = f"{po.get('notes') or ''}\nReceived via {grn_num} on {now.strftime('%Y-%m-%d')} (GL: {je_id_str})".strip()

        audit_service.record_event(
            action="PURCHASE_ORDER_RECEIVED",
            entity_type="PurchaseOrder",
            entity_id=po_id,
            user_email=user_email,
            organization_id=po["organization_id"],
            details=(
                f"Received PO {po['po_number']} ({total_items_received} units). "
                f"Generated {grn_num}, GL: {je_id_str}, AP Bill: {bill_num_str}"
            )
        )
        return PurchaseOrderOut(**po)

    # ---------------------------------------------------------
    # Inter-Warehouse Stock Transfers
    # ---------------------------------------------------------
    def transfer_stock(
        self,
        req: StockTransferRequest,
        user_email: str = "inventory@victorycrest.internal"
    ) -> StockMovementOut:
        global _MOV_COUNTER
        _seed_inventory_data()

        source_key = f"{req.source_warehouse_id}_{req.sku}"
        if source_key not in _STOCK_STORE:
            raise HTTPException(status_code=404, detail=f"SKU '{req.sku}' not found in source warehouse")

        source_stock = _STOCK_STORE[source_key]
        qty = to_decimal(req.quantity)

        if to_decimal(source_stock["quantity_available"]) < qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient available stock for transfer. Available: {source_stock['quantity_available']}, Requested: {qty}"
            )

        now = datetime.utcnow()
        u_cost = to_decimal(source_stock["unit_cost"])

        # Deduct from source warehouse
        source_stock["quantity_on_hand"] -= qty
        source_stock["quantity_available"] -= qty
        source_stock["total_value"] = (source_stock["quantity_on_hand"] * u_cost).quantize(Decimal("0.01"))
        source_stock["stock_status"] = "LOW_STOCK" if source_stock["quantity_on_hand"] <= source_stock["reorder_point"] else "IN_STOCK"

        # Add to target warehouse
        target_wh = self.get_warehouse(req.target_warehouse_id)
        target_key = f"{req.target_warehouse_id}_{req.sku}"

        if target_key in _STOCK_STORE:
            target_stock = _STOCK_STORE[target_key]
            old_qty = to_decimal(target_stock["quantity_on_hand"])
            old_cost = to_decimal(target_stock["unit_cost"])
            new_cost = calculate_weighted_average_cost(old_qty, old_cost, qty, u_cost)

            target_stock["quantity_on_hand"] += qty
            target_stock["quantity_available"] += qty
            target_stock["unit_cost"] = new_cost
            target_stock["total_value"] = (target_stock["quantity_on_hand"] * new_cost).quantize(Decimal("0.01"))
            target_stock["stock_status"] = "IN_STOCK" if target_stock["quantity_on_hand"] > target_stock["reorder_point"] else "LOW_STOCK"
            target_stock["last_restocked_at"] = now
        else:
            _STOCK_STORE[target_key] = {
                "id": f"stock_{uuid.uuid4().hex[:8]}",
                "organization_id": target_wh.organization_id,
                "property_id": target_wh.property_id,
                "warehouse_id": target_wh.id,
                "warehouse_name": target_wh.name,
                "product_id": source_stock.get("product_id"),
                "sku": req.sku,
                "product_name": source_stock["product_name"],
                "category": source_stock["category"],
                "unit_of_measure": source_stock["unit_of_measure"],
                "quantity_on_hand": qty,
                "quantity_reserved": Decimal("0.00"),
                "quantity_available": qty,
                "reorder_point": Decimal("10.00"),
                "unit_cost": u_cost,
                "total_value": (qty * u_cost).quantize(Decimal("0.01")),
                "stock_status": "IN_STOCK",
                "last_restocked_at": now
            }

        # Record Transfer Movement
        _MOV_COUNTER += 1
        mov_num = f"MOV-2026-{_MOV_COUNTER:05d}"
        mov_record = {
            "id": f"mov_{uuid.uuid4().hex[:8]}",
            "organization_id": source_stock["organization_id"],
            "movement_number": mov_num,
            "movement_type": "TRANSFER",
            "product_id": source_stock.get("product_id"),
            "sku": req.sku,
            "product_name": source_stock["product_name"],
            "source_warehouse_id": req.source_warehouse_id,
            "target_warehouse_id": req.target_warehouse_id,
            "quantity": qty,
            "unit_cost": u_cost,
            "total_value": (qty * u_cost).quantize(Decimal("0.01")),
            "reference_doc": f"TRANSFER-{req.sku}",
            "notes": req.notes or f"Transferred {qty} units from {source_stock['warehouse_name']} to {target_wh.name}",
            "created_at": now
        }
        _MOVEMENT_STORE.append(mov_record)

        audit_service.record_event(
            action="STOCK_TRANSFERRED",
            entity_type="StockMovement",
            entity_id=mov_record["id"],
            user_email=user_email,
            organization_id=source_stock["organization_id"],
            details=f"Transferred {qty} of {req.sku} to {target_wh.name} ({mov_num})"
        )
        return StockMovementOut(**mov_record)

    def list_stock_movements(self, limit: int = 50) -> List[StockMovementOut]:
        _seed_inventory_data()
        movs = list(_MOVEMENT_STORE)
        movs.sort(key=lambda m: m.get("created_at") or datetime.min, reverse=True)
        return [StockMovementOut(**m) for m in movs[:limit]]

    # ---------------------------------------------------------
    # Cycle Counts & Stocktaking
    # ---------------------------------------------------------
    def list_cycle_counts(self) -> List[CycleCountOut]:
        _seed_inventory_data()
        return [CycleCountOut(**c) for c in _CYCLE_COUNT_STORE.values()]

    def create_cycle_count(self, count_in: CycleCountCreate) -> CycleCountOut:
        _seed_inventory_data()
        wh = self.get_warehouse(count_in.warehouse_id)
        now = datetime.utcnow()
        session_id = f"cc_{uuid.uuid4().hex[:8]}"
        session_code = f"CC-2026-{uuid.uuid4().hex[:4].upper()}"

        record = {
            "id": session_id,
            "organization_id": wh.organization_id,
            "property_id": wh.property_id,
            "warehouse_id": wh.id,
            "warehouse_name": wh.name,
            "session_code": session_code,
            "status": "OPEN",
            "total_items_counted": 0,
            "total_variance_value": Decimal("0.00"),
            "reconciled_at": None,
            "notes": count_in.notes or "Scheduled cycle count session",
            "created_at": now
        }
        _CYCLE_COUNT_STORE[session_id] = record
        return CycleCountOut(**record)

    def reconcile_cycle_count(
        self,
        session_id: str,
        reconcile_req: CycleCountReconcileRequest
    ) -> CycleCountOut:
        _seed_inventory_data()
        if session_id not in _CYCLE_COUNT_STORE:
            raise HTTPException(status_code=404, detail="Cycle count session not found")

        session = _CYCLE_COUNT_STORE[session_id]
        wh_id = session["warehouse_id"]

        tot_variance_val = Decimal("0.00")
        for item in reconcile_req.counts:
            key = f"{wh_id}_{item.sku}"
            counted = to_decimal(item.counted_quantity)
            if key in _STOCK_STORE:
                stock = _STOCK_STORE[key]
                cost = to_decimal(stock["unit_cost"])
                var = calculate_stock_variance(stock["quantity_on_hand"], counted, cost)
                tot_variance_val += var["variance_value"]
                # Adjust stock on hand to counted physical quantity
                stock["quantity_on_hand"] = counted
                stock["quantity_available"] = counted - to_decimal(stock["quantity_reserved"])
                stock["total_value"] = (counted * cost).quantize(Decimal("0.01"))

        now = datetime.utcnow()
        session["status"] = "RECONCILED"
        session["total_items_counted"] = len(reconcile_req.counts)
        session["total_variance_value"] = tot_variance_val
        session["reconciled_at"] = now
        if reconcile_req.notes:
            session["notes"] = f"{session.get('notes') or ''}\n{reconcile_req.notes}".strip()

        return CycleCountOut(**session)

    # ---------------------------------------------------------
    # ERP & Inventory Telemetry KPIs
    # ---------------------------------------------------------
    def get_inventory_metrics(self) -> InventoryMetricsOut:
        _seed_inventory_data()
        stocks = list(_STOCK_STORE.values())
        pos = list(_PO_STORE.values())

        val_data = calculate_inventory_valuation(stocks)
        low_stock_cnt = len([s for s in stocks if s["stock_status"] in ("LOW_STOCK", "OUT_OF_STOCK")])

        open_pos = [p for p in pos if p["status"] in ("ISSUED", "PARTIALLY_RECEIVED", "DRAFT")]
        open_po_val = sum((to_decimal(p["total_amount"]) for p in open_pos), Decimal("0.00"))

        return InventoryMetricsOut(
            total_warehouses_count=len(_WAREHOUSE_STORE),
            total_active_skus=val_data["total_skus"],
            total_stock_units=val_data["total_units"],
            total_inventory_valuation=val_data["total_valuation"],
            low_stock_items_count=low_stock_cnt,
            active_purchase_orders_count=len(open_pos),
            total_open_po_value=open_po_val.quantize(Decimal("0.01")),
            goods_receipts_completed_count=len(_GRN_STORE),
            stock_movements_today_count=len(_MOVEMENT_STORE)
        )


inventory_service = InventoryService()
