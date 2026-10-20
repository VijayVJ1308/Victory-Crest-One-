"""Victory Crest One - User & RBAC Security Models
Role-Based Access Control and user property permissions.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, BaseModelMixin


class User(Base, BaseModelMixin):
    """User account entity."""
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    phone_number = Column(String(30), nullable=True)

    # Scoping
    primary_organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    primary_property_id = Column(String(36), ForeignKey("properties.id", ondelete="SET NULL"), nullable=True)


class Role(Base, BaseModelMixin):
    """Role definition entity."""
    __tablename__ = "roles"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)
