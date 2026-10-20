"""Victory Crest One - Supplier Master Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from backend.app.schemas.master_data import SupplierCreate, SupplierOut
from backend.app.services.master_data_service import supplier_service
from backend.app.core.permissions import get_current_user

router = APIRouter(prefix="/suppliers", tags=["Supplier Master"])


@router.get(
    "",
    response_model=List[SupplierOut],
    summary="List Suppliers & Vendors",
    description="Returns vendor master records scoped to active organization."
)
def list_suppliers(
    organization_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return supplier_service.list_suppliers(org_id)


@router.post(
    "",
    response_model=SupplierOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register Supplier"
)
def create_supplier(
    supplier_in: SupplierCreate,
    user: dict = Depends(get_current_user)
):
    return supplier_service.create_supplier(supplier_in, creator_email=user.get("email", "admin"))


@router.get(
    "/{supplier_id}",
    response_model=SupplierOut,
    summary="Get Supplier Details"
)
def get_supplier(supplier_id: str, user: dict = Depends(get_current_user)):
    return supplier_service.get_supplier(supplier_id)
