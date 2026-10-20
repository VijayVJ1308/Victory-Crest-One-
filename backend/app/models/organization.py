"""Victory Crest One - Organization & Multi-Tenancy Models
Core hierarchy: Organisation -> LegalEntity -> Property/Branch -> Department.
Enforces multi-tenant data isolation and property-level scoping.
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, BaseModelMixin


class Organization(Base, BaseModelMixin):
    """Top-level enterprise tenant entity."""
    __tablename__ = "organizations"

    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    legal_name = Column(String(200), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    tax_identifier = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_simulated = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    properties = relationship("Property", back_populates="organization", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")


class Property(Base, BaseModelMixin):
    """Specific hotel, resort, branch, restaurant, or retail store belonging to an organization."""
    __tablename__ = "properties"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    property_type = Column(String(50), nullable=False)  # hotel, resort, restaurant, retail_store, corporate_office
    status = Column(String(50), default="active", nullable=False)
    
    # Address details
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default="India")
    postal_code = Column(String(20), nullable=True)

    rooms_count = Column(Integer, default=0, nullable=False)
    is_simulated = Column(Boolean, default=False, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="properties")


class Department(Base, BaseModelMixin):
    """Organizational functional division (Finance, Front Office, Housekeeping, IT, Sales, etc.)."""
    __tablename__ = "departments"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    organization = relationship("Organization", back_populates="departments")
