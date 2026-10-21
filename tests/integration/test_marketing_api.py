"""Victory Crest One - Integration Tests for Marketing Automation API
Endpoints for multi-channel campaigns, segmentation, automated journeys,
creative templates, and conversion attribution.
"""

from decimal import Decimal
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_marketing_campaigns_list_and_create():
    # 1. List campaigns
    res = client.get("/api/v1/marketing/campaigns")
    assert res.status_code == 200
    campaigns = res.json()
    assert len(campaigns) >= 3
    codes = [c["campaign_code"] for c in campaigns]
    assert any("CORP" in c for c in codes)
    assert any("FEST" in c for c in codes)

    # 2. Create new campaign
    payload = {
        "name": "Summer Luxury Villa Getaway",
        "channel": "EMAIL",
        "budget": 75000.00,
        "notes": "Early bird summer bookings"
    }
    res_create = client.post("/api/v1/marketing/campaigns", json=payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["name"] == "Summer Luxury Villa Getaway"
    assert created["channel"] == "EMAIL"
    assert created["status"] == "DRAFT"
    assert Decimal(str(created["budget"])) == Decimal("75000.00")
    assert "CMP-2026-" in created["campaign_code"]


def test_marketing_campaign_launch_dispatch():
    # Fetch a campaign and trigger launch
    res = client.get("/api/v1/marketing/campaigns?status=SCHEDULED")
    assert res.status_code == 200
    sched = res.json()
    assert len(sched) >= 1
    camp_id = sched[0]["id"]

    res_launch = client.post(f"/api/v1/marketing/campaigns/{camp_id}/launch")
    assert res_launch.status_code == 200
    dispatch = res_launch.json()
    assert dispatch["status"] == "RUNNING"
    assert dispatch["messages_dispatched"] > 0
    assert dispatch["simulated_delivered"] > 0


def test_marketing_segments_crud():
    # 1. List segments
    res = client.get("/api/v1/marketing/segments")
    assert res.status_code == 200
    segments = res.json()
    assert len(segments) >= 3
    names = [s["name"] for s in segments]
    assert any("Royal Heritage" in n for n in names)

    # 2. Create segment
    payload = {
        "name": "Banqueting & Wedding Prospects",
        "description": "Engaged couples and wedding planners inquiring about palace lawns",
        "segment_type": "DYNAMIC",
        "filter_criteria": '{"event_type": "Wedding", "guest_count_min": 200}'
    }
    res_create = client.post("/api/v1/marketing/segments", json=payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["name"] == "Banqueting & Wedding Prospects"
    assert created["member_count"] > 0


def test_marketing_journeys_list_and_create():
    # 1. List customer journeys
    res = client.get("/api/v1/marketing/journeys")
    assert res.status_code == 200
    journeys = res.json()
    assert len(journeys) >= 2
    assert any("VIP" in j["name"] for j in journeys)

    # 2. Create new journey
    payload = {
        "name": "Dining Club Loyalty Onboarding",
        "description": "Welcome sequence for royal restaurant patrons",
        "trigger_event": "FIRST_DINING_TRANSACTION",
        "steps": [
            {
                "step_number": 1,
                "action_type": "SEND_SMS",
                "delay_hours": 1,
                "description": "Welcome to Chettinad Dining Club"
            },
            {
                "step_number": 2,
                "action_type": "SEND_EMAIL",
                "delay_hours": 48,
                "description": "Chef tasting invitation & sommelier wine pairing"
            }
        ]
    }
    res_create = client.post("/api/v1/marketing/journeys", json=payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert len(created["steps"]) == 2


def test_marketing_templates_list_and_create():
    # 1. List templates
    res = client.get("/api/v1/marketing/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 3

    # 2. Create template
    payload = {
        "name": "Palace Lawn Gala Dinner Invitation",
        "channel": "EMAIL",
        "subject": "Exclusive Invitation: Royal Heritage Gala Dinner",
        "body_content": "Dear {{first_name}}, please join our royal culinary evening at {{property_name}}."
    }
    res_create = client.post("/api/v1/marketing/templates", json=payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["channel"] == "EMAIL"


def test_marketing_attributions_and_roi():
    # 1. List attributions
    res = client.get("/api/v1/marketing/attributions")
    assert res.status_code == 200
    attributions = res.json()
    assert len(attributions) >= 3

    # 2. Create revenue attribution
    attrib_payload = {
        "campaign_id": "camp_q4_corp",
        "customer_name": "Wipro Enterprise Solutions",
        "attribution_model": "LAST_TOUCH",
        "attributed_revenue": 220000.00
    }
    res_attrib = client.post("/api/v1/marketing/attributions", json=attrib_payload)
    assert res_attrib.status_code == 200
    created = res_attrib.json()
    assert Decimal(str(created["attributed_revenue"])) == Decimal("220000.00")


def test_marketing_metrics_telemetry():
    res = client.get("/api/v1/marketing/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["total_campaigns_count"] >= 3
    assert Decimal(str(metrics["total_budget"])) > Decimal("0.00")
    assert Decimal(str(metrics["total_spend"])) > Decimal("0.00")
    assert Decimal(str(metrics["total_attributed_revenue"])) > Decimal("0.00")
    assert Decimal(str(metrics["overall_roas"])) > Decimal("1.00")
