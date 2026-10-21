"""Victory Crest One - Human Resources (HR) & Payroll Service
Employee Directory, Shift Attendance, Leave Management, Statutory Salary Calculations,
Monthly Payroll Processing, and Automated GL Double-Entry Postings.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.hr import (
    EmployeeCreate, EmployeeUpdate, EmployeeOut,
    AttendanceClockInRequest, AttendanceClockOutRequest, AttendanceRecordOut,
    LeaveRequestCreate, LeaveReviewRequest, LeaveRequestOut,
    SalaryBreakdownOut, PayslipOut, PayrollRunCreate, PayrollRunOut,
    HrMetricsOut
)
from backend.app.schemas.finance import JournalEntryCreate, JournalLineCreate
from backend.app.services.finance_service import finance_service
from backend.app.services.audit_service import audit_service
from shared.calculations import (
    to_decimal, calculate_salary_breakdown, calculate_overtime_pay,
    calculate_payroll_run_totals, calculate_attendance_rate
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory stores
_DEPARTMENT_STORE: Dict[str, Dict[str, Any]] = {}
_EMPLOYEE_STORE: Dict[str, Dict[str, Any]] = {}
_ATTENDANCE_STORE: List[Dict[str, Any]] = []
_LEAVE_STORE: Dict[str, Dict[str, Any]] = {}
_PAYROLL_RUN_STORE: Dict[str, Dict[str, Any]] = {}
_PAYSLIP_STORE: Dict[str, Dict[str, Any]] = {}

_EMP_COUNTER = 100
_RUN_COUNTER = 10


def _seed_hr_data():
    """Populate realistic staff roster, departments, attendance, leaves, and payroll records."""
    global _EMP_COUNTER, _RUN_COUNTER
    if _EMPLOYEE_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]  # Madurai Heritage
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]  # Kodaikanal
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]  # Chennai Hub
    now = datetime.utcnow()
    today = now.date()

    # 1. Seed Departments
    departments = [
        {"id": "dep_front_office", "code": "FO", "name": "Front Office & Concierge", "manager": "P. Meenakshi"},
        {"id": "dep_culinary_fnb", "code": "FNB", "name": "Culinary & F&B Service", "manager": "Chef S. Murugan"},
        {"id": "dep_housekeeping", "code": "HSK", "name": "Housekeeping & Facilities", "manager": "R. Selvi"},
        {"id": "dep_finance_acc", "code": "FIN", "name": "Finance & General Accounting", "manager": "V. Krishnan"},
        {"id": "dep_sales_mktg", "code": "MKT", "name": "Sales & Revenue Optimization", "manager": "D. Karthik"},
        {"id": "dep_engineering", "code": "ENG", "name": "Engineering & Asset Maintenance", "manager": "M. Sundaram"}
    ]
    for d in departments:
        _DEPARTMENT_STORE[d["id"]] = d

    # 2. Seed Employees
    raw_employees = [
        # Madurai
        (
            "EMP-2026-00101", "Meenakshi", "Ponnusamy", "meenakshi.p@victorycrest.internal",
            "+91 98421 11001", "dep_front_office", "Front Office & Concierge",
            "Front Desk & Guest Experience Manager", "FULL_TIME", "ACTIVE",
            today - timedelta(days=750), Decimal("65000.00"), "AAAPM1234F", "HDFC0001827361", prop_mdu
        ),
        (
            "EMP-2026-00102", "Murugan", "Subramanian", "murugan.s@victorycrest.internal",
            "+91 98421 11002", "dep_culinary_fnb", "Culinary & F&B Service",
            "Executive Sous Chef & F&B Lead", "FULL_TIME", "ACTIVE",
            today - timedelta(days=600), Decimal("85000.00"), "AAAPM5678K", "ICIC0009871234", prop_mdu
        ),
        (
            "EMP-2026-00103", "Selvi", "Ramanathan", "selvi.r@victorycrest.internal",
            "+91 98421 11003", "dep_housekeeping", "Housekeeping & Facilities",
            "Executive Housekeeper", "FULL_TIME", "ACTIVE",
            today - timedelta(days=400), Decimal("38000.00"), "AAAPS9012L", "SBI0004567890", prop_mdu
        ),
        (
            "EMP-2026-00104", "Sundaram", "Muthu", "sundaram.m@victorycrest.internal",
            "+91 98421 11004", "dep_engineering", "Engineering & Asset Maintenance",
            "Chief Facilities Engineer", "FULL_TIME", "ACTIVE",
            today - timedelta(days=500), Decimal("52000.00"), "AAAPM3456P", "CAN0001234567", prop_mdu
        ),
        (
            "EMP-2026-00105", "Kavitha", "Anand", "kavitha.a@victorycrest.internal",
            "+91 98421 11005", "dep_front_office", "Front Office & Concierge",
            "Senior Receptionist & Night Auditor", "FULL_TIME", "ACTIVE",
            today - timedelta(days=180), Decimal("32000.00"), "AAAPK7890Q", "HDFC0005544332", prop_mdu
        ),
        # Corporate Finance
        (
            "EMP-2026-00106", "Krishnan", "Venkatesh", "krishnan.v@victorycrest.internal",
            "+91 98421 11006", "dep_finance_acc", "Finance & General Accounting",
            "Chief Financial Officer (CFO)", "FULL_TIME", "ACTIVE",
            today - timedelta(days=900), Decimal("145000.00"), "AAAPV1122R", "KOT0009988776", prop_mdu
        ),
        # Kodaikanal
        (
            "EMP-2026-00107", "Joseph", "Thomas", "joseph.t@victorycrest.internal",
            "+91 98421 11007", "dep_front_office", "Front Office & Concierge",
            "Resort Resident Manager", "FULL_TIME", "ACTIVE",
            today - timedelta(days=360), Decimal("70000.00"), "AAAPJ3344T", "SBI0008877665", prop_kod
        )
    ]

    for code, fn, ln, em, ph, did, dname, desig, etype, st, doj, sal, pan, bank, pid in raw_employees:
        emp_id = f"emp_{code.lower().replace('-', '_')}"
        _EMPLOYEE_STORE[emp_id] = {
            "id": emp_id,
            "organization_id": org_id,
            "property_id": pid,
            "department_id": did,
            "department_name": dname,
            "employee_code": code,
            "first_name": fn,
            "last_name": ln,
            "full_name": f"{fn} {ln}",
            "email": em,
            "phone": ph,
            "designation": desig,
            "employment_type": etype,
            "status": st,
            "date_of_joining": doj,
            "monthly_gross_salary": sal,
            "pan_number": pan,
            "bank_account_number": bank,
            "emergency_contact": "+91 98421 99999",
            "created_at": now - timedelta(days=100),
            "updated_at": now
        }

    # 3. Seed Attendance Records for Today
    for emp in list(_EMPLOYEE_STORE.values())[:5]:
        _ATTENDANCE_STORE.append({
            "id": f"att_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "property_id": emp["property_id"],
            "employee_id": emp["id"],
            "employee_code": emp["employee_code"],
            "employee_name": emp["full_name"],
            "date": today,
            "shift_type": "MORNING",
            "clock_in": now.replace(hour=8, minute=55, second=0),
            "clock_out": None,
            "work_hours": Decimal("8.00"),
            "overtime_hours": Decimal("0.00"),
            "status": "PRESENT",
            "notes": "Biometric fingerprint verification on time",
            "created_at": now
        })

    # 4. Seed Leave Requests
    leave_id = "leave_2026_01"
    _LEAVE_STORE[leave_id] = {
        "id": leave_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "employee_id": "emp_emp_2026_00105",
        "employee_code": "EMP-2026-00105",
        "employee_name": "Kavitha Anand",
        "leave_type": "CASUAL",
        "start_date": today + timedelta(days=3),
        "end_date": today + timedelta(days=4),
        "total_days": Decimal("2.0"),
        "reason": "Family wedding celebration in Madurai",
        "status": "PENDING",
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": now - timedelta(days=1)
    }

    # 5. Seed Prior Month's Disbursed Payroll Run (September 2026)
    sept_run_id = "run_2026_09"
    sept_payslips = []
    tot_gross = Decimal("0.00")
    tot_ded = Decimal("0.00")
    tot_net = Decimal("0.00")

    for emp in _EMPLOYEE_STORE.values():
        brk = calculate_salary_breakdown(emp["monthly_gross_salary"])
        ps_id = f"ps_sept_{emp['employee_code'].lower()}"
        ps = {
            "id": ps_id,
            "payroll_run_id": sept_run_id,
            "employee_id": emp["id"],
            "employee_code": emp["employee_code"],
            "employee_name": emp["full_name"],
            "designation": emp["designation"],
            "department_name": emp["department_name"],
            "days_worked": 30,
            "leave_days_unpaid": 0,
            "overtime_hours": Decimal("4.00"),
            "overtime_pay": calculate_overtime_pay(emp["monthly_gross_salary"], overtime_hours=4),
            "basic_salary": brk["basic"],
            "hra": brk["hra"],
            "conveyance": brk["conveyance"],
            "special_allowance": brk["special_allowance"],
            "gross_earnings": brk["gross_salary"],
            "pf_deduction": brk["pf_deduction"],
            "professional_tax": brk["professional_tax"],
            "tds_deduction": brk["tds_deduction"],
            "total_deductions": brk["total_deductions"],
            "net_pay": brk["net_salary"],
            "payment_status": "DISBURSED"
        }
        _PAYSLIP_STORE[ps_id] = ps
        sept_payslips.append(ps)
        tot_gross += brk["gross_salary"]
        tot_ded += brk["total_deductions"]
        tot_net += brk["net_salary"]

    _PAYROLL_RUN_STORE[sept_run_id] = {
        "id": sept_run_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "run_code": "PAY-2026-09",
        "month": 9,
        "year": 2026,
        "period_start": date(2026, 9, 1),
        "period_end": date(2026, 9, 30),
        "status": "DISBURSED",
        "total_employees": len(sept_payslips),
        "total_gross_earnings": tot_gross,
        "total_statutory_deductions": tot_ded,
        "total_net_disbursement": tot_net,
        "journal_entry_id": "je_payroll_2026_09",
        "approved_at": now - timedelta(days=21),
        "disbursed_at": now - timedelta(days=20),
        "notes": "September 2026 enterprise payroll disbursed via HDFC Bank corporate direct debit.",
        "created_at": now - timedelta(days=22)
    }

    _EMP_COUNTER = 108
    _RUN_COUNTER = 11


class HrService:
    """Enterprise Human Resources and Payroll Execution Service."""

    def __init__(self):
        _seed_hr_data()

    # ---------------------------------------------------------
    # Employee Directory
    # ---------------------------------------------------------
    def list_employees(
        self,
        property_id: Optional[str] = None,
        department_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[EmployeeOut]:
        _seed_hr_data()
        employees = list(_EMPLOYEE_STORE.values())

        if property_id:
            employees = [e for e in employees if e["property_id"] == property_id]
        if department_id:
            employees = [e for e in employees if e["department_id"] == department_id]
        if status:
            s_norm = status.strip().upper()
            employees = [e for e in employees if e["status"].upper() == s_norm]

        employees.sort(key=lambda e: e["employee_code"])
        return [EmployeeOut(**e) for e in employees]

    def get_employee(self, employee_id: str) -> EmployeeOut:
        _seed_hr_data()
        if employee_id not in _EMPLOYEE_STORE:
            raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found")
        return EmployeeOut(**_EMPLOYEE_STORE[employee_id])

    def create_employee(self, emp_in: EmployeeCreate) -> EmployeeOut:
        global _EMP_COUNTER
        _seed_hr_data()
        org_id = emp_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        prop_id = emp_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]

        # Check email uniqueness
        for e in _EMPLOYEE_STORE.values():
            if e["email"].lower() == emp_in.email.lower():
                raise HTTPException(status_code=400, detail=f"Email '{emp_in.email}' already registered.")

        _EMP_COUNTER += 1
        emp_code = emp_in.employee_code or f"EMP-2026-{_EMP_COUNTER:05d}"
        emp_id = f"emp_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        dept_name = emp_in.department_name or _DEPARTMENT_STORE.get(emp_in.department_id, {}).get("name", "Operations")

        record = {
            "id": emp_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "department_id": emp_in.department_id,
            "department_name": dept_name,
            "employee_code": emp_code,
            "first_name": emp_in.first_name,
            "last_name": emp_in.last_name,
            "full_name": f"{emp_in.first_name} {emp_in.last_name}".strip(),
            "email": emp_in.email,
            "phone": emp_in.phone,
            "designation": emp_in.designation,
            "employment_type": emp_in.employment_type.upper(),
            "status": emp_in.status.upper(),
            "date_of_joining": emp_in.date_of_joining or now.date(),
            "monthly_gross_salary": to_decimal(emp_in.monthly_gross_salary),
            "pan_number": emp_in.pan_number,
            "bank_account_number": emp_in.bank_account_number,
            "emergency_contact": emp_in.emergency_contact,
            "created_at": now,
            "updated_at": now
        }
        _EMPLOYEE_STORE[emp_id] = record

        audit_service.record_event(
            action="EMPLOYEE_ONBOARDED",
            entity_type="Employee",
            entity_id=emp_id,
            user_email="hr@victorycrest.internal",
            organization_id=org_id,
            details=f"Onboarded {record['full_name']} ({emp_code}) as {record['designation']}"
        )
        return EmployeeOut(**record)

    def update_employee(self, employee_id: str, emp_in: EmployeeUpdate) -> EmployeeOut:
        _seed_hr_data()
        if employee_id not in _EMPLOYEE_STORE:
            raise HTTPException(status_code=404, detail="Employee not found")

        record = _EMPLOYEE_STORE[employee_id]
        update_data = emp_in.model_dump(exclude_unset=True)

        for k, v in update_data.items():
            if v is not None:
                record[k] = v

        if "first_name" in update_data or "last_name" in update_data:
            record["full_name"] = f"{record['first_name']} {record['last_name']}".strip()

        record["updated_at"] = datetime.utcnow()
        return EmployeeOut(**record)

    # ---------------------------------------------------------
    # Attendance Tracking
    # ---------------------------------------------------------
    def list_attendance(
        self,
        property_id: Optional[str] = None,
        date_filter: Optional[date] = None
    ) -> List[AttendanceRecordOut]:
        _seed_hr_data()
        records = list(_ATTENDANCE_STORE)

        if property_id:
            records = [r for r in records if r["property_id"] == property_id]
        if date_filter:
            records = [r for r in records if r["date"] == date_filter]

        records.sort(key=lambda r: r.get("clock_in") or datetime.min, reverse=True)
        return [AttendanceRecordOut(**r) for r in records]

    def clock_in(self, req: AttendanceClockInRequest) -> AttendanceRecordOut:
        _seed_hr_data()
        emp = self.get_employee(req.employee_id)
        now = datetime.utcnow()
        today = now.date()

        # Check existing clock-in today
        for r in _ATTENDANCE_STORE:
            if r["employee_id"] == emp.id and r["date"] == today:
                r["clock_in"] = now
                r["status"] = "PRESENT"
                if req.notes:
                    r["notes"] = req.notes
                return AttendanceRecordOut(**r)

        rec = {
            "id": f"att_{uuid.uuid4().hex[:8]}",
            "organization_id": emp.organization_id,
            "property_id": emp.property_id,
            "employee_id": emp.id,
            "employee_code": emp.employee_code,
            "employee_name": emp.full_name,
            "date": today,
            "shift_type": req.shift_type.upper(),
            "clock_in": now,
            "clock_out": None,
            "work_hours": Decimal("8.00"),
            "overtime_hours": Decimal("0.00"),
            "status": "PRESENT",
            "notes": req.notes or "Biometric station clock-in",
            "created_at": now
        }
        _ATTENDANCE_STORE.append(rec)
        return AttendanceRecordOut(**rec)

    def clock_out(self, employee_id: str, req: AttendanceClockOutRequest) -> AttendanceRecordOut:
        _seed_hr_data()
        now = datetime.utcnow()
        today = now.date()

        for r in _ATTENDANCE_STORE:
            if r["employee_id"] == employee_id and r["date"] == today:
                r["clock_out"] = now
                if r.get("clock_in"):
                    elapsed = (now - r["clock_in"]).total_seconds() / 3600.0
                    hrs = Decimal(f"{elapsed:.2f}")
                    r["work_hours"] = hrs
                    if hrs > Decimal("8.00"):
                        r["overtime_hours"] = (hrs - Decimal("8.00")).quantize(Decimal("0.01"))
                if req.notes:
                    r["notes"] = f"{r.get('notes') or ''}\nClock-out: {req.notes}".strip()
                return AttendanceRecordOut(**r)

        raise HTTPException(status_code=404, detail="No active clock-in found for today.")

    # ---------------------------------------------------------
    # Leave Management
    # ---------------------------------------------------------
    def list_leaves(
        self,
        property_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[LeaveRequestOut]:
        _seed_hr_data()
        leaves = list(_LEAVE_STORE.values())

        if property_id:
            leaves = [l for l in leaves if l["property_id"] == property_id]
        if status_filter:
            s_norm = status_filter.strip().upper()
            leaves = [l for l in leaves if l["status"].upper() == s_norm]

        leaves.sort(key=lambda l: l.get("created_at") or datetime.min, reverse=True)
        return [LeaveRequestOut(**l) for l in leaves]

    def create_leave_request(self, req_in: LeaveRequestCreate) -> LeaveRequestOut:
        _seed_hr_data()
        emp = self.get_employee(req_in.employee_id)
        leave_id = f"leave_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        record = {
            "id": leave_id,
            "organization_id": emp.organization_id,
            "property_id": emp.property_id,
            "employee_id": emp.id,
            "employee_code": emp.employee_code,
            "employee_name": emp.full_name,
            "leave_type": req_in.leave_type.upper(),
            "start_date": req_in.start_date,
            "end_date": req_in.end_date,
            "total_days": to_decimal(req_in.total_days),
            "reason": req_in.reason,
            "status": "PENDING",
            "reviewed_by": None,
            "reviewed_at": None,
            "created_at": now
        }
        _LEAVE_STORE[leave_id] = record
        return LeaveRequestOut(**record)

    def review_leave_request(self, leave_id: str, review_in: LeaveReviewRequest) -> LeaveRequestOut:
        _seed_hr_data()
        if leave_id not in _LEAVE_STORE:
            raise HTTPException(status_code=404, detail="Leave request not found")

        record = _LEAVE_STORE[leave_id]
        now = datetime.utcnow()
        new_status = review_in.status.upper()
        if new_status not in ("APPROVED", "REJECTED"):
            raise HTTPException(status_code=400, detail="Review status must be APPROVED or REJECTED")

        record["status"] = new_status
        record["reviewed_by"] = review_in.reviewed_by or "HR Operations"
        record["reviewed_at"] = now
        if review_in.notes:
            record["reason"] = f"{record['reason']}\nReview: {review_in.notes}".strip()

        return LeaveRequestOut(**record)

    # ---------------------------------------------------------
    # Payroll Processing & Payslips
    # ---------------------------------------------------------
    def list_payroll_runs(self, property_id: Optional[str] = None) -> List[PayrollRunOut]:
        _seed_hr_data()
        runs = list(_PAYROLL_RUN_STORE.values())
        if property_id:
            runs = [r for r in runs if r["property_id"] == property_id]

        runs.sort(key=lambda r: (r["year"], r["month"]), reverse=True)
        res = []
        for r in runs:
            run_slips = [PayslipOut(**p) for p in _PAYSLIP_STORE.values() if p["payroll_run_id"] == r["id"]]
            res.append(PayrollRunOut(**r, payslips=run_slips))
        return res

    def get_payroll_run(self, run_id: str) -> PayrollRunOut:
        _seed_hr_data()
        if run_id not in _PAYROLL_RUN_STORE:
            raise HTTPException(status_code=404, detail=f"Payroll run '{run_id}' not found")
        run_data = _PAYROLL_RUN_STORE[run_id]
        run_slips = [PayslipOut(**p) for p in _PAYSLIP_STORE.values() if p["payroll_run_id"] == run_id]
        return PayrollRunOut(**run_data, payslips=run_slips)

    def create_payroll_run(self, run_in: PayrollRunCreate) -> PayrollRunOut:
        global _RUN_COUNTER
        _seed_hr_data()
        org_id = DEMO_ORGANISATIONS[0]["id"]
        prop_id = DEMO_ORGANISATIONS[0]["properties"][0]["id"]

        run_code = f"PAY-{run_in.year}-{run_in.month:02d}"
        for r in _PAYROLL_RUN_STORE.values():
            if r["run_code"] == run_code:
                raise HTTPException(status_code=400, detail=f"Payroll run {run_code} already exists.")

        _RUN_COUNTER += 1
        run_id = f"run_{run_in.year}_{run_in.month:02d}"
        now = datetime.utcnow()

        # Generate individual payslips for all active employees
        active_emps = [e for e in _EMPLOYEE_STORE.values() if e["status"] == "ACTIVE"]
        payslips = []
        tot_gross = Decimal("0.00")
        tot_statutory = Decimal("0.00")
        tot_net = Decimal("0.00")

        for emp in active_emps:
            brk = calculate_salary_breakdown(emp["monthly_gross_salary"])
            ps_id = f"ps_{run_id}_{emp['employee_code'].lower()}"
            ps_dict = {
                "id": ps_id,
                "payroll_run_id": run_id,
                "employee_id": emp["id"],
                "employee_code": emp["employee_code"],
                "employee_name": emp["full_name"],
                "designation": emp["designation"],
                "department_name": emp["department_name"],
                "days_worked": 30,
                "leave_days_unpaid": 0,
                "overtime_hours": Decimal("0.00"),
                "overtime_pay": Decimal("0.00"),
                "basic_salary": brk["basic"],
                "hra": brk["hra"],
                "conveyance": brk["conveyance"],
                "special_allowance": brk["special_allowance"],
                "gross_earnings": brk["gross_salary"],
                "pf_deduction": brk["pf_deduction"],
                "professional_tax": brk["professional_tax"],
                "tds_deduction": brk["tds_deduction"],
                "total_deductions": brk["total_deductions"],
                "net_pay": brk["net_salary"],
                "payment_status": "PENDING"
            }
            _PAYSLIP_STORE[ps_id] = ps_dict
            payslips.append(PayslipOut(**ps_dict))
            tot_gross += brk["gross_salary"]
            tot_statutory += brk["total_deductions"]
            tot_net += brk["net_salary"]

        p_start = date(run_in.year, run_in.month, 1)
        p_end = date(run_in.year, run_in.month, 28) if run_in.month == 2 else date(run_in.year, run_in.month, 30)

        record = {
            "id": run_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "run_code": run_code,
            "month": run_in.month,
            "year": run_in.year,
            "period_start": p_start,
            "period_end": p_end,
            "status": "CALCULATED",
            "total_employees": len(payslips),
            "total_gross_earnings": tot_gross,
            "total_statutory_deductions": tot_statutory,
            "total_net_disbursement": tot_net,
            "journal_entry_id": None,
            "approved_at": None,
            "disbursed_at": None,
            "notes": run_in.notes or f"Monthly payroll batch for {run_in.month:02d}/{run_in.year}",
            "created_at": now
        }
        _PAYROLL_RUN_STORE[run_id] = record

        audit_service.record_event(
            action="PAYROLL_RUN_CALCULATED",
            entity_type="PayrollRun",
            entity_id=run_id,
            user_email="payroll@victorycrest.internal",
            organization_id=org_id,
            details=f"Calculated payroll run {run_code} ({len(payslips)} staff) for ₹{tot_gross:,.2f}"
        )
        return PayrollRunOut(**record, payslips=payslips)

    def disburse_payroll_run(
        self,
        run_id: str,
        user_id: str = "usr_superadmin_01",
        user_email: str = "payroll@victorycrest.internal"
    ) -> PayrollRunOut:
        """
        Approve & Disburse Payroll Run with AUTOMATIC GENERAL ACCOUNTING POSTING:
        1. Balanced double-entry GL journal entry:
           - DR 6010 Payroll & Staff Compensation (Gross Earnings)
           - CR 2030 Accrued Payroll & Statutory Liabilities (PF, ESI, TDS)
           - CR 1010 Main Operating Account (Net Disbursement)
        2. Sets all employee payslips to DISBURSED.
        3. Updates payroll run status to DISBURSED.
        """
        _seed_hr_data()
        if run_id not in _PAYROLL_RUN_STORE:
            raise HTTPException(status_code=404, detail="Payroll run not found")

        run = _PAYROLL_RUN_STORE[run_id]
        if run["status"] == "DISBURSED":
            raise HTTPException(status_code=400, detail="Payroll run is already disbursed.")

        now = datetime.utcnow()
        tot_gross = to_decimal(run["total_gross_earnings"])
        tot_statutory = to_decimal(run["total_statutory_deductions"])
        tot_net = to_decimal(run["total_net_disbursement"])

        # -----------------------------------------------------
        # AUTOMATED GL POSTING (Phase 4 Finance Integration)
        # -----------------------------------------------------
        gl_lines = [
            JournalLineCreate(
                account_code="6010",  # Payroll & Staff Compensation (Expense)
                debit=tot_gross,
                credit=Decimal("0.00"),
                description=f"Payroll Gross Earnings - Run {run['run_code']}"
            ),
            JournalLineCreate(
                account_code="2030",  # Accrued Payroll & Statutory Liabilities
                debit=Decimal("0.00"),
                credit=tot_statutory,
                description=f"Statutory Deductions (PF/TDS/PT) - Run {run['run_code']}"
            ),
            JournalLineCreate(
                account_code="1010",  # Main Operating Account (HDFC Bank)
                debit=Decimal("0.00"),
                credit=tot_net,
                description=f"Net Direct Salary Transfers - Run {run['run_code']}"
            )
        ]
        je_create = JournalEntryCreate(
            organization_id=run["organization_id"],
            property_id=run["property_id"],
            entry_type="PAYMENT",
            reference=run["run_code"],
            description=f"Automated GL post for Staff Payroll Disbursement {run['run_code']}",
            lines=gl_lines
        )
        posted_je = finance_service.create_journal_entry(je_create, user_id=user_id)
        je_id = posted_je["id"] if isinstance(posted_je, dict) else getattr(posted_je, "id", "je_payroll")

        # Update run status
        run["status"] = "DISBURSED"
        run["journal_entry_id"] = je_id
        run["approved_at"] = now
        run["disbursed_at"] = now

        # Update all payslips
        for ps in _PAYSLIP_STORE.values():
            if ps["payroll_run_id"] == run_id:
                ps["payment_status"] = "DISBURSED"

        audit_service.record_event(
            action="PAYROLL_DISBURSED",
            entity_type="PayrollRun",
            entity_id=run_id,
            user_email=user_email,
            organization_id=run["organization_id"],
            details=(
                f"Disbursed payroll run {run['run_code']} for ₹{tot_net:,.2f} net (GL: {je_id}). "
                f"Posted to accounts 6010, 2030, and 1010."
            )
        )
        run_slips = [PayslipOut(**p) for p in _PAYSLIP_STORE.values() if p["payroll_run_id"] == run_id]
        return PayrollRunOut(**run, payslips=run_slips)

    def get_employee_salary_structure(self, employee_id: str) -> SalaryBreakdownOut:
        emp = self.get_employee(employee_id)
        brk = calculate_salary_breakdown(emp.monthly_gross_salary)
        return SalaryBreakdownOut(**brk)

    # ---------------------------------------------------------
    # HR Executive Telemetry Metrics
    # ---------------------------------------------------------
    def get_hr_metrics(self) -> HrMetricsOut:
        _seed_hr_data()
        employees = list(_EMPLOYEE_STORE.values())
        active_cnt = len([e for e in employees if e["status"] == "ACTIVE"])
        pending_leaves = len([l for l in _LEAVE_STORE.values() if l["status"] == "PENDING"])

        # Calculate monthly payroll cost
        monthly_cost = sum((to_decimal(e["monthly_gross_salary"]) for e in employees if e["status"] == "ACTIVE"), Decimal("0.00"))

        # Disbursed runs
        disbursed_runs = [r for r in _PAYROLL_RUN_STORE.values() if r["status"] == "DISBURSED"]
        tot_disbursed = sum((to_decimal(r["total_net_disbursement"]) for r in disbursed_runs), Decimal("0.00"))

        # Today's attendance rate
        today = datetime.utcnow().date()
        today_att = [a for a in _ATTENDANCE_STORE if a["date"] == today]
        present_cnt = len([a for a in today_att if a["status"] in ("PRESENT", "LATE")])
        rostered_cnt = max(active_cnt, 1)
        att_rate = calculate_attendance_rate(rostered_cnt, present_cnt)

        return HrMetricsOut(
            total_headcount=len(employees),
            active_employees=active_cnt,
            departments_count=len(_DEPARTMENT_STORE),
            today_attendance_rate=att_rate,
            pending_leaves_count=pending_leaves,
            current_month_payroll_cost=monthly_cost.quantize(Decimal("0.01")),
            current_month_net_disbursed=tot_disbursed.quantize(Decimal("0.01"))
        )


hr_service = HrService()
