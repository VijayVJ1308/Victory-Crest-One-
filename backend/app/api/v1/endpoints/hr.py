"""Victory Crest One - Human Resources (HR) & Payroll Management REST API Endpoints
Employee Directory, Shift Attendance, Leave Management, Statutory Payroll Processing,
and Automated General Ledger Postings.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Query, Path, Body
from backend.app.schemas.hr import (
    EmployeeCreate, EmployeeUpdate, EmployeeOut,
    AttendanceClockInRequest, AttendanceClockOutRequest, AttendanceRecordOut,
    LeaveRequestCreate, LeaveReviewRequest, LeaveRequestOut,
    SalaryBreakdownOut, PayrollRunCreate, PayrollRunOut,
    HrMetricsOut
)
from backend.app.services.hr_service import hr_service

router = APIRouter(prefix="/hr")


# -------------------------------------------------------------
# Employee Master Directory Endpoints
# -------------------------------------------------------------
@router.get("/employees", response_model=List[EmployeeOut])
def list_employees(
    property_id: Optional[str] = Query(None, description="Filter employees by property ID"),
    department_id: Optional[str] = Query(None, description="Filter employees by department ID"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, ON_LEAVE, PROBATION, TERMINATED)")
):
    """List staff directory with employment status and departmental assignment."""
    return hr_service.list_employees(
        property_id=property_id,
        department_id=department_id,
        status=status
    )


@router.post("/employees", response_model=EmployeeOut)
def create_employee(emp_in: EmployeeCreate):
    """Onboard a new employee with statutory salary structure and department."""
    return hr_service.create_employee(emp_in)


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: str = Path(..., description="Employee ID")):
    """Get detailed profile and compensation data for an employee."""
    return hr_service.get_employee(employee_id)


@router.put("/employees/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: str = Path(..., description="Employee ID"),
    emp_in: EmployeeUpdate = Body(...)
):
    """Update employee details, designation, department, or salary."""
    return hr_service.update_employee(employee_id, emp_in)


@router.get("/employees/{employee_id}/salary-structure", response_model=SalaryBreakdownOut)
def get_employee_salary_structure(employee_id: str = Path(..., description="Employee ID")):
    """Calculate and return statutory salary breakdown (Basic, HRA, PF, PT, TDS, Net)."""
    return hr_service.get_employee_salary_structure(employee_id)


# -------------------------------------------------------------
# Shift Attendance Tracking Endpoints
# -------------------------------------------------------------
@router.get("/attendance", response_model=List[AttendanceRecordOut])
def list_attendance(
    property_id: Optional[str] = Query(None, description="Filter attendance by property ID"),
    date_filter: Optional[date] = Query(None, description="Filter attendance by date (YYYY-MM-DD)")
):
    """List daily employee shift attendance, clock-in/out stamps, and overtime hours."""
    return hr_service.list_attendance(property_id=property_id, date_filter=date_filter)


@router.post("/attendance/clock-in", response_model=AttendanceRecordOut)
def clock_in(req: AttendanceClockInRequest):
    """Record biometric or portal shift clock-in for an employee."""
    return hr_service.clock_in(req)


@router.post("/attendance/{employee_id}/clock-out", response_model=AttendanceRecordOut)
def clock_out(
    employee_id: str = Path(..., description="Employee ID"),
    req: AttendanceClockOutRequest = Body(...)
):
    """Record shift clock-out, calculate hours worked, and record overtime."""
    return hr_service.clock_out(employee_id, req)


# -------------------------------------------------------------
# Leave Management Endpoints
# -------------------------------------------------------------
@router.get("/leaves", response_model=List[LeaveRequestOut])
def list_leaves(
    property_id: Optional[str] = Query(None, description="Filter leaves by property ID"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED)")
):
    """List leave requests and time-off applications across properties."""
    return hr_service.list_leaves(property_id=property_id, status_filter=status)


@router.post("/leaves", response_model=LeaveRequestOut)
def create_leave_request(req_in: LeaveRequestCreate):
    """Submit a paid or unpaid leave application."""
    return hr_service.create_leave_request(req_in)


@router.post("/leaves/{leave_id}/review", response_model=LeaveRequestOut)
def review_leave_request(
    leave_id: str = Path(..., description="Leave Request ID"),
    review_in: LeaveReviewRequest = Body(...)
):
    """Approve or reject a staff leave application with managerial audit comments."""
    return hr_service.review_leave_request(leave_id, review_in)


# -------------------------------------------------------------
# Payroll Processing Endpoints
# -------------------------------------------------------------
@router.get("/payroll/runs", response_model=List[PayrollRunOut])
def list_payroll_runs(
    property_id: Optional[str] = Query(None, description="Filter payroll runs by property ID")
):
    """List monthly payroll runs with itemized staff payslips."""
    return hr_service.list_payroll_runs(property_id=property_id)


@router.post("/payroll/runs", response_model=PayrollRunOut)
def create_payroll_run(run_in: PayrollRunCreate):
    """Generate a new monthly payroll batch and calculate payslips for all active staff."""
    return hr_service.create_payroll_run(run_in)


@router.get("/payroll/runs/{run_id}", response_model=PayrollRunOut)
def get_payroll_run(run_id: str = Path(..., description="Payroll Run ID")):
    """Get detailed payroll run calculation summary and employee payslips."""
    return hr_service.get_payroll_run(run_id)


@router.post("/payroll/runs/{run_id}/disburse", response_model=PayrollRunOut)
def disburse_payroll_run(run_id: str = Path(..., description="Payroll Run ID")):
    """
    Approve & Disburse Payroll Run:
    1. Sets all employee payslips to DISBURSED.
    2. Automatically posts balanced double-entry GL journal in Phase 4 Finance:
       - DR 6010 Payroll & Staff Compensation (Gross Earnings)
       - CR 2030 Accrued Payroll & Statutory Liabilities (PF, ESI, TDS)
       - CR 1010 Main Operating Account (Net Disbursement)
    """
    return hr_service.disburse_payroll_run(run_id)


# -------------------------------------------------------------
# HR Executive Telemetry Metrics
# -------------------------------------------------------------
@router.get("/metrics", response_model=HrMetricsOut)
def get_hr_metrics():
    """Retrieve top-level HR & workforce KPIs (Headcount, Attendance %, Payroll Cost, Pending Leaves)."""
    return hr_service.get_hr_metrics()
