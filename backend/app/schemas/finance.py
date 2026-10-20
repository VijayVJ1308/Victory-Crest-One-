"""Victory Crest One - Finance and Accounting Schemas
Pydantic DTOs for Chart of Accounts, General Ledger Journals, AR Invoices, AP Bills, and Financial Reports.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# --- Chart of Accounts Schemas ---
class AccountBase(BaseModel):
    account_code: str
    account_name: str
    account_type: str  # ASSET, LIABILITY, EQUITY, REVENUE, COGS, EXPENSE
    normal_balance: str  # DEBIT, CREDIT
    currency: str = "INR"
    is_active: bool = True
    is_system: bool = False
    description: Optional[str] = None
    property_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AccountCreate(AccountBase):
    organization_id: Optional[str] = None


class AccountOut(AccountBase):
    id: str
    organization_id: str
    current_balance: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- General Ledger Journal Schemas ---
class JournalLineBase(BaseModel):
    account_id: Optional[str] = None
    account_code: str
    account_name: Optional[str] = None
    debit: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit: Decimal = Field(default=Decimal("0.00"), ge=0)
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JournalLineCreate(JournalLineBase):
    pass


class JournalLineOut(JournalLineBase):
    id: str
    journal_entry_id: str

    model_config = ConfigDict(from_attributes=True)


class JournalEntryBase(BaseModel):
    entry_number: Optional[str] = None
    entry_date: Optional[datetime] = None
    entry_type: str = "GENERAL"  # GENERAL, INVOICE, BILL, PAYMENT, REVERSAL
    reference: Optional[str] = None
    description: str
    property_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JournalEntryCreate(JournalEntryBase):
    organization_id: Optional[str] = None
    lines: List[JournalLineCreate]


class JournalEntryOut(JournalEntryBase):
    id: str
    organization_id: str
    status: str
    total_debit: Decimal
    total_credit: Decimal
    posted_at: datetime
    posted_by_user_id: Optional[str] = None
    reversal_entry_id: Optional[str] = None
    lines: List[JournalLineOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalEntryReverseRequest(BaseModel):
    reason: Optional[str] = "Correction reversal"


# --- Accounts Receivable (Customer Invoices) Schemas ---
class InvoiceLineBase(BaseModel):
    product_id: Optional[str] = None
    description: str
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    amount: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceLineCreate(InvoiceLineBase):
    pass


class InvoiceLineOut(InvoiceLineBase):
    id: str
    invoice_id: str
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class CustomerInvoiceBase(BaseModel):
    customer_id: str
    customer_name: Optional[str] = None
    issue_date: Optional[datetime] = None
    due_date: datetime
    currency: str = "INR"
    notes: Optional[str] = None
    property_id: Optional[str] = None
    tax_rate_percent: Decimal = Decimal("0.00")

    model_config = ConfigDict(from_attributes=True)


class CustomerInvoiceCreate(CustomerInvoiceBase):
    organization_id: Optional[str] = None
    invoice_number: Optional[str] = None
    lines: List[InvoiceLineCreate]


class CustomerInvoiceOut(BaseModel):
    id: str
    organization_id: str
    property_id: Optional[str] = None
    invoice_number: str
    customer_id: str
    customer_name: str
    issue_date: datetime
    due_date: datetime
    status: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    journal_entry_id: Optional[str] = None
    notes: Optional[str] = None
    lines: List[InvoiceLineOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerPaymentCreate(BaseModel):
    invoice_id: str
    amount: Decimal = Field(..., gt=0)
    payment_method: str = "BANK_TRANSFER"
    reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    organization_id: Optional[str] = None


class CustomerPaymentOut(BaseModel):
    id: str
    organization_id: str
    payment_number: str
    customer_id: str
    invoice_id: str
    payment_date: datetime
    payment_method: str
    amount: Decimal
    reference: Optional[str] = None
    journal_entry_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Accounts Payable (Supplier Bills) Schemas ---
class BillLineBase(BaseModel):
    account_id: Optional[str] = None
    description: str
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    amount: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class BillLineCreate(BillLineBase):
    pass


class BillLineOut(BillLineBase):
    id: str
    bill_id: str
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class SupplierBillBase(BaseModel):
    supplier_id: str
    supplier_name: Optional[str] = None
    vendor_invoice_ref: Optional[str] = None
    bill_date: Optional[datetime] = None
    due_date: datetime
    currency: str = "INR"
    notes: Optional[str] = None
    property_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SupplierBillCreate(SupplierBillBase):
    organization_id: Optional[str] = None
    bill_number: Optional[str] = None
    lines: List[BillLineCreate]


class SupplierBillOut(BaseModel):
    id: str
    organization_id: str
    property_id: Optional[str] = None
    bill_number: str
    supplier_id: str
    supplier_name: str
    vendor_invoice_ref: Optional[str] = None
    bill_date: datetime
    due_date: datetime
    status: str
    currency: str
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    journal_entry_id: Optional[str] = None
    notes: Optional[str] = None
    lines: List[BillLineOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BillPaymentCreate(BaseModel):
    bill_id: str
    amount: Decimal = Field(..., gt=0)
    payment_method: str = "BANK_TRANSFER"
    reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    organization_id: Optional[str] = None


class BillPaymentOut(BaseModel):
    id: str
    organization_id: str
    payment_number: str
    supplier_id: str
    bill_id: str
    payment_date: datetime
    payment_method: str
    amount: Decimal
    reference: Optional[str] = None
    journal_entry_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Financial Reports Schemas ---
class TrialBalanceRow(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    debit_total: Decimal
    credit_total: Decimal
    ending_debit: Decimal
    ending_credit: Decimal


class TrialBalanceResponse(BaseModel):
    organization_id: str
    as_of_date: datetime
    rows: List[TrialBalanceRow]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool


class AccountCategorySummary(BaseModel):
    category: str
    accounts: List[Dict[str, Any]]
    total: Decimal


class ProfitAndLossResponse(BaseModel):
    organization_id: str
    period_start: Optional[datetime] = None
    period_end: datetime
    revenue: AccountCategorySummary
    cogs: AccountCategorySummary
    gross_profit: Decimal
    operating_expenses: AccountCategorySummary
    operating_income: Decimal
    net_profit: Decimal


class BalanceSheetResponse(BaseModel):
    organization_id: str
    as_of_date: datetime
    assets: AccountCategorySummary
    liabilities: AccountCategorySummary
    equity: AccountCategorySummary
    current_earnings: Decimal
    total_assets: Decimal
    total_liabilities_and_equity: Decimal
    is_balanced: bool
