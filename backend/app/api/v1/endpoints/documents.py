"""Victory Crest One - Document Vault Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, Body
from backend.app.schemas.master_data import DocumentOut
from backend.app.services.master_data_service import document_service
from backend.app.core.permissions import get_current_user

router = APIRouter(prefix="/documents", tags=["Document Vault"])


@router.get(
    "",
    response_model=List[DocumentOut],
    summary="List Stored Documents",
    description="Returns document vault records scoped to organization."
)
def list_documents(
    organization_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return document_service.list_documents(org_id, category=category)


@router.post(
    "/register",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register Document Metadata",
    description="Registers a new document in the secure vault."
)
def register_document(
    file_name: str = Body(..., embed=True),
    category: str = Body("GENERAL", embed=True),
    linked_entity_type: Optional[str] = Body(None, embed=True),
    linked_entity_id: Optional[str] = Body(None, embed=True),
    user: dict = Depends(get_current_user)
):
    return document_service.register_document(
        file_name=file_name,
        category=category,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
        uploader_email=user.get("email", "admin@victorycrest.internal"),
        organization_id=user.get("org_id"),
        property_id=user.get("prop_id")
    )
