"""Victory Crest One - Role-Based Access Control (RBAC) & Permissions Engine
Implements granular permission matrices, separation of duties checks, and server-side authorization dependencies.
"""

from typing import List, Dict, Set, Optional, Callable, Any
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from shared.enums import UserRole, PermissionAction, ModuleType
from backend.app.core.security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)


# Default Domain Permission Mapping for Enterprise Roles
ROLE_PERMISSIONS: Dict[str, Dict[str, Set[str]]] = {
    UserRole.SYSTEM_ADMIN.value: {
        "*": {a.value for a in PermissionAction}  # Superuser access across all modules
    },
    UserRole.ORG_OWNER.value: {
        "*": {a.value for a in PermissionAction}
    },
    UserRole.GROUP_GM.value: {
        "*": {
            PermissionAction.VIEW.value,
            PermissionAction.EXPORT.value,
            PermissionAction.APPROVE.value,
            PermissionAction.REJECT.value,
            PermissionAction.ACCESS_SENSITIVE.value
        }
    },
    UserRole.GENERAL_MANAGER.value: {
        "*": {
            PermissionAction.VIEW.value,
            PermissionAction.CREATE.value,
            PermissionAction.EDIT.value,
            PermissionAction.SUBMIT.value,
            PermissionAction.APPROVE.value,
            PermissionAction.REJECT.value,
            PermissionAction.EXPORT.value
        }
    },
    UserRole.FINANCE_MANAGER.value: {
        ModuleType.FINANCE.value: {a.value for a in PermissionAction if a != PermissionAction.DELETE},
        ModuleType.ACCOUNTING.value: {a.value for a in PermissionAction if a != PermissionAction.DELETE},
        ModuleType.PAYROLL.value: {PermissionAction.VIEW.value, PermissionAction.APPROVE.value, PermissionAction.EXPORT.value},
        ModuleType.DASHBOARD.value: {PermissionAction.VIEW.value, PermissionAction.EXPORT.value},
        ModuleType.BI.value: {PermissionAction.VIEW.value, PermissionAction.EXPORT.value},
    },
    UserRole.ACCOUNTANT.value: {
        ModuleType.FINANCE.value: {
            PermissionAction.VIEW.value,
            PermissionAction.CREATE.value,
            PermissionAction.EDIT.value,
            PermissionAction.SUBMIT.value,
            PermissionAction.EXPORT.value
            # Note: Cannot APPROVE (Separation of duties requires Finance Manager)
        },
        ModuleType.ACCOUNTING.value: {
            PermissionAction.VIEW.value,
            PermissionAction.CREATE.value,
            PermissionAction.EDIT.value,
            PermissionAction.SUBMIT.value,
            PermissionAction.EXPORT.value
        },
        ModuleType.DASHBOARD.value: {PermissionAction.VIEW.value},
    },
    UserRole.SALES_MANAGER.value: {
        ModuleType.SALES.value: {a.value for a in PermissionAction},
        ModuleType.MARKETING.value: {PermissionAction.VIEW.value, PermissionAction.EXPORT.value},
        ModuleType.COMMERCE.value: {PermissionAction.VIEW.value, PermissionAction.EXPORT.value},
        ModuleType.DASHBOARD.value: {PermissionAction.VIEW.value, PermissionAction.EXPORT.value},
    },
    UserRole.SALES_REP.value: {
        ModuleType.SALES.value: {
            PermissionAction.VIEW.value,
            PermissionAction.CREATE.value,
            PermissionAction.EDIT.value,
            PermissionAction.SUBMIT.value
        },
        ModuleType.DASHBOARD.value: {PermissionAction.VIEW.value},
    },
    UserRole.HOTEL_MANAGER.value: {
        ModuleType.HOTEL.value: {a.value for a in PermissionAction},
        ModuleType.RESTAURANT.value: {PermissionAction.VIEW.value, PermissionAction.APPROVE.value, PermissionAction.EXPORT.value},
        ModuleType.SERVICE.value: {PermissionAction.VIEW.value, PermissionAction.CREATE.value, PermissionAction.EDIT.value},
        ModuleType.DASHBOARD.value: {PermissionAction.VIEW.value, PermissionAction.EXPORT.value},
    },
    UserRole.RECEPTIONIST.value: {
        ModuleType.HOTEL.value: {
            PermissionAction.VIEW.value,
            PermissionAction.CREATE.value,
            PermissionAction.EDIT.value
            # Cannot DELETE or APPROVE exceptional adjustments
        },
        ModuleType.DASHBOARD.value: {PermissionAction.VIEW.value},
    },
    UserRole.RESTAURANT_MANAGER.value: {
        ModuleType.RESTAURANT.value: {a.value for a in PermissionAction},
        ModuleType.POS.value: {PermissionAction.VIEW.value, PermissionAction.CREATE.value, PermissionAction.EDIT.value, PermissionAction.APPROVE.value},
        ModuleType.INVENTORY.value: {PermissionAction.VIEW.value, PermissionAction.SUBMIT.value},
        ModuleType.DASHBOARD.value: {PermissionAction.VIEW.value},
    },
    UserRole.POS_CASHIER.value: {
        ModuleType.POS.value: {
            PermissionAction.VIEW.value,
            PermissionAction.CREATE.value,
            PermissionAction.EDIT.value
        },
        ModuleType.RESTAURANT.value: {PermissionAction.VIEW.value, PermissionAction.CREATE.value},
    },
    UserRole.AUDITOR.value: {
        "*": {
            PermissionAction.VIEW.value,
            PermissionAction.EXPORT.value,
            PermissionAction.ACCESS_SENSITIVE.value
            # Explicitly CANNOT CREATE, EDIT, or DELETE any records
        }
    },
    UserRole.READ_ONLY.value: {
        "*": {
            PermissionAction.VIEW.value,
            PermissionAction.EXPORT.value
        }
    }
}


def has_permission(
    role: str,
    action: PermissionAction,
    module: str
) -> bool:
    """
    Evaluate if a role is authorized to perform action on module.
    Enforces wildcards and separation of duties.
    """
    perms_for_role = ROLE_PERMISSIONS.get(role)
    if not perms_for_role:
        return False

    # Check wildcard module permission
    if "*" in perms_for_role:
        if action.value in perms_for_role["*"]:
            return True

    # Check module-specific permission
    if module in perms_for_role:
        if action.value in perms_for_role[module]:
            return True

    return False


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> Dict[str, Any]:
    """FastAPI dependency extracting and verifying user token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload


def require_permission(action: PermissionAction, module: str) -> Callable:
    """FastAPI route decorator enforcing server-side RBAC authorization."""
    async def permission_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role", UserRole.READ_ONLY.value)
        if not has_permission(user_role, action, module):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user_role}' lacks '{action.value}' permission for module '{module}'"
            )
        return user
    return permission_checker
