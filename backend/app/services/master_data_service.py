"""Victory Crest One - Master Data & Shared Business Services
Core business services for Customers, Suppliers, Products & Services, Document Vault, and In-App Notifications.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import uuid
from pathlib import Path
from fastapi import HTTPException, status

from backend.app.schemas.master_data import (
    CustomerCreate, CustomerOut,
    SupplierCreate, SupplierOut,
    ProductCreate, ProductOut,
    DocumentOut, NotificationOut
)
from backend.app.services.audit_service import audit_service
from shared.constants import DEMO_ORGANISATIONS

# In-memory stores with initial seed data
_CUSTOMER_STORE: Dict[str, Dict[str, Any]] = {}
_SUPPLIER_STORE: Dict[str, Dict[str, Any]] = {}
_PRODUCT_STORE: Dict[str, Dict[str, Any]] = {}
_DOCUMENT_STORE: Dict[str, Dict[str, Any]] = {}
_NOTIFICATION_STORE: List[Dict[str, Any]] = []


def _seed_master_data():
    """Populate realistic demonstration master data records."""
    if _CUSTOMER_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_madurai = DEMO_ORGANISATIONS[0]["properties"][0]["id"]
    prop_chennai = DEMO_ORGANISATIONS[0]["properties"][2]["id"]

    # 1. Seed Customers
    customers = [
        {
            "id": "cust_reliance_corp",
            "organization_id": org_id,
            "property_id": prop_chennai,
            "code": "CUST-CORP-001",
            "name": "Tata Global Technologies Ltd",
            "customer_type": "CORPORATE",
            "email": "procurement@tataglobal.com",
            "phone": "+91 44 2855 0100",
            "billing_address": "Tata Tech Park, OMR, Chennai, Tamil Nadu 600096",
            "shipping_address": "Tata Tech Park, OMR, Chennai, Tamil Nadu 600096",
            "tax_identifier": "33AAACT1234F1Z8",
            "loyalty_points": 4500,
            "credit_limit": Decimal("500000.00"),
            "currency": "INR",
            "is_active": True,
            "notes": "Corporate retreat & annual conference partner.",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "cust_vip_guest",
            "organization_id": org_id,
            "property_id": prop_madurai,
            "code": "CUST-VIP-002",
            "name": "Dr. Ananya Sundaram",
            "customer_type": "INDIVIDUAL",
            "email": "dr.ananya@heritagehealth.org",
            "phone": "+91 98401 23456",
            "billing_address": "14 Palace Road, Madurai, Tamil Nadu 625001",
            "shipping_address": "14 Palace Road, Madurai, Tamil Nadu 625001",
            "tax_identifier": None,
            "loyalty_points": 1850,
            "credit_limit": Decimal("100000.00"),
            "currency": "INR",
            "is_active": True,
            "notes": "Frequent guest at GrandVista Heritage Hotel Madurai.",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    for c in customers:
        _CUSTOMER_STORE[c["id"]] = c

    # 2. Seed Suppliers
    suppliers = [
        {
            "id": "supp_linen_textiles",
            "organization_id": org_id,
            "code": "SUPP-TXT-101",
            "name": "Coimbatore Luxury Linens & Fabrics",
            "contact_person": "R. Ramanathan",
            "email": "orders@coimbatorelinens.com",
            "phone": "+91 422 254 9900",
            "address": "48 Mill Road, Coimbatore, Tamil Nadu 641001",
            "tax_identifier": "33AACCL9988G1ZQ",
            "payment_terms_days": 30,
            "lead_time_days": 4,
            "rating": Decimal("4.85"),
            "currency": "INR",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "supp_organic_foods",
            "organization_id": org_id,
            "code": "SUPP-FNB-202",
            "name": "Nilgiri Organics & Gourmet Supplies",
            "contact_person": "Meera Kurian",
            "email": "fresh@nilgiriorganics.in",
            "phone": "+91 423 244 5511",
            "address": "Ooty Valley Road, Nilgiris, Tamil Nadu 643001",
            "tax_identifier": "33AAAFN1122D1Z4",
            "payment_terms_days": 15,
            "lead_time_days": 2,
            "rating": Decimal("4.95"),
            "currency": "INR",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    for s in suppliers:
        _SUPPLIER_STORE[s["id"]] = s

    # 3. Seed Products & Services
    products = [
        {
            "id": "prod_heritage_suite",
            "organization_id": org_id,
            "sku": "ROOM-HERITAGE-STE",
            "barcode": "890123450001",
            "name": "Royal Heritage Palace Suite",
            "description": "Luxury palace suite with king bed, courtyard view, and heritage decor.",
            "category": "Hospitality Rooms",
            "item_type": "SERVICE",
            "unit_of_measure": "NIGHT",
            "unit_price": Decimal("8500.00"),
            "cost_price": Decimal("2200.00"),
            "tax_rate_percent": Decimal("18.00"),
            "reorder_threshold": 0,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "prod_mountain_deluxe",
            "organization_id": org_id,
            "sku": "ROOM-KODAI-DLX",
            "barcode": "890123450002",
            "name": "Mountain Vista Deluxe Chalet",
            "description": "Hill view pine cottage with fireplace and private balcony in Kodaikanal.",
            "category": "Hospitality Rooms",
            "item_type": "SERVICE",
            "unit_of_measure": "NIGHT",
            "unit_price": Decimal("6200.00"),
            "cost_price": Decimal("1800.00"),
            "tax_rate_percent": Decimal("18.00"),
            "reorder_threshold": 0,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "prod_chettinad_thali",
            "organization_id": org_id,
            "sku": "DINE-CHET-THALI",
            "barcode": "890123450003",
            "name": "Royal Chettinad Feast Thali",
            "description": "Traditional 18-course royal South Indian culinary dining experience.",
            "category": "Restaurant & Dining",
            "item_type": "RECIPE_DISH",
            "unit_of_measure": "UNIT",
            "unit_price": Decimal("1250.00"),
            "cost_price": Decimal("410.00"),
            "tax_rate_percent": Decimal("5.00"),
            "reorder_threshold": 20,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": "prod_spa_treatment",
            "organization_id": org_id,
            "sku": "SPA-AYUR-RELAX",
            "barcode": "890123450004",
            "name": "Ayurvedic Herbal Rejuvenation (90m)",
            "description": "Full body herbal oil massage and steam therapy.",
            "category": "Wellness & Spa",
            "item_type": "SERVICE",
            "unit_of_measure": "HOUR",
            "unit_price": Decimal("3500.00"),
            "cost_price": Decimal("900.00"),
            "tax_rate_percent": Decimal("18.00"),
            "reorder_threshold": 0,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    for p in products:
        _PRODUCT_STORE[p["id"]] = p

    # 4. Seed Document Vault
    doc_vault_dir = Path("local_data/documents")
    doc_vault_dir.mkdir(parents=True, exist_ok=True)
    sample_doc_path = doc_vault_dir / "hospitality_operating_standards_2026.pdf"
    if not sample_doc_path.exists():
        sample_doc_path.write_text("Victory Crest ONE - Standard Operating Procedure & Compliance Guidelines 2026")

    documents = [
        {
            "id": "doc_sop_2026",
            "organization_id": org_id,
            "property_id": prop_madurai,
            "file_name": "hospitality_operating_standards_2026.pdf",
            "file_path": str(sample_doc_path),
            "file_size_bytes": 1024 * 72,
            "mime_type": "application/pdf",
            "category": "REPORT",
            "linked_entity_type": "Organization",
            "linked_entity_id": org_id,
            "version": 1,
            "uploaded_by_email": "admin@victorycrest.internal",
            "created_at": datetime.utcnow()
        }
    ]
    for d in documents:
        _DOCUMENT_STORE[d["id"]] = d

    # 5. Seed Notifications
    notifications = [
        {
            "id": "notif_001",
            "organization_id": org_id,
            "title": "Welcome to Victory Crest ONE",
            "message": "Enterprise Operating System Phase 3 Master Data & Document Vault initialized.",
            "notification_type": "INFO",
            "is_read": False,
            "target_user_id": None,
            "target_role": None,
            "link_url": "/modules",
            "created_at": datetime.utcnow()
        },
        {
            "id": "notif_002",
            "organization_id": org_id,
            "title": "Corporate Master Account Created",
            "message": "Tata Global Technologies Ltd registered with ₹500,000 credit limit.",
            "notification_type": "APPROVAL",
            "is_read": False,
            "target_user_id": None,
            "target_role": "Finance Manager",
            "link_url": "/customers",
            "created_at": datetime.utcnow()
        }
    ]
    for n in notifications:
        _NOTIFICATION_STORE.append(n)


_seed_master_data()


# -------------------------------------------------------------
# Customer Service
# -------------------------------------------------------------
class CustomerService:
    @staticmethod
    def list_customers(organization_id: Optional[str] = None) -> List[CustomerOut]:
        _seed_master_data()
        results = list(_CUSTOMER_STORE.values())
        if organization_id:
            results = [c for c in results if c["organization_id"] == organization_id]
        return [CustomerOut(**c) for c in results]

    @staticmethod
    def create_customer(customer_in: CustomerCreate, creator_email: str = "admin") -> CustomerOut:
        _seed_master_data()
        org_id = customer_in.organization_id or DEMO_ORGANISATIONS[0]["id"]

        # Deduplication check
        for c in _CUSTOMER_STORE.values():
            if c["organization_id"] == org_id:
                if c["code"].lower() == customer_in.code.lower():
                    raise HTTPException(status_code=400, detail=f"Customer with code '{customer_in.code}' already exists")
                if customer_in.email and c.get("email") and c["email"].lower() == customer_in.email.lower():
                    raise HTTPException(status_code=400, detail=f"Customer with email '{customer_in.email}' already exists")
                if customer_in.phone and c.get("phone") and c["phone"] == customer_in.phone:
                    raise HTTPException(status_code=400, detail=f"Customer with phone '{customer_in.phone}' already exists")

        new_id = f"cust_{uuid.uuid4().hex[:8]}"
        record = {
            "id": new_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **customer_in.model_dump(),
            "organization_id": org_id
        }
        _CUSTOMER_STORE[new_id] = record

        audit_service.record_event(
            action="CUSTOMER_CREATED",
            entity_type="Customer",
            entity_id=new_id,
            user_email=creator_email,
            organization_id=org_id,
            details=f"Created customer '{customer_in.name}' ({customer_in.code})"
        )
        return CustomerOut(**record)

    @staticmethod
    def get_customer(customer_id: str) -> CustomerOut:
        _seed_master_data()
        if customer_id not in _CUSTOMER_STORE:
            raise HTTPException(status_code=404, detail="Customer not found")
        return CustomerOut(**_CUSTOMER_STORE[customer_id])


# -------------------------------------------------------------
# Supplier Service
# -------------------------------------------------------------
class SupplierService:
    @staticmethod
    def list_suppliers(organization_id: Optional[str] = None) -> List[SupplierOut]:
        _seed_master_data()
        results = list(_SUPPLIER_STORE.values())
        if organization_id:
            results = [s for s in results if s["organization_id"] == organization_id]
        return [SupplierOut(**s) for s in results]

    @staticmethod
    def create_supplier(supplier_in: SupplierCreate, creator_email: str = "admin") -> SupplierOut:
        _seed_master_data()
        org_id = supplier_in.organization_id or DEMO_ORGANISATIONS[0]["id"]

        for s in _SUPPLIER_STORE.values():
            if s["organization_id"] == org_id and s["code"].lower() == supplier_in.code.lower():
                raise HTTPException(status_code=400, detail=f"Supplier with code '{supplier_in.code}' already exists")

        new_id = f"supp_{uuid.uuid4().hex[:8]}"
        record = {
            "id": new_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **supplier_in.model_dump(),
            "organization_id": org_id
        }
        _SUPPLIER_STORE[new_id] = record

        audit_service.record_event(
            action="SUPPLIER_CREATED",
            entity_type="Supplier",
            entity_id=new_id,
            user_email=creator_email,
            organization_id=org_id,
            details=f"Created supplier '{supplier_in.name}' ({supplier_in.code})"
        )
        return SupplierOut(**record)

    @staticmethod
    def get_supplier(supplier_id: str) -> SupplierOut:
        _seed_master_data()
        if supplier_id not in _SUPPLIER_STORE:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return SupplierOut(**_SUPPLIER_STORE[supplier_id])


# -------------------------------------------------------------
# Product Service
# -------------------------------------------------------------
class ProductService:
    @staticmethod
    def list_products(organization_id: Optional[str] = None) -> List[ProductOut]:
        _seed_master_data()
        results = list(_PRODUCT_STORE.values())
        if organization_id:
            results = [p for p in results if p["organization_id"] == organization_id]
        return [ProductOut(**p) for p in results]

    @staticmethod
    def create_product(product_in: ProductCreate, creator_email: str = "admin") -> ProductOut:
        _seed_master_data()
        org_id = product_in.organization_id or DEMO_ORGANISATIONS[0]["id"]

        for p in _PRODUCT_STORE.values():
            if p["organization_id"] == org_id and p["sku"].lower() == product_in.sku.lower():
                raise HTTPException(status_code=400, detail=f"Product with SKU '{product_in.sku}' already exists")

        new_id = f"prod_{uuid.uuid4().hex[:8]}"
        record = {
            "id": new_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **product_in.model_dump(),
            "organization_id": org_id
        }
        _PRODUCT_STORE[new_id] = record

        audit_service.record_event(
            action="PRODUCT_CREATED",
            entity_type="Product",
            entity_id=new_id,
            user_email=creator_email,
            organization_id=org_id,
            details=f"Created catalog product '{product_in.name}' (SKU: {product_in.sku})"
        )
        return ProductOut(**record)

    @staticmethod
    def get_product(product_id: str) -> ProductOut:
        _seed_master_data()
        if product_id not in _PRODUCT_STORE:
            raise HTTPException(status_code=404, detail="Product not found")
        return ProductOut(**_PRODUCT_STORE[product_id])


# -------------------------------------------------------------
# Document Vault Service
# -------------------------------------------------------------
class DocumentService:
    @staticmethod
    def list_documents(organization_id: Optional[str] = None, category: Optional[str] = None) -> List[DocumentOut]:
        _seed_master_data()
        results = list(_DOCUMENT_STORE.values())
        if organization_id:
            results = [d for d in results if d["organization_id"] == organization_id]
        if category:
            results = [d for d in results if d["category"] == category]
        return [DocumentOut(**d) for d in results]

    @staticmethod
    def register_document(
        file_name: str,
        category: str = "GENERAL",
        file_bytes: Optional[bytes] = None,
        linked_entity_type: Optional[str] = None,
        linked_entity_id: Optional[str] = None,
        uploader_email: str = "admin@victorycrest.internal",
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> DocumentOut:
        _seed_master_data()
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        vault_dir = Path("local_data/documents")
        vault_dir.mkdir(parents=True, exist_ok=True)

        new_id = f"doc_{uuid.uuid4().hex[:8]}"
        file_path = vault_dir / f"{new_id}_{file_name}"
        file_size = 0
        if file_bytes:
            file_path.write_bytes(file_bytes)
            file_size = len(file_bytes)
        else:
            file_path.write_text(f"Placeholder content for {file_name}")
            file_size = len(f"Placeholder content for {file_name}")

        record = {
            "id": new_id,
            "organization_id": org_id,
            "property_id": property_id,
            "file_name": file_name,
            "file_path": str(file_path),
            "file_size_bytes": file_size,
            "mime_type": "application/pdf" if file_name.endswith(".pdf") else "application/octet-stream",
            "category": category,
            "linked_entity_type": linked_entity_type,
            "linked_entity_id": linked_entity_id,
            "version": 1,
            "uploaded_by_email": uploader_email,
            "created_at": datetime.utcnow()
        }
        _DOCUMENT_STORE[new_id] = record

        audit_service.record_event(
            action="DOCUMENT_UPLOADED",
            entity_type="Document",
            entity_id=new_id,
            user_email=uploader_email,
            organization_id=org_id,
            details=f"Uploaded document '{file_name}' ({category})"
        )
        return DocumentOut(**record)


# -------------------------------------------------------------
# Notification Service
# -------------------------------------------------------------
class NotificationService:
    @staticmethod
    def list_notifications(is_read: Optional[bool] = None) -> List[NotificationOut]:
        _seed_master_data()
        results = _NOTIFICATION_STORE
        if is_read is not None:
            results = [n for n in results if n["is_read"] == is_read]
        return [NotificationOut(**n) for n in results]

    @staticmethod
    def mark_as_read(notification_id: str) -> bool:
        _seed_master_data()
        for n in _NOTIFICATION_STORE:
            if n["id"] == notification_id:
                n["is_read"] = True
                return True
        return False

    @staticmethod
    def unread_count() -> int:
        _seed_master_data()
        return sum(1 for n in _NOTIFICATION_STORE if not n.get("is_read", False))


customer_service = CustomerService()
supplier_service = SupplierService()
product_service = ProductService()
document_service = DocumentService()
notification_service = NotificationService()
