"""Victory Crest One - Human Resources (HR) & Payroll Management Models
Departments, Employee Master Directory, Shift Attendance, Leave Management,
Salary Structures, Monthly Payroll Runs, and Automated GL Journal Integration.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, DateTime, Date
from backend.app.models.base import Base, BaseModelMixin
from backend.app.models.organization import Department


class Employee(Base, BaseModelMixin):
    """Staff member profile and employment record."""
    __tablename__ = "hr_employees"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)
    department_id = Column(String(36), nullable=False, index=True)
    department_name = Column(String(100), nullable=False)

    employee_code = Column(String(30), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    full_name = Column(String(120), nullable=False, index=True)

    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)

    designation = Column(String(100), nullable=False, index=True)
    employment_type = Column(String(30), default="FULL_TIME", nullable=False)  # FULL_TIME, CONTRACT, PART_TIME, INTERN
    status = Column(String(30), default="ACTIVE", nullable=False, index=True)  # ACTIVE, ON_LEAVE, PROBATION, TERMINATED

    date_of_joining = Column(Date, default=datetime.utcnow, nullable=False)
    monthly_gross_salary = Column(Numeric(12, 2), default=0.00, nullable=False)

    pan_number = Column(String(20), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    emergency_contact = Column(String(100), nullable=True)


class AttendanceRecord(Base, BaseModelMixin):
    """Daily shift clock-in, clock-out, and attendance verification."""
    __tablename__ = "hr_attendance_records"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)
    employee_id = Column(String(36), nullable=False, index=True)
    employee_code = Column(String(30), nullable=False, index=True)
    employee_name = Column(String(120), nullable=False)

    date = Column(Date, default=datetime.utcnow, nullable=False, index=True)
    shift_type = Column(String(30), default="MORNING", nullable=False)  # MORNING, EVENING, NIGHT
    clock_in = Column(DateTime, nullable=True)
    clock_out = Column(DateTime, nullable=True)

    work_hours = Column(Numeric(5, 2), default=8.00, nullable=False)
    overtime_hours = Column(Numeric(5, 2), default=0.00, nullable=False)
    status = Column(String(20), default="PRESENT", nullable=False, index=True)  # PRESENT, ABSENT, HALF_DAY, LATE, ON_LEAVE
    notes = Column(Text, nullable=True)


class LeaveRequest(Base, BaseModelMixin):
    """Paid and unpaid time-off applications."""
    __tablename__ = "hr_leave_requests"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)
    employee_id = Column(String(36), nullable=False, index=True)
    employee_code = Column(String(30), nullable=False, index=True)
    employee_name = Column(String(120), nullable=False)

    leave_type = Column(String(30), default="CASUAL", nullable=False, index=True)  # CASUAL, SICK, EARNED, UNPAID
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Numeric(5, 1), default=1.0, nullable=False)

    reason = Column(Text, nullable=False)
    status = Column(String(20), default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED, CANCELLED

    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)


class PayrollRun(Base, BaseModelMixin):
    """Batch monthly compensation calculation and disbursement."""
    __tablename__ = "hr_payroll_runs"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    run_code = Column(String(50), unique=True, nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    status = Column(String(30), default="DRAFT", nullable=False, index=True)  # DRAFT, CALCULATED, APPROVED, DISBURSED, CANCELLED

    total_employees = Column(Integer, default=0, nullable=False)
    total_gross_earnings = Column(Numeric(14, 2), default=0.00, nullable=False)
    total_statutory_deductions = Column(Numeric(14, 2), default=0.00, nullable=False)
    total_net_disbursement = Column(Numeric(14, 2), default=0.00, nullable=False)

    # GL Journal posting reference (DR 6010 Payroll Expense, CR 2030 Statutory, CR 1010 Bank)
    journal_entry_id = Column(String(36), nullable=True, index=True)

    approved_at = Column(DateTime, nullable=True)
    disbursed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class Payslip(Base, BaseModelMixin):
    """Itemized earnings, deductions, and net wage slip for an employee."""
    __tablename__ = "hr_payslips"

    payroll_run_id = Column(String(36), nullable=False, index=True)
    employee_id = Column(String(36), nullable=False, index=True)
    employee_code = Column(String(30), nullable=False, index=True)
    employee_name = Column(String(120), nullable=False)
    designation = Column(String(100), nullable=False)
    department_name = Column(String(100), nullable=False)

    days_worked = Column(Integer, default=30, nullable=False)
    leave_days_unpaid = Column(Integer, default=0, nullable=False)
    overtime_hours = Column(Numeric(5, 2), default=0.00, nullable=False)
    overtime_pay = Column(Numeric(10, 2), default=0.00, nullable=False)

    basic_salary = Column(Numeric(12, 2), nullable=False)
    hra = Column(Numeric(12, 2), nullable=False)
    conveyance = Column(Numeric(12, 2), nullable=False)
    special_allowance = Column(Numeric(12, 2), nullable=False)
    gross_earnings = Column(Numeric(12, 2), nullable=False)

    pf_deduction = Column(Numeric(12, 2), nullable=False)
    professional_tax = Column(Numeric(12, 2), default=200.00, nullable=False)
    tds_deduction = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_deductions = Column(Numeric(12, 2), nullable=False)

    net_pay = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String(20), default="PENDING", nullable=False)  # PENDING, DISBURSED
