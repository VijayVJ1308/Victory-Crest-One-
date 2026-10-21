"""Victory Crest One - Customer & Field Service Management Schemas
Pydantic DTOs for Support Tickets, SLA Policies, Field Work Orders,
Technician Dispatch, Parts Requisitions, and Service Metrics.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# SLA Policy Schemas
# -------------------------------------------------------------
class SLAPolicyOut(BaseModel):
    id: str
    name: str
    priority: str
    response_target_hours: Decimal
    resolution_target_hours: Decimal
    description: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Support Ticket Schemas
# -------------------------------------------------------------
class SupportTicketBase(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_id: Optional[str] = None
    subject: str
    description: str
    category: str = "FACILITIES_MAINTENANCE"
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, URGENT, CRITICAL
    channel: str = "PORTAL"   # PORTAL, EMAIL, PHONE, CHAT, ON_SITE, IOT_ALARM


class SupportTicketCreate(SupportTicketBase):
    organization_id: Optional[str] = None
    property_id: Optional[str] = None
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    sla_target_response_hours: Optional[Decimal] = None
    sla_target_resolution_hours: Optional[Decimal] = None


class SupportTicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None  # NEW, OPEN, IN_PROGRESS, PENDING_PARTS, RESOLVED, CLOSED
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    first_contact_resolved: Optional[bool] = None


class SupportTicketOut(SupportTicketBase):
    id: str
    ticket_number: str
    organization_id: str
    property_id: str
    status: str
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    sla_target_response_hours: Decimal
    sla_target_resolution_hours: Decimal
    sla_remaining_hours: Optional[Decimal] = None
    sla_breached: bool = False
    first_contact_resolved: bool = False
    first_responded_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Work Order Parts Schemas
# -------------------------------------------------------------
class WorkOrderPartBase(BaseModel):
    item_code: str
    item_name: str
    quantity_demanded: Decimal = Field(default=Decimal("1.00"), ge=0)
    unit_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    item_id: Optional[str] = None
    warehouse_id: Optional[str] = None


class WorkOrderPartCreate(WorkOrderPartBase):
    pass


class WorkOrderPartOut(WorkOrderPartBase):
    id: str
    work_order_id: str
    quantity_issued: Decimal
    total_cost: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Field Work Order Schemas
# -------------------------------------------------------------
class FieldWorkOrderBase(BaseModel):
    customer_name: str
    customer_id: Optional[str] = None
    service_type: str = "EMERGENCY_REPAIR"  # WARRANTY, PREVENTIVE_MAINTENANCE, EMERGENCY_REPAIR, INSTALLATION, AMC
    priority: str = "MEDIUM"
    site_address: str
    technician_id: Optional[str] = None
    technician_name: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    labor_hours: Decimal = Field(default=Decimal("0.00"), ge=0)
    labor_rate_per_hour: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_rate_percent: Decimal = Field(default=Decimal("18.00"), ge=0)


class FieldWorkOrderCreate(FieldWorkOrderBase):
    ticket_id: Optional[str] = None
    ticket_number: Optional[str] = None
    organization_id: Optional[str] = None
    property_id: Optional[str] = None


class FieldWorkOrderDispatch(BaseModel):
    technician_id: str
    technician_name: str
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None


class FieldWorkOrderComplete(BaseModel):
    actual_labor_hours: Decimal = Field(ge=0)
    labor_rate_per_hour: Decimal = Field(ge=0)
    resolution_summary: str
    mark_ticket_resolved: bool = True


class FieldWorkOrderOut(FieldWorkOrderBase):
    id: str
    work_order_number: str
    ticket_id: Optional[str] = None
    ticket_number: Optional[str] = None
    organization_id: str
    property_id: str
    status: str
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    labor_total: Decimal
    parts_total: Decimal
    tax_amount: Decimal
    grand_total: Decimal
    resolution_summary: Optional[str] = None
    is_invoiced: bool = False
    invoice_id: Optional[str] = None
    journal_entry_id: Optional[str] = None
    parts: List[WorkOrderPartOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Service Telemetry & Executive Metrics
# -------------------------------------------------------------
class ServiceMetricsOut(BaseModel):
    total_tickets: int
    active_tickets: int
    breached_tickets: int
    resolved_tickets: int
    sla_compliance_rate: Decimal
    first_contact_resolution_rate: Decimal
    active_work_orders: int
    dispatched_work_orders: int
    completed_work_orders: int
    total_service_revenue: Decimal
    total_parts_cost: Decimal
