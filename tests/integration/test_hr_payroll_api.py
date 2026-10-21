"""Victory Crest One - Integration Tests for Human Resources & Payroll API
Employee Directory, Shift Attendance, Leave Workflow, Monthly Payroll Processing,
and Automated General Ledger Disbursements.
"""

from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_employee_directory_crud_and_salary_breakdown():
    # 1. List employees
    res = client.get("/api/v1/hr/employees")
    assert res.status_code == 200
    emps = res.json()
    assert len(emps) >= 7

    # 2. Onboard new employee
    payload = {
        "first_name": "Deepa",
        "last_name": "Natarajan",
        "email": "deepa.n@victorycrest.internal",
        "phone": "+91 98421 88776",
        "department_id": "dep_culinary_fnb",
        "department_name": "Culinary & F&B Service",
        "designation": "Chef de Partie — Pastry",
        "employment_type": "FULL_TIME",
        "status": "ACTIVE",
        "monthly_gross_salary": 42000.00,
        "pan_number": "AAAPD1234N",
        "bank_account_number": "HDFC0009876543"
    }
    res_create = client.post("/api/v1/hr/employees", json=payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["full_name"] == "Deepa Natarajan"
    assert created["employee_code"].startswith("EMP-2026-")
    assert Decimal(str(created["monthly_gross_salary"])) == Decimal("42000.00")

    # 3. Get single employee
    emp_id = created["id"]
    res_get = client.get(f"/api/v1/hr/employees/{emp_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == emp_id

    # 4. Update employee
    res_up = client.put(f"/api/v1/hr/employees/{emp_id}", json={"designation": "Senior Chef de Partie — Pastry"})
    assert res_up.status_code == 200
    assert res_up.json()["designation"] == "Senior Chef de Partie — Pastry"

    # 5. Get Salary Structure breakdown
    res_sal = client.get(f"/api/v1/hr/employees/{emp_id}/salary-structure")
    assert res_sal.status_code == 200
    sal = res_sal.json()
    assert Decimal(str(sal["gross_salary"])) == Decimal("42000.00")
    # Basic is 50% = 21,000.00
    assert Decimal(str(sal["basic"])) == Decimal("21000.00")
    # PF is 12% of 21,000 = 2,520.00
    assert Decimal(str(sal["pf_deduction"])) == Decimal("2520.00")
    assert Decimal(str(sal["net_salary"])) > 0


def test_shift_attendance_clock_in_and_out():
    # 1. Clock in
    clock_in_payload = {
        "employee_id": "emp_emp_2026_00101",
        "shift_type": "MORNING",
        "notes": "Testing morning clock-in"
    }
    res_in = client.post("/api/v1/hr/attendance/clock-in", json=clock_in_payload)
    assert res_in.status_code == 200
    att = res_in.json()
    assert att["status"] == "PRESENT"
    assert att["shift_type"] == "MORNING"
    assert att["clock_in"] is not None

    # 2. Clock out
    res_out = client.post(
        "/api/v1/hr/attendance/emp_emp_2026_00101/clock-out",
        json={"notes": "Normal shift completion"}
    )
    assert res_out.status_code == 200
    out_rec = res_out.json()
    assert out_rec["clock_out"] is not None
    assert Decimal(str(out_rec["work_hours"])) >= 0

    # 3. List attendance
    res_list = client.get("/api/v1/hr/attendance")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1


def test_leave_request_workflow():
    # 1. Submit leave request
    leave_payload = {
        "employee_id": "emp_emp_2026_00102",
        "leave_type": "SICK",
        "start_date": str(date.today()),
        "end_date": str(date.today()),
        "total_days": 1.0,
        "reason": "Seasonal viral fever recuperation"
    }
    res_apply = client.post("/api/v1/hr/leaves", json=leave_payload)
    assert res_apply.status_code == 200
    leave = res_apply.json()
    assert leave["status"] == "PENDING"
    assert leave["leave_type"] == "SICK"

    # 2. Review and approve
    leave_id = leave["id"]
    res_review = client.post(
        f"/api/v1/hr/leaves/{leave_id}/review",
        json={"status": "APPROVED", "reviewed_by": "Chef Executive", "notes": "Medical certificate verified"}
    )
    assert res_review.status_code == 200
    approved = res_review.json()
    assert approved["status"] == "APPROVED"
    assert approved["reviewed_by"] == "Chef Executive"

    # 3. List leaves with status filter
    res_leaves = client.get("/api/v1/hr/leaves?status=APPROVED")
    assert res_leaves.status_code == 200
    assert any(l["id"] == leave_id for l in res_leaves.json())


def test_payroll_run_and_automated_gl_disbursement():
    # 1. List existing payroll runs
    res_runs = client.get("/api/v1/hr/payroll/runs")
    assert res_runs.status_code == 200
    runs = res_runs.json()
    assert len(runs) >= 1
    # September 2026 run is already seeded and disbursed
    assert any(r["run_code"] == "PAY-2026-09" for r in runs)

    # 2. Calculate new payroll run for November 2026
    batch_payload = {
        "month": 11,
        "year": 2026,
        "notes": "November 2026 staff compensation run"
    }
    res_calc = client.post("/api/v1/hr/payroll/runs", json=batch_payload)
    assert res_calc.status_code == 200
    calc_run = res_calc.json()
    assert calc_run["run_code"] == "PAY-2026-11"
    assert calc_run["status"] == "CALCULATED"
    assert calc_run["total_employees"] >= 7
    assert Decimal(str(calc_run["total_gross_earnings"])) > 0
    assert Decimal(str(calc_run["total_net_disbursement"])) > 0
    assert len(calc_run["payslips"]) >= 7

    # 3. Disburse Payroll & post automated GL journal
    run_id = calc_run["id"]
    res_disburse = client.post(f"/api/v1/hr/payroll/runs/{run_id}/disburse")
    assert res_disburse.status_code == 200
    disbursed = res_disburse.json()
    assert disbursed["status"] == "DISBURSED"
    assert disbursed["journal_entry_id"] is not None
    assert disbursed["disbursed_at"] is not None

    # Verify all payslips in this run are now marked DISBURSED
    for slip in disbursed["payslips"]:
        assert slip["payment_status"] == "DISBURSED"


def test_hr_metrics_telemetry():
    res = client.get("/api/v1/hr/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["total_headcount"] >= 7
    assert metrics["active_employees"] >= 7
    assert metrics["departments_count"] >= 5
    assert Decimal(str(metrics["today_attendance_rate"])) > 0
    assert Decimal(str(metrics["current_month_payroll_cost"])) > 0
    assert Decimal(str(metrics["current_month_net_disbursed"])) > 0
