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


class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CampaignChannel(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    PUSH_NOTIFICATION = "PUSH_NOTIFICATION"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    DIRECT_MAIL = "DIRECT_MAIL"


class SegmentType(str, Enum):
    DYNAMIC = "DYNAMIC"
    STATIC = "STATIC"


class JourneyStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class AttributionModel(str, Enum):
    FIRST_TOUCH = "FIRST_TOUCH"
    LAST_TOUCH = "LAST_TOUCH"
    LINEAR = "LINEAR"
    TIME_DECAY = "TIME_DECAY"


class PurchaseOrderStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class RequisitionStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONVERTED = "CONVERTED"


class MovementType(str, Enum):
    RECEIPT = "RECEIPT"
    TRANSFER = "TRANSFER"
    CONSUMPTION = "CONSUMPTION"
    ADJUSTMENT = "ADJUSTMENT"
    SCRAP = "SCRAP"


class StockStatus(str, Enum):
    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    OVERSTOCKED = "OVERSTOCKED"


class CycleCountStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RECONCILED = "RECONCILED"
    CANCELLED = "CANCELLED"


class WarehouseType(str, Enum):
    CENTRAL = "CENTRAL"
    FNB_COMMISSARY = "FNB_COMMISSARY"
    COLD_STORAGE = "COLD_STORAGE"
    RETAIL_STORE = "RETAIL_STORE"
    MAINTENANCE = "MAINTENANCE"


class EmploymentType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERN = "INTERN"


class EmployeeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    PROBATION = "PROBATION"
    TERMINATED = "TERMINATED"


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"
    LATE = "LATE"
    ON_LEAVE = "ON_LEAVE"


class LeaveType(str, Enum):
    CASUAL = "CASUAL"
    SICK = "SICK"
    EARNED = "EARNED"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"
    UNPAID = "UNPAID"


class LeaveStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PayrollRunStatus(str, Enum):
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    APPROVED = "APPROVED"
    DISBURSED = "DISBURSED"
    CANCELLED = "CANCELLED"


class SalaryComponentType(str, Enum):
    BASIC = "BASIC"
    HRA = "HRA"
    ALLOWANCE = "ALLOWANCE"
    OVERTIME = "OVERTIME"
    PF = "PF"
    ESI = "ESI"
    PROFESSIONAL_TAX = "PROFESSIONAL_TAX"
    TDS = "TDS"


class TicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class TicketStatus(str, Enum):
    NEW = "NEW"
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_PARTS = "PENDING_PARTS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketChannel(str, Enum):
    PORTAL = "PORTAL"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CHAT = "CHAT"
    ON_SITE = "ON_SITE"
    IOT_ALARM = "IOT_ALARM"


class WorkOrderStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    DISPATCHED = "DISPATCHED"
    ON_SITE = "ON_SITE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ServiceType(str, Enum):
    WARRANTY = "WARRANTY"
    PREVENTIVE_MAINTENANCE = "PREVENTIVE_MAINTENANCE"
    EMERGENCY_REPAIR = "EMERGENCY_REPAIR"
    INSTALLATION = "INSTALLATION"
    AMC = "AMC"


class PartRequisitionStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    ISSUED = "ISSUED"
    CONSUMED = "CONSUMED"
    RETURNED = "RETURNED"


class RoomStatus(str, Enum):
    AVAILABLE_CLEAN = "AVAILABLE_CLEAN"
    DIRTY = "DIRTY"
    INSPECTED = "INSPECTED"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"


class ReservationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class MealPlan(str, Enum):
    EP = "EP"    # European Plan (Room Only)
    CP = "CP"    # Continental Plan (Bed & Breakfast)
    MAP = "MAP"  # Modified American Plan (Half Board: Breakfast + Dinner)
    AP = "AP"    # American Plan (Full Board: All Meals)


class FolioLineType(str, Enum):
    ROOM_CHARGE = "ROOM_CHARGE"
    FOOD_BEVERAGE = "FOOD_BEVERAGE"
    SPA = "SPA"
    LAUNDRY = "LAUNDRY"
    MISC = "MISC"
    PAYMENT = "PAYMENT"


class FolioStatus(str, Enum):
    OPEN = "OPEN"
    SETTLED = "SETTLED"
    TRANSFERRED = "TRANSFERRED"


class DiningTableStatus(str, Enum):
    VACANT = "VACANT"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    BILLING = "BILLING"


class KdsOrderStatus(str, Enum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    CANCELLED = "CANCELLED"


# ============================================================================
# Phase 12: Manufacturing & Production Orders / Bill of Materials (BOM)
# ============================================================================

class WorkCenterStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


class BomStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ProductionOrderStatus(str, Enum):
    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    QUALITY_CHECK = "QUALITY_CHECK"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ProductionPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class QualityStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    CONDITIONAL = "CONDITIONAL"


# ============================================================================
# Phase 13: Project Management & Professional Services (PSA)
# ============================================================================

class ProjectStatus(str, Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ProjectPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class MilestoneStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    ACHIEVED = "ACHIEVED"
    INVOICED = "INVOICED"
    CANCELLED = "CANCELLED"


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class BillingType(str, Enum):
    FIXED_PRICE = "FIXED_PRICE"
    TIME_AND_MATERIALS = "TIME_AND_MATERIALS"
    MILESTONE_BASED = "MILESTONE_BASED"
    NON_BILLABLE = "NON_BILLABLE"


class TimesheetStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    INVOICED = "INVOICED"


class ProjectExpenseCategory(str, Enum):
    TRAVEL = "TRAVEL"
    SOFTWARE_LICENSE = "SOFTWARE_LICENSE"
    EQUIPMENT = "EQUIPMENT"
    SUBCONTRACTOR = "SUBCONTRACTOR"
    MATERIALS = "MATERIALS"
    MISC = "MISC"


# ============================================================================
# Phase 14: Business Intelligence & Executive Analytics
# ============================================================================

class ReportType(str, Enum):
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    FINANCIAL_PERFORMANCE = "FINANCIAL_PERFORMANCE"
    DEPARTMENTAL_P_AND_L = "DEPARTMENTAL_P_AND_L"
    OCCUPANCY_AND_REVPAR = "OCCUPANCY_AND_REVPAR"
    SALES_PIPELINE = "SALES_PIPELINE"
    MANUFACTURING_EFFICIENCY = "MANUFACTURING_EFFICIENCY"
    PROJECT_PROFITABILITY = "PROJECT_PROFITABILITY"


class ReportFormat(str, Enum):
    JSON = "JSON"
    CSV = "CSV"
    EXCEL = "EXCEL"
    PDF = "PDF"


class MetricPeriod(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEAR_TO_DATE = "YEAR_TO_DATE"


class AnalyticalDimension(str, Enum):
    PROPERTY = "PROPERTY"
    ORGANISATION = "ORGANISATION"
    DEPARTMENT = "DEPARTMENT"
    CUSTOMER_SEGMENT = "CUSTOMER_SEGMENT"








