"""Victory Crest One - Marketing Automation Business Service
Multi-channel campaigns, audience segmentation engine, automated lifecycle journeys,
creative templates, message dispatch simulation, and conversion attribution.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
import json
from fastapi import HTTPException, status

from backend.app.schemas.marketing import (
    CampaignCreate, CampaignUpdate, CampaignOut, CampaignDispatchResponse,
    AudienceSegmentCreate, AudienceSegmentOut,
    JourneyStep, CustomerJourneyCreate, CustomerJourneyOut,
    CampaignTemplateCreate, CampaignTemplateOut,
    AttributionCreate, AttributionOut,
    MarketingMetricsOut
)
from backend.app.services.audit_service import audit_service
from shared.calculations import to_decimal, calculate_campaign_kpis
from shared.constants import DEMO_ORGANISATIONS


# In-memory stores
_CAMPAIGN_STORE: Dict[str, Dict[str, Any]] = {}
_SEGMENT_STORE: Dict[str, Dict[str, Any]] = {}
_JOURNEY_STORE: Dict[str, Dict[str, Any]] = {}
_TEMPLATE_STORE: Dict[str, Dict[str, Any]] = {}
_ATTRIBUTION_STORE: List[Dict[str, Any]] = []


def _seed_marketing_data():
    """Populate realistic demonstration marketing entities, campaigns, and telemetry."""
    if _CAMPAIGN_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]
    now = datetime.utcnow()

    # 1. Seed Audience Segments
    segments = [
        {
            "id": "seg_vip_heritage",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "name": "Royal Heritage Club — VIP High Spenders",
            "description": "High net-worth leisure & corporate guests with historical spend > ₹50,000",
            "segment_type": "DYNAMIC",
            "filter_criteria": json.dumps({"min_spend": 50000, "properties": [prop_mdu], "min_stays": 2}),
            "member_count": 320,
            "is_active": True,
            "created_at": now - timedelta(days=60),
            "updated_at": now - timedelta(days=5)
        },
        {
            "id": "seg_corporate_planners",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "name": "Corporate MICE & Symposium Planners",
            "description": "Technology, pharmaceutical, and financial enterprise event coordinators",
            "segment_type": "DYNAMIC",
            "filter_criteria": json.dumps({"industries": ["Technology", "Healthcare", "Finance"], "is_corporate": True}),
            "member_count": 180,
            "is_active": True,
            "created_at": now - timedelta(days=60),
            "updated_at": now - timedelta(days=10)
        },
        {
            "id": "seg_wellness_seekers",
            "organization_id": org_id,
            "property_id": prop_kod,
            "name": "Kodaikanal Mountain Wellness & Spa Seekers",
            "description": "Guests who booked Ayurvedic treatments, pine chalets, and mountain retreats",
            "segment_type": "DYNAMIC",
            "filter_criteria": json.dumps({"interest": "Wellness", "preferred_property": prop_kod}),
            "member_count": 450,
            "is_active": True,
            "created_at": now - timedelta(days=45),
            "updated_at": now - timedelta(days=8)
        },
        {
            "id": "seg_dormant_guests",
            "organization_id": org_id,
            "property_id": None,
            "name": "Dormant Guests — Inactive > 180 Days",
            "description": "Previous verified guests who have not booked in the last 6 months",
            "segment_type": "DYNAMIC",
            "filter_criteria": json.dumps({"days_since_last_booking_gt": 180}),
            "member_count": 640,
            "is_active": True,
            "created_at": now - timedelta(days=30),
            "updated_at": now - timedelta(days=2)
        }
    ]
    for seg in segments:
        _SEGMENT_STORE[seg["id"]] = seg

    # 2. Seed Creative Message Templates
    templates = [
        {
            "id": "tmpl_corp_mice",
            "organization_id": org_id,
            "name": "Corporate MICE & Executive Ballroom Invitation",
            "channel": "EMAIL",
            "subject": "Elevate Your Strategic Summits at {{property_name}} — Privileges for {{company}}",
            "body_content": (
                "Dear {{first_name}},\n\n"
                "Victory Crest ONE is honored to invite {{company}} to host your upcoming executive symposium "
                "in our heritage grand ballroom. Enjoy bespoke audiovisual setups, fine Chettinad royal catering, "
                "and private executive suites.\n\n"
                "Reply to schedule a guided concierge tour.\n\n"
                "Warm regards,\nVictory Crest Luxury Hospitality"
            ),
            "merge_tags": "{{first_name}},{{company}},{{property_name}}",
            "is_active": True,
            "created_at": now - timedelta(days=50),
            "updated_at": now - timedelta(days=50)
        },
        {
            "id": "tmpl_festive_gala",
            "organization_id": org_id,
            "name": "Diwali Royal Heritage Dining Gala",
            "channel": "EMAIL",
            "subject": "Join Us for Royal Heritage Dining Privileges — {{first_name}}",
            "body_content": (
                "Greetings {{first_name}},\n\n"
                "Experience our celebrated 18-course Royal Chettinad feast this festive season. "
                "Complimentary welcome sparkling wine for Royal Heritage Club members.\n\n"
                "Reserve your table now via Victory Crest Concierge."
            ),
            "merge_tags": "{{first_name}},{{property_name}}",
            "is_active": True,
            "created_at": now - timedelta(days=40),
            "updated_at": now - timedelta(days=40)
        },
        {
            "id": "tmpl_spa_wellness",
            "organization_id": org_id,
            "name": "Kodaikanal Ayurvedic Spa WhatsApp Alert",
            "channel": "WHATSAPP",
            "subject": "Winter Wellness Retreat",
            "body_content": (
                "🌿 Hello {{first_name}}! Unwind in the misty hills of Kodaikanal. "
                "Book 2 nights in our Pine Vista Chalet and receive a complimentary 90-minute "
                "Ayurvedic Herbal Rejuvenation therapy. Tap to book instantly: https://victorycrest.internal/spa"
            ),
            "merge_tags": "{{first_name}},{{property_name}}",
            "is_active": True,
            "created_at": now - timedelta(days=35),
            "updated_at": now - timedelta(days=35)
        },
        {
            "id": "tmpl_winback_sms",
            "organization_id": org_id,
            "name": "VIP Winback SMS Voucher",
            "channel": "SMS",
            "subject": None,
            "body_content": (
                "Victory Crest Privileges: We miss you, {{first_name}}! Enjoy 20% off your next luxury stay "
                "at any GrandVista property with code WELCOME20. Valid till end of quarter."
            ),
            "merge_tags": "{{first_name}}",
            "is_active": True,
            "created_at": now - timedelta(days=20),
            "updated_at": now - timedelta(days=20)
        }
    ]
    for tmpl in templates:
        _TEMPLATE_STORE[tmpl["id"]] = tmpl

    # 3. Seed Campaigns
    campaigns = [
        {
            "id": "camp_q4_corp",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "campaign_code": "CMP-2026-CORP-01",
            "name": "Q4 Executive Corporate Retreats 2026",
            "channel": "EMAIL",
            "status": "RUNNING",
            "budget": Decimal("150000.00"),
            "actual_spend": Decimal("120000.00"),
            "attributed_revenue": Decimal("850000.00"),
            "start_date": now - timedelta(days=25),
            "end_date": now + timedelta(days=35),
            "segment_id": "seg_corporate_planners",
            "segment_name": "Corporate MICE & Symposium Planners",
            "template_id": "tmpl_corp_mice",
            "target_count": 1200,
            "sent_count": 1200,
            "delivered_count": 1180,
            "opened_count": 420,
            "clicked_count": 185,
            "converted_count": 16,
            "bounced_count": 20,
            "notes": "Targeted enterprise accounts for grand ballroom conferences and catering.",
            "created_at": now - timedelta(days=30),
            "updated_at": now - timedelta(days=2)
        },
        {
            "id": "camp_diwali_gala",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "campaign_code": "CMP-2026-FEST-02",
            "name": "Diwali Royal Festive Dining Gala",
            "channel": "EMAIL",
            "status": "COMPLETED",
            "budget": Decimal("80000.00"),
            "actual_spend": Decimal("75000.00"),
            "attributed_revenue": Decimal("480000.00"),
            "start_date": now - timedelta(days=60),
            "end_date": now - timedelta(days=15),
            "segment_id": "seg_vip_heritage",
            "segment_name": "Royal Heritage Club — VIP High Spenders",
            "template_id": "tmpl_festive_gala",
            "target_count": 2500,
            "sent_count": 2500,
            "delivered_count": 2460,
            "opened_count": 980,
            "clicked_count": 410,
            "converted_count": 38,
            "bounced_count": 40,
            "notes": "Celebration gala banquet promotion with record table reservations.",
            "created_at": now - timedelta(days=65),
            "updated_at": now - timedelta(days=15)
        },
        {
            "id": "camp_kodai_spa",
            "organization_id": org_id,
            "property_id": prop_kod,
            "campaign_code": "CMP-2026-SPA-03",
            "name": "Kodaikanal Winter Solstice Spa Escape",
            "channel": "WHATSAPP",
            "status": "RUNNING",
            "budget": Decimal("95000.00"),
            "actual_spend": Decimal("60000.00"),
            "attributed_revenue": Decimal("340000.00"),
            "start_date": now - timedelta(days=14),
            "end_date": now + timedelta(days=20),
            "segment_id": "seg_wellness_seekers",
            "segment_name": "Kodaikanal Mountain Wellness & Spa Seekers",
            "template_id": "tmpl_spa_wellness",
            "target_count": 800,
            "sent_count": 800,
            "delivered_count": 790,
            "opened_count": 640,
            "clicked_count": 310,
            "converted_count": 24,
            "bounced_count": 10,
            "notes": "Promoting pine chalets and Ayurvedic massage treatment bookings.",
            "created_at": now - timedelta(days=18),
            "updated_at": now - timedelta(days=1)
        },
        {
            "id": "camp_winback_sms",
            "organization_id": org_id,
            "property_id": None,
            "campaign_code": "CMP-2026-REENG-04",
            "name": "VIP Re-engagement Drip 2026",
            "channel": "SMS",
            "status": "SCHEDULED",
            "budget": Decimal("45000.00"),
            "actual_spend": Decimal("0.00"),
            "attributed_revenue": Decimal("0.00"),
            "start_date": now + timedelta(days=3),
            "end_date": now + timedelta(days=30),
            "segment_id": "seg_dormant_guests",
            "segment_name": "Dormant Guests — Inactive > 180 Days",
            "template_id": "tmpl_winback_sms",
            "target_count": 640,
            "sent_count": 0,
            "delivered_count": 0,
            "opened_count": 0,
            "clicked_count": 0,
            "converted_count": 0,
            "bounced_count": 0,
            "notes": "Upcoming scheduled SMS dispatch for dormant guest win-back.",
            "created_at": now - timedelta(days=5),
            "updated_at": now - timedelta(days=5)
        }
    ]
    for c in campaigns:
        _CAMPAIGN_STORE[c["id"]] = c

    # 4. Seed Automated Customer Journeys
    journeys = [
        {
            "id": "jrn_vip_onboarding",
            "organization_id": org_id,
            "name": "VIP Guest Onboarding & Post-Stay Delight",
            "description": "Automated 4-step sequence triggered immediately upon guest checkout.",
            "trigger_event": "GUEST_CHECKOUT",
            "status": "ACTIVE",
            "steps": [
                {
                    "step_number": 1,
                    "action_type": "SEND_EMAIL",
                    "delay_hours": 2,
                    "template_id": "tmpl_festive_gala",
                    "description": "Send checkout thank-you letter with digital invoice vault receipt."
                },
                {
                    "step_number": 2,
                    "action_type": "SEND_SMS",
                    "delay_hours": 24,
                    "template_id": "tmpl_winback_sms",
                    "description": "Send 2-question hospitality experience rating survey."
                },
                {
                    "step_number": 3,
                    "action_type": "WAIT_DELAY",
                    "delay_hours": 168,
                    "template_id": None,
                    "description": "Wait 7 days for return trip consideration."
                },
                {
                    "step_number": 4,
                    "action_type": "SEND_EMAIL",
                    "delay_hours": 0,
                    "template_id": "tmpl_spa_wellness",
                    "description": "Deliver 15% Royal Privilege return booking voucher."
                }
            ],
            "enrolled_count": 240,
            "completed_count": 195,
            "created_at": now - timedelta(days=50),
            "updated_at": now - timedelta(days=2)
        },
        {
            "id": "jrn_mice_nurture",
            "organization_id": org_id,
            "name": "Corporate MICE Symposium Conversion Flow",
            "description": "Nurture sequence triggered when prospective corporate inquiry is logged in CRM.",
            "trigger_event": "LEAD_CAPTURED",
            "status": "ACTIVE",
            "steps": [
                {
                    "step_number": 1,
                    "action_type": "SEND_EMAIL",
                    "delay_hours": 0,
                    "template_id": "tmpl_corp_mice",
                    "description": "Instantly dispatch executive ballroom capacity and AV catalog."
                },
                {
                    "step_number": 2,
                    "action_type": "CREATE_TASK",
                    "delay_hours": 24,
                    "template_id": None,
                    "description": "Assign high-priority discovery call to Senior Corporate Sales Rep."
                },
                {
                    "step_number": 3,
                    "action_type": "SEND_EMAIL",
                    "delay_hours": 72,
                    "template_id": "tmpl_corp_mice",
                    "description": "Follow up with tailored multi-day symposium quotation."
                }
            ],
            "enrolled_count": 85,
            "completed_count": 62,
            "created_at": now - timedelta(days=40),
            "updated_at": now - timedelta(days=4)
        }
    ]
    for j in journeys:
        _JOURNEY_STORE[j["id"]] = j

    # 5. Seed Conversion Attributions
    attributions = [
        {
            "id": f"attrib_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "campaign_id": "camp_q4_corp",
            "campaign_name": "Q4 Executive Corporate Retreats 2026",
            "deal_id": "deal_infosys_symposium",
            "order_id": None,
            "customer_id": "cust_tata_consultancy",
            "customer_name": "Tata Consultancy Services (TCS)",
            "attribution_model": "LAST_TOUCH",
            "attributed_revenue": Decimal("350000.00"),
            "attributed_at": now - timedelta(days=12)
        },
        {
            "id": f"attrib_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "campaign_id": "camp_q4_corp",
            "campaign_name": "Q4 Executive Corporate Retreats 2026",
            "deal_id": None,
            "order_id": None,
            "customer_id": "cust_cognizant",
            "customer_name": "Cognizant Global Solutions",
            "attribution_model": "LAST_TOUCH",
            "attributed_revenue": Decimal("500000.00"),
            "attributed_at": now - timedelta(days=8)
        },
        {
            "id": f"attrib_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "campaign_id": "camp_diwali_gala",
            "campaign_name": "Diwali Royal Festive Dining Gala",
            "deal_id": None,
            "order_id": "ord_pos_102",
            "customer_id": "cust_apollo_hospitals",
            "customer_name": "Apollo Hospitals Enterprise",
            "attribution_model": "FIRST_TOUCH",
            "attributed_revenue": Decimal("480000.00"),
            "attributed_at": now - timedelta(days=18)
        },
        {
            "id": f"attrib_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "campaign_id": "camp_kodai_spa",
            "campaign_name": "Kodaikanal Winter Solstice Spa Escape",
            "deal_id": None,
            "order_id": None,
            "customer_id": None,
            "customer_name": "Dr. V. Sundaram (Private Client)",
            "attribution_model": "LINEAR",
            "attributed_revenue": Decimal("340000.00"),
            "attributed_at": now - timedelta(days=5)
        }
    ]
    _ATTRIBUTION_STORE.extend(attributions)


class MarketingService:
    """Full-lifecycle Marketing Automation Business Service."""

    def __init__(self):
        _seed_marketing_data()

    # ---------------------------------------------------------
    # Campaigns
    # ---------------------------------------------------------
    def _enrich_campaign(self, c: Dict[str, Any]) -> CampaignOut:
        """Calculate live performance KPIs and return Pydantic DTO."""
        kpis = calculate_campaign_kpis(
            delivered=c.get("delivered_count", 0),
            opened=c.get("opened_count", 0),
            clicked=c.get("clicked_count", 0),
            converted=c.get("converted_count", 0),
            spend=c.get("actual_spend", 0),
            revenue=c.get("attributed_revenue", 0)
        )
        return CampaignOut(
            id=c["id"],
            organization_id=c["organization_id"],
            property_id=c.get("property_id"),
            campaign_code=c["campaign_code"],
            name=c["name"],
            channel=c["channel"],
            status=c["status"],
            budget=to_decimal(c.get("budget", 0)),
            actual_spend=to_decimal(c.get("actual_spend", 0)),
            attributed_revenue=to_decimal(c.get("attributed_revenue", 0)),
            start_date=c.get("start_date"),
            end_date=c.get("end_date"),
            segment_id=c.get("segment_id"),
            segment_name=c.get("segment_name"),
            template_id=c.get("template_id"),
            target_count=c.get("target_count", 0),
            sent_count=c.get("sent_count", 0),
            delivered_count=c.get("delivered_count", 0),
            opened_count=c.get("opened_count", 0),
            clicked_count=c.get("clicked_count", 0),
            converted_count=c.get("converted_count", 0),
            bounced_count=c.get("bounced_count", 0),
            open_rate_percent=kpis["open_rate_percent"],
            ctr_percent=kpis["ctr_percent"],
            conversion_rate_percent=kpis["conversion_rate_percent"],
            roas=kpis["roas"],
            cpa=kpis["cpa"],
            notes=c.get("notes"),
            created_at=c["created_at"],
            updated_at=c["updated_at"]
        )

    def list_campaigns(
        self,
        status_filter: Optional[str] = None,
        channel_filter: Optional[str] = None
    ) -> List[CampaignOut]:
        _seed_marketing_data()
        camps = list(_CAMPAIGN_STORE.values())

        if status_filter:
            s_norm = status_filter.strip().upper()
            camps = [c for c in camps if c.get("status", "").upper() == s_norm]

        if channel_filter:
            ch_norm = channel_filter.strip().upper()
            camps = [c for c in camps if c.get("channel", "").upper() == ch_norm]

        camps.sort(key=lambda x: x.get("created_at") or datetime.min, reverse=True)
        return [self._enrich_campaign(c) for c in camps]

    def get_campaign(self, campaign_id: str) -> CampaignOut:
        _seed_marketing_data()
        if campaign_id not in _CAMPAIGN_STORE:
            raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")
        return self._enrich_campaign(_CAMPAIGN_STORE[campaign_id])

    def create_campaign(
        self,
        camp_in: CampaignCreate,
        user_email: str = "marketing@victorycrest.internal"
    ) -> CampaignOut:
        _seed_marketing_data()
        org_id = camp_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        prop_id = camp_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]

        new_id = f"camp_{uuid.uuid4().hex[:8]}"
        code = f"CMP-2026-{uuid.uuid4().hex[:4].upper()}"
        now = datetime.utcnow()

        seg_name = None
        target_count = 0
        if camp_in.segment_id and camp_in.segment_id in _SEGMENT_STORE:
            seg = _SEGMENT_STORE[camp_in.segment_id]
            seg_name = seg["name"]
            target_count = seg["member_count"]

        record = {
            "id": new_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "campaign_code": code,
            "name": camp_in.name,
            "channel": camp_in.channel.upper(),
            "status": camp_in.status.upper(),
            "budget": to_decimal(camp_in.budget),
            "actual_spend": Decimal("0.00"),
            "attributed_revenue": Decimal("0.00"),
            "start_date": camp_in.start_date or now,
            "end_date": camp_in.end_date,
            "segment_id": camp_in.segment_id,
            "segment_name": seg_name,
            "template_id": camp_in.template_id,
            "target_count": target_count,
            "sent_count": 0,
            "delivered_count": 0,
            "opened_count": 0,
            "clicked_count": 0,
            "converted_count": 0,
            "bounced_count": 0,
            "notes": camp_in.notes,
            "created_at": now,
            "updated_at": now
        }
        _CAMPAIGN_STORE[new_id] = record

        audit_service.record_event(
            action="MARKETING_CAMPAIGN_CREATED",
            entity_type="MarketingCampaign",
            entity_id=new_id,
            user_email=user_email,
            organization_id=org_id,
            details=f"Created marketing campaign '{camp_in.name}' ({code}) via channel {camp_in.channel}"
        )
        return self._enrich_campaign(record)

    def update_campaign(self, campaign_id: str, camp_update: CampaignUpdate) -> CampaignOut:
        _seed_marketing_data()
        if campaign_id not in _CAMPAIGN_STORE:
            raise HTTPException(status_code=404, detail="Campaign not found")

        c = _CAMPAIGN_STORE[campaign_id]
        if camp_update.name is not None:
            c["name"] = camp_update.name
        if camp_update.channel is not None:
            c["channel"] = camp_update.channel.upper()
        if camp_update.status is not None:
            c["status"] = camp_update.status.upper()
        if camp_update.budget is not None:
            c["budget"] = to_decimal(camp_update.budget)
        if camp_update.start_date is not None:
            c["start_date"] = camp_update.start_date
        if camp_update.end_date is not None:
            c["end_date"] = camp_update.end_date
        if camp_update.segment_id is not None:
            c["segment_id"] = camp_update.segment_id
            if camp_update.segment_id in _SEGMENT_STORE:
                c["segment_name"] = _SEGMENT_STORE[camp_update.segment_id]["name"]
                c["target_count"] = _SEGMENT_STORE[camp_update.segment_id]["member_count"]
        if camp_update.template_id is not None:
            c["template_id"] = camp_update.template_id
        if camp_update.notes is not None:
            c["notes"] = camp_update.notes

        c["updated_at"] = datetime.utcnow()
        return self._enrich_campaign(c)

    def launch_campaign(
        self,
        campaign_id: str,
        user_email: str = "marketing@victorycrest.internal"
    ) -> CampaignDispatchResponse:
        _seed_marketing_data()
        if campaign_id not in _CAMPAIGN_STORE:
            raise HTTPException(status_code=404, detail="Campaign not found")

        c = _CAMPAIGN_STORE[campaign_id]
        target = c["target_count"] or 500
        delivered = int(target * 0.98)

        c["status"] = "RUNNING"
        c["sent_count"] = target
        c["delivered_count"] = delivered
        c["bounced_count"] = target - delivered
        c["updated_at"] = datetime.utcnow()

        audit_service.record_event(
            action="MARKETING_CAMPAIGN_LAUNCHED",
            entity_type="MarketingCampaign",
            entity_id=campaign_id,
            user_email=user_email,
            organization_id=c["organization_id"],
            details=f"Launched campaign '{c['name']}' ({c['campaign_code']}). Dispatched {target} messages."
        )

        return CampaignDispatchResponse(
            campaign_id=campaign_id,
            campaign_code=c["campaign_code"],
            status="RUNNING",
            messages_dispatched=target,
            simulated_delivered=delivered,
            message=f"Campaign '{c['name']}' launched successfully across {c['channel']} channel."
        )

    def pause_campaign(self, campaign_id: str) -> CampaignOut:
        _seed_marketing_data()
        if campaign_id not in _CAMPAIGN_STORE:
            raise HTTPException(status_code=404, detail="Campaign not found")
        c = _CAMPAIGN_STORE[campaign_id]
        c["status"] = "PAUSED"
        c["updated_at"] = datetime.utcnow()
        return self._enrich_campaign(c)

    # ---------------------------------------------------------
    # Audience Segments
    # ---------------------------------------------------------
    def list_segments(self) -> List[AudienceSegmentOut]:
        _seed_marketing_data()
        return [AudienceSegmentOut(**s) for s in _SEGMENT_STORE.values()]

    def get_segment(self, segment_id: str) -> AudienceSegmentOut:
        _seed_marketing_data()
        if segment_id not in _SEGMENT_STORE:
            raise HTTPException(status_code=404, detail="Audience segment not found")
        return AudienceSegmentOut(**_SEGMENT_STORE[segment_id])

    def create_segment(self, seg_in: AudienceSegmentCreate) -> AudienceSegmentOut:
        _seed_marketing_data()
        org_id = seg_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        new_id = f"seg_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        record = {
            "id": new_id,
            "organization_id": org_id,
            "property_id": seg_in.property_id,
            "name": seg_in.name,
            "description": seg_in.description,
            "segment_type": seg_in.segment_type.upper(),
            "filter_criteria": seg_in.filter_criteria or "{}",
            "member_count": 125,  # simulated initial matching audience
            "is_active": seg_in.is_active,
            "created_at": now,
            "updated_at": now
        }
        _SEGMENT_STORE[new_id] = record
        return AudienceSegmentOut(**record)

    # ---------------------------------------------------------
    # Customer Journeys
    # ---------------------------------------------------------
    def list_journeys(self) -> List[CustomerJourneyOut]:
        _seed_marketing_data()
        return [CustomerJourneyOut(**j) for j in _JOURNEY_STORE.values()]

    def create_journey(self, jrn_in: CustomerJourneyCreate) -> CustomerJourneyOut:
        _seed_marketing_data()
        org_id = jrn_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        new_id = f"jrn_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        record = {
            "id": new_id,
            "organization_id": org_id,
            "name": jrn_in.name,
            "description": jrn_in.description,
            "trigger_event": jrn_in.trigger_event,
            "status": jrn_in.status.upper(),
            "steps": [s.model_dump() for s in jrn_in.steps],
            "enrolled_count": 0,
            "completed_count": 0,
            "created_at": now,
            "updated_at": now
        }
        _JOURNEY_STORE[new_id] = record
        return CustomerJourneyOut(**record)

    # ---------------------------------------------------------
    # Creative Templates
    # ---------------------------------------------------------
    def list_templates(self, channel: Optional[str] = None) -> List[CampaignTemplateOut]:
        _seed_marketing_data()
        templates = list(_TEMPLATE_STORE.values())
        if channel:
            c_norm = channel.strip().upper()
            templates = [t for t in templates if t.get("channel", "").upper() == c_norm]
        return [CampaignTemplateOut(**t) for t in templates]

    def create_template(self, tmpl_in: CampaignTemplateCreate) -> CampaignTemplateOut:
        _seed_marketing_data()
        org_id = tmpl_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        new_id = f"tmpl_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        record = {
            "id": new_id,
            "organization_id": org_id,
            "name": tmpl_in.name,
            "channel": tmpl_in.channel.upper(),
            "subject": tmpl_in.subject,
            "body_content": tmpl_in.body_content,
            "merge_tags": tmpl_in.merge_tags,
            "is_active": tmpl_in.is_active,
            "created_at": now,
            "updated_at": now
        }
        _TEMPLATE_STORE[new_id] = record
        return CampaignTemplateOut(**record)

    # ---------------------------------------------------------
    # Conversion Attribution
    # ---------------------------------------------------------
    def list_attributions(self, campaign_id: Optional[str] = None) -> List[AttributionOut]:
        _seed_marketing_data()
        results = list(_ATTRIBUTION_STORE)
        if campaign_id:
            results = [a for a in results if a.get("campaign_id") == campaign_id]
        return [AttributionOut(**a) for a in results]

    def create_attribution(self, attrib_in: AttributionCreate) -> AttributionOut:
        _seed_marketing_data()
        camp = _CAMPAIGN_STORE.get(attrib_in.campaign_id)
        camp_name = camp["name"] if camp else "Marketing Campaign"
        org_id = camp["organization_id"] if camp else DEMO_ORGANISATIONS[0]["id"]

        new_id = f"attrib_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        rev = to_decimal(attrib_in.attributed_revenue)

        record = {
            "id": new_id,
            "organization_id": org_id,
            "campaign_id": attrib_in.campaign_id,
            "campaign_name": camp_name,
            "deal_id": attrib_in.deal_id,
            "order_id": attrib_in.order_id,
            "customer_id": attrib_in.customer_id,
            "customer_name": attrib_in.customer_name,
            "attribution_model": attrib_in.attribution_model.upper(),
            "attributed_revenue": rev,
            "attributed_at": now
        }
        _ATTRIBUTION_STORE.append(record)

        # Update campaign's total attributed revenue
        if camp:
            camp["attributed_revenue"] = to_decimal(camp.get("attributed_revenue", 0)) + rev
            camp["converted_count"] = camp.get("converted_count", 0) + 1

        return AttributionOut(**record)

    # ---------------------------------------------------------
    # Marketing Metrics Telemetry
    # ---------------------------------------------------------
    def get_marketing_metrics(self) -> MarketingMetricsOut:
        _seed_marketing_data()
        camps = list(_CAMPAIGN_STORE.values())

        total_campaigns = len(camps)
        active_campaigns = len([c for c in camps if c.get("status") == "RUNNING"])
        total_budget = sum((to_decimal(c.get("budget", 0)) for c in camps), Decimal("0.00"))
        total_spend = sum((to_decimal(c.get("actual_spend", 0)) for c in camps), Decimal("0.00"))
        total_revenue = sum((to_decimal(c.get("attributed_revenue", 0)) for c in camps), Decimal("0.00"))

        total_target = sum(c.get("target_count", 0) for c in camps)
        total_delivered = sum(c.get("delivered_count", 0) for c in camps)
        total_opened = sum(c.get("opened_count", 0) for c in camps)
        total_clicked = sum(c.get("clicked_count", 0) for c in camps)
        total_converted = sum(c.get("converted_count", 0) for c in camps)

        kpis = calculate_campaign_kpis(
            delivered=total_delivered,
            opened=total_opened,
            clicked=total_clicked,
            converted=total_converted,
            spend=total_spend,
            revenue=total_revenue
        )

        return MarketingMetricsOut(
            total_campaigns_count=total_campaigns,
            active_campaigns_count=active_campaigns,
            total_budget=total_budget.quantize(Decimal("0.01")),
            total_spend=total_spend.quantize(Decimal("0.01")),
            total_attributed_revenue=total_revenue.quantize(Decimal("0.01")),
            overall_roas=kpis["roas"],
            total_targeted_audience=total_target,
            total_delivered_messages=total_delivered,
            overall_open_rate_percent=kpis["open_rate_percent"],
            overall_ctr_percent=kpis["ctr_percent"],
            overall_conversion_rate_percent=kpis["conversion_rate_percent"],
            total_segments_count=len(_SEGMENT_STORE),
            active_journeys_count=len([j for j in _JOURNEY_STORE.values() if j.get("status") == "ACTIVE"])
        )


marketing_service = MarketingService()
