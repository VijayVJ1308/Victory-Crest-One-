"""Victory Crest One - Manufacturing & Production Management Service
Work Centers, Multi-Level Bill of Materials (BOM), Production Orders (MO),
Routing Labor & Machine Absorption, Quality Checks, and Automated GL Integration.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta, timezone
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.manufacturing import (
    WorkCenterCreate, WorkCenterUpdate, WorkCenterOut,
    BomComponentCreate, BomComponentOut,
    BomOperationCreate, BomOperationOut,
    BillOfMaterialsCreate, BillOfMaterialsUpdate, BillOfMaterialsOut,
    MaterialUsageCreate, MaterialUsageOut,
    QualityInspectionCreate, QualityInspectionOut,
    ProductionOrderCreate, ProductionOrderStartRequest,
    ProductionOrderCompleteRequest, ProductionOrderOut,
    ManufacturingMetricsOut
)
from backend.app.schemas.finance import JournalEntryCreate, JournalLineCreate
from backend.app.services.finance_service import finance_service
from backend.app.services.audit_service import audit_service
from shared.calculations import (
    to_decimal,
    calculate_bom_line_cost,
    calculate_bom_totals,
    calculate_production_order_cost,
    calculate_manufacturing_kpis
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory data stores
_WORK_CENTER_STORE: Dict[str, Dict[str, Any]] = {}
_BOM_STORE: Dict[str, Dict[str, Any]] = {}
_BOM_COMPONENT_STORE: Dict[str, List[Dict[str, Any]]] = {}
_BOM_OPERATION_STORE: Dict[str, List[Dict[str, Any]]] = {}
_PRODUCTION_ORDER_STORE: Dict[str, Dict[str, Any]] = {}
_MATERIAL_USAGE_STORE: Dict[str, List[Dict[str, Any]]] = {}
_QUALITY_INSPECTION_STORE: Dict[str, List[Dict[str, Any]]] = {}

_ORDER_COUNTER = 100


def _seed_manufacturing_data():
    """Populate initial work centers, BOMs with components & routing, and production orders."""
    global _ORDER_COUNTER
    if _WORK_CENTER_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]  # Madurai Heritage Hotel
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]  # Kodaikanal Mountain Resort
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]  # Chennai Hub
    now = datetime.now(timezone.utc)

    # 1. Work Centers
    wc_data = [
        ("wc_carp_01", "WC-CARP-01", "Colonial Teak Joinery & Carving Bay", "ASSEMBLY", Decimal("550.00"), Decimal("350.00"), Decimal("8.00"), "AVAILABLE", prop_mdu),
        ("wc_met_01", "WC-MET-01", "Precision Architectural Metalwork Bay", "MACHINING", Decimal("600.00"), Decimal("500.00"), Decimal("8.00"), "AVAILABLE", prop_mdu),
        ("wc_bky_01", "WC-BKY-01", "Artisan Hearth Bakery & Confectionery Deck", "BAKING", Decimal("450.00"), Decimal("400.00"), Decimal("10.00"), "BUSY", prop_kod),
        ("wc_asm_01", "WC-ASM-01", "Guest Amenity & Linens Production Cell", "PACKAGING", Decimal("380.00"), Decimal("250.00"), Decimal("8.00"), "AVAILABLE", prop_maa),
    ]

    for wc_id, code, name, wc_type, l_rate, m_rate, cap, st, prop in wc_data:
        _WORK_CENTER_STORE[wc_id] = {
            "id": wc_id,
            "organization_id": org_id,
            "property_id": prop,
            "code": code,
            "name": name,
            "work_center_type": wc_type,
            "hourly_labor_rate": l_rate,
            "hourly_machine_rate": m_rate,
            "daily_capacity_hours": cap,
            "status": st,
            "is_active": True,
            "created_at": now - timedelta(days=60)
        }

    # 2. Bill of Materials 1: Heritage Desk (Madurai)
    bom_id_1 = "bom_htg_desk_01"
    bom_comps_1 = [
        {"id": "comp_101", "bom_id": bom_id_1, "item_code": "RAW-TEAK-PLK", "item_name": "Quarter-Sawn Teak Hardwood Planks (bd ft)", "quantity": Decimal("25.00"), "uom": "bd ft", "unit_cost": Decimal("850.00"), "scrap_percent": Decimal("5.00"), "total_cost": Decimal("22312.50")},
        {"id": "comp_102", "bom_id": bom_id_1, "item_code": "RAW-BRS-PULL", "item_name": "Antiqued Solid Brass Drawer Pulls", "quantity": Decimal("20.00"), "uom": "Units", "unit_cost": Decimal("180.00"), "scrap_percent": Decimal("0.00"), "total_cost": Decimal("3600.00")},
        {"id": "comp_103", "bom_id": bom_id_1, "item_code": "RAW-LACQ-POL", "item_name": "Heritage Natural Shellac & Wax Lacquer", "quantity": Decimal("5.00"), "uom": "Liters", "unit_cost": Decimal("450.00"), "scrap_percent": Decimal("2.00"), "total_cost": Decimal("2295.00")},
    ]
    bom_ops_1 = [
        {"id": "op_101", "bom_id": bom_id_1, "sequence": 10, "work_center_id": "wc_carp_01", "work_center_name": "Colonial Teak Joinery & Carving Bay", "operation_name": "Timber Milling, Jointing & Dimensioning", "setup_time_hours": Decimal("1.00"), "run_time_per_unit_hours": Decimal("1.50"), "hourly_rate": Decimal("550.00"), "cost": Decimal("4675.00")},
        {"id": "op_102", "bom_id": bom_id_1, "sequence": 20, "work_center_id": "wc_carp_01", "work_center_name": "Colonial Teak Joinery & Carving Bay", "operation_name": "Mortise-and-Tenon Hand Joinery Assembly", "setup_time_hours": Decimal("0.50"), "run_time_per_unit_hours": Decimal("2.00"), "hourly_rate": Decimal("550.00"), "cost": Decimal("5775.00")},
        {"id": "op_103", "bom_id": bom_id_1, "sequence": 30, "work_center_id": "wc_carp_01", "work_center_name": "Colonial Teak Joinery & Carving Bay", "operation_name": "Multi-Coat Hand Rubbed Shellac Finishing", "setup_time_hours": Decimal("0.50"), "run_time_per_unit_hours": Decimal("1.00"), "hourly_rate": Decimal("450.00"), "cost": Decimal("2475.00")},
    ]
    totals_1 = calculate_bom_totals(bom_comps_1, bom_ops_1, batch_quantity=5)
    _BOM_STORE[bom_id_1] = {
        "id": bom_id_1,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "bom_code": "BOM-HTG-DESK-01",
        "product_id": "prd_htg_desk",
        "product_name": "Solid Teak Heritage Writing Desk",
        "product_sku": "PRD-HTG-DESK-01",
        "version": "v1.2",
        "batch_quantity": Decimal("5.00"),
        "uom": "Units",
        "total_material_cost": totals_1["total_material_cost"],
        "total_labor_cost": totals_1["total_operations_cost"],
        "total_bom_cost": totals_1["total_bom_cost"],
        "unit_cost": totals_1["unit_cost"],
        "status": "ACTIVE",
        "notes": "Premium colonial guestroom furnishing crafted from certified aged teak.",
        "created_at": now - timedelta(days=45)
    }
    _BOM_COMPONENT_STORE[bom_id_1] = bom_comps_1
    _BOM_OPERATION_STORE[bom_id_1] = bom_ops_1

    # 3. Bill of Materials 2: Artisan Sourdough Batard (Kodaikanal)
    bom_id_2 = "bom_bak_sd_01"
    bom_comps_2 = [
        {"id": "comp_201", "bom_id": bom_id_2, "item_code": "RAW-FLR-ORG", "item_name": "Stoneground Organic Wheat Flour", "quantity": Decimal("30.00"), "uom": "Kg", "unit_cost": Decimal("95.00"), "scrap_percent": Decimal("2.00"), "total_cost": Decimal("2907.00")},
        {"id": "comp_202", "bom_id": bom_id_2, "item_code": "RAW-BTR-FRN", "item_name": "French Cultured Salted Butter", "quantity": Decimal("5.00"), "uom": "Kg", "unit_cost": Decimal("650.00"), "scrap_percent": Decimal("0.00"), "total_cost": Decimal("3250.00")},
        {"id": "comp_203", "bom_id": bom_id_2, "item_code": "RAW-MIN-WTR", "item_name": "Spring Water & Unrefined Sea Salt", "quantity": Decimal("22.00"), "uom": "Kg", "unit_cost": Decimal("15.00"), "scrap_percent": Decimal("0.00"), "total_cost": Decimal("330.00")},
    ]
    bom_ops_2 = [
        {"id": "op_201", "bom_id": bom_id_2, "sequence": 10, "work_center_id": "wc_bky_01", "work_center_name": "Artisan Hearth Bakery & Confectionery Deck", "operation_name": "Wild Yeast Levain Mixing & Cold Fermentation", "setup_time_hours": Decimal("1.00"), "run_time_per_unit_hours": Decimal("0.04"), "hourly_rate": Decimal("450.00"), "cost": Decimal("1350.00")},
        {"id": "op_202", "bom_id": bom_id_2, "sequence": 20, "work_center_id": "wc_bky_01", "work_center_name": "Artisan Hearth Bakery & Confectionery Deck", "operation_name": "Stone Deck Hearth Steam Baking", "setup_time_hours": Decimal("0.50"), "run_time_per_unit_hours": Decimal("0.02"), "hourly_rate": Decimal("400.00"), "cost": Decimal("600.00")},
    ]
    totals_2 = calculate_bom_totals(bom_comps_2, bom_ops_2, batch_quantity=50)
    _BOM_STORE[bom_id_2] = {
        "id": bom_id_2,
        "organization_id": org_id,
        "property_id": prop_kod,
        "bom_code": "BOM-BAK-SD-01",
        "product_id": "prd_bak_sd",
        "product_name": "Wild Yeast Artisan Sourdough Batard",
        "product_sku": "PRD-BAK-SD-01",
        "version": "v2.0",
        "batch_quantity": Decimal("50.00"),
        "uom": "Loaves",
        "total_material_cost": totals_2["total_material_cost"],
        "total_labor_cost": totals_2["total_operations_cost"],
        "total_bom_cost": totals_2["total_bom_cost"],
        "unit_cost": totals_2["unit_cost"],
        "status": "ACTIVE",
        "notes": "36-hour slow fermented sourdough served at resort dining and retail deli.",
        "created_at": now - timedelta(days=30)
    }
    _BOM_COMPONENT_STORE[bom_id_2] = bom_comps_2
    _BOM_OPERATION_STORE[bom_id_2] = bom_ops_2

    # 4. Production Orders
    # Order 1: Completed Desk production (GL already posted)
    order_id_1 = "mo_2026_001"
    _PRODUCTION_ORDER_STORE[order_id_1] = {
        "id": order_id_1,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "order_number": "MO-2026-001",
        "bom_id": bom_id_1,
        "bom_code": "BOM-HTG-DESK-01",
        "product_id": "prd_htg_desk",
        "product_name": "Solid Teak Heritage Writing Desk",
        "target_quantity": Decimal("5.00"),
        "produced_quantity": Decimal("5.00"),
        "rejected_quantity": Decimal("0.00"),
        "status": "COMPLETED",
        "priority": "HIGH",
        "work_center_id": "wc_carp_01",
        "work_center_name": "Colonial Teak Joinery & Carving Bay",
        "supervisor_name": "Master Craftsman Ramanathan K.",
        "planned_start_date": now - timedelta(days=10),
        "planned_end_date": now - timedelta(days=3),
        "actual_start_date": now - timedelta(days=10),
        "actual_end_date": now - timedelta(days=3),
        "material_cost": Decimal("28207.50"),
        "labor_cost": Decimal("12925.00"),
        "overhead_cost": Decimal("2500.00"),
        "total_actual_cost": Decimal("43632.50"),
        "unit_actual_cost": Decimal("8726.50"),
        "journal_entry_id": "jn_mfg_001",
        "notes": "5 luxury desks completed for Presidential Suites renovation.",
        "created_at": now - timedelta(days=10)
    }
    _MATERIAL_USAGE_STORE[order_id_1] = [
        {"id": "mat_101", "production_order_id": order_id_1, "item_code": "RAW-TEAK-PLK", "item_name": "Quarter-Sawn Teak Hardwood Planks (bd ft)", "planned_quantity": Decimal("25.00"), "actual_quantity": Decimal("25.00"), "uom": "bd ft", "unit_cost": Decimal("850.00"), "total_cost": Decimal("21250.00")},
        {"id": "mat_102", "production_order_id": order_id_1, "item_code": "RAW-BRS-PULL", "item_name": "Antiqued Solid Brass Drawer Pulls", "planned_quantity": Decimal("20.00"), "actual_quantity": Decimal("20.00"), "uom": "Units", "unit_cost": Decimal("180.00"), "total_cost": Decimal("3600.00")},
        {"id": "mat_103", "production_order_id": order_id_1, "item_code": "RAW-LACQ-POL", "item_name": "Heritage Natural Shellac & Wax Lacquer", "planned_quantity": Decimal("5.00"), "actual_quantity": Decimal("5.50"), "uom": "Liters", "unit_cost": Decimal("450.00"), "total_cost": Decimal("2475.00")},
    ]
    _QUALITY_INSPECTION_STORE[order_id_1] = [
        {"id": "qi_101", "production_order_id": order_id_1, "parameter_name": "Dimensional Square & Joint Fit", "target_specification": "±0.5 mm tolerance on all dovetail joints", "measured_value": "0.2 mm exact match", "status": "PASSED", "inspector_name": "QA Specialist Anand S.", "inspected_at": now - timedelta(days=3), "remarks": "Exceptional precision timber jointing."},
        {"id": "qi_102", "production_order_id": order_id_1, "parameter_name": "Moisture Content & Finish Luster", "target_specification": "< 8% wood moisture, high gloss satin", "measured_value": "6.8% moisture, 92 GU satin sheen", "status": "PASSED", "inspector_name": "QA Specialist Anand S.", "inspected_at": now - timedelta(days=3), "remarks": "Approved for five-star suite deployment."},
    ]

    # Order 2: In-Progress Bakery Run (Kodaikanal)
    order_id_2 = "mo_2026_002"
    _PRODUCTION_ORDER_STORE[order_id_2] = {
        "id": order_id_2,
        "organization_id": org_id,
        "property_id": prop_kod,
        "order_number": "MO-2026-002",
        "bom_id": bom_id_2,
        "bom_code": "BOM-BAK-SD-01",
        "product_id": "prd_bak_sd",
        "product_name": "Wild Yeast Artisan Sourdough Batard",
        "target_quantity": Decimal("50.00"),
        "produced_quantity": Decimal("48.00"),
        "rejected_quantity": Decimal("2.00"),
        "status": "IN_PROGRESS",
        "priority": "NORMAL",
        "work_center_id": "wc_bky_01",
        "work_center_name": "Artisan Hearth Bakery & Confectionery Deck",
        "supervisor_name": "Head Baker Jacques Moreau",
        "planned_start_date": now - timedelta(hours=6),
        "planned_end_date": now + timedelta(hours=2),
        "actual_start_date": now - timedelta(hours=6),
        "actual_end_date": None,
        "material_cost": Decimal("6487.00"),
        "labor_cost": Decimal("1950.00"),
        "overhead_cost": Decimal("400.00"),
        "total_actual_cost": Decimal("8837.00"),
        "unit_actual_cost": Decimal("176.74"),
        "journal_entry_id": None,
        "notes": "Daily morning bake for mountain resort breakfast and deli orders.",
        "created_at": now - timedelta(hours=8)
    }
    _MATERIAL_USAGE_STORE[order_id_2] = [
        {"id": "mat_201", "production_order_id": order_id_2, "item_code": "RAW-FLR-ORG", "item_name": "Stoneground Organic Wheat Flour", "planned_quantity": Decimal("30.00"), "actual_quantity": Decimal("30.00"), "uom": "Kg", "unit_cost": Decimal("95.00"), "total_cost": Decimal("2850.00")},
        {"id": "mat_202", "production_order_id": order_id_2, "item_code": "RAW-BTR-FRN", "item_name": "French Cultured Salted Butter", "planned_quantity": Decimal("5.00"), "actual_quantity": Decimal("5.00"), "uom": "Kg", "unit_cost": Decimal("650.00"), "total_cost": Decimal("3250.00")},
    ]

    # Order 3: Planned Order (Chennai)
    order_id_3 = "mo_2026_003"
    _PRODUCTION_ORDER_STORE[order_id_3] = {
        "id": order_id_3,
        "organization_id": org_id,
        "property_id": prop_maa,
        "order_number": "MO-2026-003",
        "bom_id": bom_id_1,
        "bom_code": "BOM-HTG-DESK-01",
        "product_id": "prd_htg_desk",
        "product_name": "Solid Teak Heritage Writing Desk",
        "target_quantity": Decimal("10.00"),
        "produced_quantity": Decimal("0.00"),
        "rejected_quantity": Decimal("0.00"),
        "status": "PLANNED",
        "priority": "NORMAL",
        "work_center_id": "wc_carp_01",
        "work_center_name": "Colonial Teak Joinery & Carving Bay",
        "supervisor_name": "Production Lead Srinivasan P.",
        "planned_start_date": now + timedelta(days=2),
        "planned_end_date": now + timedelta(days=12),
        "actual_start_date": None,
        "actual_end_date": None,
        "material_cost": Decimal("0.00"),
        "labor_cost": Decimal("0.00"),
        "overhead_cost": Decimal("0.00"),
        "total_actual_cost": Decimal("0.00"),
        "unit_actual_cost": Decimal("0.00"),
        "journal_entry_id": None,
        "notes": "Scheduled production run for Chennai corporate boutique.",
        "created_at": now - timedelta(days=1)
    }


class ManufacturingService:
    """Enterprise Manufacturing, BOM, Production Routing, and Costing Engine."""

    def __init__(self):
        _seed_manufacturing_data()

    # -------------------------------------------------------------
    # Work Centers
    # -------------------------------------------------------------
    def list_work_centers(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        work_center_type: Optional[str] = None
    ) -> List[WorkCenterOut]:
        _seed_manufacturing_data()
        res = []
        for wc in _WORK_CENTER_STORE.values():
            if organization_id and wc["organization_id"] != organization_id:
                continue
            if property_id and wc["property_id"] != property_id:
                continue
            if work_center_type and wc["work_center_type"].upper() != work_center_type.upper():
                continue
            res.append(WorkCenterOut(**wc))
        return sorted(res, key=lambda x: x.code)

    def create_work_center(self, payload: WorkCenterCreate) -> WorkCenterOut:
        _seed_manufacturing_data()
        wc_id = f"wc_{uuid.uuid4().hex[:8]}"
        org_id = payload.organization_id or DEMO_ORGANISATIONS[0]["id"]
        prop_id = payload.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]

        wc_dict = {
            "id": wc_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "code": payload.code,
            "name": payload.name,
            "work_center_type": payload.work_center_type,
            "hourly_labor_rate": to_decimal(payload.hourly_labor_rate),
            "hourly_machine_rate": to_decimal(payload.hourly_machine_rate),
            "daily_capacity_hours": to_decimal(payload.daily_capacity_hours),
            "status": payload.status,
            "is_active": payload.is_active,
            "created_at": datetime.now(timezone.utc)
        }
        _WORK_CENTER_STORE[wc_id] = wc_dict
        return WorkCenterOut(**wc_dict)

    def update_work_center(self, work_center_id: str, payload: WorkCenterUpdate) -> WorkCenterOut:
        _seed_manufacturing_data()
        if work_center_id not in _WORK_CENTER_STORE:
            raise HTTPException(status_code=404, detail=f"Work Center {work_center_id} not found")

        wc = _WORK_CENTER_STORE[work_center_id]
        if payload.name is not None:
            wc["name"] = payload.name
        if payload.work_center_type is not None:
            wc["work_center_type"] = payload.work_center_type
        if payload.hourly_labor_rate is not None:
            wc["hourly_labor_rate"] = to_decimal(payload.hourly_labor_rate)
        if payload.hourly_machine_rate is not None:
            wc["hourly_machine_rate"] = to_decimal(payload.hourly_machine_rate)
        if payload.daily_capacity_hours is not None:
            wc["daily_capacity_hours"] = to_decimal(payload.daily_capacity_hours)
        if payload.status is not None:
            wc["status"] = payload.status
        if payload.is_active is not None:
            wc["is_active"] = payload.is_active

        return WorkCenterOut(**wc)

    # -------------------------------------------------------------
    # Bill of Materials (BOM)
    # -------------------------------------------------------------
    def list_boms(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[BillOfMaterialsOut]:
        _seed_manufacturing_data()
        res = []
        for b_id, bom in _BOM_STORE.items():
            if organization_id and bom["organization_id"] != organization_id:
                continue
            if property_id and bom["property_id"] != property_id:
                continue
            if status and bom["status"].upper() != status.upper():
                continue

            comps = [BomComponentOut(**c) for c in _BOM_COMPONENT_STORE.get(b_id, [])]
            ops = [BomOperationOut(**o) for o in _BOM_OPERATION_STORE.get(b_id, [])]
            b_dict = dict(bom)
            b_dict["components"] = comps
            b_dict["operations"] = ops
            res.append(BillOfMaterialsOut(**b_dict))

        return sorted(res, key=lambda x: x.bom_code)

    def get_bom(self, bom_id: str) -> BillOfMaterialsOut:
        _seed_manufacturing_data()
        if bom_id not in _BOM_STORE:
            raise HTTPException(status_code=404, detail=f"BOM {bom_id} not found")

        bom = _BOM_STORE[bom_id]
        comps = [BomComponentOut(**c) for c in _BOM_COMPONENT_STORE.get(bom_id, [])]
        ops = [BomOperationOut(**o) for o in _BOM_OPERATION_STORE.get(bom_id, [])]
        b_dict = dict(bom)
        b_dict["components"] = comps
        b_dict["operations"] = ops
        return BillOfMaterialsOut(**b_dict)

    def create_bom(self, payload: BillOfMaterialsCreate) -> BillOfMaterialsOut:
        _seed_manufacturing_data()
        bom_id = f"bom_{uuid.uuid4().hex[:8]}"
        org_id = payload.organization_id or DEMO_ORGANISATIONS[0]["id"]
        prop_id = payload.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]

        # Calculate component and operation totals
        comps_list = []
        for c in payload.components:
            cid = f"comp_{uuid.uuid4().hex[:6]}"
            q_res = calculate_bom_line_cost(c.quantity, c.unit_cost, c.scrap_percent)
            c_dict = {
                "id": cid,
                "bom_id": bom_id,
                "item_code": c.item_code,
                "item_name": c.item_name,
                "quantity": q_res["quantity_required"],
                "uom": c.uom,
                "unit_cost": q_res["unit_cost"],
                "scrap_percent": q_res["scrap_percent"],
                "total_cost": q_res["total_line_cost"]
            }
            comps_list.append(c_dict)

        ops_list = []
        batch_qty = to_decimal(payload.batch_quantity)
        for o in payload.operations:
            oid = f"op_{uuid.uuid4().hex[:6]}"
            setup = to_decimal(o.setup_time_hours)
            run = to_decimal(o.run_time_per_unit_hours)
            rate = to_decimal(o.hourly_rate)
            cost = (setup + run * batch_qty) * rate
            o_dict = {
                "id": oid,
                "bom_id": bom_id,
                "sequence": o.sequence,
                "work_center_id": o.work_center_id,
                "work_center_name": o.work_center_name,
                "operation_name": o.operation_name,
                "setup_time_hours": setup,
                "run_time_per_unit_hours": run,
                "hourly_rate": rate,
                "cost": cost.quantize(Decimal("0.01"))
            }
            ops_list.append(o_dict)

        totals = calculate_bom_totals(comps_list, ops_list, batch_quantity=batch_qty)

        bom_dict = {
            "id": bom_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "bom_code": payload.bom_code,
            "product_id": payload.product_id,
            "product_name": payload.product_name,
            "product_sku": payload.product_sku,
            "version": payload.version,
            "batch_quantity": batch_qty,
            "uom": payload.uom,
            "total_material_cost": totals["total_material_cost"],
            "total_labor_cost": totals["total_operations_cost"],
            "total_bom_cost": totals["total_bom_cost"],
            "unit_cost": totals["unit_cost"],
            "status": "ACTIVE",
            "notes": payload.notes,
            "created_at": datetime.now(timezone.utc)
        }

        _BOM_STORE[bom_id] = bom_dict
        _BOM_COMPONENT_STORE[bom_id] = comps_list
        _BOM_OPERATION_STORE[bom_id] = ops_list

        audit_service.log_action(
            user_id="SYSTEM",
            user_email="system@victorycrest.com",
            action="CREATE",
            entity_type="BILL_OF_MATERIALS",
            entity_id=bom_id,
            details=f"Created BOM {payload.bom_code} for {payload.product_name}"
        )

        return self.get_bom(bom_id)

    # -------------------------------------------------------------
    # Production Orders (Manufacturing Work Orders)
    # -------------------------------------------------------------
    def list_production_orders(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[ProductionOrderOut]:
        _seed_manufacturing_data()
        res = []
        for o_id, order in _PRODUCTION_ORDER_STORE.items():
            if organization_id and order["organization_id"] != organization_id:
                continue
            if property_id and order["property_id"] != property_id:
                continue
            if status and order["status"].upper() != status.upper():
                continue
            if priority and order["priority"].upper() != priority.upper():
                continue

            mats = [MaterialUsageOut(**m) for m in _MATERIAL_USAGE_STORE.get(o_id, [])]
            qis = [QualityInspectionOut(**q) for q in _QUALITY_INSPECTION_STORE.get(o_id, [])]
            o_dict = dict(order)
            o_dict["materials"] = mats
            o_dict["inspections"] = qis
            res.append(ProductionOrderOut(**o_dict))

        return sorted(res, key=lambda x: x.order_number, reverse=True)

    def get_production_order(self, order_id: str) -> ProductionOrderOut:
        _seed_manufacturing_data()
        if order_id not in _PRODUCTION_ORDER_STORE:
            raise HTTPException(status_code=404, detail=f"Production Order {order_id} not found")

        order = _PRODUCTION_ORDER_STORE[order_id]
        mats = [MaterialUsageOut(**m) for m in _MATERIAL_USAGE_STORE.get(order_id, [])]
        qis = [QualityInspectionOut(**q) for q in _QUALITY_INSPECTION_STORE.get(order_id, [])]
        o_dict = dict(order)
        o_dict["materials"] = mats
        o_dict["inspections"] = qis
        return ProductionOrderOut(**o_dict)

    def create_production_order(self, payload: ProductionOrderCreate) -> ProductionOrderOut:
        _seed_manufacturing_data()
        global _ORDER_COUNTER

        if payload.bom_id not in _BOM_STORE:
            raise HTTPException(status_code=404, detail=f"BOM {payload.bom_id} not found")

        bom = _BOM_STORE[payload.bom_id]
        _ORDER_COUNTER += 1
        order_num = f"MO-2026-{_ORDER_COUNTER:03d}"
        order_id = f"mo_{uuid.uuid4().hex[:8]}"

        org_id = payload.organization_id or bom["organization_id"]
        prop_id = payload.property_id or bom["property_id"]

        wc_name = None
        if payload.work_center_id and payload.work_center_id in _WORK_CENTER_STORE:
            wc_name = _WORK_CENTER_STORE[payload.work_center_id]["name"]

        order_dict = {
            "id": order_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "order_number": order_num,
            "bom_id": bom["id"],
            "bom_code": bom["bom_code"],
            "product_id": bom["product_id"],
            "product_name": bom["product_name"],
            "target_quantity": to_decimal(payload.target_quantity),
            "produced_quantity": Decimal("0.00"),
            "rejected_quantity": Decimal("0.00"),
            "status": "PLANNED",
            "priority": payload.priority.upper(),
            "work_center_id": payload.work_center_id,
            "work_center_name": wc_name,
            "supervisor_name": payload.supervisor_name or "Plant Floor Supervisor",
            "planned_start_date": payload.planned_start_date,
            "planned_end_date": payload.planned_end_date,
            "actual_start_date": None,
            "actual_end_date": None,
            "material_cost": Decimal("0.00"),
            "labor_cost": Decimal("0.00"),
            "overhead_cost": Decimal("0.00"),
            "total_actual_cost": Decimal("0.00"),
            "unit_actual_cost": Decimal("0.00"),
            "journal_entry_id": None,
            "notes": payload.notes,
            "created_at": datetime.now(timezone.utc)
        }

        # Initialize planned materials from BOM components scaled to target quantity
        scale_factor = to_decimal(payload.target_quantity) / max(Decimal("1.00"), to_decimal(bom["batch_quantity"]))
        mats_list = []
        for c in _BOM_COMPONENT_STORE.get(bom["id"], []):
            planned_qty = to_decimal(c["quantity"]) * scale_factor
            mats_list.append({
                "id": f"mat_{uuid.uuid4().hex[:6]}",
                "production_order_id": order_id,
                "item_code": c["item_code"],
                "item_name": c["item_name"],
                "planned_quantity": planned_qty.quantize(Decimal("0.01")),
                "actual_quantity": Decimal("0.00"),
                "uom": c["uom"],
                "unit_cost": to_decimal(c["unit_cost"]),
                "total_cost": Decimal("0.00")
            })

        _PRODUCTION_ORDER_STORE[order_id] = order_dict
        _MATERIAL_USAGE_STORE[order_id] = mats_list
        _QUALITY_INSPECTION_STORE[order_id] = []

        audit_service.log_action(
            user_id="SYSTEM",
            user_email="system@victorycrest.com",
            action="CREATE",
            entity_type="PRODUCTION_ORDER",
            entity_id=order_id,
            details=f"Created Production Order {order_num} for {order_dict['target_quantity']} x {bom['product_name']}"
        )

        return self.get_production_order(order_id)

    def start_production_order(
        self,
        order_id: str,
        payload: Optional[ProductionOrderStartRequest] = None
    ) -> ProductionOrderOut:
        _seed_manufacturing_data()
        if order_id not in _PRODUCTION_ORDER_STORE:
            raise HTTPException(status_code=404, detail=f"Production Order {order_id} not found")

        order = _PRODUCTION_ORDER_STORE[order_id]
        if order["status"] == "COMPLETED":
            raise HTTPException(status_code=400, detail="Completed orders cannot be restarted")

        order["status"] = "IN_PROGRESS"
        order["actual_start_date"] = (payload.actual_start_date if payload and payload.actual_start_date else datetime.now(timezone.utc))

        if payload and payload.work_center_id:
            order["work_center_id"] = payload.work_center_id
            if payload.work_center_id in _WORK_CENTER_STORE:
                order["work_center_name"] = _WORK_CENTER_STORE[payload.work_center_id]["name"]
                _WORK_CENTER_STORE[payload.work_center_id]["status"] = "BUSY"

        if payload and payload.supervisor_name:
            order["supervisor_name"] = payload.supervisor_name

        return self.get_production_order(order_id)

    def complete_production_order(
        self,
        order_id: str,
        payload: ProductionOrderCompleteRequest
    ) -> ProductionOrderOut:
        """
        Finalize production run, calculate absorption cost, log QA, and post Finance GL Journal:
        DR 1230 Finished Goods Inventory (Total Production Cost)
        CR 1210 Raw Materials Inventory (Materials Consumed)
        CR 5030 Manufacturing Direct Labor & Overhead Absorbed
        """
        _seed_manufacturing_data()
        if order_id not in _PRODUCTION_ORDER_STORE:
            raise HTTPException(status_code=404, detail=f"Production Order {order_id} not found")

        order = _PRODUCTION_ORDER_STORE[order_id]
        if order["status"] == "COMPLETED":
            raise HTTPException(status_code=400, detail="Production order is already completed")

        now = datetime.now(timezone.utc)
        produced_qty = to_decimal(payload.produced_quantity)
        rejected_qty = to_decimal(payload.rejected_quantity)

        # 1. Update Materials Consumed
        mats_list = _MATERIAL_USAGE_STORE.get(order_id, [])
        if payload.actual_materials:
            mats_list = []
            for m in payload.actual_materials:
                tot = (to_decimal(m.actual_quantity) * to_decimal(m.unit_cost)).quantize(Decimal("0.01"))
                mats_list.append({
                    "id": f"mat_{uuid.uuid4().hex[:6]}",
                    "production_order_id": order_id,
                    "item_code": m.item_code,
                    "item_name": m.item_name,
                    "planned_quantity": to_decimal(m.planned_quantity),
                    "actual_quantity": to_decimal(m.actual_quantity),
                    "uom": m.uom,
                    "unit_cost": to_decimal(m.unit_cost),
                    "total_cost": tot
                })
            _MATERIAL_USAGE_STORE[order_id] = mats_list
        else:
            # Scale actual quantities to planned if not explicitly provided
            for m in mats_list:
                m["actual_quantity"] = m["planned_quantity"]
                m["total_cost"] = (m["actual_quantity"] * m["unit_cost"]).quantize(Decimal("0.01"))

        # Determine hourly labor rate
        labor_rate = Decimal("450.00")
        if payload.labor_hourly_rate:
            labor_rate = to_decimal(payload.labor_hourly_rate)
        elif order["work_center_id"] and order["work_center_id"] in _WORK_CENTER_STORE:
            labor_rate = to_decimal(_WORK_CENTER_STORE[order["work_center_id"]]["hourly_labor_rate"])

        # 2. Compute Actual Cost Breakdown
        cost_res = calculate_production_order_cost(
            actual_materials=mats_list,
            actual_labor_hours=payload.actual_labor_hours,
            labor_hourly_rate=labor_rate,
            overhead_cost=payload.overhead_cost,
            produced_quantity=produced_qty
        )

        order["produced_quantity"] = produced_qty
        order["rejected_quantity"] = rejected_qty
        order["material_cost"] = cost_res["material_cost"]
        order["labor_cost"] = cost_res["labor_cost"]
        order["overhead_cost"] = cost_res["overhead_cost"]
        order["total_actual_cost"] = cost_res["total_actual_cost"]
        order["unit_actual_cost"] = cost_res["unit_actual_cost"]
        order["status"] = "COMPLETED"
        order["actual_end_date"] = now
        if not order["actual_start_date"]:
            order["actual_start_date"] = now - timedelta(hours=4)

        if payload.notes:
            order["notes"] = payload.notes

        # 3. Add Quality Check Record
        qi_id = f"qi_{uuid.uuid4().hex[:6]}"
        qa_record = {
            "id": qi_id,
            "production_order_id": order_id,
            "parameter_name": "Finished Goods Quality Inspection & Tolerance",
            "target_specification": f"Standard manufacturing tolerances for {order['product_name']}",
            "measured_value": f"Verified {produced_qty} units compliant; {rejected_qty} scrap units logged",
            "status": payload.quality_status.upper(),
            "inspector_name": "Chief Quality Inspector",
            "inspected_at": now,
            "remarks": "Batch cleared quality control checkpoint for warehouse receipting."
        }
        _QUALITY_INSPECTION_STORE.setdefault(order_id, []).append(qa_record)

        # Release work center back to AVAILABLE
        if order["work_center_id"] and order["work_center_id"] in _WORK_CENTER_STORE:
            _WORK_CENTER_STORE[order["work_center_id"]]["status"] = "AVAILABLE"

        # 4. Automated Double-Entry General Ledger Posting
        tot_production = cost_res["total_actual_cost"]
        mat_cost = cost_res["material_cost"]
        labor_plus_overhead = cost_res["labor_cost"] + cost_res["overhead_cost"]

        if tot_production > Decimal("0.00"):
            try:
                # Find GL accounts in Chart of Accounts
                accounts = finance_service.get_accounts(organization_id=order["organization_id"])
                acc_by_code = {a["account_code"]: a["id"] for a in accounts}

                # Debit: Finished Goods Inventory (1230 or fallback 1200)
                dr_acc_id = acc_by_code.get("1230") or acc_by_code.get("1200") or list(acc_by_code.values())[0]

                # Credit: Raw Materials Inventory (1210 or fallback 1200)
                cr_mat_acc_id = acc_by_code.get("1210") or acc_by_code.get("1200") or list(acc_by_code.values())[0]

                # Credit: Manufacturing Direct Cost & Overhead (5030 or fallback 6010 / 5010)
                cr_overhead_acc_id = acc_by_code.get("5030") or acc_by_code.get("6010") or acc_by_code.get("5010") or list(acc_by_code.values())[0]

                journal_lines = [
                    JournalLineCreate(
                        account_code="1230",
                        debit=tot_production,
                        credit=Decimal("0.00"),
                        description=f"Finished goods receipt - {produced_qty} x {order['product_name']} ({order['order_number']})"
                    )
                ]

                if mat_cost > Decimal("0.00"):
                    journal_lines.append(
                        JournalLineCreate(
                            account_code="1210",
                            debit=Decimal("0.00"),
                            credit=mat_cost,
                            description=f"Raw materials inventory consumed - {order['order_number']}"
                        )
                    )

                if labor_plus_overhead > Decimal("0.00"):
                    journal_lines.append(
                        JournalLineCreate(
                            account_code="5030",
                            debit=Decimal("0.00"),
                            credit=labor_plus_overhead,
                            description=f"Direct labor and absorbed plant overhead - {order['order_number']}"
                        )
                    )
                elif mat_cost == Decimal("0.00"):
                    # Fallback if both 0
                    journal_lines.append(
                        JournalLineCreate(
                            account_code="5030",
                            debit=Decimal("0.00"),
                            credit=tot_production,
                            description=f"Absorbed production cost - {order['order_number']}"
                        )
                    )

                journal_payload = JournalEntryCreate(
                    organization_id=order["organization_id"],
                    property_id=order["property_id"],
                    entry_date=datetime.utcnow(),
                    entry_type="GENERAL",
                    reference=f"MFG-{order['order_number']}",
                    description=f"Manufacturing Order Completion: {produced_qty} units {order['product_name']}",
                    lines=journal_lines
                )
                posted_journal = finance_service.create_journal_entry(journal_payload)
                order["journal_entry_id"] = posted_journal["id"] if isinstance(posted_journal, dict) else posted_journal.id
            except Exception as e:
                # Log non-fatal error to audit
                audit_service.log_action(
                    user_id="SYSTEM",
                    user_email="system@victorycrest.com",
                    action="ERROR",
                    entity_type="PRODUCTION_ORDER",
                    entity_id=order_id,
                    details=f"Manufacturing GL posting skipped/errored: {str(e)}"
                )

        audit_service.log_action(
            user_id="SYSTEM",
            user_email="system@victorycrest.com",
            action="COMPLETE",
            entity_type="PRODUCTION_ORDER",
            entity_id=order_id,
            details=f"Completed {order['order_number']}: Produced {produced_qty} units at total cost ₹{order['total_actual_cost']}"
        )

        return self.get_production_order(order_id)

    def record_quality_inspection(
        self,
        order_id: str,
        payload: QualityInspectionCreate
    ) -> QualityInspectionOut:
        _seed_manufacturing_data()
        if order_id not in _PRODUCTION_ORDER_STORE:
            raise HTTPException(status_code=404, detail=f"Production Order {order_id} not found")

        qi_id = f"qi_{uuid.uuid4().hex[:6]}"
        record = {
            "id": qi_id,
            "production_order_id": order_id,
            "parameter_name": payload.parameter_name,
            "target_specification": payload.target_specification,
            "measured_value": payload.measured_value,
            "status": payload.status.upper(),
            "inspector_name": payload.inspector_name,
            "inspected_at": datetime.now(timezone.utc),
            "remarks": payload.remarks
        }
        _QUALITY_INSPECTION_STORE.setdefault(order_id, []).append(record)
        return QualityInspectionOut(**record)

    # -------------------------------------------------------------
    # Manufacturing Executive Telemetry & KPIs
    # -------------------------------------------------------------
    def get_manufacturing_metrics(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> ManufacturingMetricsOut:
        _seed_manufacturing_data()

        orders = [
            o for o in _PRODUCTION_ORDER_STORE.values()
            if (not organization_id or o["organization_id"] == organization_id)
            and (not property_id or o["property_id"] == property_id)
        ]
        work_centers = [
            wc for wc in _WORK_CENTER_STORE.values()
            if (not organization_id or wc["organization_id"] == organization_id)
            and (not property_id or wc["property_id"] == property_id)
        ]

        total_cap_hours = sum(to_decimal(wc["daily_capacity_hours"]) for wc in work_centers)
        # Approximate used hours based on active orders
        used_hours = sum(Decimal("8.00") for o in orders if o["status"] in ("IN_PROGRESS", "QUALITY_CHECK"))

        kpis = calculate_manufacturing_kpis(
            orders=orders,
            total_capacity_hours=total_cap_hours,
            actual_hours_used=used_hours
        )

        active_orders = sum(1 for o in orders if o["status"] in ("PLANNED", "IN_PROGRESS", "QUALITY_CHECK"))
        completed_orders = sum(1 for o in orders if o["status"] == "COMPLETED")
        active_wcs = sum(1 for wc in work_centers if wc["status"] in ("AVAILABLE", "BUSY"))

        completed_with_qty = [o for o in orders if o["status"] == "COMPLETED" and to_decimal(o["produced_quantity"]) > Decimal("0.00")]
        if completed_with_qty:
            avg_unit_cost = (sum(to_decimal(o["total_actual_cost"]) for o in completed_with_qty) / sum(to_decimal(o["produced_quantity"]) for o in completed_with_qty)).quantize(Decimal("0.01"))
        else:
            avg_unit_cost = Decimal("0.00")

        return ManufacturingMetricsOut(
            total_orders=len(orders),
            active_orders=active_orders,
            completed_orders=completed_orders,
            total_produced_units=kpis["total_produced_units"],
            total_rejected_units=kpis["total_rejected_units"],
            scrap_rate_percent=kpis["scrap_rate_percent"],
            total_wip_valuation=kpis["total_wip_value"],
            active_work_centers=active_wcs,
            total_work_centers=len(work_centers),
            average_unit_cost=avg_unit_cost,
            capacity_utilization_percent=kpis["capacity_utilization_percent"]
        )


manufacturing_service = ManufacturingService()
