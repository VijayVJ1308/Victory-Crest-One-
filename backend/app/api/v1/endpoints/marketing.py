"""Victory Crest One - Marketing Automation REST API Endpoints
Campaigns, Multi-Channel Channels, Audience Segments, Customer Journeys,
Creative Templates, and Conversion Attribution Tracking.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Path, Body
from backend.app.schemas.marketing import (
    CampaignCreate, CampaignUpdate, CampaignOut, CampaignDispatchResponse,
    AudienceSegmentCreate, AudienceSegmentOut,
    CustomerJourneyCreate, CustomerJourneyOut,
    CampaignTemplateCreate, CampaignTemplateOut,
    AttributionCreate, AttributionOut,
    MarketingMetricsOut
)
from backend.app.services.marketing_service import marketing_service

router = APIRouter(prefix="/marketing")


# -------------------------------------------------------------
# Campaign Endpoints
# -------------------------------------------------------------
@router.get("/campaigns", response_model=List[CampaignOut])
def list_campaigns(
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, SCHEDULED, RUNNING, COMPLETED)"),
    channel: Optional[str] = Query(None, description="Filter by channel (EMAIL, SMS, WHATSAPP, etc.)")
):
    """List marketing campaigns with real-time performance KPIs."""
    return marketing_service.list_campaigns(status_filter=status, channel_filter=channel)


@router.post("/campaigns", response_model=CampaignOut)
def create_campaign(campaign_in: CampaignCreate):
    """Create a new multi-channel marketing campaign."""
    return marketing_service.create_campaign(campaign_in)


@router.get("/campaigns/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: str = Path(..., description="Campaign ID")):
    """Get single campaign details and telemetry."""
    return marketing_service.get_campaign(campaign_id)


@router.put("/campaigns/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    campaign_id: str = Path(..., description="Campaign ID"),
    campaign_update: CampaignUpdate = Body(...)
):
    """Update campaign parameters, budget, dates, or creative template."""
    return marketing_service.update_campaign(campaign_id, campaign_update)


@router.post("/campaigns/{campaign_id}/launch", response_model=CampaignDispatchResponse)
def launch_campaign(campaign_id: str = Path(..., description="Campaign ID")):
    """Trigger dispatch of marketing campaign to target audience segment."""
    return marketing_service.launch_campaign(campaign_id)


@router.post("/campaigns/{campaign_id}/pause", response_model=CampaignOut)
def pause_campaign(campaign_id: str = Path(..., description="Campaign ID")):
    """Pause an actively running marketing campaign."""
    return marketing_service.pause_campaign(campaign_id)


# -------------------------------------------------------------
# Audience Segment Endpoints
# -------------------------------------------------------------
@router.get("/segments", response_model=List[AudienceSegmentOut])
def list_segments():
    """List all dynamic and static audience segments."""
    return marketing_service.list_segments()


@router.post("/segments", response_model=AudienceSegmentOut)
def create_segment(segment_in: AudienceSegmentCreate):
    """Define a new target audience segment with behavioural filters."""
    return marketing_service.create_segment(segment_in)


@router.get("/segments/{segment_id}", response_model=AudienceSegmentOut)
def get_segment(segment_id: str = Path(..., description="Segment ID")):
    """Get segment details and member criteria."""
    return marketing_service.get_segment(segment_id)


# -------------------------------------------------------------
# Customer Journey Endpoints
# -------------------------------------------------------------
@router.get("/journeys", response_model=List[CustomerJourneyOut])
def list_journeys():
    """List automated multi-step customer lifecycle journeys."""
    return marketing_service.list_journeys()


@router.post("/journeys", response_model=CustomerJourneyOut)
def create_journey(journey_in: CustomerJourneyCreate):
    """Create an automated trigger-based drip sequence."""
    return marketing_service.create_journey(journey_in)


# -------------------------------------------------------------
# Creative Template Endpoints
# -------------------------------------------------------------
@router.get("/templates", response_model=List[CampaignTemplateOut])
def list_templates(channel: Optional[str] = Query(None, description="Filter by channel")):
    """List creative message templates."""
    return marketing_service.list_templates(channel=channel)


@router.post("/templates", response_model=CampaignTemplateOut)
def create_template(template_in: CampaignTemplateCreate):
    """Create a new message template with merge variables."""
    return marketing_service.create_template(template_in)


# -------------------------------------------------------------
# Attribution & Overall Telemetry
# -------------------------------------------------------------
@router.get("/attributions", response_model=List[AttributionOut])
def list_attributions(campaign_id: Optional[str] = Query(None, description="Filter by campaign ID")):
    """List revenue attributions linked to marketing campaigns."""
    return marketing_service.list_attributions(campaign_id=campaign_id)


@router.post("/attributions", response_model=AttributionOut)
def create_attribution(attrib_in: AttributionCreate):
    """Attribute closed revenue to an active marketing campaign."""
    return marketing_service.create_attribution(attrib_in)


@router.get("/metrics", response_model=MarketingMetricsOut)
def get_marketing_metrics():
    """Retrieve overall marketing portfolio metrics and ROI telemetry."""
    return marketing_service.get_marketing_metrics()
