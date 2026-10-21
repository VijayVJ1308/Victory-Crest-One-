"""Victory Crest One - System Enums
Shared enumeration types for business modules, roles, permissions, statuses, and multi-tenant scoping.
"""

from enum import Enum


class ModuleType(str, Enum):
    DASHBOARD = "dashboard"
    SALES = "sales"
    MARKETING = "marketing"
    COMMERCE = "commerce"
    POS = "pos"
    SERVICE = "service"
    FINANCE = "finance"
    ACCOUNTING = "accounting"
    ERP = "erp"
    INVENTORY = "inventory"
    PROCUREMENT = "procurement"
    MANUFACTURING = "manufacturing"
    HR = "hr"
    PAYROLL = "payroll"
    BI = "bi"
    PROJECTS = "projects"
    HOTEL = "hotel"
    RESTAURANT = "restaurant"
    DOCUMENTS = "documents"
    AUTOMATION = "automation"
    AI_ASSISTANT = "ai_assistant"
    SETTINGS = "settings"


class UserRole(str, Enum):
    SYSTEM_ADMIN = "System Administrator"
    ORG_OWNER = "Organisation Owner"
    GROUP_GM = "Group General Manager"
    GENERAL_MANAGER = "General Manager"
    FINANCE_MANAGER = "Finance Manager"
    ACCOUNTANT = "Accountant"
    SALES_MANAGER = "Sales Manager"
    SALES_REP = "Sales Representative"
    MARKETING_MANAGER = "Marketing Manager"
    ECOMMERCE_MANAGER = "E-commerce Manager"
    STORE_MANAGER = "Store Manager"
    POS_CASHIER = "POS Cashier"
    SERVICE_MANAGER = "Customer Service Manager"
    SERVICE_TECH = "Service Technician"
    ERP_MANAGER = "ERP Manager"
    PROCUREMENT_MANAGER = "Procurement Manager"
    INVENTORY_MANAGER = "Inventory Manager"
    MANUFACTURING_MANAGER = "Manufacturing Manager"
    HR_MANAGER = "HR Manager"
    HR_STAFF = "HR Staff"
    PAYROLL_ADMIN = "Payroll Administrator"
    BI_ANALYST = "Business Intelligence Analyst"
    DATA_ANALYST = "Data Analyst"
    PROJECT_MANAGER = "Project Manager"
    HOTEL_MANAGER = "Hotel Manager"
    RECEPTIONIST = "Receptionist"
    HOUSEKEEPING_MANAGER = "Housekeeping Manager"
    RESTAURANT_MANAGER = "Restaurant Manager"
    AUDITOR = "Auditor"
    READ_ONLY = "Read-Only User"


class PermissionAction(str, Enum):
    VIEW = "view"
    CREATE = "create"
    EDIT = "edit"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT = "export"
    ARCHIVE = "archive"
    DELETE = "delete"
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_USERS = "manage_users"
    ACCESS_SENSITIVE = "access_sensitive"


class PropertyType(str, Enum):
    HOTEL = "hotel"
    RESORT = "resort"
    RESTAURANT = "restaurant"
    RETAIL_STORE = "retail_store"
    WAREHOUSE = "warehouse"
    CORPORATE_OFFICE = "corporate_office"
    MANUFACTURING_PLANT = "manufacturing_plant"


class PropertyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    SIMULATED = "simulated"


class SyncStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    ERROR = "error"
    DEGRADED = "degraded"


class DatabaseStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    OFFLINE_LOCAL = "offline_local"


class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    COGS = "cogs"
    EXPENSE = "expense"


class NormalBalance(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class JournalEntryType(str, Enum):
    GENERAL = "general"
    INVOICE = "invoice"
    BILL = "bill"
    PAYMENT = "payment"
    PAYROLL = "payroll"
    REVERSAL = "reversal"
    ADJUSTING = "adjusting"
    CLOSING = "closing"


class JournalStatus(str, Enum):
    DRAFT = "draft"
    POSTED = "posted"
    REVERSED = "reversed"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    VOID = "void"


class BillStatus(str, Enum):
    DRAFT = "draft"
    RECEIVED = "received"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    VOID = "void"


class PaymentMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    CHECK = "check"
    ELECTRONIC = "electronic"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"


class LeadSource(str, Enum):
    WEBSITE = "website"
    REFERRAL = "referral"
    COLD_OUTREACH = "cold_outreach"
    TRADE_SHOW = "trade_show"
    PARTNER = "partner"
    SOCIAL_MEDIA = "social_media"
    DIRECT = "direct"


class DealStage(str, Enum):
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ActivityType(str, Enum):
    CALL = "call"
    MEETING = "meeting"
    EMAIL = "email"
    NOTE = "note"
    TASK = "task"


class PosSessionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    SUSPENDED = "SUSPENDED"


class PosOrderStatus(str, Enum):
    OPEN = "OPEN"
    HELD = "HELD"
    COMPLETED = "COMPLETED"
    VOIDED = "VOIDED"
    REFUNDED = "REFUNDED"


class TenderType(str, Enum):
    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    UPI_QR = "UPI_QR"
    ROOM_CHARGE = "ROOM_CHARGE"
    GIFT_CARD = "GIFT_CARD"


class PosTerminalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"



