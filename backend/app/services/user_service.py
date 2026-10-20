"""Victory Crest One - User & Identity Management Service
Handles user authentication, Argon2 verification, user provisioning, and role cataloging.
"""

from typing import List, Dict, Any, Optional
import uuid
from fastapi import HTTPException, status

from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.core.config import settings
from backend.app.schemas.user import UserSummary, TokenResponse, UserCreate
from backend.app.services.audit_service import audit_service
from shared.enums import UserRole
from shared.constants import DEMO_ORGANISATIONS

# In-memory user store seeded with standard enterprise accounts and Argon2 hashes
_USER_STORE: Dict[str, Dict[str, Any]] = {}


def _seed_initial_users():
    """Seed standard enterprise demonstration accounts with Argon2 hashes."""
    if _USER_STORE:
        return

    demo_org_id = DEMO_ORGANISATIONS[0]["id"]
    demo_props = DEMO_ORGANISATIONS[0]["properties"]
    
    users_data = [
        {
            "id": "usr_system_admin",
            "email": "admin@victorycrest.internal",
            "username": "admin",
            "password": "AdminPassword123!",
            "full_name": "Chief Enterprise Administrator",
            "role": UserRole.SYSTEM_ADMIN.value,
            "primary_organization_id": demo_org_id,
            "primary_property_id": demo_props[0]["id"],
            "is_superuser": True
        },
        {
            "id": "usr_hotel_manager",
            "email": "hotel.manager@victorycrest.internal",
            "username": "hotel_gm",
            "password": "HotelPassword123!",
            "full_name": "Madurai General Manager",
            "role": UserRole.HOTEL_MANAGER.value,
            "primary_organization_id": demo_org_id,
            "primary_property_id": demo_props[0]["id"],
            "is_superuser": False
        },
        {
            "id": "usr_accountant",
            "email": "accountant@victorycrest.internal",
            "username": "accountant",
            "password": "AccountantPass123!",
            "full_name": "Senior Corporate Accountant",
            "role": UserRole.ACCOUNTANT.value,
            "primary_organization_id": demo_org_id,
            "primary_property_id": demo_props[3]["id"],  # Corporate HQ
            "is_superuser": False
        },
        {
            "id": "usr_auditor",
            "email": "auditor@victorycrest.internal",
            "username": "auditor",
            "password": "AuditorPass123!",
            "full_name": "Compliance & Audit Specialist",
            "role": UserRole.AUDITOR.value,
            "primary_organization_id": demo_org_id,
            "primary_property_id": demo_props[3]["id"],
            "is_superuser": False
        },
        {
            "id": "usr_pos_cashier",
            "email": "cashier@victorycrest.internal",
            "username": "cashier_mdu",
            "password": "CashierPass123!",
            "full_name": "Front Desk Cashier",
            "role": UserRole.POS_CASHIER.value,
            "primary_organization_id": demo_org_id,
            "primary_property_id": demo_props[0]["id"],
            "is_superuser": False
        },
        {
            "id": "usr_readonly",
            "email": "readonly@victorycrest.internal",
            "username": "readonly",
            "password": "ReadOnlyPass123!",
            "full_name": "Board Observer",
            "role": UserRole.READ_ONLY.value,
            "primary_organization_id": demo_org_id,
            "primary_property_id": demo_props[0]["id"],
            "is_superuser": False
        }
    ]

    for u in users_data:
        _USER_STORE[u["username"]] = {
            "id": u["id"],
            "email": u["email"],
            "username": u["username"],
            "hashed_password": hash_password(u["password"]),
            "full_name": u["full_name"],
            "role": u["role"],
            "primary_organization_id": u["primary_organization_id"],
            "primary_property_id": u["primary_property_id"],
            "is_active": True,
            "is_superuser": u["is_superuser"]
        }


# Initialize seed data
_seed_initial_users()


class UserService:
    """Service handling identity verification, user creation, and role inspection."""

    @staticmethod
    def authenticate(
        username_or_email: str,
        password: str,
        ip_address: str = "127.0.0.1"
    ) -> TokenResponse:
        """Verify user credentials with Argon2 and issue JWT token."""
        _seed_initial_users()
        user_record = None

        # Search by username or email
        for user in _USER_STORE.values():
            if user["username"].lower() == username_or_email.lower() or user["email"].lower() == username_or_email.lower():
                user_record = user
                break

        if not user_record or not verify_password(password, user_record["hashed_password"]):
            audit_service.record_event(
                action="LOGIN_FAILED",
                entity_type="User",
                entity_id=None,
                user_email=username_or_email,
                details="Invalid username or password attempt",
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        if not user_record.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        # Create JWT access token
        token_payload = {
            "sub": user_record["id"],
            "username": user_record["username"],
            "email": user_record["email"],
            "role": user_record["role"],
            "org_id": user_record["primary_organization_id"],
            "prop_id": user_record["primary_property_id"]
        }
        token = create_access_token(token_payload)

        audit_service.record_event(
            action="LOGIN_SUCCESS",
            entity_type="User",
            entity_id=user_record["id"],
            user_email=user_record["email"],
            organization_id=user_record["primary_organization_id"],
            property_id=user_record["primary_property_id"],
            details="Successful authentication",
            ip_address=ip_address
        )

        user_summary = UserSummary(
            id=user_record["id"],
            email=user_record["email"],
            username=user_record["username"],
            full_name=user_record["full_name"],
            role=user_record["role"],
            primary_organization_id=user_record["primary_organization_id"],
            primary_property_id=user_record["primary_property_id"],
            is_active=user_record["is_active"],
            is_superuser=user_record["is_superuser"]
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=user_summary
        )

    @staticmethod
    def create_user(user_create: UserCreate, creator_email: str = "admin") -> UserSummary:
        """Create a new user with Argon2 password hashing and audit log."""
        _seed_initial_users()
        
        # Check uniqueness
        for u in _USER_STORE.values():
            if u["username"].lower() == user_create.username.lower():
                raise HTTPException(status_code=400, detail="Username already exists")
            if u["email"].lower() == user_create.email.lower():
                raise HTTPException(status_code=400, detail="Email already registered")

        new_id = str(uuid.uuid4())
        hashed = hash_password(user_create.password)

        record = {
            "id": new_id,
            "email": user_create.email,
            "username": user_create.username,
            "hashed_password": hashed,
            "full_name": user_create.full_name,
            "role": user_create.role,
            "primary_organization_id": user_create.organization_id or DEMO_ORGANISATIONS[0]["id"],
            "primary_property_id": user_create.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"],
            "is_active": True,
            "is_superuser": user_create.role == UserRole.SYSTEM_ADMIN.value
        }
        _USER_STORE[user_create.username] = record

        audit_service.record_event(
            action="USER_CREATED",
            entity_type="User",
            entity_id=new_id,
            user_email=creator_email,
            organization_id=record["primary_organization_id"],
            details=f"Created user '{user_create.username}' with role '{user_create.role}'"
        )

        return UserSummary(**record)

    @staticmethod
    def list_users(organization_id: Optional[str] = None) -> List[UserSummary]:
        _seed_initial_users()
        users = list(_USER_STORE.values())
        if organization_id:
            users = [u for u in users if u["primary_organization_id"] == organization_id]
        return [UserSummary(**u) for u in users]

    @staticmethod
    def list_roles() -> List[Dict[str, Any]]:
        return [{"role": r.value} for r in UserRole]


user_service = UserService()
