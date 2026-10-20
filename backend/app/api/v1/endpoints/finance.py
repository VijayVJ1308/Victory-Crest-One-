"""Victory Crest One - Finance and Accounting API Endpoints
General Ledger, Chart of Accounts, Invoices (AR), Bills (AP), and Financial Reporting.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from backend.app.schemas.finance import (
    AccountCreate, AccountOut,
    JournalEntryCreate, JournalEntryOut, JournalEntryReverseRequest,
    CustomerInvoiceCreate, CustomerInvoiceOut, CustomerPaymentCreate, CustomerPaymentOut,
    SupplierBillCreate, SupplierBillOut, BillPaymentCreate, BillPaymentOut,
    TrialBalanceResponse, ProfitAndLossResponse, BalanceSheetResponse
)
from backend.app.services.finance_service import finance_service
from backend.app.core.permissions import get_current_user

router = APIRouter(prefix="/finance", tags=["Finance & General Accounting"])


# --- Chart of Accounts Endpoints ---
@router.get(
    "/accounts",
    response_model=List[AccountOut],
    summary="List Chart of Accounts",
    description="Returns accounts with dynamically calculated ending balances."
)
def list_accounts(
    organization_id: Optional[str] = Query(None),
    account_type: Optional[str] = Query(None),
    active_only: bool = Query(False),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return finance_service.get_accounts(organization_id=org_id, account_type=account_type, active_only=active_only)


@router.post(
    "/accounts",
    response_model=AccountOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Account in Chart of Accounts"
)
def create_account(
    account_in: AccountCreate,
    user: dict = Depends(get_current_user)
):
    return finance_service.create_account(account_in, user_id=user.get("user_id"))


@router.get(
    "/accounts/{account_id}",
    response_model=AccountOut,
    summary="Get Account by ID"
)
def get_account(account_id: str, user: dict = Depends(get_current_user)):
    acc = finance_service.get_account_by_id(account_id)
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return acc


# --- General Ledger Journal Endpoints ---
@router.get(
    "/journals",
    response_model=List[JournalEntryOut],
    summary="List General Ledger Journal Entries"
)
def list_journals(
    organization_id: Optional[str] = Query(None),
    entry_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return finance_service.get_journal_entries(organization_id=org_id, entry_type=entry_type, status_filter=status_filter)


@router.post(
    "/journals",
    response_model=JournalEntryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Post Balanced Journal Entry",
    description="Posts double-entry journal. Strictly enforces Sum(Debit) == Sum(Credit)."
)
def create_journal(
    entry_in: JournalEntryCreate,
    user: dict = Depends(get_current_user)
):
    return finance_service.create_journal_entry(entry_in, user_id=user.get("user_id"))


@router.get(
    "/journals/{entry_id}",
    response_model=JournalEntryOut,
    summary="Get Journal Entry by ID"
)
def get_journal(entry_id: str, user: dict = Depends(get_current_user)):
    entry = finance_service.get_journal_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found.")
    return entry


@router.post(
    "/journals/{entry_id}/reverse",
    response_model=JournalEntryOut,
    summary="Reverse a Posted Journal Entry",
    description="Creates an opposite mirror reversing entry and marks original as REVERSED."
)
def reverse_journal(
    entry_id: str,
    req: JournalEntryReverseRequest,
    user: dict = Depends(get_current_user)
):
    return finance_service.reverse_journal_entry(
        entry_id=entry_id,
        reason=req.reason or "Correction reversal",
        user_id=user.get("user_id")
    )


# --- Accounts Receivable (Customer Invoices) Endpoints ---
@router.get(
    "/invoices",
    response_model=List[CustomerInvoiceOut],
    summary="List Customer Invoices (AR)"
)
def list_invoices(
    organization_id: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return finance_service.get_invoices(organization_id=org_id, customer_id=customer_id, status_filter=status_filter)


@router.post(
    "/invoices",
    response_model=CustomerInvoiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Customer Invoice (AR)",
    description="Creates customer invoice and automatically posts balanced GL journal (DR AR, CR Revenue/Tax)."
)
def create_invoice(
    invoice_in: CustomerInvoiceCreate,
    user: dict = Depends(get_current_user)
):
    return finance_service.create_invoice(invoice_in, user_id=user.get("user_id"))


@router.get(
    "/invoices/{invoice_id}",
    response_model=CustomerInvoiceOut,
    summary="Get Customer Invoice Details"
)
def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    inv = finance_service.get_invoice_by_id(invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    return inv


@router.post(
    "/invoices/payments",
    response_model=CustomerPaymentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record Customer Payment Against Invoice",
    description="Records payment, updates invoice balance/status, and posts GL journal (DR Cash, CR AR)."
)
def record_customer_payment(
    payment_in: CustomerPaymentCreate,
    user: dict = Depends(get_current_user)
):
    return finance_service.record_customer_payment(payment_in, user_id=user.get("user_id"))


# --- Accounts Payable (Supplier Bills) Endpoints ---
@router.get(
    "/bills",
    response_model=List[SupplierBillOut],
    summary="List Supplier Bills (AP)"
)
def list_bills(
    organization_id: Optional[str] = Query(None),
    supplier_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return finance_service.get_bills(organization_id=org_id, supplier_id=supplier_id, status_filter=status_filter)


@router.post(
    "/bills",
    response_model=SupplierBillOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record Supplier Bill (AP)",
    description="Records vendor bill and automatically posts balanced GL journal (DR Expense, CR AP)."
)
def create_bill(
    bill_in: SupplierBillCreate,
    user: dict = Depends(get_current_user)
):
    return finance_service.create_bill(bill_in, user_id=user.get("user_id"))


@router.get(
    "/bills/{bill_id}",
    response_model=SupplierBillOut,
    summary="Get Supplier Bill Details"
)
def get_bill(bill_id: str, user: dict = Depends(get_current_user)):
    bill = finance_service.get_bill_by_id(bill_id)
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found.")
    return bill


@router.post(
    "/bills/payments",
    response_model=BillPaymentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record Payment for Supplier Bill",
    description="Records disbursement, updates bill balance/status, and posts GL journal (DR AP, CR Cash)."
)
def record_bill_payment(
    payment_in: BillPaymentCreate,
    user: dict = Depends(get_current_user)
):
    return finance_service.record_bill_payment(payment_in, user_id=user.get("user_id"))


# --- Financial Reports Endpoints ---
@router.get(
    "/reports/trial-balance",
    response_model=TrialBalanceResponse,
    summary="Generate Trial Balance Report",
    description="Aggregates debits and credits across all accounts. Verifies Total Debits == Total Credits."
)
def get_trial_balance(
    organization_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return finance_service.get_trial_balance(org_id)


@router.get(
    "/reports/profit-and-loss",
    response_model=ProfitAndLossResponse,
    summary="Generate Profit & Loss (Income Statement)",
    description="Summarizes Revenue, Cost of Goods Sold, Gross Profit, Expenses, and Net Profit."
)
def get_profit_and_loss(
    organization_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return finance_service.get_profit_and_loss(org_id)


@router.get(
    "/reports/balance-sheet",
    response_model=BalanceSheetResponse,
    summary="Generate Balance Sheet Statement",
    description="Verifies fundamental accounting equation: Assets == Liabilities + Equity (+ Net Earnings)."
)
def get_balance_sheet(
    organization_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    org_id = organization_id or user.get("org_id")
    return finance_service.get_balance_sheet(org_id)
