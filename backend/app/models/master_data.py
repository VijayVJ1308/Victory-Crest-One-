"""Victory Crest One - Shared Master Data Models
Canonical models for Customers, Suppliers, Products & Services, Documents, and Notifications.
Shared across CRM, POS, Commerce, Hotel PMS, Dining, ERP, and Finance modules.
"""

from sqlalchemy import Column, String, Boolean, Integer, Numeric, ForeignKey, Text, DateTime
from datetime import datetime
from backend.app.models.base import Base, BaseModelMixin


class Customer(Base, BaseModelMixin):
    """Canonical customer and account entity."""
    __tablename__ = "customers"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)
    
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    customer_type = Column(String(30), default="INDIVIDUAL", nullable=False)  # INDIVIDUAL, CORPORATE
    
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(30), nullable=True, index=True)
    
    billing_address = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    tax_identifier = Column(String(50), nullable=True)
    
    loyalty_points = Column(Integer, default=0, nullable=False)
    credit_limit = Column(Numeric(12, 2), default=0.00, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)


class Supplier(Base, BaseModelMixin):
    """Vendor and supplier master entity for procurement and supply chain."""
    __tablename__ = "suppliers"

    organization_id = Column(String(36), nullable=False, index=True)
    
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    contact_person = Column(String(100), nullable=True)
    
    email = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    tax_identifier = Column(String(50), nullable=True)
    
    payment_terms_days = Column(Integer, default=30, nullable=False)
    lead_time_days = Column(Integer, default=5, nullable=False)
    rating = Column(Numeric(3, 2), default=5.00, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class ProductMaster(Base, BaseModelMixin):
    """Canonical catalog of products, services, raw materials, and recipes."""
    __tablename__ = "products"

    organization_id = Column(String(36), nullable=False, index=True)
    
    sku = Column(String(50), unique=True, nullable=False, index=True)
    barcode = Column(String(50), nullable=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    item_type = Column(String(30), default="PHYSICAL", nullable=False)  # PHYSICAL, SERVICE, RAW_MATERIAL, RECIPE_DISH
    
    unit_of_measure = Column(String(20), default="UNIT", nullable=False)  # UNIT, NIGHT, KG, LITER, HOUR
    unit_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=18.00, nullable=False)
    
    reorder_threshold = Column(Integer, default=10, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class DocumentMetadata(Base, BaseModelMixin):
    """Secure document vault metadata linked to cross-module business records."""
    __tablename__ = "documents"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)
    
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    mime_type = Column(String(100), default="application/octet-stream", nullable=False)
    category = Column(String(50), default="GENERAL", nullable=False)  # INVOICE, CONTRACT, ID_PROOF, REPORT, GENERAL
    
    linked_entity_type = Column(String(50), nullable=True, index=True)  # Customer, Supplier, Reservation, Invoice
    linked_entity_id = Column(String(36), nullable=True, index=True)
    version = Column(Integer, default=1, nullable=False)
    uploaded_by_email = Column(String(255), nullable=False)


class Notification(Base, BaseModelMixin):
    """In-app enterprise notification and workflow alert."""
    __tablename__ = "notifications"

    organization_id = Column(String(36), nullable=False, index=True)
    
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(30), default="INFO", nullable=False)  # INFO, WARNING, ALERT, APPROVAL
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    
    target_user_id = Column(String(36), nullable=True, index=True)
    target_role = Column(String(50), nullable=True, index=True)
    link_url = Column(String(255), nullable=True)
