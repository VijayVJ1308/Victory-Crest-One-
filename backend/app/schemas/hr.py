"""Victory Crest One - Human Resources (HR) & Payroll Management Schemas
Pydantic DTOs for employee records, shift attendance, leave requests,
salary structures, monthly payroll runs, payslips, and HR executive metrics.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, EmailStr


# -------------------------------------------------------------
# Employee Schemas
# -------------------------------------------------------------
class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department_id: str
    department_name: Optional[str] = None
    designation: str
    employment_type: str = "FULL_TIME"  # FULL_TIME, CONTRACT, PART_TIME, INTERN
    status: str = "ACTIVE"              # ACTIVE, ON_LEAVE, PROBATION, TERMINATED
    date_of_joining: Optional[date] = None
    monthly_gross_salary: Decimal = Field(default=Decimal("0.00"), ge=0)
    pan_number: Optional[str] = None
    bank_account_number: Optional[str] = None
    emergency_contact: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    organization_id: Optional[str] = None
    property_id: Optional[str] = None
    employee_code: Optional[str] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    designation: Optional[str] = None
    employment_type: Optional[str] = None
    status: Optional[str] = None
    monthly_gross_salary: Optional[Decimal] = None
    pan_number: Optional[str] = None
    bank_account_number: Optional[str] = None


class EmployeeOut(EmployeeBase):
    id: str
    organization_id: str
    property_id: str
    employee_code: str
    full_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Attendance Schemas
# -------------------------------------------------------------
class AttendanceClockInRequest(BaseModel):
    employee_id: str
    shift_type: str = "MORNING"  # MORNING, EVENING, NIGHT
    notes: Optional[str] = None


class AttendanceClockOutRequest(BaseModel):
    notes: Optional[str] = None


class AttendanceRecordCreate(BaseModel):
    employee_id: str
    date: date
    shift_type: str = "MORNING"
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    work_hours: Decimal = Decimal("8.00")
    overtime_hours: Decimal = Decimal("0.00")
    status: str = "PRESENT"  # PRESENT, ABSENT, HALF_DAY, LATE, ON_LEAVE
    notes: Optional[str] = None


class AttendanceRecordOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    employee_id: str
    employee_code: str
    employee_name: str
    date: date
    shift_type: str
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    work_hours: Decimal
    overtime_hours: Decimal
    status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Leave Management Schemas
# -------------------------------------------------------------
class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: str = "CASUAL"  # CASUAL, SICK, EARNED, UNPAID
    start_date: date
    end_date: date
    total_days: Decimal = Field(default=Decimal("1.0"), gt=0)
    reason: str


class LeaveReviewRequest(BaseModel):
    status: str  # APPROVED, REJECTED
    reviewed_by: Optional[str] = "HR Manager"
    notes: Optional[str] = None


class LeaveRequestOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    employee_id: str
    employee_code: str
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    total_days: Decimal
    reason: str
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Salary Structure & Payslip Schemas
# -------------------------------------------------------------
class SalaryBreakdownOut(BaseModel):
    gross_salary: Decimal
    basic: Decimal
    hra: Decimal
    conveyance: Decimal
    special_allowance: Decimal
    pf_deduction: Decimal
    professional_tax: Decimal
    tds_deduction: Decimal
    total_deductions: Decimal
    net_salary: Decimal


class PayslipOut(BaseModel):
    id: str
    payroll_run_id: str
    employee_id: str
    employee_code: str
    employee_name: str
    designation: str
    department_name: str
    days_worked: int
    leave_days_unpaid: int
    overtime_hours: Decimal
    overtime_pay: Decimal
    basic_salary: Decimal
    hra: Decimal
    conveyance: Decimal
    special_allowance: Decimal
    gross_earnings: Decimal
    pf_deduction: Decimal
    professional_tax: Decimal
    tds_deduction: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    payment_status: str

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Payroll Run Schemas
# -------------------------------------------------------------
class PayrollRunCreate(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020, le=2050)
    notes: Optional[str] = None


class PayrollRunOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    run_code: str
    month: int
    year: int
    period_start: date
    period_end: date
    status: str
    total_employees: int
    total_gross_earnings: Decimal
    total_statutory_deductions: Decimal
    total_net_disbursement: Decimal
    journal_entry_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    disbursed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    payslips: List[PayslipOut] = []

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# HR & Payroll Metrics Schemas
# -------------------------------------------------------------
class HrMetricsOut(BaseModel):
    total_headcount: int
    active_employees: int
    departments_count: int
    today_attendance_rate: Decimal
    pending_leaves_count: int
    current_month_payroll_cost: Decimal
    current_month_net_disbursed: Decimal
