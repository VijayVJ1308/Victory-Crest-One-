"""Victory Crest One - Marketing Automation Database Models
Campaigns, Multi-Channel Channels, Audience Segments, Customer Journeys,
Creative Templates, and Conversion Attribution Tracking.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, DateTime
from backend.app.models.base import Base, BaseModelMixin


class MarketingCampaign(Base, BaseModelMixin):
    """Marketing Campaign entity with multi-channel telemetry and ROI tracking."""
    __tablename__ = "mkt_campaigns"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    campaign_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    channel = Column(String(30), default="EMAIL", nullable=False, index=True)  # EMAIL, SMS, WHATSAPP, etc.
    status = Column(String(20), default="DRAFT", nullable=False, index=True)  # DRAFT, SCHEDULED, RUNNING, etc.

    budget = Column(Numeric(12, 2), default=0.00, nullable=False)
    actual_spend = Column(Numeric(12, 2), default=0.00, nullable=False)
    attributed_revenue = Column(Numeric(12, 2), default=0.00, nullable=False)

    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    segment_id = Column(String(36), nullable=True, index=True)
    segment_name = Column(String(150), nullable=True)
    template_id = Column(String(36), nullable=True)

    target_count = Column(Integer, default=0, nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    delivered_count = Column(Integer, default=0, nullable=False)
    opened_count = Column(Integer, default=0, nullable=False)
    clicked_count = Column(Integer, default=0, nullable=False)
    converted_count = Column(Integer, default=0, nullable=False)
    bounced_count = Column(Integer, default=0, nullable=False)

    notes = Column(Text, nullable=True)


class AudienceSegment(Base, BaseModelMixin):
    """Target audience segment based on demographic, behavioural, or spend criteria."""
    __tablename__ = "mkt_segments"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    segment_type = Column(String(20), default="DYNAMIC", nullable=False)  # DYNAMIC, STATIC
    filter_criteria = Column(Text, nullable=True)  # JSON representation of criteria
    member_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class CustomerJourney(Base, BaseModelMixin):
    """Multi-step automated marketing lifecycle / drip sequence."""
    __tablename__ = "mkt_journeys"

    organization_id = Column(String(36), nullable=False, index=True)

    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    trigger_event = Column(String(100), nullable=False)  # e.g., "GUEST_CHECKOUT", "LEAD_CAPTURED"
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # DRAFT, ACTIVE, PAUSED

    steps_json = Column(Text, nullable=False)  # JSON-encoded array of steps
    enrolled_count = Column(Integer, default=0, nullable=False)
    completed_count = Column(Integer, default=0, nullable=False)


class CampaignTemplate(Base, BaseModelMixin):
    """Reusable email, SMS, or WhatsApp message template with merge variables."""
    __tablename__ = "mkt_templates"

    organization_id = Column(String(36), nullable=False, index=True)

    name = Column(String(150), nullable=False, index=True)
    channel = Column(String(30), default="EMAIL", nullable=False)
    subject = Column(String(255), nullable=True)
    body_content = Column(Text, nullable=False)
    merge_tags = Column(String(255), default="{{first_name}},{{company}},{{property_name}}")
    is_active = Column(Boolean, default=True, nullable=False)


class CampaignAttribution(Base, BaseModelMixin):
    """Revenue attribution record connecting a marketing campaign to a Sale or Invoice."""
    __tablename__ = "mkt_attributions"

    organization_id = Column(String(36), nullable=False, index=True)
    campaign_id = Column(String(36), nullable=False, index=True)
    campaign_name = Column(String(150), nullable=False)

    deal_id = Column(String(36), nullable=True, index=True)
    order_id = Column(String(36), nullable=True, index=True)
    customer_id = Column(String(36), nullable=True, index=True)
    customer_name = Column(String(150), nullable=False)

    attribution_model = Column(String(30), default="LAST_TOUCH", nullable=False)
    attributed_revenue = Column(Numeric(12, 2), nullable=False)
    attributed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
