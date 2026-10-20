"""Victory Crest One - Integration Tests for Finance and Accounting API
Tests Chart of Accounts, Double-Entry Journals, AR Invoices, AP Bills, and Financial Reports.
"""

from decimal import Decimal
from fastapi.testclient import TestClient


def _get_admin_token(api_client: TestClient) -> str:
    res = api_client.post("/api/v1/auth/login", json={"username_or_email": "admin", "password": "AdminPassword123!"})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_list_chart_of_accounts(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    res = api_client.get("/api/v1/finance/accounts", headers=headers)
    assert res.status_code == 200
    accounts = res.json()
    assert len(accounts) >= 15
    codes = [a["account_code"] for a in accounts]
    assert "1010" in codes  # Operating Cash
    assert "1020" in codes  # Accounts Receivable
    assert "2010" in codes  # Accounts Payable
    assert "3010" in codes  # Owner Capital


def test_create_account(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    new_acc = {
        "account_code": "6080",
        "account_name": "Audit and Legal Advisory",
        "account_type": "EXPENSE",
        "normal_balance": "DEBIT",
        "description": "External audit compliance fees"
    }
    res = api_client.post("/api/v1/finance/accounts", json=new_acc, headers=headers)
    assert res.status_code == 201
    created = res.json()
    assert created["account_code"] == "6080"
    assert created["account_name"] == "Audit and Legal Advisory"

    # Duplicate code rejection
    dup_res = api_client.post("/api/v1/finance/accounts", json=new_acc, headers=headers)
    assert dup_res.status_code == 409


def test_journal_entries_and_balanced_invariant(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Unbalanced entry must fail with HTTP 422
    unbalanced = {
        "description": "Unbalanced test transaction",
        "reference": "FAIL-001",
        "entry_type": "GENERAL",
        "lines": [
            {"account_code": "1010", "debit": "1000.00", "credit": "0.00"},
            {"account_code": "6030", "debit": "0.00", "credit": "900.00"},
        ]
    }
    fail_res = api_client.post("/api/v1/finance/journals", json=unbalanced, headers=headers)
    assert fail_res.status_code == 422

    # 2. Balanced entry must succeed
    balanced = {
        "description": "Utility bill cash payment",
        "reference": "UTIL-TEST-01",
        "entry_type": "GENERAL",
        "lines": [
            {"account_code": "6030", "account_name": "Utilities & Energy", "debit": "15000.00", "credit": "0.00"},
            {"account_code": "1010", "account_name": "Operating Cash & Bank Account", "debit": "0.00", "credit": "15000.00"},
        ]
    }
    post_res = api_client.post("/api/v1/finance/journals", json=balanced, headers=headers)
    assert post_res.status_code == 201
    je = post_res.json()
    assert je["status"] == "POSTED"
    assert Decimal(str(je["total_debit"])) == Decimal("15000.00")
    assert Decimal(str(je["total_credit"])) == Decimal("15000.00")
    entry_id = je["id"]

    # 3. Reverse posted entry
    rev_res = api_client.post(f"/api/v1/finance/journals/{entry_id}/reverse", json={"reason": "Incorrect utility code"}, headers=headers)
    assert rev_res.status_code == 200
    rev_entry = rev_res.json()
    assert rev_entry["entry_type"] == "REVERSAL"
    assert "REV-" in rev_entry["entry_number"]

    # 4. Attempting to reverse an already reversed entry must fail
    dup_rev = api_client.post(f"/api/v1/finance/journals/{entry_id}/reverse", json={"reason": "Repeat attempt"}, headers=headers)
    assert dup_rev.status_code == 400


def test_customer_invoice_and_payment_flow(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Invoice (AR)
    inv_data = {
        "customer_id": "cust_reliance_corp",
        "customer_name": "Tata Global Technologies Ltd",
        "due_date": "2026-11-20T00:00:00",
        "tax_rate_percent": "18.00",
        "notes": "Annual conference package",
        "lines": [
            {"description": "Executive Suites Booking", "quantity": "2.00", "unit_price": "10000.00"}
        ]
    }
    inv_res = api_client.post("/api/v1/finance/invoices", json=inv_data, headers=headers)
    assert inv_res.status_code == 201
    inv = inv_res.json()
    assert inv["status"] == "ISSUED"
    assert Decimal(str(inv["subtotal"])) == Decimal("20000.00")
    assert Decimal(str(inv["tax_amount"])) == Decimal("3600.00")
    assert Decimal(str(inv["total_amount"])) == Decimal("23600.00")
    assert Decimal(str(inv["balance_due"])) == Decimal("23600.00")
    assert inv["journal_entry_id"] is not None  # Auto-posted GL journal
    inv_id = inv["id"]

    # 2. Make Partial Payment
    pay1_data = {
        "invoice_id": inv_id,
        "amount": "10000.00",
        "payment_method": "BANK_TRANSFER",
        "reference": "NEFT-TEST-001"
    }
    pay1_res = api_client.post("/api/v1/finance/invoices/payments", json=pay1_data, headers=headers)
    assert pay1_res.status_code == 201

    # Check invoice updated status
    inv_updated = api_client.get(f"/api/v1/finance/invoices/{inv_id}", headers=headers).json()
    assert inv_updated["status"] == "PARTIALLY_PAID"
    assert Decimal(str(inv_updated["paid_amount"])) == Decimal("10000.00")
    assert Decimal(str(inv_updated["balance_due"])) == Decimal("13600.00")

    # 3. Pay Remaining Balance
    pay2_data = {
        "invoice_id": inv_id,
        "amount": "13600.00",
        "payment_method": "CREDIT_CARD",
        "reference": "CC-TEST-002"
    }
    pay2_res = api_client.post("/api/v1/finance/invoices/payments", json=pay2_data, headers=headers)
    assert pay2_res.status_code == 201

    # Check invoice fully settled
    inv_settled = api_client.get(f"/api/v1/finance/invoices/{inv_id}", headers=headers).json()
    assert inv_settled["status"] == "PAID"
    assert Decimal(str(inv_settled["balance_due"])) == Decimal("0.00")


def test_supplier_bill_and_disbursement_flow(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Supplier Bill (AP)
    bill_data = {
        "supplier_id": "supp_fresh_farms",
        "supplier_name": "Fresh Organic Farms & Produce",
        "vendor_invoice_ref": "FOF-TEST-550",
        "due_date": "2026-11-15T00:00:00",
        "lines": [
            {"description": "Organic Dairy and Poultry Supply", "quantity": "1.00", "unit_price": "18000.00"}
        ]
    }
    bill_res = api_client.post("/api/v1/finance/bills", json=bill_data, headers=headers)
    assert bill_res.status_code == 201
    bill = bill_res.json()
    assert bill["status"] == "RECEIVED"
    assert Decimal(str(bill["total_amount"])) == Decimal("18000.00")
    assert Decimal(str(bill["balance_due"])) == Decimal("18000.00")
    assert bill["journal_entry_id"] is not None
    bill_id = bill["id"]

    # 2. Pay Bill
    bpay_data = {
        "bill_id": bill_id,
        "amount": "18000.00",
        "payment_method": "BANK_TRANSFER",
        "reference": "DISB-TEST-771"
    }
    bpay_res = api_client.post("/api/v1/finance/bills/payments", json=bpay_data, headers=headers)
    assert bpay_res.status_code == 201

    # Check bill status updated
    bill_updated = api_client.get(f"/api/v1/finance/bills/{bill_id}", headers=headers).json()
    assert bill_updated["status"] == "PAID"
    assert Decimal(str(bill_updated["balance_due"])) == Decimal("0.00")


def test_financial_reports_endpoints(api_client: TestClient):
    token = _get_admin_token(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Trial Balance
    tb_res = api_client.get("/api/v1/finance/reports/trial-balance", headers=headers)
    assert tb_res.status_code == 200
    tb = tb_res.json()
    assert tb["is_balanced"] is True
    assert Decimal(str(tb["total_debits"])) == Decimal(str(tb["total_credits"]))
    assert len(tb["rows"]) >= 5

    # 2. Profit and Loss
    pnl_res = api_client.get("/api/v1/finance/reports/profit-and-loss", headers=headers)
    assert pnl_res.status_code == 200
    pnl = pnl_res.json()
    assert "revenue" in pnl
    assert "cogs" in pnl
    assert "gross_profit" in pnl
    assert "operating_expenses" in pnl
    assert "net_profit" in pnl
    # Gross Profit = Revenue - COGS
    rev = Decimal(str(pnl["revenue"]["total"]))
    cogs = Decimal(str(pnl["cogs"]["total"]))
    gp = Decimal(str(pnl["gross_profit"]))
    assert gp == rev - cogs

    # 3. Balance Sheet
    bs_res = api_client.get("/api/v1/finance/reports/balance-sheet", headers=headers)
    assert bs_res.status_code == 200
    bs = bs_res.json()
    assert "total_assets" in bs
    assert "total_liabilities_and_equity" in bs
    assert bs["is_balanced"] is True
    assert Decimal(str(bs["total_assets"])) == Decimal(str(bs["total_liabilities_and_equity"]))
