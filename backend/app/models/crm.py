"""Victory Crest One - Sales & CRM Database Models
Leads, Opportunities/Deals, Sales Pipeline Stages, Quotations, and Sales Activities.
Seamlessly connects with Customer Master and Finance AR Invoicing.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Numeric, ForeignKey, Text, DateTime
from backend.app.models.base import Base, BaseModelMixin


class Lead(Base, BaseModelMixin):
    """Prospective customer lead entity."""
    __tablename__ = "crm_leads"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company_name = Column(String(150), nullable=True)
    job_title = Column(String(100), nullable=True)

    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True, index=True)

    lead_source = Column(String(50), default="WEBSITE", nullable=False)  # WEBSITE, REFERRAL, COLD_OUTREACH, etc.
    status = Column(String(30), default="NEW", nullable=False, index=True)  # NEW, CONTACTED, QUALIFIED, UNQUALIFIED, CONVERTED
    lead_score = Column(Integer, default=50, nullable=False)  # 0 to 100 rating
    estimated_budget = Column(Numeric(15, 2), default=0.00, nullable=False)

    assigned_rep_id = Column(String(36), nullable=True)
    assigned_rep_name = Column(String(100), nullable=True)

    converted_at = Column(DateTime, nullable=True)
    converted_customer_id = Column(String(36), nullable=True)
    converted_deal_id = Column(String(36), nullable=True)

    notes = Column(Text, nullable=True)


class Deal(Base, BaseModelMixin):
    """Sales Opportunity / Pipeline Deal entity."""
    __tablename__ = "crm_deals"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    deal_number = Column(String(50), nullable=False, unique=True, index=True)
    deal_name = Column(String(150), nullable=False, index=True)

    customer_id = Column(String(36), nullable=False, index=True)
    customer_name = Column(String(150), nullable=False)

    stage = Column(String(50), default="QUALIFICATION", nullable=False, index=True)
    amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    probability_percent = Column(Integer, default=10, nullable=False)
    weighted_amount = Column(Numeric(15, 2), default=0.00, nullable=False)

    expected_close_date = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    assigned_rep_id = Column(String(36), nullable=True)
    assigned_rep_name = Column(String(100), nullable=True)

    notes = Column(Text, nullable=True)


class Quote(Base, BaseModelMixin):
    """Formal Sales Quotation / Commercial Proposal."""
    __tablename__ = "crm_quotes"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    quote_number = Column(String(50), nullable=False, unique=True, index=True)
    deal_id = Column(String(36), nullable=True, index=True)
    customer_id = Column(String(36), nullable=False, index=True)
    customer_name = Column(String(150), nullable=False)

    issue_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    status = Column(String(30), default="DRAFT", nullable=False, index=True)  # DRAFT, SENT, ACCEPTED, REJECTED, EXPIRED

    currency = Column(String(3), default="INR", nullable=False)
    subtotal = Column(Numeric(15, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(15, 2), default=0.00, nullable=False)

    converted_invoice_id = Column(String(36), nullable=True)  # Links to Finance AR CustomerInvoice
    notes = Column(Text, nullable=True)


class QuoteLine(Base, BaseModelMixin):
    """Line item in a sales quotation."""
    __tablename__ = "crm_quote_lines"

    quote_id = Column(String(36), ForeignKey("crm_quotes.id"), nullable=False, index=True)
    product_id = Column(String(36), nullable=True)
    description = Column(String(255), nullable=False)

    quantity = Column(Numeric(10, 2), default=1.00, nullable=False)
    unit_price = Column(Numeric(15, 2), default=0.00, nullable=False)
    amount = Column(Numeric(15, 2), default=0.00, nullable=False)


class SalesActivity(Base, BaseModelMixin):
    """Sales team interaction log (Calls, Meetings, Tasks, Notes)."""
    __tablename__ = "crm_activities"

    organization_id = Column(String(36), nullable=False, index=True)
    entity_type = Column(String(30), nullable=False, index=True)  # LEAD, DEAL, CUSTOMER
    entity_id = Column(String(36), nullable=False, index=True)

    activity_type = Column(String(30), default="NOTE", nullable=False)  # CALL, MEETING, EMAIL, NOTE, TASK
    subject = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)

    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    assigned_rep_name = Column(String(100), nullable=True)
