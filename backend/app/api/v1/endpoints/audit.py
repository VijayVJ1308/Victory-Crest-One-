"""Victory Crest One - Audit Trail Endpoints
Inspect immutable records of administrative, security, and transaction events.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from backend.app.schemas.user import AuditLogOut
from backend.app.services.audit_service import audit_service
from backend.app.core.permissions import require_permission
from shared.enums import PermissionAction, ModuleType

router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])


@router.get(
    "/logs",
    response_model=List[AuditLogOut],
    summary="Retrieve Audit Trail",
    description="Returns immutable system and security event logs. Requires access_sensitive permission on settings."
)
def get_audit_logs(
    organization_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(require_permission(PermissionAction.ACCESS_SENSITIVE, ModuleType.SETTINGS.value))
):
    org_id = organization_id or user.get("org_id")
    return audit_service.get_logs(org_id, limit=limit)
