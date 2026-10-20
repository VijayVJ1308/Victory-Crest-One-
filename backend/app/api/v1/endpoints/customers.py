"""Victory Crest One - Customer Master Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from backend.app.schemas.master_data import CustomerCreate, CustomerOut
from backend.app.services.master_data_service import customer_service
from backend.app.core.permissions import require_permission, get_current_user
from shared.enums import PermissionAction, ModuleType

router = APIRouter(prefix="/customers", tags=["Customer Master"])


@router.get(
    "",
    response_model=List[CustomerOut],
    summary="List Customers & Corporate Accounts",
    description="Returns customer master records scoped to active organization."
)
def list_customers(
    organization_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return customer_service.list_customers(org_id)


@router.post(
    "",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register Customer",
    description="Registers new customer or corporate account with deduplication validation."
)
def create_customer(
    customer_in: CustomerCreate,
    user: dict = Depends(get_current_user)
):
    return customer_service.create_customer(customer_in, creator_email=user.get("email", "admin"))


@router.get(
    "/{customer_id}",
    response_model=CustomerOut,
    summary="Get Customer Details"
)
def get_customer(customer_id: str, user: dict = Depends(get_current_user)):
    return customer_service.get_customer(customer_id)
