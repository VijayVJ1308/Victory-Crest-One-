"""Victory Crest One - Marketing Automation Schemas
Pydantic DTOs for multi-channel campaigns, audience segments, automated journeys,
creative templates, and conversion attribution telemetry.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# Campaign Schemas
# -------------------------------------------------------------
class CampaignBase(BaseModel):
    name: str
    channel: str = "EMAIL"  # EMAIL, SMS, WHATSAPP, PUSH_NOTIFICATION, SOCIAL_MEDIA, DIRECT_MAIL
    status: str = "DRAFT"   # DRAFT, SCHEDULED, RUNNING, PAUSED, COMPLETED, CANCELLED
    budget: Decimal = Field(default=Decimal("0.00"), ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    segment_id: Optional[str] = None
    template_id: Optional[str] = None
    notes: Optional[str] = None


class CampaignCreate(CampaignBase):
    organization_id: Optional[str] = None
    property_id: Optional[str] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    segment_id: Optional[str] = None
    template_id: Optional[str] = None
    notes: Optional[str] = None


class CampaignOut(CampaignBase):
    id: str
    organization_id: str
    property_id: Optional[str] = None
    campaign_code: str
    actual_spend: Decimal
    attributed_revenue: Decimal
    segment_name: Optional[str] = None
    target_count: int
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    converted_count: int
    bounced_count: int
    open_rate_percent: Decimal = Decimal("0.00")
    ctr_percent: Decimal = Decimal("0.00")
    conversion_rate_percent: Decimal = Decimal("0.00")
    roas: Decimal = Decimal("0.00")
    cpa: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignDispatchResponse(BaseModel):
    campaign_id: str
    campaign_code: str
    status: str
    messages_dispatched: int
    simulated_delivered: int
    message: str


# -------------------------------------------------------------
# Audience Segment Schemas
# -------------------------------------------------------------
class AudienceSegmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    segment_type: str = "DYNAMIC"  # DYNAMIC, STATIC
    filter_criteria: Optional[str] = None
    is_active: bool = True


class AudienceSegmentCreate(AudienceSegmentBase):
    organization_id: Optional[str] = None
    property_id: Optional[str] = None


class AudienceSegmentOut(AudienceSegmentBase):
    id: str
    organization_id: str
    property_id: Optional[str] = None
    member_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Automated Customer Journey Schemas
# -------------------------------------------------------------
class JourneyStep(BaseModel):
    step_number: int
    action_type: str  # SEND_EMAIL, SEND_SMS, WAIT_DELAY, CHECK_CONDITION, CREATE_TASK
    delay_hours: int = 0
    template_id: Optional[str] = None
    description: str


class CustomerJourneyBase(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_event: str  # GUEST_CHECKOUT, LEAD_CAPTURED, ORDER_COMPLETED
    status: str = "ACTIVE"
    steps: List[JourneyStep] = []


class CustomerJourneyCreate(CustomerJourneyBase):
    organization_id: Optional[str] = None


class CustomerJourneyOut(CustomerJourneyBase):
    id: str
    organization_id: str
    enrolled_count: int
    completed_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Creative Template Schemas
# -------------------------------------------------------------
class CampaignTemplateBase(BaseModel):
    name: str
    channel: str = "EMAIL"
    subject: Optional[str] = None
    body_content: str
    merge_tags: str = "{{first_name}},{{company}},{{property_name}}"
    is_active: bool = True


class CampaignTemplateCreate(CampaignTemplateBase):
    organization_id: Optional[str] = None


class CampaignTemplateOut(CampaignTemplateBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Attribution & Overall Analytics
# -------------------------------------------------------------
class AttributionCreate(BaseModel):
    campaign_id: str
    deal_id: Optional[str] = None
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: str
    attribution_model: str = "LAST_TOUCH"  # FIRST_TOUCH, LAST_TOUCH, LINEAR
    attributed_revenue: Decimal = Field(gt=0)


class AttributionOut(AttributionCreate):
    id: str
    organization_id: str
    campaign_name: str
    attributed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketingMetricsOut(BaseModel):
    total_campaigns_count: int
    active_campaigns_count: int
    total_budget: Decimal
    total_spend: Decimal
    total_attributed_revenue: Decimal
    overall_roas: Decimal
    total_targeted_audience: int
    total_delivered_messages: int
    overall_open_rate_percent: Decimal
    overall_ctr_percent: Decimal
    overall_conversion_rate_percent: Decimal
    total_segments_count: int
    active_journeys_count: int
