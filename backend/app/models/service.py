"""Victory Crest One - Customer & Field Service Management Models
Support Tickets, SLA Policies, Field Work Orders, Technician Dispatch,
Spare Parts Requisitions, and Invoiced Service Completion.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime
from backend.app.models.base import Base, BaseModelMixin


class SLAPolicy(Base, BaseModelMixin):
    """Service Level Agreement (SLA) policy tiers and commitments."""
    __tablename__ = "service_sla_policies"

    name = Column(String(100), nullable=False)
    priority = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, URGENT, CRITICAL
    response_target_hours = Column(Numeric(6, 2), nullable=False)
    resolution_target_hours = Column(Numeric(6, 2), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class SupportTicket(Base, BaseModelMixin):
    """Customer omnichannel support incident or maintenance ticket."""
    __tablename__ = "service_tickets"

    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    customer_id = Column(String(36), nullable=True, index=True)
    customer_name = Column(String(255), nullable=False, index=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)

    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), default="FACILITIES_MAINTENANCE", nullable=False)

    priority = Column(String(20), default="MEDIUM", nullable=False, index=True)  # LOW, MEDIUM, HIGH, URGENT, CRITICAL
    status = Column(String(30), default="NEW", nullable=False, index=True)       # NEW, OPEN, IN_PROGRESS, PENDING_PARTS, RESOLVED, CLOSED
    channel = Column(String(30), default="PORTAL", nullable=False)               # PORTAL, EMAIL, PHONE, CHAT, ON_SITE, IOT_ALARM

    assigned_to_id = Column(String(36), nullable=True, index=True)
    assigned_to_name = Column(String(255), nullable=True)

    sla_target_response_hours = Column(Numeric(6, 2), default=4.00, nullable=False)
    sla_target_resolution_hours = Column(Numeric(6, 2), default=24.00, nullable=False)

    first_responded_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    sla_breached = Column(Boolean, default=False, nullable=False, index=True)
    first_contact_resolved = Column(Boolean, default=False, nullable=False)
    resolution_notes = Column(Text, nullable=True)


class FieldWorkOrder(Base, BaseModelMixin):
    """On-site technical dispatch, diagnostic repair, and labor execution."""
    __tablename__ = "service_work_orders"

    work_order_number = Column(String(50), unique=True, nullable=False, index=True)
    ticket_id = Column(String(36), nullable=True, index=True)
    ticket_number = Column(String(50), nullable=True)

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    customer_id = Column(String(36), nullable=True, index=True)
    customer_name = Column(String(255), nullable=False)

    service_type = Column(String(50), default="EMERGENCY_REPAIR", nullable=False)  # WARRANTY, PREVENTIVE_MAINTENANCE, EMERGENCY_REPAIR, INSTALLATION, AMC
    status = Column(String(30), default="SCHEDULED", nullable=False, index=True)   # SCHEDULED, DISPATCHED, ON_SITE, IN_PROGRESS, COMPLETED, CANCELLED
    priority = Column(String(20), default="MEDIUM", nullable=False)

    technician_id = Column(String(36), nullable=True, index=True)
    technician_name = Column(String(255), nullable=True)
    site_address = Column(Text, nullable=False)

    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    labor_hours = Column(Numeric(6, 2), default=0.00, nullable=False)
    labor_rate_per_hour = Column(Numeric(10, 2), default=0.00, nullable=False)
    labor_total = Column(Numeric(12, 2), default=0.00, nullable=False)
    parts_total = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=18.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    grand_total = Column(Numeric(12, 2), default=0.00, nullable=False)

    resolution_summary = Column(Text, nullable=True)
    is_invoiced = Column(Boolean, default=False, nullable=False)
    invoice_id = Column(String(36), nullable=True)
    journal_entry_id = Column(String(36), nullable=True)


class WorkOrderPart(Base, BaseModelMixin):
    """Requisition of spare parts from warehouse inventory for a work order."""
    __tablename__ = "service_work_order_parts"

    work_order_id = Column(String(36), nullable=False, index=True)
    item_id = Column(String(36), nullable=True, index=True)
    item_code = Column(String(50), nullable=False)
    item_name = Column(String(255), nullable=False)

    quantity_demanded = Column(Numeric(10, 2), default=1.00, nullable=False)
    quantity_issued = Column(Numeric(10, 2), default=0.00, nullable=False)
    unit_cost = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_cost = Column(Numeric(12, 2), default=0.00, nullable=False)

    status = Column(String(30), default="REQUESTED", nullable=False)  # REQUESTED, APPROVED, ISSUED, CONSUMED, RETURNED
    warehouse_id = Column(String(36), nullable=True)
