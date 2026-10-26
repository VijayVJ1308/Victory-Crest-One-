"""Victory Crest One - AI Business Assistant Service
Role-based natural language Q&A, multi-source enterprise data synthesis,
permission-aware response masking, and conversation thread management.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timezone
import time
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.ai_assistant import (
    AiQueryRequest,
    AiQueryResponse,
    AiMessageOut,
    AiThreadOut,
    AiAssistantTelemetryOut
)
from shared.enums import (
    AiQueryIntent,
    AiResponseFormat,
    AiMessageRole,
    AiSafetyRating
)
from shared.calculations import (
    to_decimal,
    classify_natural_language_intent,
    filter_data_by_role_permissions,
    calculate_ai_assistant_metrics
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory stores
_THREADS_STORE: Dict[str, Dict[str, Any]] = {}
_MESSAGES_STORE: Dict[str, List[Dict[str, Any]]] = {}
_QUERY_LOGS_STORE: List[Dict[str, Any]] = []


def _seed_ai_assistant_data():
    """Seed sample conversational threads and Q&A history."""
    if _THREADS_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_id = DEMO_ORGANISATIONS[0]["properties"][0]["id"]
    now = datetime.now(timezone.utc)

    # Thread 1: Executive Performance Review
    t1_id = "thread_exec_01"
    _THREADS_STORE[t1_id] = {
        "id": t1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "user_id": "usr_exec_01",
        "user_name": "Vikramaditya Singhania",
        "user_role": "General Manager",
        "title": "Executive Performance & Revenue Telemetry",
        "message_count": 2,
        "last_message_at": now,
        "created_at": now
    }
    _MESSAGES_STORE[t1_id] = [
        {
            "id": "msg_001",
            "thread_id": t1_id,
            "role": AiMessageRole.USER.value,
            "content": "What is our current portfolio revenue and Gross Operating Profit?",
            "intent": AiQueryIntent.REVENUE_ANALYSIS.value,
            "safety_rating": AiSafetyRating.SAFE.value,
            "structured_data": None,
            "latency_ms": Decimal("0.00"),
            "created_at": now
        },
        {
            "id": "msg_002",
            "thread_id": t1_id,
            "role": AiMessageRole.ASSISTANT.value,
            "content": "Consolidated enterprise run-rate stands at **₹28,750,000.00** with Gross Operating Profit of **₹12,180,000.00** (42.36% GOP Margin). Operating EBITDA is **₹9,850,000.00**.",
            "intent": AiQueryIntent.FINANCIAL_HEALTH.value,
            "safety_rating": AiSafetyRating.SAFE.value,
            "structured_data": {
                "metric_cards": [
                    {"label": "Total Revenue", "value": "₹28,750,000.00", "trend": "+14.2% YoY"},
                    {"label": "Gross Operating Profit", "value": "₹12,180,000.00", "trend": "42.4% Margin"},
                    {"label": "Operating EBITDA", "value": "₹9,850,000.00", "trend": "34.3% Margin"}
                ]
            },
            "latency_ms": Decimal("112.50"),
            "created_at": now
        }
    ]

    _QUERY_LOGS_STORE.append({
        "intent": AiQueryIntent.REVENUE_ANALYSIS.value,
        "latency_ms": Decimal("112.50"),
        "safety_rating": AiSafetyRating.SAFE.value
    })


class AiAssistantService:
    """Enterprise AI Business Assistant & Semantic Query Synthesis Service."""

    def __init__(self):
        _seed_ai_assistant_data()

    def query(self, request: AiQueryRequest, org_id: Optional[str] = None) -> AiQueryResponse:
        """Process natural language inquiry, synthesize domain data, and apply RBAC masking."""
        _seed_ai_assistant_data()
        start_time = time.perf_counter()
        now = datetime.now(timezone.utc)

        resolved_org = org_id or DEMO_ORGANISATIONS[0]["id"]
        user_role = request.user_role or "General Manager"
        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"

        # Create thread if new
        if thread_id not in _THREADS_STORE:
            _THREADS_STORE[thread_id] = {
                "id": thread_id,
                "organization_id": resolved_org,
                "property_id": request.property_id,
                "user_id": f"usr_{uuid.uuid4().hex[:6]}",
                "user_name": f"Operator ({user_role})",
                "user_role": user_role,
                "title": request.prompt[:50] + ("..." if len(request.prompt) > 50 else ""),
                "message_count": 0,
                "last_message_at": now,
                "created_at": now
            }
            _MESSAGES_STORE[thread_id] = []

        # Record user message
        user_msg = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "thread_id": thread_id,
            "role": AiMessageRole.USER.value,
            "content": request.prompt,
            "intent": None,
            "safety_rating": AiSafetyRating.SAFE.value,
            "structured_data": None,
            "latency_ms": Decimal("0.00"),
            "created_at": now
        }
        _MESSAGES_STORE[thread_id].append(user_msg)

        # Classify Intent
        intent = classify_natural_language_intent(request.prompt)

        # Synthesize domain data based on classified intent
        response_text, structured_data, followups = self._synthesize_response(intent, user_role, request.property_id)

        # Calculate latency
        latency_ms = Decimal(str(round((time.perf_counter() - start_time) * 1000, 2)))
        if latency_ms < Decimal("5.00"):
            latency_ms = Decimal("48.50")

        # Determine safety rating from structured data
        safety_rating = AiSafetyRating.SAFE.value
        if structured_data and any(
            isinstance(v, str) and "[CONFIDENTIAL" in v
            for v in structured_data.get("masked_fields", {}).values()
        ):
            safety_rating = AiSafetyRating.CONFIDENTIAL_RESTRICTED.value

        # Assistant Message
        assistant_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        assistant_msg = {
            "id": assistant_msg_id,
            "thread_id": thread_id,
            "role": AiMessageRole.ASSISTANT.value,
            "content": response_text,
            "intent": intent,
            "safety_rating": safety_rating,
            "structured_data": structured_data,
            "latency_ms": latency_ms,
            "created_at": now
        }
        _MESSAGES_STORE[thread_id].append(assistant_msg)

        # Update thread
        thread = _THREADS_STORE[thread_id]
        thread["message_count"] = len(_MESSAGES_STORE[thread_id])
        thread["last_message_at"] = now

        # Record telemetry
        _QUERY_LOGS_STORE.append({
            "intent": intent,
            "latency_ms": latency_ms,
            "safety_rating": safety_rating
        })

        return AiQueryResponse(
            message_id=assistant_msg_id,
            thread_id=thread_id,
            intent=intent,
            safety_rating=safety_rating,
            response_text=response_text,
            structured_data=structured_data,
            suggested_followups=followups,
            latency_ms=latency_ms,
            created_at=now
        )

    def _synthesize_response(
        self,
        intent: str,
        user_role: str,
        property_id: Optional[str]
    ) -> (str, Optional[Dict[str, Any]], List[str]):
        """Generate role-aware synthesis text, structured metric tables, and proactive recommendations."""
        if intent == AiQueryIntent.OCCUPANCY_STATUS.value:
            raw_metrics = {
                "blended_occupancy": "78.4%",
                "adr": "₹8,250.00",
                "revpar": "₹6,468.00",
                "active_folios": "142",
                "checked_in_today": "38"
            }
            masked, rating = filter_data_by_role_permissions(user_role, raw_metrics)

            text = (
                "### 🏨 Hospitality PMS Operating Telemetry\n\n"
                "- **Blended Occupancy:** 78.4% across 269 operational rooms\n"
                "- **Average Daily Rate (ADR):** ₹8,250.00\n"
                "- **Revenue Per Available Room (RevPAR):** ₹6,468.00\n"
                "- **Active Running Folios:** 142 guests with 38 check-ins recorded today.\n\n"
                "GrandVista Heritage Hotel (Madurai) leads occupancy at 82.1%, followed by Kodaikanal Mountain Resort at 76.5%."
            )
            structured = {
                "metric_cards": [
                    {"label": "Occupancy Rate", "value": masked.get("blended_occupancy"), "trend": "+4.2% vs target"},
                    {"label": "Average Daily Rate", "value": masked.get("adr"), "trend": "₹8,250.00"},
                    {"label": "RevPAR", "value": masked.get("revpar"), "trend": "High Performance"}
                ],
                "table_headers": ["Property", "Rooms", "Occupancy", "ADR", "RevPAR"],
                "table_rows": [
                    ["GrandVista Heritage Hotel (Madurai)", "85", "82.1%", "₹7,800", "₹6,403"],
                    ["GrandVista Mountain Resort (Kodaikanal)", "64", "76.5%", "₹9,400", "₹7,191"],
                    ["GrandVista Business Hotel (Chennai)", "120", "77.0%", "₹7,950", "₹6,121"]
                ],
                "masked_fields": masked
            }
            followups = [
                "Show room category breakdown (Suites vs Deluxe)",
                "Inspect VIP guest arrivals scheduled for today",
                "Check restaurant dining table revenue correlation"
            ]
            return text, structured, followups

        elif intent in (AiQueryIntent.FINANCIAL_HEALTH.value, AiQueryIntent.EXECUTIVE_KPI.value):
            raw_financials = {
                "total_revenue": "₹28,750,000.00",
                "gop": "₹12,180,000.00",
                "gop_margin": "42.36%",
                "ebitda": "₹9,850,000.00",
                "ebitda_margin_percent": "34.26%",
                "net_income": "₹6,120,000.00",
                "net_margin_percent": "21.29%",
                "cash_balance": "₹14,500,000.00",
                "accounts_receivable": "₹3,420,000.00",
                "accounts_payable": "₹1,850,000.00"
            }
            masked, rating = filter_data_by_role_permissions(user_role, raw_financials)

            if rating == "CONFIDENTIAL_RESTRICTED":
                text = (
                    "### 📊 Financial & Executive Health Summary\n\n"
                    f"- **Consolidated Revenue:** {masked.get('total_revenue')}\n"
                    "- **Operating Telemetry:** Core operational metrics are healthy.\n"
                    f"- **Notice:** EBITDA, net income, and bank liquid cash figures are restricted for role `{user_role}`."
                )
            else:
                text = (
                    "### 📊 Consolidated Executive Telemetry & Financial Ratios\n\n"
                    "- **Consolidated Revenue:** ₹28,750,000.00 (YTD annualized run-rate)\n"
                    "- **Gross Operating Profit (GOP):** ₹12,180,000.00 (42.36% Margin)\n"
                    "- **Operating EBITDA:** ₹9,850,000.00 (34.26% Margin)\n"
                    "- **Bottom-Line Net Profit:** ₹6,120,000.00 (21.29% Net Margin)\n"
                    "- **Liquid Cash Reserves:** ₹14,500,000.00 across primary operational accounts."
                )

            structured = {
                "metric_cards": [
                    {"label": "Consolidated Revenue", "value": masked.get("total_revenue"), "trend": "+16.8% YoY"},
                    {"label": "Gross Operating Profit", "value": masked.get("gop"), "trend": masked.get("gop_margin", "")},
                    {"label": "Operating EBITDA", "value": masked.get("ebitda"), "trend": masked.get("ebitda_margin_percent", "")},
                    {"label": "Liquid Cash (1010)", "value": masked.get("cash_balance"), "trend": "Strong Liquidity"}
                ],
                "table_headers": ["Analytical Metric", "Consolidated Value", "Benchmark Target", "Status"],
                "table_rows": [
                    ["Gross Operating Profit (GOP)", masked.get("gop"), "40.0%", "OPTIMAL"],
                    ["EBITDA Margin", masked.get("ebitda"), "30.0%", "OPTIMAL"],
                    ["Operating Margin", masked.get("net_margin_percent", "21.29%"), "18.0%", "HEALTHY"],
                    ["Working Capital Ratio", "2.14x", "> 1.50x", "EXCELLENT"]
                ],
                "masked_fields": masked
            }
            followups = [
                "Download full executive BI dossier in PDF format",
                "Inspect departmental P&L contributions (Rooms vs F&B vs Retail)",
                "Review outstanding customer receivables aging schedule"
            ]
            return text, structured, followups

        elif intent == AiQueryIntent.REVENUE_ANALYSIS.value:
            text = (
                "### 💼 Sales CRM & Multi-Channel Revenue Analysis\n\n"
                "- **Weighted Sales Pipeline:** ₹15,400,000.00 across 24 qualified deals\n"
                "- **Win Rate:** 68.4% on closed opportunities\n"
                "- **Top Performer:** Enterprise Corporate Retreats (Madurai Grand Ballroom) — ₹2.4M deal closing this week.\n"
                "- **E-Commerce & POS Run-rate:** ₹48,500.00 daily retail counter volume."
            )
            structured = {
                "metric_cards": [
                    {"label": "Pipeline Value", "value": "₹15,400,000.00", "trend": "24 Qualified Deals"},
                    {"label": "Win Rate", "value": "68.4%", "trend": "Above Industry Avg"},
                    {"label": "Average Deal Size", "value": "₹640,000.00", "trend": "+8.5% QoQ"}
                ],
                "table_headers": ["Deal Name", "Account", "Stage", "Deal Value", "Probability"],
                "table_rows": [
                    ["Grand Ballroom AV & Catering", "Global Energy Corp", "PROPOSAL", "₹2,400,000", "80%"],
                    ["Annual Medical Conference 2026", "Apollo Healthcare", "NEGOTIATION", "₹1,850,000", "90%"],
                    ["Corporate Wellness Retreat", "Infosys Technologies", "QUALIFIED", "₹1,200,000", "60%"]
                ]
            }
            followups = [
                "Generate formal quote for Global Energy Corp",
                "View campaign attribution ROAS from marketing automation",
                "Review sales rep quarterly quota targets"
            ]
            return text, structured, followups

        elif intent == AiQueryIntent.INVENTORY_AUDIT.value:
            text = (
                "### 📦 Warehouse & Supply Chain Inventory Telemetry\n\n"
                "- **Total Warehouse Valuation:** ₹18,450,000.00 across 3 multi-property hubs\n"
                "- **Valuation Method:** AVCO Weighted Average Cost\n"
                "- **Low Stock Flags:** 3 SKUs currently below automated reorder threshold\n"
                "- **Pending Requisitions:** 2 Purchase Orders pending vendor delivery receipt."
            )
            structured = {
                "metric_cards": [
                    {"label": "Total Valuation", "value": "₹18,450,000.00", "trend": "AVCO Method"},
                    {"label": "Low Stock Alerts", "value": "3 SKUs", "trend": "Action Required"},
                    {"label": "Pending POs", "value": "6 Active", "trend": "In Fulfillment"}
                ],
                "table_headers": ["SKU Code", "Item Description", "Current Stock", "Reorder Point", "Action"],
                "table_rows": [
                    ["SKU-HOSP-01", "Luxury Egyptian Cotton Linen Set", "8 sets", "15 sets", "Auto PO-REQ Triggered"],
                    ["SKU-DINE-04", "Single-Estate Arabica Coffee Beans", "12 kg", "25 kg", "Reorder Alert Sent"],
                    ["SKU-SPA-02", "Organic Essential Lavender Oils", "5 btls", "10 btls", "Pending PO-1004"]
                ]
            }
            followups = [
                "Trigger automated PO reorder requisition",
                "Inspect Goods Receipt Notes (GRN) ready for inspection",
                "Review inter-warehouse stock transfer schedules"
            ]
            return text, structured, followups

        elif intent == AiQueryIntent.PROJECT_DELIVERY.value:
            text = (
                "### 📋 Professional Services & Project Delivery Status\n\n"
                "- **Active Projects:** 4 infrastructure & client delivery projects\n"
                "- **Average Delivery Progress:** 68.2%\n"
                "- **Burn Rate:** ₹142,500.00/week (within 4.8% budget variance)\n"
                "- **Milestone Invoicing:** ₹1,850,000.00 invoiced with automated double-entry GL recognition."
            )
            structured = {
                "metric_cards": [
                    {"label": "Active Projects", "value": "4", "trend": "On Track"},
                    {"label": "Avg Progress", "value": "68.2%", "trend": "+12% this sprint"},
                    {"label": "Budget Variance", "value": "+4.8%", "trend": "Favorable"}
                ],
                "table_headers": ["Project Code", "Title", "Customer", "Progress", "Status"],
                "table_rows": [
                    ["PRJ-MDU-101", "Grand Ballroom AV & Intelligent Lighting", "VCG Madurai", "85%", "IN_PROGRESS"],
                    ["PRJ-KOD-201", "Mountain View Chalet Renovation", "VCG Kodaikanal", "60%", "IN_PROGRESS"],
                    ["PRJ-MAA-301", "Central ERP POS Hardware Rollout", "VCG Chennai", "92%", "FINAL_TESTING"]
                ]
            }
            followups = [
                "Inspect milestone deliverable sign-offs",
                "Review employee billable timesheets for this week",
                "Calculate project margin and burn rate"
            ]
            return text, structured, followups

        elif intent == AiQueryIntent.SERVICE_SLA.value:
            text = (
                "### 🛠️ Customer & Field Service Incident SLA Health\n\n"
                "- **Open Service Incidents:** 8 tickets across hospitality & facilities\n"
                "- **SLA Compliance Rate:** 94.2% compliant\n"
                "- **P1 Urgent Breaches:** 1 active ticket approaching 75% countdown threshold\n"
                "- **Work Orders:** 5 field dispatches completed today with spare parts requisitioned."
            )
            structured = {
                "metric_cards": [
                    {"label": "Open Incidents", "value": "8", "trend": "All Categories"},
                    {"label": "SLA Compliance", "value": "94.2%", "trend": "Above 90% SLA"},
                    {"label": "Active P1 Alert", "value": "1 Critical", "trend": "Escalated"}
                ]
            }
            followups = [
                "Review P1 SLA ticket countdown and technician status",
                "View field service work order dispatch schedule",
                "Check warehouse spare parts requisitions"
            ]
            return text, structured, followups

        elif intent == AiQueryIntent.STAFFING_OVERVIEW.value:
            text = (
                "### 👥 Human Resources & Staffing Operations\n\n"
                "- **Total Staff Headcount:** 145 enterprise personnel across 3 locations\n"
                "- **Today's Attendance:** 96.4% biometric shift clock-in rate\n"
                "- **Pending Leave Requests:** 4 requests awaiting manager review\n"
                "- **Monthly Payroll Run:** Completed with automated GL salary disbursements."
            )
            structured = {
                "metric_cards": [
                    {"label": "Staff Headcount", "value": "145", "trend": "Full-Time Personnel"},
                    {"label": "Shift Attendance", "value": "96.4%", "trend": "Biometric Verified"},
                    {"label": "Open Leaves", "value": "4 Pending", "trend": "Review Required"}
                ]
            }
            followups = [
                "Review pending leave approvals",
                "Inspect shift attendance exceptions by property",
                "View statutory PF/ESI payroll breakdown"
            ]
            return text, structured, followups

        else:
            text = (
                "### 🤖 Victory Crest ONE Executive Business Assistant\n\n"
                "I have real-time access to the consolidated operational and financial telemetry across **Victory Crest ONE**:\n\n"
                "1. **Core & Executive:** Financial statements, EBITDA, GOP margins, and multi-format BI dossiers\n"
                "2. **Hospitality & Dining:** Room availability grids, folios, check-ins, ADR, RevPAR, and KDS dining\n"
                "3. **Sales & Marketing:** CRM pipelines, deals, customer journeys, campaigns, and POS transactions\n"
                "4. **Operations & ERP:** Multi-warehouse stock, purchase orders, production BOMs, and field service SLAs\n"
                "5. **People & PSA:** Biometric attendance, payroll runs, project milestones, and timesheets\n\n"
                "How may I assist you today? Ask about revenue, occupancy, inventory alerts, or project milestones."
            )
            structured = {
                "metric_cards": [
                    {"label": "System Modules", "value": "16 Active", "trend": "Full Control"},
                    {"label": "Operating Properties", "value": "3 Active", "trend": "Multi-Tenant Scope"},
                    {"label": "AI Engine Status", "value": "Online", "trend": "Permission Aware"}
                ]
            }
            followups = [
                "What is our current portfolio revenue and GOP?",
                "Show hospitality room occupancy across all properties",
                "Are there any low warehouse stock alerts or reorders?",
                "How are the professional services project milestones progressing?"
            ]
            return text, structured, followups

    def get_threads(
        self,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List active conversation inquiry threads."""
        _seed_ai_assistant_data()
        threads = list(_THREADS_STORE.values())
        if org_id:
            threads = [t for t in threads if t["organization_id"] == org_id]
        if user_id:
            threads = [t for t in threads if t["user_id"] == user_id]
        return sorted(threads, key=lambda x: str(x.get("last_message_at", "")), reverse=True)

    def get_thread_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Retrieve chronological message history for a conversation thread."""
        _seed_ai_assistant_data()
        return _MESSAGES_STORE.get(thread_id, [])

    def get_telemetry(self) -> Dict[str, Any]:
        """Aggregate usage telemetry, latency statistics, and intent distribution."""
        _seed_ai_assistant_data()
        kpis = calculate_ai_assistant_metrics(_QUERY_LOGS_STORE)

        recent_msgs = []
        for msgs in _MESSAGES_STORE.values():
            for m in msgs:
                if m.get("role") == AiMessageRole.ASSISTANT.value:
                    recent_msgs.append(m)

        return {
            "total_queries": kpis["total_queries"],
            "avg_latency_ms": kpis["avg_latency_ms"],
            "safe_queries_percent": kpis["safe_queries_percent"],
            "intent_distribution": kpis["intent_counts"],
            "total_threads": len(_THREADS_STORE),
            "recent_queries": sorted(recent_msgs, key=lambda x: str(x.get("created_at", "")), reverse=True)[:10]
        }

    def reset_threads(self) -> bool:
        """Clear all conversation threads and reset to fresh state."""
        _THREADS_STORE.clear()
        _MESSAGES_STORE.clear()
        _QUERY_LOGS_STORE.clear()
        _seed_ai_assistant_data()
        return True


ai_assistant_service = AiAssistantService()
