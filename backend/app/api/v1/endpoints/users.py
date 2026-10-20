"""Victory Crest One - Users & Roles Management Endpoints
Administer enterprise user directory, RBAC roles, and property assignments.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from backend.app.schemas.user import UserSummary, UserCreate
from backend.app.services.user_service import user_service
from backend.app.core.permissions import require_permission, get_current_user
from shared.enums import PermissionAction, ModuleType

router = APIRouter(tags=["User Management & RBAC"])


@router.get(
    "/users",
    response_model=List[UserSummary],
    summary="List Organization Users",
    description="Returns users belonging to the active organization."
)
def list_users(
    organization_id: Optional[str] = Query(None),
    user: dict = Depends(require_permission(PermissionAction.VIEW, ModuleType.SETTINGS.value))
):
    org_id = organization_id or user.get("org_id")
    return user_service.list_users(org_id)


@router.post(
    "/users",
    response_model=UserSummary,
    summary="Provision New User",
    description="Creates a new enterprise user account with Argon2 password hashing."
)
def create_user(
    user_in: UserCreate,
    user: dict = Depends(require_permission(PermissionAction.MANAGE_USERS, ModuleType.SETTINGS.value))
):
    return user_service.create_user(user_in, creator_email=user.get("email", "admin"))


@router.get(
    "/roles",
    summary="List Enterprise Roles",
    description="Returns all 30 enterprise roles and their domain scopes."
)
def list_roles():
    return user_service.list_roles()
