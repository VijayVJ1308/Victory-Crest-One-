"""Victory Crest One - Finance and General Accounting Models
Double-entry general ledger, chart of accounts, accounts receivable, and accounts payable.
Strictly balanced entries, immutable auditability, and multi-tenant scoping.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Numeric, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, BaseModelMixin


class Account(Base, BaseModelMixin):
    """Chart of Accounts (COA) entity."""
    __tablename__ = "finance_accounts"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    account_code = Column(String(20), nullable=False, index=True)
    account_name = Column(String(120), nullable=False, index=True)
    account_type = Column(String(30), nullable=False, index=True)  # ASSET, LIABILITY, EQUITY, REVENUE, COGS, EXPENSE
    normal_balance = Column(String(10), nullable=False)  # DEBIT, CREDIT
    currency = Column(String(3), default="INR", nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System-critical accounts cannot be deleted
    description = Column(String(255), nullable=True)


class JournalEntry(Base, BaseModelMixin):
    """Double-entry General Ledger transaction header."""
    __tablename__ = "finance_journal_entries"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    entry_number = Column(String(50), nullable=False, unique=True, index=True)
    entry_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    entry_type = Column(String(30), default="GENERAL", nullable=False)  # GENERAL, INVOICE, BILL, PAYMENT, REVERSAL
    reference = Column(String(100), nullable=True, index=True)
    description = Column(String(255), nullable=False)

    status = Column(String(20), default="POSTED", nullable=False, index=True)  # DRAFT, POSTED, REVERSED
    total_debit = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_credit = Column(Numeric(15, 2), default=0.00, nullable=False)

    posted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    posted_by_user_id = Column(String(36), nullable=True)
    reversal_entry_id = Column(String(36), nullable=True)  # References the reversing entry if reversed


class JournalLine(Base, BaseModelMixin):
    """Line item in a double-entry journal entry."""
    __tablename__ = "finance_journal_lines"

    journal_entry_id = Column(String(36), ForeignKey("finance_journal_entries.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("finance_accounts.id"), nullable=False, index=True)

    account_code = Column(String(20), nullable=False)
    account_name = Column(String(120), nullable=False)

    debit = Column(Numeric(15, 2), default=0.00, nullable=False)
    credit = Column(Numeric(15, 2), default=0.00, nullable=False)
    description = Column(String(255), nullable=True)


class CustomerInvoice(Base, BaseModelMixin):
    """Accounts Receivable (AR) customer invoice."""
    __tablename__ = "finance_invoices"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    customer_id = Column(String(36), nullable=False, index=True)
    customer_name = Column(String(150), nullable=False)

    issue_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="ISSUED", nullable=False, index=True)  # DRAFT, ISSUED, PARTIALLY_PAID, PAID, VOID

    currency = Column(String(3), default="INR", nullable=False)
    subtotal = Column(Numeric(15, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    balance_due = Column(Numeric(15, 2), default=0.00, nullable=False)

    journal_entry_id = Column(String(36), nullable=True)  # Linked GL Journal Entry
    notes = Column(Text, nullable=True)


class CustomerInvoiceLine(Base, BaseModelMixin):
    """Line item for customer invoice."""
    __tablename__ = "finance_invoice_lines"

    invoice_id = Column(String(36), ForeignKey("finance_invoices.id"), nullable=False, index=True)
    product_id = Column(String(36), nullable=True)
    description = Column(String(255), nullable=False)

    quantity = Column(Numeric(10, 2), default=1.00, nullable=False)
    unit_price = Column(Numeric(15, 2), default=0.00, nullable=False)
    amount = Column(Numeric(15, 2), default=0.00, nullable=False)


class CustomerPayment(Base, BaseModelMixin):
    """AR Customer payment allocation."""
    __tablename__ = "finance_customer_payments"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    payment_number = Column(String(50), nullable=False, unique=True, index=True)
    customer_id = Column(String(36), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("finance_invoices.id"), nullable=False, index=True)

    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    payment_method = Column(String(30), default="BANK_TRANSFER", nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    reference = Column(String(100), nullable=True)

    journal_entry_id = Column(String(36), nullable=True)


class SupplierBill(Base, BaseModelMixin):
    """Accounts Payable (AP) supplier bill/voucher."""
    __tablename__ = "finance_bills"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    bill_number = Column(String(50), nullable=False, unique=True, index=True)
    supplier_id = Column(String(36), nullable=False, index=True)
    supplier_name = Column(String(150), nullable=False)
    vendor_invoice_ref = Column(String(100), nullable=True)

    bill_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="RECEIVED", nullable=False, index=True)  # DRAFT, RECEIVED, PARTIALLY_PAID, PAID, VOID

    currency = Column(String(3), default="INR", nullable=False)
    total_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    balance_due = Column(Numeric(15, 2), default=0.00, nullable=False)

    journal_entry_id = Column(String(36), nullable=True)  # Linked GL Journal Entry
    notes = Column(Text, nullable=True)


class SupplierBillLine(Base, BaseModelMixin):
    """Line item for supplier bill."""
    __tablename__ = "finance_bill_lines"

    bill_id = Column(String(36), ForeignKey("finance_bills.id"), nullable=False, index=True)
    account_id = Column(String(36), nullable=True)
    description = Column(String(255), nullable=False)

    quantity = Column(Numeric(10, 2), default=1.00, nullable=False)
    unit_price = Column(Numeric(15, 2), default=0.00, nullable=False)
    amount = Column(Numeric(15, 2), default=0.00, nullable=False)


class BillPayment(Base, BaseModelMixin):
    """AP Supplier bill disbursement payment."""
    __tablename__ = "finance_bill_payments"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    payment_number = Column(String(50), nullable=False, unique=True, index=True)
    supplier_id = Column(String(36), nullable=False, index=True)
    bill_id = Column(String(36), ForeignKey("finance_bills.id"), nullable=False, index=True)

    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    payment_method = Column(String(30), default="BANK_TRANSFER", nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    reference = Column(String(100), nullable=True)

    journal_entry_id = Column(String(36), nullable=True)
