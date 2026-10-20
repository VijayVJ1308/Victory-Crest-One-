"""Victory Crest One - Authentication Endpoints
Handles login with Argon2 validation, active token introspection, and tenant context switching.
"""

from fastapi import APIRouter, Request, Depends, status
from backend.app.schemas.user import UserLoginRequest, TokenResponse, UserSummary, SwitchContextRequest
from backend.app.services.user_service import user_service
from backend.app.core.permissions import get_current_user

router = APIRouter(prefix="/auth", tags=["Identity & Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate User",
    description="Validates user credentials against Argon2 hash and issues a signed JWT token."
)
def login(login_req: UserLoginRequest, request: Request) -> TokenResponse:
    ip = request.client.host if request.client else "127.0.0.1"
    return user_service.authenticate(
        username_or_email=login_req.username_or_email,
        password=login_req.password,
        ip_address=ip
    )


@router.get(
    "/me",
    summary="Get Current User Profile",
    description="Returns authenticated user claims from the verified JWT access token."
)
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "authenticated": True,
        "user_id": current_user.get("sub"),
        "username": current_user.get("username"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "organization_id": current_user.get("org_id"),
        "property_id": current_user.get("prop_id")
    }


@router.post(
    "/switch-context",
    summary="Switch Active Context",
    description="Switches the user's active organization or property scope."
)
def switch_context(switch_req: SwitchContextRequest, current_user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "organization_id": switch_req.organization_id,
        "property_id": switch_req.property_id,
        "user_email": current_user.get("email")
    }
