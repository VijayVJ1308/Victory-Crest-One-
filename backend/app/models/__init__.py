"""Victory Crest One - Database Models Package
"""

from backend.app.models.base import Base, BaseModelMixin
from backend.app.models.organization import Organization, Property, Department
from backend.app.models.user import User, Role
from backend.app.models.audit import AuditLog
from backend.app.models.master_data import (
    Customer,
    Supplier,
    ProductMaster,
    DocumentMetadata,
    Notification
)
from backend.app.models.finance import (
    Account,
    JournalEntry,
    JournalLine,
    CustomerInvoice,
    CustomerInvoiceLine,
    CustomerPayment,
    SupplierBill,
    SupplierBillLine,
    BillPayment
)
from backend.app.models.crm import (
    Lead,
    Deal,
    Quote,
    QuoteLine,
    SalesActivity
)

__all__ = [
    "Base",
    "BaseModelMixin",
    "Organization",
    "Property",
    "Department",
    "User",
    "Role",
    "AuditLog",
    "Customer",
    "Supplier",
    "ProductMaster",
    "DocumentMetadata",
    "Notification",
    "Account",
    "JournalEntry",
    "JournalLine",
    "CustomerInvoice",
    "CustomerInvoiceLine",
    "CustomerPayment",
    "SupplierBill",
    "SupplierBillLine",
    "BillPayment",
    "Lead",
    "Deal",
    "Quote",
    "QuoteLine",
    "SalesActivity"
]


