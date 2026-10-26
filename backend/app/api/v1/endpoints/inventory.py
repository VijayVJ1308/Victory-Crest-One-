"""Victory Crest One - Supply Chain, ERP & Warehouse Inventory REST API Endpoints
Warehouses, Stock Catalog, Purchase Orders (ERP), Goods Receipt (GRN),
Stock Transfers, Cycle Counts, and Valuation Metrics.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, Path, Body
from backend.app.schemas.inventory import (
    WarehouseCreate, WarehouseOut,
    PurchaseOrderCreate, PurchaseOrderOut, PurchaseOrderReceiveRequest,
    WarehouseStockOut, StockReplenishmentAlert,
    StockTransferRequest, StockMovementOut,
    CycleCountCreate, CycleCountReconcileRequest, CycleCountOut,
    InventoryMetricsOut
)
from backend.app.services.inventory_service import inventory_service

router = APIRouter(prefix="/inventory")


# -------------------------------------------------------------
# Warehouse Endpoints
# -------------------------------------------------------------
@router.get("/warehouses", response_model=List[WarehouseOut])
def list_warehouses(
    property_id: Optional[str] = Query(None, description="Filter warehouses by property ID")
):
    """List all logistics hubs, storage depots, and property warehouses."""
    return inventory_service.list_warehouses(property_id=property_id)


@router.post("/warehouses", response_model=WarehouseOut)
def create_warehouse(warehouse_in: WarehouseCreate):
    """Register a new storage depot or distribution center."""
    return inventory_service.create_warehouse(warehouse_in)


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseOut)
def get_warehouse(warehouse_id: str = Path(..., description="Warehouse ID")):
    """Get warehouse details and facility manager info."""
    return inventory_service.get_warehouse(warehouse_id)


# -------------------------------------------------------------
# Stock Catalog & Replenishment Alerts
# -------------------------------------------------------------
@router.get("/stock", response_model=List[WarehouseStockOut])
def list_stock(
    warehouse_id: Optional[str] = Query(None, description="Filter stock by warehouse ID"),
    category: Optional[str] = Query(None, description="Filter stock by product category"),
    stock_status: Optional[str] = Query(None, description="Filter stock by status (IN_STOCK, LOW_STOCK, OUT_OF_STOCK)")
):
    """List live stock balances across warehouses with AVCO valuation."""
    return inventory_service.list_stock(
        warehouse_id=warehouse_id,
        category=category,
        stock_status=stock_status
    )


@router.get("/stock/{warehouse_id}/{sku}", response_model=WarehouseStockOut)
def get_stock_item(
    warehouse_id: str = Path(..., description="Warehouse ID"),
    sku: str = Path(..., description="Stock Keeping Unit (SKU)")
):
    """Get live inventory balance for a specific SKU in a given warehouse."""
    return inventory_service.get_stock_item(warehouse_id, sku)


@router.put("/stock/{stock_id}", response_model=WarehouseStockOut)
def update_stock_item(
    stock_id: str = Path(..., description="Stock item ID or warehouse_sku key"),
    updates: Dict[str, Any] = Body(..., description="Stock fields to update (product_name, category, quantity_on_hand, reorder_point, unit_cost)")
):
    """Update stock item quantities, reorder thresholds, or unit costs."""
    return inventory_service.update_stock_item(stock_id, updates)


@router.get("/alerts/replenishment", response_model=List[StockReplenishmentAlert])
def list_replenishment_alerts(
    warehouse_id: Optional[str] = Query(None, description="Filter alerts by warehouse ID")
):
    """Detect all stock items at or below reorder point with suggested order quantities."""
    return inventory_service.list_replenishment_alerts(warehouse_id=warehouse_id)


# -------------------------------------------------------------
# Purchase Orders & Procurement (ERP)
# -------------------------------------------------------------
@router.get("/purchase-orders", response_model=List[PurchaseOrderOut])
def list_purchase_orders(
    supplier_id: Optional[str] = Query(None, description="Filter POs by supplier ID"),
    status: Optional[str] = Query(None, description="Filter POs by status (DRAFT, ISSUED, RECEIVED, CLOSED)")
):
    """List procurement purchase orders with line items and financial tracking."""
    return inventory_service.list_purchase_orders(
        supplier_id=supplier_id,
        status_filter=status
    )


@router.post("/purchase-orders", response_model=PurchaseOrderOut)
def create_purchase_order(po_in: PurchaseOrderCreate):
    """Issue a new procurement purchase order with automated tax and total calculation."""
    return inventory_service.create_purchase_order(po_in)


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
def get_purchase_order(po_id: str = Path(..., description="Purchase Order ID")):
    """Get detailed purchase order line items and receipt history."""
    return inventory_service.get_purchase_order(po_id)


@router.post("/purchase-orders/{po_id}/receive", response_model=PurchaseOrderOut)
def receive_purchase_order(
    po_id: str = Path(..., description="Purchase Order ID"),
    receipt_req: PurchaseOrderReceiveRequest = Body(...)
):
    """
    Receive goods against a purchase order:
    1. Increments warehouse stock on hand.
    2. Recalculates Weighted Average Cost (AVCO).
    3. Generates Goods Receipt Note (GRN).
    4. Automatically posts balanced double-entry GL journal (DR 1200 Inventory, CR 2010 AP).
    5. Automatically generates Accounts Payable Supplier Bill in Phase 4 Finance.
    """
    return inventory_service.receive_purchase_order(po_id, receipt_req)


# -------------------------------------------------------------
# Stock Transfers & Movements
# -------------------------------------------------------------
@router.post("/transfers", response_model=StockMovementOut)
def transfer_stock(req: StockTransferRequest = Body(...)):
    """Execute an atomic inter-warehouse stock transfer with live audit trail."""
    return inventory_service.transfer_stock(req)


@router.get("/movements", response_model=List[StockMovementOut])
def list_stock_movements(
    limit: int = Query(50, description="Max movements to return", ge=1, le=200)
):
    """List recent stock movements (Receipts, Transfers, Adjustments, Dispatches)."""
    return inventory_service.list_stock_movements(limit=limit)


# -------------------------------------------------------------
# Cycle Counts & Stocktaking
# -------------------------------------------------------------
@router.get("/cycle-counts", response_model=List[CycleCountOut])
def list_cycle_counts():
    """List periodic cycle counts and inventory reconciliation sessions."""
    return inventory_service.list_cycle_counts()


@router.post("/cycle-counts", response_model=CycleCountOut)
def create_cycle_count(count_in: CycleCountCreate):
    """Initiate a new physical inventory verification session."""
    return inventory_service.create_cycle_count(count_in)


@router.post("/cycle-counts/{session_id}/reconcile", response_model=CycleCountOut)
def reconcile_cycle_count(
    session_id: str = Path(..., description="Cycle Count Session ID"),
    reconcile_req: CycleCountReconcileRequest = Body(...)
):
    """Submit counted quantities, compute variance against system stock, and adjust ledger."""
    return inventory_service.reconcile_cycle_count(session_id, reconcile_req)


# -------------------------------------------------------------
# ERP & Inventory Telemetry Metrics
# -------------------------------------------------------------
@router.get("/metrics", response_model=InventoryMetricsOut)
def get_inventory_metrics():
    """Retrieve top-level ERP and warehouse KPIs (Valuation, SKUs, Stock Units, Open POs)."""
    return inventory_service.get_inventory_metrics()
