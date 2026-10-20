"""Victory Crest One - Master Data Schemas
Pydantic DTOs for Customer Master, Supplier Master, Products & Services, Documents, and Notifications.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CustomerBase(BaseModel):
    name: str
    code: str
    customer_type: str = "INDIVIDUAL"
    email: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    tax_identifier: Optional[str] = None
    loyalty_points: int = 0
    credit_limit: Decimal = Decimal("0.00")
    currency: str = "INR"
    is_active: bool = True
    notes: Optional[str] = None
    property_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CustomerCreate(CustomerBase):
    organization_id: Optional[str] = None


class CustomerOut(CustomerBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplierBase(BaseModel):
    name: str
    code: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_identifier: Optional[str] = None
    payment_terms_days: int = 30
    lead_time_days: int = 5
    rating: Decimal = Decimal("5.00")
    currency: str = "INR"
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class SupplierCreate(SupplierBase):
    organization_id: Optional[str] = None


class SupplierOut(SupplierBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    sku: str
    barcode: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: str
    item_type: str = "PHYSICAL"
    unit_of_measure: str = "UNIT"
    unit_price: Decimal
    cost_price: Decimal = Decimal("0.00")
    tax_rate_percent: Decimal = Decimal("18.00")
    reorder_threshold: int = 10
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(ProductBase):
    organization_id: Optional[str] = None


class ProductOut(ProductBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentOut(BaseModel):
    id: str
    organization_id: str
    property_id: Optional[str] = None
    file_name: str
    file_path: str
    file_size_bytes: int
    mime_type: str
    category: str
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[str] = None
    version: int
    uploaded_by_email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationOut(BaseModel):
    id: str
    organization_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    target_user_id: Optional[str] = None
    target_role: Optional[str] = None
    link_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
