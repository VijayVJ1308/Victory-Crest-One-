"""Victory Crest One - Sales CRM & Revenue Pipeline API Endpoints
Leads, Opportunities/Deals, Quotations, Sales Activities, and Pipeline Forecasting.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from backend.app.schemas.crm import (
    LeadCreate, LeadUpdate, LeadOut, LeadConvertRequest, LeadConvertResponse,
    DealCreate, DealUpdate, DealOut, DealStageUpdateRequest,
    QuoteCreate, QuoteOut, QuoteConvertInvoiceResponse,
    SalesActivityCreate, SalesActivityOut,
    SalesPipelineMetricsResponse
)
from backend.app.services.crm_service import crm_service
from backend.app.core.permissions import get_current_user

router = APIRouter(prefix="/crm", tags=["Sales CRM & Revenue Pipeline"])


# --- Leads Endpoints ---
@router.get(
    "/leads",
    response_model=List[LeadOut],
    summary="List Sales Leads",
    description="Returns leads filtered optionally by organization and status."
)
def list_leads(
    organization_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return crm_service.get_leads(organization_id=org_id, status_filter=status_filter)


@router.post(
    "/leads",
    response_model=LeadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Capture New Sales Lead"
)
def create_lead(
    lead_in: LeadCreate,
    user: dict = Depends(get_current_user)
):
    return crm_service.create_lead(lead_in, user_id=user.get("user_id"))


@router.get(
    "/leads/{lead_id}",
    response_model=LeadOut,
    summary="Get Lead Details"
)
def get_lead(lead_id: str, user: dict = Depends(get_current_user)):
    lead = crm_service.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    return lead


@router.put(
    "/leads/{lead_id}",
    response_model=LeadOut,
    summary="Update Lead"
)
def update_lead(
    lead_id: str,
    lead_in: LeadUpdate,
    user: dict = Depends(get_current_user)
):
    return crm_service.update_lead(lead_id, lead_in, user_id=user.get("user_id"))


@router.post(
    "/leads/{lead_id}/convert",
    response_model=LeadConvertResponse,
    summary="Convert Lead to Opportunity & Customer",
    description="Converts qualified lead into an active Customer Master record and opens a pipeline Deal."
)
def convert_lead(
    lead_id: str,
    convert_in: LeadConvertRequest,
    user: dict = Depends(get_current_user)
):
    return crm_service.convert_lead(lead_id, convert_in, user_id=user.get("user_id"))


# --- Opportunities & Deals Pipeline Endpoints ---
@router.get(
    "/deals",
    response_model=List[DealOut],
    summary="List Opportunity Deals",
    description="Returns pipeline deals filtered optionally by stage."
)
def list_deals(
    organization_id: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return crm_service.get_deals(organization_id=org_id, stage_filter=stage)


@router.post(
    "/deals",
    response_model=DealOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Opportunity Deal"
)
def create_deal(
    deal_in: DealCreate,
    user: dict = Depends(get_current_user)
):
    return crm_service.create_deal(deal_in, user_id=user.get("user_id"))


@router.get(
    "/deals/{deal_id}",
    response_model=DealOut,
    summary="Get Deal Details"
)
def get_deal(deal_id: str, user: dict = Depends(get_current_user)):
    deal = crm_service.get_deal_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found.")
    return deal


@router.patch(
    "/deals/{deal_id}/stage",
    response_model=DealOut,
    summary="Update Deal Stage",
    description="Advances deal through pipeline stages and recalculates weighted probability."
)
def update_deal_stage(
    deal_id: str,
    stage_req: DealStageUpdateRequest,
    user: dict = Depends(get_current_user)
):
    return crm_service.update_deal_stage(deal_id, stage_req, user_id=user.get("user_id"))


# --- Quotations Endpoints ---
@router.get(
    "/quotes",
    response_model=List[QuoteOut],
    summary="List Quotations"
)
def list_quotes(
    organization_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return crm_service.get_quotes(organization_id=org_id, status_filter=status_filter)


@router.post(
    "/quotes",
    response_model=QuoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Commercial Quotation"
)
def create_quote(
    quote_in: QuoteCreate,
    user: dict = Depends(get_current_user)
):
    return crm_service.create_quote(quote_in, user_id=user.get("user_id"))


@router.get(
    "/quotes/{quote_id}",
    response_model=QuoteOut,
    summary="Get Quotation Details"
)
def get_quote(quote_id: str, user: dict = Depends(get_current_user)):
    quote = crm_service.get_quote_by_id(quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")
    return quote


@router.post(
    "/quotes/{quote_id}/convert-invoice",
    response_model=QuoteConvertInvoiceResponse,
    summary="Convert Accepted Quote to Finance AR Invoice",
    description="Transitions quotation to accepted and creates formal AR Customer Invoice with GL journal."
)
def convert_quote_to_invoice(
    quote_id: str,
    user: dict = Depends(get_current_user)
):
    return crm_service.convert_quote_to_invoice(quote_id, user_id=user.get("user_id"))


# --- Sales Activities Endpoints ---
@router.get(
    "/activities",
    response_model=List[SalesActivityOut],
    summary="List Sales Activities & Interaction Logs"
)
def list_activities(
    organization_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return crm_service.get_activities(organization_id=org_id)


@router.post(
    "/activities",
    response_model=SalesActivityOut,
    status_code=status.HTTP_201_CREATED,
    summary="Log Sales Activity (Call, Meeting, Task)"
)
def log_activity(
    activity_in: SalesActivityCreate,
    user: dict = Depends(get_current_user)
):
    return crm_service.log_activity(activity_in, user_id=user.get("user_id"))


# --- Pipeline Forecasting & Metrics ---
@router.get(
    "/metrics",
    response_model=SalesPipelineMetricsResponse,
    summary="Get Sales Pipeline Forecast Metrics",
    description="Returns total active pipeline value, weighted forecast value, win rate, and stage breakdown."
)
def get_pipeline_metrics(
    organization_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return crm_service.get_pipeline_metrics(organization_id=org_id)
