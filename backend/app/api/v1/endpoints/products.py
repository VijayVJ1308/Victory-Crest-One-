"""Victory Crest One - Product & Service Master Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from backend.app.schemas.master_data import ProductCreate, ProductOut
from backend.app.services.master_data_service import product_service
from backend.app.core.permissions import get_current_user

router = APIRouter(prefix="/products", tags=["Product Master"])


@router.get(
    "",
    response_model=List[ProductOut],
    summary="List Products & Services",
    description="Returns canonical product, service, dish, and raw material catalog."
)
def list_products(
    organization_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return product_service.list_products(org_id)


@router.post(
    "",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product or Service"
)
def create_product(
    product_in: ProductCreate,
    user: dict = Depends(get_current_user)
):
    return product_service.create_product(product_in, creator_email=user.get("email", "admin"))


@router.get(
    "/{product_id}",
    response_model=ProductOut,
    summary="Get Product Details"
)
def get_product(product_id: str, user: dict = Depends(get_current_user)):
    return product_service.get_product(product_id)
