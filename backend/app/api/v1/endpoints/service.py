"""Victory Crest One - Customer & Field Service REST API Endpoints
Support Tickets, SLA Tracking, Field Work Orders, Technician Dispatch,
Spare Parts Requisitions, and Invoicing with GL Posting.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Path, Body
from backend.app.schemas.service import (
    SLAPolicyOut,
    SupportTicketCreate, SupportTicketUpdate, SupportTicketOut,
    WorkOrderPartCreate, WorkOrderPartOut,
    FieldWorkOrderCreate, FieldWorkOrderDispatch, FieldWorkOrderComplete, FieldWorkOrderOut,
    ServiceMetricsOut
)
from backend.app.services.service_management import service_management_service

router = APIRouter(prefix="/service")


# -------------------------------------------------------------
# SLA Policies
# -------------------------------------------------------------
@router.get("/sla-policies", response_model=List[SLAPolicyOut])
def list_sla_policies():
    """Retrieve active Service Level Agreement (SLA) policy tiers and commitments."""
    return service_management_service.get_sla_policies()


# -------------------------------------------------------------
# Support Tickets Desk
# -------------------------------------------------------------
@router.get("/tickets", response_model=List[SupportTicketOut])
def list_tickets(
    property_id: Optional[str] = Query(None, description="Filter by property ID"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, IN_PROGRESS, PENDING_PARTS, RESOLVED, CLOSED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, URGENT, CRITICAL)"),
    search: Optional[str] = Query(None, description="Search ticket number, customer, or subject")
):
    """List customer support incidents and work tickets with live SLA countdowns."""
    return service_management_service.get_tickets(
        property_id=property_id,
        status_filter=status,
        priority_filter=priority,
        search_query=search
    )


@router.post("/tickets", response_model=SupportTicketOut)
def create_ticket(ticket_in: SupportTicketCreate):
    """Log a new customer support incident or maintenance ticket."""
    return service_management_service.create_ticket(ticket_in)


@router.get("/tickets/{ticket_id}", response_model=SupportTicketOut)
def get_ticket(ticket_id: str = Path(..., description="Ticket ID")):
    """Get support ticket details and current SLA timer status."""
    return service_management_service.get_ticket(ticket_id)


@router.put("/tickets/{ticket_id}", response_model=SupportTicketOut)
def update_ticket(
    ticket_id: str = Path(..., description="Ticket ID"),
    ticket_in: SupportTicketUpdate = Body(...)
):
    """Update support ticket status, assigned technician, or resolution notes."""
    return service_management_service.update_ticket(ticket_id, ticket_in)


# -------------------------------------------------------------
# Field Work Orders & Dispatch
# -------------------------------------------------------------
@router.get("/work-orders", response_model=List[FieldWorkOrderOut])
def list_work_orders(
    property_id: Optional[str] = Query(None, description="Filter by property ID"),
    status: Optional[str] = Query(None, description="Filter by status (SCHEDULED, DISPATCHED, IN_PROGRESS, COMPLETED)"),
    search: Optional[str] = Query(None, description="Search work order number, customer, or technician")
):
    """List field service work orders, scheduling, and labor totals."""
    return service_management_service.get_work_orders(
        property_id=property_id,
        status_filter=status,
        search_query=search
    )


@router.post("/work-orders", response_model=FieldWorkOrderOut)
def create_work_order(wo_in: FieldWorkOrderCreate):
    """Create a new field work order for an on-site technician repair."""
    return service_management_service.create_work_order(wo_in)


@router.get("/work-orders/{wo_id}", response_model=FieldWorkOrderOut)
def get_work_order(wo_id: str = Path(..., description="Work Order ID")):
    """Get field work order details, technician schedule, and parts requisitions."""
    return service_management_service.get_work_order(wo_id)


@router.post("/work-orders/{wo_id}/dispatch", response_model=FieldWorkOrderOut)
def dispatch_work_order(
    wo_id: str = Path(..., description="Work Order ID"),
    dispatch_in: FieldWorkOrderDispatch = Body(...)
):
    """Dispatch a service technician to a field work order."""
    return service_management_service.dispatch_work_order(wo_id, dispatch_in)


# -------------------------------------------------------------
# Spare Parts Requisitions
# -------------------------------------------------------------
@router.post("/work-orders/{wo_id}/parts", response_model=WorkOrderPartOut)
def add_work_order_part(
    wo_id: str = Path(..., description="Work Order ID"),
    part_in: WorkOrderPartCreate = Body(...)
):
    """Requisition spare parts from warehouse inventory for a work order."""
    return service_management_service.add_work_order_part(wo_id, part_in)


@router.post("/work-orders/{wo_id}/parts/{part_id}/issue", response_model=WorkOrderPartOut)
def issue_work_order_part(
    wo_id: str = Path(..., description="Work Order ID"),
    part_id: str = Path(..., description="Part Requisition ID")
):
    """Issue requested spare parts from warehouse inventory to the work order."""
    return service_management_service.issue_work_order_part(wo_id, part_id)


# -------------------------------------------------------------
# Completion and GL Invoicing
# -------------------------------------------------------------
@router.post("/work-orders/{wo_id}/complete-and-bill", response_model=FieldWorkOrderOut)
def complete_and_bill_work_order(
    wo_id: str = Path(..., description="Work Order ID"),
    complete_in: FieldWorkOrderComplete = Body(...)
):
    """Complete work order, compute labor/parts totals, and automatically post balanced GL journal entry."""
    return service_management_service.complete_and_bill_work_order(wo_id, complete_in)


# -------------------------------------------------------------
# Service Telemetry & Executive Metrics
# -------------------------------------------------------------
@router.get("/metrics", response_model=ServiceMetricsOut)
def get_service_metrics(
    property_id: Optional[str] = Query(None, description="Filter metrics by property ID")
):
    """Retrieve executive service KPIs: active incidents, SLA compliance rate, FCR, and revenue."""
    return service_management_service.get_service_metrics(property_id=property_id)
