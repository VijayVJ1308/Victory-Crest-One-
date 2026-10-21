"""Victory Crest One - Manufacturing & Production REST API Endpoints
Work Centers, Multi-Level Bills of Materials (BOM), Production Orders,
Material Usages, Quality Checkpoints, and Executive Telemetry.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Path, Body
from backend.app.schemas.manufacturing import (
    WorkCenterCreate, WorkCenterUpdate, WorkCenterOut,
    BillOfMaterialsCreate, BillOfMaterialsUpdate, BillOfMaterialsOut,
    ProductionOrderCreate, ProductionOrderStartRequest,
    ProductionOrderCompleteRequest, ProductionOrderOut,
    QualityInspectionCreate, QualityInspectionOut,
    ManufacturingMetricsOut
)
from backend.app.services.manufacturing_service import manufacturing_service

router = APIRouter(prefix="/manufacturing")


# -------------------------------------------------------------
# Work Centers
# -------------------------------------------------------------
@router.get("/work-centers", response_model=List[WorkCenterOut])
def list_work_centers(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by property ID"),
    work_center_type: Optional[str] = Query(None, description="Filter by work center type (ASSEMBLY, MACHINING, BAKING, PACKAGING, LAB)")
):
    """Retrieve manufacturing work centers, machine bays, and labor/machine rates."""
    return manufacturing_service.list_work_centers(
        organization_id=organization_id,
        property_id=property_id,
        work_center_type=work_center_type
    )


@router.post("/work-centers", response_model=WorkCenterOut)
def create_work_center(payload: WorkCenterCreate):
    """Register a new manufacturing work center or production line."""
    return manufacturing_service.create_work_center(payload)


@router.put("/work-centers/{work_center_id}", response_model=WorkCenterOut)
def update_work_center(
    work_center_id: str = Path(..., description="Work Center ID"),
    payload: WorkCenterUpdate = Body(...)
):
    """Update work center parameters, capacity, and operational status."""
    return manufacturing_service.update_work_center(work_center_id, payload)


# -------------------------------------------------------------
# Bills of Materials (BOM)
# -------------------------------------------------------------
@router.get("/boms", response_model=List[BillOfMaterialsOut])
def list_boms(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by property ID"),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, ACTIVE, ARCHIVED)")
):
    """List Bills of Materials with component materials and routing operations."""
    return manufacturing_service.list_boms(
        organization_id=organization_id,
        property_id=property_id,
        status=status
    )


@router.get("/boms/{bom_id}", response_model=BillOfMaterialsOut)
def get_bom(bom_id: str = Path(..., description="BOM Master ID")):
    """Get single Bill of Materials recipe details and unit cost breakdown."""
    return manufacturing_service.get_bom(bom_id)


@router.post("/boms", response_model=BillOfMaterialsOut)
def create_bom(payload: BillOfMaterialsCreate):
    """Create a new Bill of Materials recipe with components and routing operations."""
    return manufacturing_service.create_bom(payload)


# -------------------------------------------------------------
# Production Orders (Manufacturing Work Orders)
# -------------------------------------------------------------
@router.get("/production-orders", response_model=List[ProductionOrderOut])
def list_production_orders(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by property ID"),
    status: Optional[str] = Query(None, description="Filter by order status (PLANNED, IN_PROGRESS, QUALITY_CHECK, COMPLETED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, NORMAL, HIGH, URGENT)")
):
    """Retrieve production orders with actual costs, status, and material usage logs."""
    return manufacturing_service.list_production_orders(
        organization_id=organization_id,
        property_id=property_id,
        status=status,
        priority=priority
    )


@router.get("/production-orders/{order_id}", response_model=ProductionOrderOut)
def get_production_order(order_id: str = Path(..., description="Production Order ID")):
    """Get production work order details including materials consumed and quality checks."""
    return manufacturing_service.get_production_order(order_id)


@router.post("/production-orders", response_model=ProductionOrderOut)
def create_production_order(payload: ProductionOrderCreate):
    """Release a new production order against an active Bill of Materials."""
    return manufacturing_service.create_production_order(payload)


@router.post("/production-orders/{order_id}/start", response_model=ProductionOrderOut)
def start_production_order(
    order_id: str = Path(..., description="Production Order ID"),
    payload: Optional[ProductionOrderStartRequest] = None
):
    """Transition a planned order to IN_PROGRESS and allocate work center capacity."""
    return manufacturing_service.start_production_order(order_id, payload)


@router.post("/production-orders/{order_id}/complete", response_model=ProductionOrderOut)
def complete_production_order(
    order_id: str = Path(..., description="Production Order ID"),
    payload: ProductionOrderCompleteRequest = Body(...)
):
    """Finalize production run, compute unit absorption cost, and post double-entry GL journal."""
    return manufacturing_service.complete_production_order(order_id, payload)


@router.post("/production-orders/{order_id}/inspections", response_model=QualityInspectionOut)
def record_quality_inspection(
    order_id: str = Path(..., description="Production Order ID"),
    payload: QualityInspectionCreate = Body(...)
):
    """Log an in-process or post-production quality assurance checkpoint."""
    return manufacturing_service.record_quality_inspection(order_id, payload)


# -------------------------------------------------------------
# Manufacturing Executive Telemetry & KPIs
# -------------------------------------------------------------
@router.get("/metrics", response_model=ManufacturingMetricsOut)
def get_manufacturing_metrics(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by property ID")
):
    """Retrieve executive manufacturing telemetry, scrap rates, and WIP valuation."""
    return manufacturing_service.get_manufacturing_metrics(
        organization_id=organization_id,
        property_id=property_id
    )
