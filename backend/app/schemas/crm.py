"""Victory Crest One - Sales & CRM API Schemas
Pydantic DTOs for Leads, Opportunities/Deals, Quotes, and Sales Activity tracking.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# --- Lead Schemas ---
class LeadBase(BaseModel):
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    email: str
    phone: Optional[str] = None
    lead_source: str = "WEBSITE"
    status: str = "NEW"
    lead_score: int = Field(default=50, ge=0, le=100)
    estimated_budget: Decimal = Field(default=Decimal("0.00"), ge=0)
    assigned_rep_name: Optional[str] = None
    notes: Optional[str] = None
    property_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeadCreate(LeadBase):
    organization_id: Optional[str] = None


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    lead_source: Optional[str] = None
    status: Optional[str] = None
    lead_score: Optional[int] = Field(default=None, ge=0, le=100)
    estimated_budget: Optional[Decimal] = None
    assigned_rep_name: Optional[str] = None
    notes: Optional[str] = None


class LeadOut(LeadBase):
    id: str
    organization_id: str
    converted_at: Optional[datetime] = None
    converted_customer_id: Optional[str] = None
    converted_deal_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadConvertRequest(BaseModel):
    deal_name: Optional[str] = None
    estimated_amount: Optional[Decimal] = None
    expected_close_date: Optional[datetime] = None


class LeadConvertResponse(BaseModel):
    lead_id: str
    customer_id: str
    customer_code: str
    deal_id: str
    deal_number: str
    status: str = "CONVERTED"


# --- Opportunity & Deal Schemas ---
class DealBase(BaseModel):
    deal_name: str
    customer_id: str
    customer_name: Optional[str] = None
    stage: str = "QUALIFICATION"
    amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    probability_percent: Optional[int] = Field(default=None, ge=0, le=100)
    expected_close_date: datetime
    assigned_rep_name: Optional[str] = None
    notes: Optional[str] = None
    property_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DealCreate(DealBase):
    organization_id: Optional[str] = None
    deal_number: Optional[str] = None


class DealUpdate(BaseModel):
    deal_name: Optional[str] = None
    stage: Optional[str] = None
    amount: Optional[Decimal] = None
    probability_percent: Optional[int] = None
    expected_close_date: Optional[datetime] = None
    assigned_rep_name: Optional[str] = None
    notes: Optional[str] = None


class DealStageUpdateRequest(BaseModel):
    stage: str
    probability_percent: Optional[int] = None
    notes: Optional[str] = None


class DealOut(DealBase):
    id: str
    organization_id: str
    deal_number: str
    weighted_amount: Decimal
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Quotation Schemas ---
class QuoteLineBase(BaseModel):
    product_id: Optional[str] = None
    description: str
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    amount: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class QuoteLineCreate(QuoteLineBase):
    pass


class QuoteLineOut(QuoteLineBase):
    id: str
    quote_id: str
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class QuoteBase(BaseModel):
    customer_id: str
    customer_name: Optional[str] = None
    deal_id: Optional[str] = None
    valid_until: datetime
    currency: str = "INR"
    notes: Optional[str] = None
    property_id: Optional[str] = None
    tax_rate_percent: Decimal = Decimal("18.00")

    model_config = ConfigDict(from_attributes=True)


class QuoteCreate(QuoteBase):
    organization_id: Optional[str] = None
    quote_number: Optional[str] = None
    lines: List[QuoteLineCreate]


class QuoteOut(BaseModel):
    id: str
    organization_id: str
    property_id: Optional[str] = None
    quote_number: str
    deal_id: Optional[str] = None
    customer_id: str
    customer_name: str
    issue_date: datetime
    valid_until: datetime
    status: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    converted_invoice_id: Optional[str] = None
    notes: Optional[str] = None
    lines: List[QuoteLineOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuoteConvertInvoiceResponse(BaseModel):
    quote_id: str
    invoice_id: str
    invoice_number: str
    status: str = "CONVERTED"


# --- Sales Activity Schemas ---
class SalesActivityBase(BaseModel):
    entity_type: str = "LEAD"  # LEAD, DEAL, CUSTOMER
    entity_id: str
    activity_type: str = "NOTE"  # CALL, MEETING, EMAIL, NOTE, TASK
    subject: str
    details: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_rep_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SalesActivityCreate(SalesActivityBase):
    organization_id: Optional[str] = None


class SalesActivityOut(SalesActivityBase):
    id: str
    organization_id: str
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Pipeline Metrics Schemas ---
class StageMetric(BaseModel):
    stage: str
    count: int
    total_value: Decimal
    weighted_value: Decimal


class SalesPipelineMetricsResponse(BaseModel):
    organization_id: str
    total_active_pipeline_value: Decimal
    weighted_forecast_value: Decimal
    win_rate_percentage: Decimal
    open_deals_count: int
    closed_won_count: int
    closed_lost_count: int
    stages: List[StageMetric]
