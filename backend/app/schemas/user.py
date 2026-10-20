"""Victory Crest One - User & Authentication Schemas
Pydantic schemas for authentication requests, JWT tokens, user creation, and audit trails.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str


class UserSummary(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: str
    primary_organization_id: Optional[str] = None
    primary_property_id: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserSummary


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=8)
    full_name: str
    role: str
    organization_id: Optional[str] = None
    property_id: Optional[str] = None


class SwitchContextRequest(BaseModel):
    organization_id: str
    property_id: Optional[str] = None


class AuditLogOut(BaseModel):
    id: str
    organization_id: Optional[str] = None
    property_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
