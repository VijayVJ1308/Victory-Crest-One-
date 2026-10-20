"""Victory Crest One - Finance and General Accounting Engine
Double-entry general ledger, chart of accounts, accounts receivable, accounts payable, and financial reports.
Strict invariant enforcement: Sum(Debit) == Sum(Credit). Immutable posted journals with audit reversals.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.finance import (
    AccountCreate, AccountOut,
    JournalEntryCreate, JournalEntryOut, JournalLineCreate, JournalLineOut,
    CustomerInvoiceCreate, CustomerInvoiceOut, CustomerPaymentCreate, CustomerPaymentOut,
    SupplierBillCreate, SupplierBillOut, BillPaymentCreate, BillPaymentOut,
    TrialBalanceResponse, TrialBalanceRow,
    ProfitAndLossResponse, BalanceSheetResponse, AccountCategorySummary
)
from shared.calculations import (
    to_decimal, validate_journal_balance, calculate_invoice_totals, calculate_account_net_balance
)
from shared.constants import DEMO_ORGANISATIONS
from backend.app.services.audit_service import audit_service


# In-memory storage stores with seed data
_ACCOUNT_STORE: Dict[str, Dict[str, Any]] = {}
_JOURNAL_STORE: Dict[str, Dict[str, Any]] = {}
_INVOICE_STORE: Dict[str, Dict[str, Any]] = {}
_PAYMENT_STORE: Dict[str, Dict[str, Any]] = {}
_BILL_STORE: Dict[str, Dict[str, Any]] = {}
_BILL_PAYMENT_STORE: Dict[str, Dict[str, Any]] = {}


def _seed_finance_data():
    """Seed enterprise chart of accounts, opening journals, sample invoices and bills."""
    if _ACCOUNT_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_id = DEMO_ORGANISATIONS[0]["properties"][0]["id"]

    # 1. Standard Enterprise Chart of Accounts (COA)
    coa_definitions = [
        # Assets (1000 - 1999)
        ("1010", "Operating Cash & Bank Account", "ASSET", "DEBIT", True, "Primary operating bank account"),
        ("1020", "Accounts Receivable (AR)", "ASSET", "DEBIT", True, "Customer receivables control account"),
        ("1030", "Petty Cash & Undeposited Funds", "ASSET", "DEBIT", True, "Cash registers and undeposited funds"),
        ("1200", "Inventory Asset", "ASSET", "DEBIT", True, "F&B, retail merchandise, and operating inventory"),
        ("1500", "Property, Plant & Equipment", "ASSET", "DEBIT", False, "Buildings, vehicles, machinery, and fixtures"),

        # Liabilities (2000 - 2999)
        ("2010", "Accounts Payable (AP)", "LIABILITY", "CREDIT", True, "Trade vendor liabilities control account"),
        ("2020", "Sales Tax & GST Payable", "LIABILITY", "CREDIT", True, "Collected output sales tax and GST liability"),
        ("2030", "Accrued Payroll & Statutory Liabilities", "LIABILITY", "CREDIT", True, "Accrued salaries and deductions"),

        # Equity (3000 - 3999)
        ("3010", "Owner / Share Capital", "EQUITY", "CREDIT", True, "Contributed capital by shareholders"),
        ("3020", "Retained Earnings", "EQUITY", "CREDIT", True, "Accumulated earnings carried forward"),

        # Revenue (4000 - 4999)
        ("4010", "Hospitality & Lodging Revenue", "REVENUE", "CREDIT", False, "Guest room nights and resort villas"),
        ("4020", "Food & Beverage Revenue", "REVENUE", "CREDIT", False, "Restaurant dining, room service, and banqueting"),
        ("4030", "Retail & Commerce Sales", "REVENUE", "CREDIT", False, "Boutique, spa products, and merchandise"),
        ("4040", "Service & Event Fee Revenue", "REVENUE", "CREDIT", False, "Conferences, spa treatments, and activities"),

        # Cost of Goods Sold (5000 - 5999)
        ("5010", "Food & Beverage Cost of Sales", "COGS", "DEBIT", False, "Raw food materials, produce, and ingredients"),
        ("5020", "Retail Merchandise Cost of Sales", "COGS", "DEBIT", False, "Purchase cost of items sold in store"),

        # Operating Expenses (6000 - 6999)
        ("6010", "Payroll & Staff Compensation", "EXPENSE", "DEBIT", False, "Salaries, wages, overtime, and staff welfare"),
        ("6020", "Rent, Property & Facilities", "EXPENSE", "DEBIT", False, "Property lease, ground rent, and facility costs"),
        ("6030", "Utilities & Energy", "EXPENSE", "DEBIT", False, "Electricity, water, gas, and waste management"),
        ("6040", "Software, Cloud & Technology", "EXPENSE", "DEBIT", False, "ERP licenses, cloud servers, and POS SaaS"),
        ("6050", "Marketing, PR & Advertising", "EXPENSE", "DEBIT", False, "Brand campaigns, OTA commissions, and media"),
        ("6060", "Maintenance & Operating Supplies", "EXPENSE", "DEBIT", False, "Guest amenities, repairs, and cleaning materials"),
    ]

    for code, name, acc_type, normal_bal, is_sys, desc in coa_definitions:
        acc_id = f"acc_{code}"
        _ACCOUNT_STORE[acc_id] = {
            "id": acc_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "account_code": code,
            "account_name": name,
            "account_type": acc_type,
            "normal_balance": normal_bal,
            "currency": "INR",
            "is_active": True,
            "is_system": is_sys,
            "description": desc,
            "created_at": datetime.utcnow() - timedelta(days=90),
            "updated_at": datetime.utcnow() - timedelta(days=90),
        }

    # 2. Seed Opening Balanced Journal Entry (JE-2026-0001)
    je1_id = "je_opening_balance"
    je1_lines = [
        {"id": str(uuid.uuid4()), "journal_entry_id": je1_id, "account_id": "acc_1010", "account_code": "1010", "account_name": "Operating Cash & Bank Account", "debit": Decimal("5000000.00"), "credit": Decimal("0.00"), "description": "Opening cash at bank"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je1_id, "account_id": "acc_1500", "account_code": "1500", "account_name": "Property, Plant & Equipment", "debit": Decimal("12000000.00"), "credit": Decimal("0.00"), "description": "Valuation of hotel resort fixtures & equipment"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je1_id, "account_id": "acc_1200", "account_code": "1200", "account_name": "Inventory Asset", "debit": Decimal("450000.00"), "credit": Decimal("0.00"), "description": "Opening physical inventory"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je1_id, "account_id": "acc_3010", "account_code": "3010", "account_name": "Owner / Share Capital", "debit": Decimal("0.00"), "credit": Decimal("15000000.00"), "description": "Issued share capital"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je1_id, "account_id": "acc_3020", "account_code": "3020", "account_name": "Retained Earnings", "debit": Decimal("0.00"), "credit": Decimal("2450000.00"), "description": "Opening retained earnings balance"},
    ]
    _JOURNAL_STORE[je1_id] = {
        "id": je1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "entry_number": "JE-2026-0001",
        "entry_date": datetime.utcnow() - timedelta(days=60),
        "entry_type": "GENERAL",
        "reference": "OPENING-2026",
        "description": "FY2026 Opening Balance Sheet initialization",
        "status": "POSTED",
        "total_debit": Decimal("17450000.00"),
        "total_credit": Decimal("17450000.00"),
        "posted_at": datetime.utcnow() - timedelta(days=60),
        "posted_by_user_id": "usr_superadmin_01",
        "reversal_entry_id": None,
        "lines": je1_lines,
        "created_at": datetime.utcnow() - timedelta(days=60),
        "updated_at": datetime.utcnow() - timedelta(days=60),
    }

    # 3. Seed Operating Expenses Journal (JE-2026-0002)
    je2_id = "je_operating_expenses"
    je2_lines = [
        {"id": str(uuid.uuid4()), "journal_entry_id": je2_id, "account_id": "acc_6020", "account_code": "6020", "account_name": "Rent, Property & Facilities", "debit": Decimal("180000.00"), "credit": Decimal("0.00"), "description": "Monthly resort facilities lease"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je2_id, "account_id": "acc_6040", "account_code": "6040", "account_name": "Software, Cloud & Technology", "debit": Decimal("45000.00"), "credit": Decimal("0.00"), "description": "Cloud hosting and software subscription"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je2_id, "account_id": "acc_1010", "account_code": "1010", "account_name": "Operating Cash & Bank Account", "debit": Decimal("0.00"), "credit": Decimal("225000.00"), "description": "Wire transfer disbursement"},
    ]
    _JOURNAL_STORE[je2_id] = {
        "id": je2_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "entry_number": "JE-2026-0002",
        "entry_date": datetime.utcnow() - timedelta(days=20),
        "entry_type": "GENERAL",
        "reference": "DISB-FEB-001",
        "description": "February lease and technology infrastructure fees",
        "status": "POSTED",
        "total_debit": Decimal("225000.00"),
        "total_credit": Decimal("225000.00"),
        "posted_at": datetime.utcnow() - timedelta(days=20),
        "posted_by_user_id": "usr_accountant_01",
        "reversal_entry_id": None,
        "lines": je2_lines,
        "created_at": datetime.utcnow() - timedelta(days=20),
        "updated_at": datetime.utcnow() - timedelta(days=20),
    }

    # 4. Seed Customer Invoice 1 (INV-2026-0001)
    inv1_id = "inv_tata_conference"
    inv1_lines = [
        {"id": str(uuid.uuid4()), "invoice_id": inv1_id, "product_id": "prod_room_deluxe", "description": "Royal Heritage Suite - 3 Nights Corporate Stay", "quantity": Decimal("3.00"), "unit_price": Decimal("12000.00"), "amount": Decimal("36000.00")},
        {"id": str(uuid.uuid4()), "invoice_id": inv1_id, "product_id": None, "description": "Grand Ballroom Conference & Banqueting Package", "quantity": Decimal("1.00"), "unit_price": Decimal("50000.00"), "amount": Decimal("50000.00")},
    ]
    je_inv1_id = "je_inv_tata_001"
    je_inv1_lines = [
        {"id": str(uuid.uuid4()), "journal_entry_id": je_inv1_id, "account_id": "acc_1020", "account_code": "1020", "account_name": "Accounts Receivable (AR)", "debit": Decimal("101480.00"), "credit": Decimal("0.00"), "description": "Invoice INV-2026-0001 to Tata Global Technologies"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je_inv1_id, "account_id": "acc_4010", "account_code": "4010", "account_name": "Hospitality & Lodging Revenue", "debit": Decimal("0.00"), "credit": Decimal("36000.00"), "description": "Lodging revenue for suite"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je_inv1_id, "account_id": "acc_4040", "account_code": "4040", "account_name": "Service & Event Fee Revenue", "debit": Decimal("0.00"), "credit": Decimal("50000.00"), "description": "Banqueting package revenue"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je_inv1_id, "account_id": "acc_2020", "account_code": "2020", "account_name": "Sales Tax & GST Payable", "debit": Decimal("0.00"), "credit": Decimal("15480.00"), "description": "18% GST output tax"},
    ]
    _JOURNAL_STORE[je_inv1_id] = {
        "id": je_inv1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "entry_number": "JE-2026-0003",
        "entry_date": datetime.utcnow() - timedelta(days=15),
        "entry_type": "INVOICE",
        "reference": "INV-2026-0001",
        "description": "Invoice INV-2026-0001 Tata Global Technologies",
        "status": "POSTED",
        "total_debit": Decimal("101480.00"),
        "total_credit": Decimal("101480.00"),
        "posted_at": datetime.utcnow() - timedelta(days=15),
        "posted_by_user_id": "usr_accountant_01",
        "reversal_entry_id": None,
        "lines": je_inv1_lines,
        "created_at": datetime.utcnow() - timedelta(days=15),
        "updated_at": datetime.utcnow() - timedelta(days=15),
    }

    _INVOICE_STORE[inv1_id] = {
        "id": inv1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "invoice_number": "INV-2026-0001",
        "customer_id": "cust_reliance_corp",
        "customer_name": "Tata Global Technologies Ltd",
        "issue_date": datetime.utcnow() - timedelta(days=15),
        "due_date": datetime.utcnow() + timedelta(days=15),
        "status": "PARTIALLY_PAID",
        "currency": "INR",
        "subtotal": Decimal("86000.00"),
        "tax_amount": Decimal("15480.00"),
        "total_amount": Decimal("101480.00"),
        "paid_amount": Decimal("50000.00"),
        "balance_due": Decimal("51480.00"),
        "journal_entry_id": je_inv1_id,
        "notes": "Net 30 corporate billing agreement.",
        "lines": inv1_lines,
        "created_at": datetime.utcnow() - timedelta(days=15),
        "updated_at": datetime.utcnow() - timedelta(days=5),
    }

    # 5. Customer Payment for Invoice 1
    pay1_id = "pay_tata_part"
    je_pay1_id = "je_pay_tata_001"
    je_pay1_lines = [
        {"id": str(uuid.uuid4()), "journal_entry_id": je_pay1_id, "account_id": "acc_1010", "account_code": "1010", "account_name": "Operating Cash & Bank Account", "debit": Decimal("50000.00"), "credit": Decimal("0.00"), "description": "Bank transfer from Tata Global Technologies"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je_pay1_id, "account_id": "acc_1020", "account_code": "1020", "account_name": "Accounts Receivable (AR)", "debit": Decimal("0.00"), "credit": Decimal("50000.00"), "description": "Payment applied to INV-2026-0001"},
    ]
    _JOURNAL_STORE[je_pay1_id] = {
        "id": je_pay1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "entry_number": "JE-2026-0004",
        "entry_date": datetime.utcnow() - timedelta(days=5),
        "entry_type": "PAYMENT",
        "reference": "PAY-2026-0001",
        "description": "Payment receipt for INV-2026-0001",
        "status": "POSTED",
        "total_debit": Decimal("50000.00"),
        "total_credit": Decimal("50000.00"),
        "posted_at": datetime.utcnow() - timedelta(days=5),
        "posted_by_user_id": "usr_accountant_01",
        "reversal_entry_id": None,
        "lines": je_pay1_lines,
        "created_at": datetime.utcnow() - timedelta(days=5),
        "updated_at": datetime.utcnow() - timedelta(days=5),
    }

    _PAYMENT_STORE[pay1_id] = {
        "id": pay1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "payment_number": "PAY-2026-0001",
        "customer_id": "cust_reliance_corp",
        "invoice_id": inv1_id,
        "payment_date": datetime.utcnow() - timedelta(days=5),
        "payment_method": "BANK_TRANSFER",
        "amount": Decimal("50000.00"),
        "reference": "NEFT-TATA-998822",
        "journal_entry_id": je_pay1_id,
        "created_at": datetime.utcnow() - timedelta(days=5)
    }

    # 6. Seed Supplier Bill 1 (BILL-2026-0001) - Paid
    bill1_id = "bill_fresh_farms_01"
    bill1_lines = [
        {"id": str(uuid.uuid4()), "bill_id": bill1_id, "account_id": "acc_5010", "description": "Organic Vegetables, Dairy & Poultry Supply", "quantity": Decimal("1.00"), "unit_price": Decimal("32500.00"), "amount": Decimal("32500.00")},
    ]
    je_bill1_id = "je_bill_farms_001"
    je_bill1_lines = [
        {"id": str(uuid.uuid4()), "journal_entry_id": je_bill1_id, "account_id": "acc_5010", "account_code": "5010", "account_name": "Food & Beverage Cost of Sales", "debit": Decimal("32500.00"), "credit": Decimal("0.00"), "description": "F&B supplies for restaurants"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je_bill1_id, "account_id": "acc_2010", "account_code": "2010", "account_name": "Accounts Payable (AP)", "debit": Decimal("0.00"), "credit": Decimal("32500.00"), "description": "Payable to Fresh Organic Farms"},
    ]
    _JOURNAL_STORE[je_bill1_id] = {
        "id": je_bill1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "entry_number": "JE-2026-0005",
        "entry_date": datetime.utcnow() - timedelta(days=12),
        "entry_type": "BILL",
        "reference": "BILL-2026-0001",
        "description": "Bill from Fresh Organic Farms & Produce",
        "status": "POSTED",
        "total_debit": Decimal("32500.00"),
        "total_credit": Decimal("32500.00"),
        "posted_at": datetime.utcnow() - timedelta(days=12),
        "posted_by_user_id": "usr_accountant_01",
        "reversal_entry_id": None,
        "lines": je_bill1_lines,
        "created_at": datetime.utcnow() - timedelta(days=12),
        "updated_at": datetime.utcnow() - timedelta(days=12),
    }

    _BILL_STORE[bill1_id] = {
        "id": bill1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "bill_number": "BILL-2026-0001",
        "supplier_id": "supp_fresh_farms",
        "supplier_name": "Fresh Organic Farms & Produce",
        "vendor_invoice_ref": "FOF-INV-9901",
        "bill_date": datetime.utcnow() - timedelta(days=12),
        "due_date": datetime.utcnow() - timedelta(days=2),
        "status": "PAID",
        "currency": "INR",
        "total_amount": Decimal("32500.00"),
        "paid_amount": Decimal("32500.00"),
        "balance_due": Decimal("0.00"),
        "journal_entry_id": je_bill1_id,
        "notes": "Weekly produce delivery voucher.",
        "lines": bill1_lines,
        "created_at": datetime.utcnow() - timedelta(days=12),
        "updated_at": datetime.utcnow() - timedelta(days=4),
    }

    # Bill 1 Payment
    bpay1_id = "bpay_farms_01"
    je_bpay1_id = "je_bpay_farms_001"
    je_bpay1_lines = [
        {"id": str(uuid.uuid4()), "journal_entry_id": je_bpay1_id, "account_id": "acc_2010", "account_code": "2010", "account_name": "Accounts Payable (AP)", "debit": Decimal("32500.00"), "credit": Decimal("0.00"), "description": "Disbursement for BILL-2026-0001"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je_bpay1_id, "account_id": "acc_1010", "account_code": "1010", "account_name": "Operating Cash & Bank Account", "debit": Decimal("0.00"), "credit": Decimal("32500.00"), "description": "Bank transfer to Fresh Organic Farms"},
    ]
    _JOURNAL_STORE[je_bpay1_id] = {
        "id": je_bpay1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "entry_number": "JE-2026-0006",
        "entry_date": datetime.utcnow() - timedelta(days=4),
        "entry_type": "PAYMENT",
        "reference": "BPAY-2026-0001",
        "description": "Bill Payment for Fresh Organic Farms",
        "status": "POSTED",
        "total_debit": Decimal("32500.00"),
        "total_credit": Decimal("32500.00"),
        "posted_at": datetime.utcnow() - timedelta(days=4),
        "posted_by_user_id": "usr_accountant_01",
        "reversal_entry_id": None,
        "lines": je_bpay1_lines,
        "created_at": datetime.utcnow() - timedelta(days=4),
        "updated_at": datetime.utcnow() - timedelta(days=4),
    }
    _BILL_PAYMENT_STORE[bpay1_id] = {
        "id": bpay1_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "payment_number": "BPAY-2026-0001",
        "supplier_id": "supp_fresh_farms",
        "bill_id": bill1_id,
        "payment_date": datetime.utcnow() - timedelta(days=4),
        "payment_method": "BANK_TRANSFER",
        "amount": Decimal("32500.00"),
        "reference": "TXN-BANK-110022",
        "journal_entry_id": je_bpay1_id,
        "created_at": datetime.utcnow() - timedelta(days=4),
    }

    # 7. Seed Supplier Bill 2 (BILL-2026-0002) - Received / Unpaid
    bill2_id = "bill_linen_01"
    bill2_lines = [
        {"id": str(uuid.uuid4()), "bill_id": bill2_id, "account_id": "acc_6060", "description": "Luxury Egyptian Cotton Bed Linen Sets", "quantity": Decimal("20.00"), "unit_price": Decimal("2800.00"), "amount": Decimal("56000.00")},
    ]
    je_bill2_id = "je_bill_linen_001"
    je_bill2_lines = [
        {"id": str(uuid.uuid4()), "journal_entry_id": je_bill2_id, "account_id": "acc_6060", "account_code": "6060", "account_name": "Maintenance & Operating Supplies", "debit": Decimal("56000.00"), "credit": Decimal("0.00"), "description": "Guest room amenities and linens"},
        {"id": str(uuid.uuid4()), "journal_entry_id": je_bill2_id, "account_id": "acc_2010", "account_code": "2010", "account_name": "Accounts Payable (AP)", "debit": Decimal("0.00"), "credit": Decimal("56000.00"), "description": "Payable to Royal Linen & Amenities Co"},
    ]
    _JOURNAL_STORE[je_bill2_id] = {
        "id": je_bill2_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "entry_number": "JE-2026-0007",
        "entry_date": datetime.utcnow() - timedelta(days=3),
        "entry_type": "BILL",
        "reference": "BILL-2026-0002",
        "description": "Bill from Royal Linen & Amenities Co",
        "status": "POSTED",
        "total_debit": Decimal("56000.00"),
        "total_credit": Decimal("56000.00"),
        "posted_at": datetime.utcnow() - timedelta(days=3),
        "posted_by_user_id": "usr_accountant_01",
        "reversal_entry_id": None,
        "lines": je_bill2_lines,
        "created_at": datetime.utcnow() - timedelta(days=3),
        "updated_at": datetime.utcnow() - timedelta(days=3),
    }

    _BILL_STORE[bill2_id] = {
        "id": bill2_id,
        "organization_id": org_id,
        "property_id": prop_id,
        "bill_number": "BILL-2026-0002",
        "supplier_id": "supp_royal_linen",
        "supplier_name": "Royal Linen & Amenities Co",
        "vendor_invoice_ref": "RLA-2026-881",
        "bill_date": datetime.utcnow() - timedelta(days=3),
        "due_date": datetime.utcnow() + timedelta(days=27),
        "status": "RECEIVED",
        "currency": "INR",
        "total_amount": Decimal("56000.00"),
        "paid_amount": Decimal("0.00"),
        "balance_due": Decimal("56000.00"),
        "journal_entry_id": je_bill2_id,
        "notes": "Replacement linen inventory for suites.",
        "lines": bill2_lines,
        "created_at": datetime.utcnow() - timedelta(days=3),
        "updated_at": datetime.utcnow() - timedelta(days=3),
    }


class FinanceService:
    """Enterprise Finance & General Accounting Service."""

    def __init__(self):
        _seed_finance_data()

    # --- Chart of Accounts Management ---
    def get_accounts(
        self,
        organization_id: Optional[str] = None,
        account_type: Optional[str] = None,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Retrieve list of accounts with dynamically computed current balances."""
        _seed_finance_data()
        accounts = list(_ACCOUNT_STORE.values())

        if organization_id:
            accounts = [a for a in accounts if a["organization_id"] == organization_id]
        if account_type:
            accounts = [a for a in accounts if a["account_type"].lower() == account_type.lower()]
        if active_only:
            accounts = [a for a in accounts if a["is_active"]]

        # Calculate current balances from posted journals
        balances = self._calculate_all_account_balances(organization_id)
        result = []
        for a in accounts:
            a_copy = dict(a)
            a_copy["current_balance"] = balances.get(a["account_code"], Decimal("0.00"))
            result.append(a_copy)

        return sorted(result, key=lambda x: x["account_code"])

    def get_account_by_code(self, account_code: str, organization_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        _seed_finance_data()
        for a in _ACCOUNT_STORE.values():
            if a["account_code"] == account_code:
                if organization_id is None or a["organization_id"] == organization_id:
                    return a
        return None

    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        _seed_finance_data()
        return _ACCOUNT_STORE.get(account_id)

    def create_account(self, account_in: AccountCreate, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new account in the Chart of Accounts."""
        _seed_finance_data()
        org_id = account_in.organization_id or DEMO_ORGANISATIONS[0]["id"]

        # Check unique account code in organisation
        existing = self.get_account_by_code(account_in.account_code, org_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Account with code '{account_in.account_code}' already exists in this organisation."
            )

        acc_id = f"acc_{str(uuid.uuid4())[:8]}"
        account_dict = {
            **account_in.model_dump(),
            "id": acc_id,
            "organization_id": org_id,
            "is_system": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        _ACCOUNT_STORE[acc_id] = account_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="FINANCE_ACCOUNT_CREATED",
            resource_type="finance_account",
            resource_id=acc_id,
            organization_id=org_id,
            details={"account_code": account_in.account_code, "account_name": account_in.account_name}
        )
        return account_dict

    # --- Double-Entry General Ledger Journals ---
    def get_journal_entries(
        self,
        organization_id: Optional[str] = None,
        entry_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve journal entries with their lines."""
        _seed_finance_data()
        entries = list(_JOURNAL_STORE.values())

        if organization_id:
            entries = [e for e in entries if e["organization_id"] == organization_id]
        if entry_type:
            entries = [e for e in entries if e["entry_type"].lower() == entry_type.lower()]
        if status_filter:
            entries = [e for e in entries if e["status"].lower() == status_filter.lower()]

        return sorted(entries, key=lambda x: x["entry_date"], reverse=True)

    def get_journal_entry_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        _seed_finance_data()
        return _JOURNAL_STORE.get(entry_id)

    def create_journal_entry(
        self,
        entry_in: JournalEntryCreate,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create and post a balanced double-entry journal entry.
        Strict Invariant: Sum(Debit) == Sum(Credit).
        """
        _seed_finance_data()
        org_id = entry_in.organization_id or DEMO_ORGANISATIONS[0]["id"]

        if not entry_in.lines or len(entry_in.lines) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A journal entry must contain at least two line items (double-entry standard)."
            )

        # Validate balance using Decimal precision
        is_balanced, total_debits, total_credits, diff = validate_journal_balance(entry_in.lines)
        if not is_balanced:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Unbalanced journal entry: Total Debits ({total_debits}) != Total Credits ({total_credits}). Difference: {diff}."
            )

        entry_id = f"je_{str(uuid.uuid4())[:8]}"
        entry_num = entry_in.entry_number or f"JE-{datetime.utcnow().year}-{len(_JOURNAL_STORE) + 1:04d}"

        # Build lines with verified accounts
        processed_lines = []
        for line in entry_in.lines:
            acc = self.get_account_by_code(line.account_code, org_id)
            acc_name = line.account_name or (acc["account_name"] if acc else "Unknown Account")
            acc_id = line.account_id or (acc["id"] if acc else f"acc_{line.account_code}")

            processed_lines.append({
                "id": str(uuid.uuid4()),
                "journal_entry_id": entry_id,
                "account_id": acc_id,
                "account_code": line.account_code,
                "account_name": acc_name,
                "debit": to_decimal(line.debit),
                "credit": to_decimal(line.credit),
                "description": line.description or entry_in.description
            })

        entry_dict = {
            "id": entry_id,
            "organization_id": org_id,
            "property_id": entry_in.property_id,
            "entry_number": entry_num,
            "entry_date": entry_in.entry_date or datetime.utcnow(),
            "entry_type": entry_in.entry_type,
            "reference": entry_in.reference,
            "description": entry_in.description,
            "status": "POSTED",
            "total_debit": total_debits,
            "total_credit": total_credits,
            "posted_at": datetime.utcnow(),
            "posted_by_user_id": user_id,
            "reversal_entry_id": None,
            "lines": processed_lines,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        _JOURNAL_STORE[entry_id] = entry_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="JOURNAL_ENTRY_POSTED",
            resource_type="journal_entry",
            resource_id=entry_id,
            organization_id=org_id,
            details={"entry_number": entry_num, "total_debit": str(total_debits)}
        )
        return entry_dict

    def reverse_journal_entry(
        self,
        entry_id: str,
        reason: str = "Correction reversal",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reverse a posted journal entry by creating an opposite mirror entry.
        Original entry is marked REVERSED and linked to the new reversal entry.
        """
        _seed_finance_data()
        original = _JOURNAL_STORE.get(entry_id)
        if not original:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found.")

        if original["status"] != "POSTED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reverse journal entry with status '{original['status']}'. Only POSTED entries can be reversed."
            )

        reversal_id = f"je_rev_{str(uuid.uuid4())[:8]}"
        reversal_num = f"REV-{original['entry_number']}"

        # Invert debits and credits
        reversal_lines = []
        for line in original["lines"]:
            reversal_lines.append({
                "id": str(uuid.uuid4()),
                "journal_entry_id": reversal_id,
                "account_id": line["account_id"],
                "account_code": line["account_code"],
                "account_name": line["account_name"],
                "debit": line["credit"],   # Swap debit and credit
                "credit": line["debit"],
                "description": f"Reversal of {original['entry_number']}: {line.get('description', '')}"
            })

        reversal_dict = {
            "id": reversal_id,
            "organization_id": original["organization_id"],
            "property_id": original.get("property_id"),
            "entry_number": reversal_num,
            "entry_date": datetime.utcnow(),
            "entry_type": "REVERSAL",
            "reference": original["entry_number"],
            "description": f"Reversal of {original['entry_number']} — Reason: {reason}",
            "status": "POSTED",
            "total_debit": original["total_credit"],
            "total_credit": original["total_debit"],
            "posted_at": datetime.utcnow(),
            "posted_by_user_id": user_id,
            "reversal_entry_id": original["id"],
            "lines": reversal_lines,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Update original status
        original["status"] = "REVERSED"
        original["reversal_entry_id"] = reversal_id
        original["updated_at"] = datetime.utcnow()

        _JOURNAL_STORE[reversal_id] = reversal_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="JOURNAL_ENTRY_REVERSED",
            resource_type="journal_entry",
            resource_id=entry_id,
            organization_id=original["organization_id"],
            details={"original_entry": original["entry_number"], "reversal_entry": reversal_num, "reason": reason}
        )
        return reversal_dict

    # --- Accounts Receivable (Customer Invoices) ---
    def get_invoices(
        self,
        organization_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        _seed_finance_data()
        invoices = list(_INVOICE_STORE.values())

        if organization_id:
            invoices = [i for i in invoices if i["organization_id"] == organization_id]
        if customer_id:
            invoices = [i for i in invoices if i["customer_id"] == customer_id]
        if status_filter:
            invoices = [i for i in invoices if i["status"].lower() == status_filter.lower()]

        return sorted(invoices, key=lambda x: x["issue_date"], reverse=True)

    def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        _seed_finance_data()
        return _INVOICE_STORE.get(invoice_id)

    def create_invoice(
        self,
        invoice_in: CustomerInvoiceCreate,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a customer invoice and automatically post balanced double-entry GL journal:
        - Debit 1020 Accounts Receivable (total_amount)
        - Credit 4010 Hospitality & Room Revenue (subtotal)
        - Credit 2020 Sales Tax Payable (tax_amount)
        """
        _seed_finance_data()
        org_id = invoice_in.organization_id or DEMO_ORGANISATIONS[0]["id"]

        if not invoice_in.lines:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invoice must contain at least one line item.")

        invoice_id = f"inv_{str(uuid.uuid4())[:8]}"
        invoice_num = invoice_in.invoice_number or f"INV-{datetime.utcnow().year}-{len(_INVOICE_STORE) + 1:04d}"

        # Calculate totals
        totals = calculate_invoice_totals(invoice_in.lines, invoice_in.tax_rate_percent)
        subtotal = totals["subtotal"]
        tax_amount = totals["tax_amount"]
        total_amount = totals["total_amount"]

        processed_lines = []
        for line in invoice_in.lines:
            line_amt = (line.amount if line.amount is not None else to_decimal(line.quantity) * to_decimal(line.unit_price))
            processed_lines.append({
                "id": str(uuid.uuid4()),
                "invoice_id": invoice_id,
                "product_id": line.product_id,
                "description": line.description,
                "quantity": to_decimal(line.quantity),
                "unit_price": to_decimal(line.unit_price),
                "amount": line_amt
            })

        # Automatically construct and post GL Journal Entry
        gl_lines = [
            JournalLineCreate(
                account_code="1020",
                account_name="Accounts Receivable (AR)",
                debit=total_amount,
                credit=Decimal("0.00"),
                description=f"Invoice {invoice_num} to {invoice_in.customer_name or invoice_in.customer_id}"
            ),
            JournalLineCreate(
                account_code="4010",
                account_name="Hospitality & Lodging Revenue",
                debit=Decimal("0.00"),
                credit=subtotal,
                description=f"Revenue for Invoice {invoice_num}"
            )
        ]
        if tax_amount > Decimal("0.00"):
            gl_lines.append(
                JournalLineCreate(
                    account_code="2020",
                    account_name="Sales Tax & GST Payable",
                    debit=Decimal("0.00"),
                    credit=tax_amount,
                    description=f"Sales Tax for Invoice {invoice_num}"
                )
            )

        je_create = JournalEntryCreate(
            organization_id=org_id,
            property_id=invoice_in.property_id,
            entry_type="INVOICE",
            reference=invoice_num,
            description=f"Automated GL post for Customer Invoice {invoice_num}",
            lines=gl_lines
        )
        posted_je = self.create_journal_entry(je_create, user_id=user_id)

        invoice_dict = {
            "id": invoice_id,
            "organization_id": org_id,
            "property_id": invoice_in.property_id,
            "invoice_number": invoice_num,
            "customer_id": invoice_in.customer_id,
            "customer_name": invoice_in.customer_name or invoice_in.customer_id,
            "issue_date": invoice_in.issue_date or datetime.utcnow(),
            "due_date": invoice_in.due_date,
            "status": "ISSUED",
            "currency": invoice_in.currency,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "paid_amount": Decimal("0.00"),
            "balance_due": total_amount,
            "journal_entry_id": posted_je["id"],
            "notes": invoice_in.notes,
            "lines": processed_lines,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        _INVOICE_STORE[invoice_id] = invoice_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="CUSTOMER_INVOICE_CREATED",
            resource_type="customer_invoice",
            resource_id=invoice_id,
            organization_id=org_id,
            details={"invoice_number": invoice_num, "total_amount": str(total_amount)}
        )
        return invoice_dict

    def record_customer_payment(
        self,
        payment_in: CustomerPaymentCreate,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a customer payment against an invoice and post GL Journal:
        - Debit 1010 Operating Cash & Bank Account
        - Credit 1020 Accounts Receivable
        """
        _seed_finance_data()
        invoice = _INVOICE_STORE.get(payment_in.invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

        pay_amt = to_decimal(payment_in.amount)
        if pay_amt <= Decimal("0.00"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Payment amount must be greater than zero.")

        if pay_amt > invoice["balance_due"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Payment amount ({pay_amt}) exceeds balance due ({invoice['balance_due']})."
            )

        pay_id = f"pay_{str(uuid.uuid4())[:8]}"
        pay_num = f"PAY-{datetime.utcnow().year}-{len(_PAYMENT_STORE) + 1:04d}"

        # Post GL Journal Entry for payment
        gl_lines = [
            JournalLineCreate(
                account_code="1010",
                account_name="Operating Cash & Bank Account",
                debit=pay_amt,
                credit=Decimal("0.00"),
                description=f"Payment received for {invoice['invoice_number']}"
            ),
            JournalLineCreate(
                account_code="1020",
                account_name="Accounts Receivable (AR)",
                debit=Decimal("0.00"),
                credit=pay_amt,
                description=f"AR settlement for {invoice['invoice_number']}"
            )
        ]
        je_create = JournalEntryCreate(
            organization_id=invoice["organization_id"],
            property_id=invoice.get("property_id"),
            entry_type="PAYMENT",
            reference=pay_num,
            description=f"Customer Payment {pay_num} for Invoice {invoice['invoice_number']}",
            lines=gl_lines
        )
        posted_je = self.create_journal_entry(je_create, user_id=user_id)

        # Update invoice
        new_paid = invoice["paid_amount"] + pay_amt
        new_balance = invoice["total_amount"] - new_paid
        invoice["paid_amount"] = new_paid
        invoice["balance_due"] = new_balance
        invoice["status"] = "PAID" if new_balance == Decimal("0.00") else "PARTIALLY_PAID"
        invoice["updated_at"] = datetime.utcnow()

        payment_dict = {
            "id": pay_id,
            "organization_id": invoice["organization_id"],
            "property_id": invoice.get("property_id"),
            "payment_number": pay_num,
            "customer_id": invoice["customer_id"],
            "invoice_id": invoice["id"],
            "payment_date": payment_in.payment_date or datetime.utcnow(),
            "payment_method": payment_in.payment_method,
            "amount": pay_amt,
            "reference": payment_in.reference,
            "journal_entry_id": posted_je["id"],
            "created_at": datetime.utcnow()
        }
        _PAYMENT_STORE[pay_id] = payment_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="CUSTOMER_PAYMENT_RECORDED",
            resource_type="customer_payment",
            resource_id=pay_id,
            organization_id=invoice["organization_id"],
            details={"payment_number": pay_num, "amount": str(pay_amt), "invoice_number": invoice["invoice_number"]}
        )
        return payment_dict

    # --- Accounts Payable (Supplier Bills) ---
    def get_bills(
        self,
        organization_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        _seed_finance_data()
        bills = list(_BILL_STORE.values())

        if organization_id:
            bills = [b for b in bills if b["organization_id"] == organization_id]
        if supplier_id:
            bills = [b for b in bills if b["supplier_id"] == supplier_id]
        if status_filter:
            bills = [b for b in bills if b["status"].lower() == status_filter.lower()]

        return sorted(bills, key=lambda x: x["bill_date"], reverse=True)

    def get_bill_by_id(self, bill_id: str) -> Optional[Dict[str, Any]]:
        _seed_finance_data()
        return _BILL_STORE.get(bill_id)

    def create_bill(
        self,
        bill_in: SupplierBillCreate,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a supplier bill and post GL Journal:
        - Debit Expense Account (e.g. 5010 COGS or 6060 Maintenance Supplies)
        - Credit 2010 Accounts Payable
        """
        _seed_finance_data()
        org_id = bill_in.organization_id or DEMO_ORGANISATIONS[0]["id"]

        if not bill_in.lines:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Bill must contain at least one line item.")

        bill_id = f"bill_{str(uuid.uuid4())[:8]}"
        bill_num = bill_in.bill_number or f"BILL-{datetime.utcnow().year}-{len(_BILL_STORE) + 1:04d}"

        # Calculate total
        total_amount = Decimal("0.00")
        processed_lines = []
        for line in bill_in.lines:
            amt = (line.amount if line.amount is not None else to_decimal(line.quantity) * to_decimal(line.unit_price))
            total_amount += amt
            processed_lines.append({
                "id": str(uuid.uuid4()),
                "bill_id": bill_id,
                "account_id": line.account_id,
                "description": line.description,
                "quantity": to_decimal(line.quantity),
                "unit_price": to_decimal(line.unit_price),
                "amount": amt
            })

        # Post GL Journal
        gl_lines = [
            JournalLineCreate(
                account_code="5010",
                account_name="Food & Beverage Cost of Sales",
                debit=total_amount,
                credit=Decimal("0.00"),
                description=f"Supplier Bill {bill_num} from {bill_in.supplier_name or bill_in.supplier_id}"
            ),
            JournalLineCreate(
                account_code="2010",
                account_name="Accounts Payable (AP)",
                debit=Decimal("0.00"),
                credit=total_amount,
                description=f"Payable for Bill {bill_num}"
            )
        ]
        je_create = JournalEntryCreate(
            organization_id=org_id,
            property_id=bill_in.property_id,
            entry_type="BILL",
            reference=bill_num,
            description=f"Automated GL post for Supplier Bill {bill_num}",
            lines=gl_lines
        )
        posted_je = self.create_journal_entry(je_create, user_id=user_id)

        bill_dict = {
            "id": bill_id,
            "organization_id": org_id,
            "property_id": bill_in.property_id,
            "bill_number": bill_num,
            "supplier_id": bill_in.supplier_id,
            "supplier_name": bill_in.supplier_name or bill_in.supplier_id,
            "vendor_invoice_ref": bill_in.vendor_invoice_ref,
            "bill_date": bill_in.bill_date or datetime.utcnow(),
            "due_date": bill_in.due_date,
            "status": "RECEIVED",
            "currency": bill_in.currency,
            "total_amount": total_amount,
            "paid_amount": Decimal("0.00"),
            "balance_due": total_amount,
            "journal_entry_id": posted_je["id"],
            "notes": bill_in.notes,
            "lines": processed_lines,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        _BILL_STORE[bill_id] = bill_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="SUPPLIER_BILL_CREATED",
            resource_type="supplier_bill",
            resource_id=bill_id,
            organization_id=org_id,
            details={"bill_number": bill_num, "total_amount": str(total_amount)}
        )
        return bill_dict

    def record_bill_payment(
        self,
        payment_in: BillPaymentCreate,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a payment disbursed for a supplier bill and post GL Journal:
        - Debit 2010 Accounts Payable
        - Credit 1010 Operating Cash & Bank Account
        """
        _seed_finance_data()
        bill = _BILL_STORE.get(payment_in.bill_id)
        if not bill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found.")

        pay_amt = to_decimal(payment_in.amount)
        if pay_amt <= Decimal("0.00"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Payment amount must be greater than zero.")

        if pay_amt > bill["balance_due"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Payment amount ({pay_amt}) exceeds bill balance due ({bill['balance_due']})."
            )

        pay_id = f"bpay_{str(uuid.uuid4())[:8]}"
        pay_num = f"BPAY-{datetime.utcnow().year}-{len(_BILL_PAYMENT_STORE) + 1:04d}"

        # Post GL Journal
        gl_lines = [
            JournalLineCreate(
                account_code="2010",
                account_name="Accounts Payable (AP)",
                debit=pay_amt,
                credit=Decimal("0.00"),
                description=f"AP settlement for {bill['bill_number']}"
            ),
            JournalLineCreate(
                account_code="1010",
                account_name="Operating Cash & Bank Account",
                debit=Decimal("0.00"),
                credit=pay_amt,
                description=f"Disbursement for {bill['bill_number']}"
            )
        ]
        je_create = JournalEntryCreate(
            organization_id=bill["organization_id"],
            property_id=bill.get("property_id"),
            entry_type="PAYMENT",
            reference=pay_num,
            description=f"Supplier Bill Payment {pay_num} for Bill {bill['bill_number']}",
            lines=gl_lines
        )
        posted_je = self.create_journal_entry(je_create, user_id=user_id)

        new_paid = bill["paid_amount"] + pay_amt
        new_balance = bill["total_amount"] - new_paid
        bill["paid_amount"] = new_paid
        bill["balance_due"] = new_balance
        bill["status"] = "PAID" if new_balance == Decimal("0.00") else "PARTIALLY_PAID"
        bill["updated_at"] = datetime.utcnow()

        payment_dict = {
            "id": pay_id,
            "organization_id": bill["organization_id"],
            "property_id": bill.get("property_id"),
            "payment_number": pay_num,
            "supplier_id": bill["supplier_id"],
            "bill_id": bill["id"],
            "payment_date": payment_in.payment_date or datetime.utcnow(),
            "payment_method": payment_in.payment_method,
            "amount": pay_amt,
            "reference": payment_in.reference,
            "journal_entry_id": posted_je["id"],
            "created_at": datetime.utcnow()
        }
        _BILL_PAYMENT_STORE[pay_id] = payment_dict

        audit_service.log_event(
            user_id=user_id or "system",
            username=user_id or "System",
            action="SUPPLIER_PAYMENT_RECORDED",
            resource_type="bill_payment",
            resource_id=pay_id,
            organization_id=bill["organization_id"],
            details={"payment_number": pay_num, "amount": str(pay_amt), "bill_number": bill["bill_number"]}
        )
        return payment_dict

    # --- Financial Reports Engine ---
    def _calculate_all_account_balances(self, organization_id: Optional[str] = None) -> Dict[str, Decimal]:
        """Aggregate debits and credits across all POSTED journals per account code."""
        _seed_finance_data()
        account_debits: Dict[str, Decimal] = {}
        account_credits: Dict[str, Decimal] = {}

        for je in _JOURNAL_STORE.values():
            if je["status"] != "POSTED":
                continue
            if organization_id and je["organization_id"] != organization_id:
                continue

            for line in je["lines"]:
                code = line["account_code"]
                account_debits[code] = account_debits.get(code, Decimal("0.00")) + to_decimal(line["debit"])
                account_credits[code] = account_credits.get(code, Decimal("0.00")) + to_decimal(line["credit"])

        balances: Dict[str, Decimal] = {}
        for acc in _ACCOUNT_STORE.values():
            code = acc["account_code"]
            deb = account_debits.get(code, Decimal("0.00"))
            crd = account_credits.get(code, Decimal("0.00"))
            balances[code] = calculate_account_net_balance(acc["account_type"], deb, crd)

        return balances

    def get_trial_balance(self, organization_id: Optional[str] = None) -> TrialBalanceResponse:
        """
        Generate formal Trial Balance verifying: Total Debits == Total Credits.
        """
        _seed_finance_data()
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        accounts = [a for a in _ACCOUNT_STORE.values() if a["organization_id"] == org_id]
        accounts = sorted(accounts, key=lambda x: x["account_code"])

        # Aggregate line debits and credits
        debit_totals: Dict[str, Decimal] = {}
        credit_totals: Dict[str, Decimal] = {}
        for je in _JOURNAL_STORE.values():
            if je["status"] != "POSTED" or je["organization_id"] != org_id:
                continue
            for line in je["lines"]:
                c = line["account_code"]
                debit_totals[c] = debit_totals.get(c, Decimal("0.00")) + to_decimal(line["debit"])
                credit_totals[c] = credit_totals.get(c, Decimal("0.00")) + to_decimal(line["credit"])

        rows = []
        grand_debit = Decimal("0.00")
        grand_credit = Decimal("0.00")

        for acc in accounts:
            code = acc["account_code"]
            deb = debit_totals.get(code, Decimal("0.00"))
            crd = credit_totals.get(code, Decimal("0.00"))
            if deb == Decimal("0.00") and crd == Decimal("0.00"):
                continue

            # Determine ending debit or credit based on net
            net = deb - crd
            ending_deb = net if net > 0 else Decimal("0.00")
            ending_crd = abs(net) if net < 0 else Decimal("0.00")

            rows.append(TrialBalanceRow(
                account_code=code,
                account_name=acc["account_name"],
                account_type=acc["account_type"],
                debit_total=deb,
                credit_total=crd,
                ending_debit=ending_deb,
                ending_credit=ending_crd
            ))
            grand_debit += deb
            grand_credit += crd

        return TrialBalanceResponse(
            organization_id=org_id,
            as_of_date=datetime.utcnow(),
            rows=rows,
            total_debits=grand_debit,
            total_credits=grand_credit,
            is_balanced=(grand_debit == grand_credit)
        )

    def get_profit_and_loss(self, organization_id: Optional[str] = None) -> ProfitAndLossResponse:
        """
        Generate Profit and Loss (Income Statement):
        Revenue - COGS = Gross Profit
        Gross Profit - Operating Expenses = Operating Income (Net Profit)
        """
        _seed_finance_data()
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        balances = self._calculate_all_account_balances(org_id)

        revenue_list = []
        cogs_list = []
        expense_list = []

        total_revenue = Decimal("0.00")
        total_cogs = Decimal("0.00")
        total_expenses = Decimal("0.00")

        for acc in _ACCOUNT_STORE.values():
            if acc["organization_id"] != org_id:
                continue
            code = acc["account_code"]
            bal = balances.get(code, Decimal("0.00"))
            if bal == Decimal("0.00"):
                continue

            entry = {"code": code, "name": acc["account_name"], "amount": bal}
            acc_type = acc["account_type"].upper()

            if acc_type == "REVENUE":
                revenue_list.append(entry)
                total_revenue += bal
            elif acc_type == "COGS":
                cogs_list.append(entry)
                total_cogs += bal
            elif acc_type == "EXPENSE":
                expense_list.append(entry)
                total_expenses += bal

        gross_profit = total_revenue - total_cogs
        net_profit = gross_profit - total_expenses

        return ProfitAndLossResponse(
            organization_id=org_id,
            period_end=datetime.utcnow(),
            revenue=AccountCategorySummary(category="Revenue", accounts=revenue_list, total=total_revenue),
            cogs=AccountCategorySummary(category="Cost of Goods Sold", accounts=cogs_list, total=total_cogs),
            gross_profit=gross_profit,
            operating_expenses=AccountCategorySummary(category="Operating Expenses", accounts=expense_list, total=total_expenses),
            operating_income=net_profit,
            net_profit=net_profit
        )

    def get_balance_sheet(self, organization_id: Optional[str] = None) -> BalanceSheetResponse:
        """
        Generate formal Balance Sheet verifying the fundamental accounting equation:
        Assets == Liabilities + Equity (+ Current Earnings)
        """
        _seed_finance_data()
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        balances = self._calculate_all_account_balances(org_id)

        assets_list = []
        liab_list = []
        equity_list = []

        total_assets = Decimal("0.00")
        total_liabilities = Decimal("0.00")
        total_equity = Decimal("0.00")

        for acc in _ACCOUNT_STORE.values():
            if acc["organization_id"] != org_id:
                continue
            code = acc["account_code"]
            bal = balances.get(code, Decimal("0.00"))
            if bal == Decimal("0.00"):
                continue

            entry = {"code": code, "name": acc["account_name"], "amount": bal}
            acc_type = acc["account_type"].upper()

            if acc_type == "ASSET":
                assets_list.append(entry)
                total_assets += bal
            elif acc_type == "LIABILITY":
                liab_list.append(entry)
                total_liabilities += bal
            elif acc_type == "EQUITY":
                equity_list.append(entry)
                total_equity += bal

        # Calculate current earnings from P&L
        pnl = self.get_profit_and_loss(org_id)
        current_earnings = pnl.net_profit

        total_liab_and_equity = total_liabilities + total_equity + current_earnings
        is_balanced = (total_assets == total_liab_and_equity)

        return BalanceSheetResponse(
            organization_id=org_id,
            as_of_date=datetime.utcnow(),
            assets=AccountCategorySummary(category="Assets", accounts=assets_list, total=total_assets),
            liabilities=AccountCategorySummary(category="Liabilities", accounts=liab_list, total=total_liabilities),
            equity=AccountCategorySummary(category="Equity", accounts=equity_list, total=total_equity),
            current_earnings=current_earnings,
            total_assets=total_assets,
            total_liabilities_and_equity=total_liab_and_equity,
            is_balanced=is_balanced
        )


# Singleton instance
finance_service = FinanceService()
