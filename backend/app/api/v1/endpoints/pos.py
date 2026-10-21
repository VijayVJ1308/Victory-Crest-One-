"""Victory Crest One - Point of Sale (POS) & Commerce REST API Endpoints
Terminal management, Shift sessions, Catalog search, Order lifecycle,
Multi-tender payment checkout, and Thermal receipts.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Path, Body
from backend.app.schemas.pos import (
    PosTerminalCreate, PosTerminalOut,
    PosSessionOpenRequest, PosSessionCloseRequest, PosSessionOut,
    PosOrderCreate, PosOrderHoldRequest, PosOrderTenderRequest, PosOrderOut,
    PosReceiptOut, PosMetricsOut
)
from backend.app.services.pos_service import pos_service

router = APIRouter(prefix="/pos")


# -------------------------------------------------------------
# Terminal Endpoints
# -------------------------------------------------------------
@router.get("/terminals", response_model=List[PosTerminalOut])
def list_terminals(property_id: Optional[str] = Query(None, description="Filter by property ID")):
    """List all Point of Sale register terminals."""
    return pos_service.list_terminals(property_id=property_id)


@router.post("/terminals", response_model=PosTerminalOut)
def create_terminal(terminal_in: PosTerminalCreate):
    """Provision a new POS register terminal."""
    return pos_service.create_terminal(terminal_in)


@router.get("/terminals/{terminal_id}", response_model=PosTerminalOut)
def get_terminal(terminal_id: str = Path(..., description="Unique Terminal ID")):
    """Retrieve details of a specific POS register terminal."""
    return pos_service.get_terminal(terminal_id)


# -------------------------------------------------------------
# Shift Session & Drawer Reconciliation Endpoints
# -------------------------------------------------------------
@router.get("/sessions/active", response_model=Optional[PosSessionOut])
def get_active_session(terminal_id: Optional[str] = Query(None, description="Optional terminal filter")):
    """Get the currently open cashier shift session."""
    return pos_service.get_active_session(terminal_id=terminal_id)


@router.post("/sessions/open", response_model=PosSessionOut)
def open_session(request: PosSessionOpenRequest):
    """Open a cashier shift register session with an initial cash float."""
    return pos_service.open_session(request)


@router.post("/sessions/{session_id}/close", response_model=PosSessionOut)
def close_session(
    session_id: str = Path(..., description="ID of shift session to close"),
    request: PosSessionCloseRequest = Body(...)
):
    """Reconcile drawer and close a cashier shift session."""
    return pos_service.close_session(session_id, request)


# -------------------------------------------------------------
# Catalog & Barcode Fast Search
# -------------------------------------------------------------
@router.get("/products", response_model=List[Dict[str, Any]])
def list_pos_products(
    query: Optional[str] = Query(None, description="Search term for name, SKU, or barcode"),
    category: Optional[str] = Query(None, description="Filter by category (Beverages, Snacks, Boutique, etc.)"),
    barcode: Optional[str] = Query(None, description="Exact barcode scan match")
):
    """Look up fast-checkout POS products, barcodes, and inventory prices."""
    return pos_service.list_products(query=query, category=category, barcode=barcode)


# -------------------------------------------------------------
# Order Lifecycle Endpoints
# -------------------------------------------------------------
@router.get("/orders", response_model=List[PosOrderOut])
def list_orders(
    session_id: Optional[str] = Query(None, description="Filter by shift session ID"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, HELD, COMPLETED, VOIDED)"),
    limit: int = Query(50, ge=1, le=200)
):
    """List recent POS orders and transaction tickets."""
    return pos_service.list_orders(session_id=session_id, status_filter=status, limit=limit)


@router.post("/orders", response_model=PosOrderOut)
def create_order(request: PosOrderCreate):
    """Create a new POS transaction order / cart ticket."""
    return pos_service.create_order(request)


@router.get("/orders/{order_id}", response_model=PosOrderOut)
def get_order(order_id: str = Path(..., description="Order ID")):
    """Get complete order details including lines, payments, and GL journal reference."""
    return pos_service.get_order(order_id)


@router.post("/orders/{order_id}/hold", response_model=PosOrderOut)
def hold_order(
    order_id: str = Path(..., description="Order ID"),
    request: PosOrderHoldRequest = Body(default=PosOrderHoldRequest())
):
    """Park / hold an in-progress order to free up register."""
    return pos_service.hold_order(order_id, reason=request.reason or "Customer request")


@router.post("/orders/{order_id}/recall", response_model=PosOrderOut)
def recall_order(order_id: str = Path(..., description="Order ID")):
    """Recall a parked/held order back to active register."""
    return pos_service.recall_order(order_id)


@router.post("/orders/{order_id}/void", response_model=PosOrderOut)
def void_order(
    order_id: str = Path(..., description="Order ID"),
    reason: Optional[str] = Query("Customer cancelled", description="Reason for voiding")
):
    """Void an open or held order."""
    return pos_service.void_order(order_id, reason=reason)


@router.post("/orders/{order_id}/tender", response_model=PosOrderOut)
def tender_order(
    order_id: str = Path(..., description="Order ID"),
    request: PosOrderTenderRequest = Body(...)
):
    """
    Process multi-tender checkout payment for an order.
    Automatically posts a balanced double-entry GL journal in Phase 4 Finance.
    """
    return pos_service.tender_order(order_id, request)


@router.get("/orders/{order_id}/receipt", response_model=PosReceiptOut)
def get_receipt(order_id: str = Path(..., description="Order ID")):
    """Generate enterprise thermal receipt data with GL posting reference."""
    return pos_service.get_receipt(order_id)


# -------------------------------------------------------------
# Telemetry & KPI Metrics
# -------------------------------------------------------------
@router.get("/metrics", response_model=PosMetricsOut)
def get_pos_metrics():
    """Retrieve real-time POS revenue telemetry and shift operational KPIs."""
    return pos_service.get_pos_metrics()
