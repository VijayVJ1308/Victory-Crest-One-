"""Victory Crest One - Project Management & Professional Services (PSA) Schemas
Pydantic DTOs for Projects, Milestones, WBS Tasks, Timesheets,
Project Expenses, Milestone Invoicing, and PSA Executive Metrics.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# Milestone Schemas
# -------------------------------------------------------------
class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    milestone_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    due_date: date
    status: str = "PENDING"  # PENDING, IN_PROGRESS, ACHIEVED, INVOICED, CANCELLED


class MilestoneCreate(MilestoneBase):
    project_id: Optional[str] = None


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    milestone_amount: Optional[Decimal] = None
    due_date: Optional[date] = None
    status: Optional[str] = None


class MilestoneOut(MilestoneBase):
    id: str
    project_id: str
    invoice_id: Optional[str] = None
    achieved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Task Schemas
# -------------------------------------------------------------
class TaskBase(BaseModel):
    task_code: str
    title: str
    description: Optional[str] = None
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    estimated_hours: Decimal = Field(default=Decimal("0.00"), ge=0)
    actual_hours: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: str = "TODO"  # TODO, IN_PROGRESS, IN_REVIEW, DONE, BLOCKED
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, URGENT
    due_date: Optional[date] = None


class TaskCreate(TaskBase):
    project_id: Optional[str] = None
    milestone_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    estimated_hours: Optional[Decimal] = None
    actual_hours: Optional[Decimal] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None


class TaskOut(TaskBase):
    id: str
    project_id: str
    milestone_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Timesheet Schemas
# -------------------------------------------------------------
class TimesheetBase(BaseModel):
    work_date: date
    hours: Decimal = Field(gt=0)
    employee_id: Optional[str] = None
    employee_name: str
    is_billable: bool = True
    hourly_billing_rate: Decimal = Field(default=Decimal("2000.00"), ge=0)
    hourly_cost_rate: Decimal = Field(default=Decimal("600.00"), ge=0)
    description: Optional[str] = None
    status: str = "APPROVED"  # DRAFT, SUBMITTED, APPROVED, INVOICED


class TimesheetCreate(TimesheetBase):
    project_id: Optional[str] = None
    task_id: Optional[str] = None


class TimesheetOut(TimesheetBase):
    id: str
    project_id: str
    task_id: Optional[str] = None
    total_billing_amount: Decimal
    total_cost_amount: Decimal
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Expense Schemas
# -------------------------------------------------------------
class ExpenseBase(BaseModel):
    category: str = "MISC"  # TRAVEL, SOFTWARE_LICENSE, EQUIPMENT, SUBCONTRACTOR, MATERIALS, MISC
    amount: Decimal = Field(gt=0)
    expense_date: date
    description: str
    is_billable: bool = True


class ExpenseCreate(ExpenseBase):
    project_id: Optional[str] = None


class ExpenseOut(ExpenseBase):
    id: str
    project_id: str
    journal_entry_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Project Schemas
# -------------------------------------------------------------
class ProjectBase(BaseModel):
    project_code: str
    name: str
    description: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: str
    project_manager_id: Optional[str] = None
    project_manager_name: str
    billing_type: str = "MILESTONE_BASED"  # FIXED_PRICE, TIME_AND_MATERIALS, MILESTONE_BASED, NON_BILLABLE
    status: str = "ACTIVE"  # PLANNING, ACTIVE, ON_HOLD, COMPLETED, CANCELLED
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, URGENT
    start_date: date
    end_date: date
    budget_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class ProjectCreate(ProjectBase):
    organization_id: Optional[str] = None
    property_id: Optional[str] = None
    milestones: List[MilestoneCreate] = []
    tasks: List[TaskCreate] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    customer_name: Optional[str] = None
    project_manager_name: Optional[str] = None
    billing_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_amount: Optional[Decimal] = None
    progress_percent: Optional[Decimal] = None


class ProjectOut(ProjectBase):
    id: str
    organization_id: str
    property_id: str
    billed_amount: Decimal
    actual_cost: Decimal
    progress_percent: Decimal
    milestones: List[MilestoneOut] = []
    tasks: List[TaskOut] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Milestone Invoicing Request / Response
# -------------------------------------------------------------
class MilestoneInvoiceRequest(BaseModel):
    tax_percent: Decimal = Field(default=Decimal("18.00"), ge=0)
    due_days: int = Field(default=30, ge=0)
    notes: Optional[str] = None


class MilestoneInvoiceResponse(BaseModel):
    milestone_id: str
    invoice_id: str
    invoice_number: str
    subtotal: Decimal
    tax_amount: Decimal
    grand_total: Decimal
    journal_entry_id: Optional[str] = None
    message: str


# -------------------------------------------------------------
# PSA Executive Metrics Schemas
# -------------------------------------------------------------
class ProjectMetricsOut(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    total_contract_value: Decimal
    total_billed_revenue: Decimal
    total_actual_costs: Decimal
    profit_margin_percent: Decimal
    total_logged_hours: Decimal
    billable_utilization_rate: Decimal
    pending_milestones_count: int

    model_config = ConfigDict(from_attributes=True)
