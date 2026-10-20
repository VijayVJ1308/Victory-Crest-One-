"""Victory Crest One - Sales CRM & Revenue Pipeline Engine
Leads lifecycle, Opportunity Pipeline Stages, Quotations, Sales Activities, and Forecast Analytics.
Seamlessly bridges Sales into Customer Master and Finance AR Invoicing.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.crm import (
    LeadCreate, LeadUpdate, LeadOut, LeadConvertRequest, LeadConvertResponse,
    DealCreate, DealUpdate, DealOut, DealStageUpdateRequest,
    QuoteCreate, QuoteOut, QuoteLineCreate, QuoteLineOut, QuoteConvertInvoiceResponse,
    SalesActivityCreate, SalesActivityOut,
    SalesPipelineMetricsResponse, StageMetric
)
from backend.app.schemas.master_data import CustomerCreate
from backend.app.schemas.finance import CustomerInvoiceCreate, InvoiceLineCreate
from backend.app.services.master_data_service import customer_service
from backend.app.services.finance_service import finance_service
from backend.app.services.audit_service import audit_service
from shared.calculations import (
    to_decimal, calculate_invoice_totals, calculate_weighted_pipeline,
    calculate_win_rate, get_default_stage_probability
)
from shared.constants import DEMO_ORGANISATIONS


# In-memory stores with demonstration seed data
_LEAD_STORE: Dict[str, Dict[str, Any]] = {}
_DEAL_STORE: Dict[str, Dict[str, Any]] = {}
_QUOTE_STORE: Dict[str, Dict[str, Any]] = {}
_ACTIVITY_STORE: List[Dict[str, Any]] = []


def _seed_crm_data():
    """Populate demonstration CRM leads, deals, quotes, and activities."""
    if _LEAD_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_id = DEMO_ORGANISATIONS[0]["properties"][0]["id"]

    # 1. Seed Leads
    leads = [
        {
            "id": "lead_cognizant_retreat",
            "organization_id": org_id,
            "property_id": prop_id,
            "first_name": "Arvind",
            "last_name": "Nambiar",
            "company_name": "Cognizant Global Solutions",
            "job_title": "Director of Administration",
            "email": "arvind.nambiar@cognizant.com",
            "phone": "+91 98400 11223",
            "lead_source": "WEBSITE",
            "status": "QUALIFIED",
            "lead_score": 85,
            "estimated_budget": Decimal("1500000.00"),
            "assigned_rep_name": "Vikram Sharma",
            "converted_at": None,
            "converted_customer_id": None,
            "converted_deal_id": None,
            "notes": "Planning 3-day executive leadership conference for 120 delegates in November.",
            "created_at": datetime.utcnow() - timedelta(days=25),
            "updated_at": datetime.utcnow() - timedelta(days=20),
        },
        {
            "id": "lead_apollo_summit",
            "organization_id": org_id,
            "property_id": prop_id,
            "first_name": "Dr. Malini",
            "last_name": "Sengupta",
            "company_name": "Apollo Hospitals Group",
            "job_title": "VP Medical Conferences",
            "email": "malini.s@apollohospitals.org",
            "phone": "+91 98200 44556",
            "lead_source": "REFERRAL",
            "status": "CONTACTED",
            "lead_score": 72,
            "estimated_budget": Decimal("850000.00"),
            "assigned_rep_name": "Ananya Iyer",
            "converted_at": None,
            "converted_customer_id": None,
            "converted_deal_id": None,
            "notes": "Inquiring about grand ballroom and catering for annual cardiology symposium.",
            "created_at": datetime.utcnow() - timedelta(days=14),
            "updated_at": datetime.utcnow() - timedelta(days=8),
        },
        {
            "id": "lead_godrej_expo",
            "organization_id": org_id,
            "property_id": prop_id,
            "first_name": "Rohan",
            "last_name": "Kulkarni",
            "company_name": "Godrej Consumer Products",
            "job_title": "Brand Marketing Lead",
            "email": "rohan.kulkarni@godrej.com",
            "phone": "+91 97600 88990",
            "lead_source": "TRADE_SHOW",
            "status": "NEW",
            "lead_score": 58,
            "estimated_budget": Decimal("450000.00"),
            "assigned_rep_name": "Vikram Sharma",
            "converted_at": None,
            "converted_customer_id": None,
            "converted_deal_id": None,
            "notes": "Exhibition booth and catering query for dealer meet.",
            "created_at": datetime.utcnow() - timedelta(days=3),
            "updated_at": datetime.utcnow() - timedelta(days=3),
        }
    ]

    for lead in leads:
        _LEAD_STORE[lead["id"]] = lead

    # 2. Seed Deals
    deals = [
        {
            "id": "deal_cognizant_conf",
            "organization_id": org_id,
            "property_id": prop_id,
            "deal_number": "DEAL-2026-0001",
            "deal_name": "Cognizant Annual Leadership Conclave",
            "customer_id": "cust_reliance_corp",
            "customer_name": "Tata Global Technologies Ltd",
            "stage": "PROPOSAL",
            "amount": Decimal("1200000.00"),
            "probability_percent": 60,
            "weighted_amount": Decimal("720000.00"),
            "expected_close_date": datetime.utcnow() + timedelta(days=28),
            "closed_at": None,
            "assigned_rep_name": "Vikram Sharma",
            "notes": "Formal quotation sent with room and banquet package.",
            "created_at": datetime.utcnow() - timedelta(days=20),
            "updated_at": datetime.utcnow() - timedelta(days=5),
        },
        {
            "id": "deal_malhotra_wedding",
            "organization_id": org_id,
            "property_id": prop_id,
            "deal_number": "DEAL-2026-0002",
            "deal_name": "Malhotra Luxury Destination Wedding",
            "customer_id": "cust_malhotra_family",
            "customer_name": "Mr. Rajiv Malhotra",
            "stage": "NEGOTIATION",
            "amount": Decimal("2500000.00"),
            "probability_percent": 80,
            "weighted_amount": Decimal("2000000.00"),
            "expected_close_date": datetime.utcnow() + timedelta(days=12),
            "closed_at": None,
            "assigned_rep_name": "Ananya Iyer",
            "notes": "Full resort buyout for 3 days including lawn dining and royal suites.",
            "created_at": datetime.utcnow() - timedelta(days=35),
            "updated_at": datetime.utcnow() - timedelta(days=2),
        },
        {
            "id": "deal_infosys_symposium",
            "organization_id": org_id,
            "property_id": prop_id,
            "deal_number": "DEAL-2026-0003",
            "deal_name": "Q4 AI & FinTech Executive Symposium",
            "customer_id": "cust_reliance_corp",
            "customer_name": "Tata Global Technologies Ltd",
            "stage": "CLOSED_WON",
            "amount": Decimal("950000.00"),
            "probability_percent": 100,
            "weighted_amount": Decimal("950000.00"),
            "expected_close_date": datetime.utcnow() - timedelta(days=6),
            "closed_at": datetime.utcnow() - timedelta(days=6),
            "assigned_rep_name": "Vikram Sharma",
            "notes": "Contract signed, deposit received, invoice generated.",
            "created_at": datetime.utcnow() - timedelta(days=45),
            "updated_at": datetime.utcnow() - timedelta(days=6),
        }
    ]

    for deal in deals:
        _DEAL_STORE[deal["id"]] = deal

    # 3. Seed Quotes
    q1_id = "quote_cognizant_01"
    q1_lines = [
        {"id": str(uuid.uuid4()), "quote_id": q1_id, "product_id": "prod_room_suite", "description": "Presidential & Executive Suites (4 Nights)", "quantity": Decimal("4.00"), "unit_price": Decimal("150000.00"), "amount": Decimal("600000.00")},
        {"id": str(uuid.uuid4()), "quote_id": q1_id, "product_id": None, "description": "Heritage Grand Ballroom & Multi-Cuisine Banqueting", "quantity": Decimal("1.00"), "unit_price": Decimal("400000.00"), "amount": Decimal("400000.00")},
    ]
    _QUOTE_STORE[q1_id] = {
        "id": q1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "quote_number": "QT-2026-0001",
        "deal_id": "deal_cognizant_conf",
        "customer_id": "cust_reliance_corp",
        "customer_name": "Tata Global Technologies Ltd",
        "issue_date": datetime.utcnow() - timedelta(days=10),
        "valid_until": datetime.utcnow() + timedelta(days=20),
        "status": "SENT",
        "currency": "INR",
        "subtotal": Decimal("1000000.00"),
        "tax_amount": Decimal("180000.00"),
        "total_amount": Decimal("1180000.00"),
        "converted_invoice_id": None,
        "notes": "Includes complimentary audio-visual suite and airport transfers.",
        "lines": q1_lines,
        "created_at": datetime.utcnow() - timedelta(days=10),
        "updated_at": datetime.utcnow() - timedelta(days=10),
    }

    # 4. Seed Activities
    activities = [
        {
            "id": "act_call_01",
            "organization_id": org_id,
            "entity_type": "LEAD",
            "entity_id": "lead_cognizant_retreat",
            "activity_type": "CALL",
            "subject": "Discovery call with Arvind Nambiar",
            "details": "Discussed accommodation dates, audio-visual requirements, and delegate dietary preferences.",
            "due_date": datetime.utcnow() - timedelta(days=22),
            "completed_at": datetime.utcnow() - timedelta(days=22),
            "assigned_rep_name": "Vikram Sharma",
            "created_at": datetime.utcnow() - timedelta(days=23)
        },
        {
            "id": "act_meeting_02",
            "organization_id": org_id,
            "entity_type": "DEAL",
            "entity_id": "deal_malhotra_wedding",
            "activity_type": "MEETING",
            "subject": "Resort walk-through & menu tasting",
            "details": "Conducted on-site tour of royal gardens, bridal villa, and grand dining pavilions.",
            "due_date": datetime.utcnow() - timedelta(days=4),
            "completed_at": datetime.utcnow() - timedelta(days=4),
            "assigned_rep_name": "Ananya Iyer",
            "created_at": datetime.utcnow() - timedelta(days=5)
        }
    ]
    for act in activities:
        _ACTIVITY_STORE.append(act)


class CrmService:
    """Enterprise Sales CRM and Revenue Pipeline Management Service."""

    def __init__(self):
        _seed_crm_data()

    # --- Lead Management ---
    def get_leads(
        self,
        organization_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        _seed_crm_data()
        leads = list(_LEAD_STORE.values())

        if organization_id:
            leads = [l for l in leads if l["organization_id"] == organization_id]
        if status_filter:
            leads = [l for l in leads if l["status"].lower() == status_filter.lower()]

        return sorted(leads, key=lambda x: x["created_at"], reverse=True)

    def get_lead_by_id(self, lead_id: str) -> Optional[Dict[str, Any]]:
        _seed_crm_data()
        return _LEAD_STORE.get(lead_id)

    def create_lead(self, lead_in: LeadCreate, user_id: Optional[str] = None) -> Dict[str, Any]:
        _seed_crm_data()
        org_id = lead_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        lead_id = f"lead_{str(uuid.uuid4())[:8]}"

        lead_dict = {
            **lead_in.model_dump(),
            "id": lead_id,
            "organization_id": org_id,
            "estimated_budget": to_decimal(lead_in.estimated_budget),
            "converted_at": None,
            "converted_customer_id": None,
            "converted_deal_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        _LEAD_STORE[lead_id] = lead_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="CRM_LEAD_CREATED",
            resource_type="crm_lead",
            resource_id=lead_id,
            organization_id=org_id,
            details={"name": f"{lead_in.first_name} {lead_in.last_name}", "email": lead_in.email}
        )
        return lead_dict

    def update_lead(self, lead_id: str, lead_in: LeadUpdate, user_id: Optional[str] = None) -> Dict[str, Any]:
        _seed_crm_data()
        lead = _LEAD_STORE.get(lead_id)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

        updates = lead_in.model_dump(exclude_unset=True)
        if "estimated_budget" in updates and updates["estimated_budget"] is not None:
            updates["estimated_budget"] = to_decimal(updates["estimated_budget"])

        lead.update(updates)
        lead["updated_at"] = datetime.utcnow()

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="CRM_LEAD_UPDATED",
            resource_type="crm_lead",
            resource_id=lead_id,
            organization_id=lead["organization_id"],
            details=updates
        )
        return lead

    def convert_lead(
        self,
        lead_id: str,
        convert_in: LeadConvertRequest,
        user_id: Optional[str] = None
    ) -> LeadConvertResponse:
        """
        Convert qualified Lead into an active Customer and new Opportunity Deal.
        """
        _seed_crm_data()
        lead = _LEAD_STORE.get(lead_id)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

        if lead["status"] == "CONVERTED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lead has already been converted.")

        org_id = lead["organization_id"]
        full_name = f"{lead['first_name']} {lead['last_name']}".strip()
        company = lead.get("company_name") or full_name

        # 1. Create Customer record in Master Data
        cust_code = f"CUST-{str(uuid.uuid4())[:6].upper()}"
        cust_in = CustomerCreate(
            organization_id=org_id,
            property_id=lead.get("property_id"),
            code=cust_code,
            name=company,
            customer_type="CORPORATE" if lead.get("company_name") else "INDIVIDUAL",
            email=lead["email"],
            phone=lead.get("phone"),
            notes=f"Converted from Lead: {full_name} ({lead.get('job_title', 'Prospect')})"
        )
        created_cust = customer_service.create_customer(cust_in, creator_email=user_id or "system")

        # 2. Create Deal Opportunity
        deal_num = f"DEAL-{datetime.utcnow().year}-{len(_DEAL_STORE) + 1:04d}"
        deal_amt = convert_in.estimated_amount or lead.get("estimated_budget") or Decimal("100000.00")
        prob = get_default_stage_probability("QUALIFICATION")
        weighted = (deal_amt * Decimal(prob) / Decimal("100")).quantize(Decimal("0.01"))

        cust_id = created_cust.id if hasattr(created_cust, "id") else created_cust["id"]
        cust_name = created_cust.name if hasattr(created_cust, "name") else created_cust["name"]

        deal_dict = {
            "id": f"deal_{str(uuid.uuid4())[:8]}",
            "organization_id": org_id,
            "property_id": lead.get("property_id"),
            "deal_number": deal_num,
            "deal_name": convert_in.deal_name or f"{company} Opportunity",
            "customer_id": cust_id,
            "customer_name": cust_name,
            "stage": "QUALIFICATION",
            "amount": deal_amt,
            "probability_percent": prob,
            "weighted_amount": weighted,
            "expected_close_date": convert_in.expected_close_date or (datetime.utcnow() + timedelta(days=45)),
            "closed_at": None,
            "assigned_rep_name": lead.get("assigned_rep_name", "Unassigned"),
            "notes": f"Converted from Lead {full_name}.",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        _DEAL_STORE[deal_dict["id"]] = deal_dict

        # 3. Update Lead status
        lead["status"] = "CONVERTED"
        lead["converted_at"] = datetime.utcnow()
        lead["converted_customer_id"] = cust_id
        lead["converted_deal_id"] = deal_dict["id"]
        lead["updated_at"] = datetime.utcnow()

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="CRM_LEAD_CONVERTED",
            resource_type="crm_lead",
            resource_id=lead_id,
            organization_id=org_id,
            details={"customer_id": cust_id, "deal_id": deal_dict["id"]}
        )

        return LeadConvertResponse(
            lead_id=lead_id,
            customer_id=cust_id,
            customer_code=cust_code,
            deal_id=deal_dict["id"],
            deal_number=deal_num,
            status="CONVERTED"
        )

    # --- Opportunities & Deals Pipeline ---
    def get_deals(
        self,
        organization_id: Optional[str] = None,
        stage_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        _seed_crm_data()
        deals = list(_DEAL_STORE.values())

        if organization_id:
            deals = [d for d in deals if d["organization_id"] == organization_id]
        if stage_filter:
            deals = [d for d in deals if d["stage"].lower() == stage_filter.lower()]

        return sorted(deals, key=lambda x: x["expected_close_date"])

    def get_deal_by_id(self, deal_id: str) -> Optional[Dict[str, Any]]:
        _seed_crm_data()
        return _DEAL_STORE.get(deal_id)

    def create_deal(self, deal_in: DealCreate, user_id: Optional[str] = None) -> Dict[str, Any]:
        _seed_crm_data()
        org_id = deal_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        deal_id = f"deal_{str(uuid.uuid4())[:8]}"
        deal_num = deal_in.deal_number or f"DEAL-{datetime.utcnow().year}-{len(_DEAL_STORE) + 1:04d}"

        prob = deal_in.probability_percent if deal_in.probability_percent is not None else get_default_stage_probability(deal_in.stage)
        amt = to_decimal(deal_in.amount)
        weighted = (amt * Decimal(prob) / Decimal("100")).quantize(Decimal("0.01"))

        deal_dict = {
            **deal_in.model_dump(),
            "id": deal_id,
            "organization_id": org_id,
            "deal_number": deal_num,
            "amount": amt,
            "probability_percent": prob,
            "weighted_amount": weighted,
            "closed_at": datetime.utcnow() if deal_in.stage in ("CLOSED_WON", "CLOSED_LOST") else None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        _DEAL_STORE[deal_id] = deal_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="CRM_DEAL_CREATED",
            resource_type="crm_deal",
            resource_id=deal_id,
            organization_id=org_id,
            details={"deal_number": deal_num, "amount": str(amt)}
        )
        return deal_dict

    def update_deal_stage(
        self,
        deal_id: str,
        stage_req: DealStageUpdateRequest,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update stage and automatically recompute probability and weighted pipeline value."""
        _seed_crm_data()
        deal = _DEAL_STORE.get(deal_id)
        if not deal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found.")

        new_stage = stage_req.stage.upper()
        prob = stage_req.probability_percent if stage_req.probability_percent is not None else get_default_stage_probability(new_stage)
        weighted = (deal["amount"] * Decimal(prob) / Decimal("100")).quantize(Decimal("0.01"))

        deal["stage"] = new_stage
        deal["probability_percent"] = prob
        deal["weighted_amount"] = weighted
        if new_stage in ("CLOSED_WON", "CLOSED_LOST"):
            deal["closed_at"] = datetime.utcnow()
        else:
            deal["closed_at"] = None

        if stage_req.notes:
            existing = deal.get("notes") or ""
            deal["notes"] = f"{existing}\n[{datetime.utcnow().strftime('%Y-%m-%d')}] Stage changed to {new_stage}: {stage_req.notes}".strip()

        deal["updated_at"] = datetime.utcnow()

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="CRM_DEAL_STAGE_CHANGED",
            resource_type="crm_deal",
            resource_id=deal_id,
            organization_id=deal["organization_id"],
            details={"new_stage": new_stage, "probability": prob, "weighted_amount": str(weighted)}
        )
        return deal

    # --- Quotations ---
    def get_quotes(
        self,
        organization_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        _seed_crm_data()
        quotes = list(_QUOTE_STORE.values())

        if organization_id:
            quotes = [q for q in quotes if q["organization_id"] == organization_id]
        if status_filter:
            quotes = [q for q in quotes if q["status"].lower() == status_filter.lower()]

        return sorted(quotes, key=lambda x: x["issue_date"], reverse=True)

    def get_quote_by_id(self, quote_id: str) -> Optional[Dict[str, Any]]:
        _seed_crm_data()
        return _QUOTE_STORE.get(quote_id)

    def create_quote(self, quote_in: QuoteCreate, user_id: Optional[str] = None) -> Dict[str, Any]:
        _seed_crm_data()
        org_id = quote_in.organization_id or DEMO_ORGANISATIONS[0]["id"]

        if not quote_in.lines:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Quote must contain at least one line item.")

        quote_id = f"quote_{str(uuid.uuid4())[:8]}"
        quote_num = quote_in.quote_number or f"QT-{datetime.utcnow().year}-{len(_QUOTE_STORE) + 1:04d}"

        totals = calculate_invoice_totals(quote_in.lines, quote_in.tax_rate_percent)
        processed_lines = []
        for line in quote_in.lines:
            amt = (line.amount if line.amount is not None else to_decimal(line.quantity) * to_decimal(line.unit_price))
            processed_lines.append({
                "id": str(uuid.uuid4()),
                "quote_id": quote_id,
                "product_id": line.product_id,
                "description": line.description,
                "quantity": to_decimal(line.quantity),
                "unit_price": to_decimal(line.unit_price),
                "amount": amt
            })

        quote_dict = {
            "id": quote_id,
            "organization_id": org_id,
            "property_id": quote_in.property_id,
            "quote_number": quote_num,
            "deal_id": quote_in.deal_id,
            "customer_id": quote_in.customer_id,
            "customer_name": quote_in.customer_name or quote_in.customer_id,
            "issue_date": datetime.utcnow(),
            "valid_until": quote_in.valid_until,
            "status": "SENT",
            "currency": quote_in.currency,
            "subtotal": totals["subtotal"],
            "tax_amount": totals["tax_amount"],
            "total_amount": totals["total_amount"],
            "converted_invoice_id": None,
            "notes": quote_in.notes,
            "lines": processed_lines,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        _QUOTE_STORE[quote_id] = quote_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="CRM_QUOTE_CREATED",
            resource_type="crm_quote",
            resource_id=quote_id,
            organization_id=org_id,
            details={"quote_number": quote_num, "total_amount": str(totals['total_amount'])}
        )
        return quote_dict

    def convert_quote_to_invoice(self, quote_id: str, user_id: Optional[str] = None) -> QuoteConvertInvoiceResponse:
        """
        Convert an accepted quote into an official AR Customer Invoice in Finance.
        Bridges Sales and General Accounting directly.
        """
        _seed_crm_data()
        quote = _QUOTE_STORE.get(quote_id)
        if not quote:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")

        if quote["converted_invoice_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quote already converted to invoice '{quote['converted_invoice_id']}'."
            )

        inv_lines = [
            InvoiceLineCreate(
                product_id=line.get("product_id"),
                description=line["description"],
                quantity=line["quantity"],
                unit_price=line["unit_price"],
                amount=line["amount"]
            )
            for line in quote["lines"]
        ]

        # Calculate effective tax percent
        tax_pct = Decimal("0.00")
        if quote["subtotal"] > Decimal("0.00"):
            tax_pct = ((quote["tax_amount"] / quote["subtotal"]) * Decimal("100")).quantize(Decimal("0.01"))

        inv_in = CustomerInvoiceCreate(
            organization_id=quote["organization_id"],
            property_id=quote.get("property_id"),
            customer_id=quote["customer_id"],
            customer_name=quote["customer_name"],
            due_date=datetime.utcnow() + timedelta(days=30),
            currency=quote["currency"],
            tax_rate_percent=tax_pct,
            notes=f"Generated from Sales Quotation {quote['quote_number']}",
            lines=inv_lines
        )

        created_inv = finance_service.create_invoice(inv_in, user_id=user_id)

        # Mark quote accepted and link invoice
        quote["status"] = "ACCEPTED"
        quote["converted_invoice_id"] = created_inv["id"]
        quote["updated_at"] = datetime.utcnow()

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="CRM_QUOTE_CONVERTED_TO_INVOICE",
            resource_type="crm_quote",
            resource_id=quote_id,
            organization_id=quote["organization_id"],
            details={"invoice_id": created_inv["id"], "invoice_number": created_inv["invoice_number"]}
        )

        return QuoteConvertInvoiceResponse(
            quote_id=quote_id,
            invoice_id=created_inv["id"],
            invoice_number=created_inv["invoice_number"],
            status="CONVERTED"
        )

    # --- Sales Activities ---
    def get_activities(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        _seed_crm_data()
        acts = _ACTIVITY_STORE
        if organization_id:
            acts = [a for a in acts if a["organization_id"] == organization_id]
        return sorted(acts, key=lambda x: x["created_at"], reverse=True)

    def log_activity(self, activity_in: SalesActivityCreate, user_id: Optional[str] = None) -> Dict[str, Any]:
        _seed_crm_data()
        org_id = activity_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        act_id = f"act_{str(uuid.uuid4())[:8]}"

        act_dict = {
            **activity_in.model_dump(),
            "id": act_id,
            "organization_id": org_id,
            "completed_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        _ACTIVITY_STORE.insert(0, act_dict)
        return act_dict

    # --- Pipeline Analytics & Forecasting ---
    def get_pipeline_metrics(self, organization_id: Optional[str] = None) -> SalesPipelineMetricsResponse:
        _seed_crm_data()
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        deals = [d for d in _DEAL_STORE.values() if d["organization_id"] == org_id]

        total_active, weighted_val = calculate_weighted_pipeline(deals)

        won_deals = [d for d in deals if d["stage"] == "CLOSED_WON"]
        lost_deals = [d for d in deals if d["stage"] == "CLOSED_LOST"]
        open_deals = [d for d in deals if d["stage"] not in ("CLOSED_WON", "CLOSED_LOST")]

        win_rate = calculate_win_rate(len(won_deals), len(lost_deals))

        # Breakdown by stage
        stages_order = ["QUALIFICATION", "NEEDS_ANALYSIS", "PROPOSAL", "NEGOTIATION", "CLOSED_WON", "CLOSED_LOST"]
        stage_metrics = []
        for st in stages_order:
            st_deals = [d for d in deals if d["stage"] == st]
            s_tot = sum((d["amount"] for d in st_deals), Decimal("0.00"))
            s_weight = sum((d["weighted_amount"] for d in st_deals), Decimal("0.00"))
            stage_metrics.append(StageMetric(
                stage=st,
                count=len(st_deals),
                total_value=s_tot,
                weighted_value=s_weight
            ))

        return SalesPipelineMetricsResponse(
            organization_id=org_id,
            total_active_pipeline_value=total_active,
            weighted_forecast_value=weighted_val,
            win_rate_percentage=win_rate,
            open_deals_count=len(open_deals),
            closed_won_count=len(won_deals),
            closed_lost_count=len(lost_deals),
            stages=stage_metrics
        )


crm_service = CrmService()
