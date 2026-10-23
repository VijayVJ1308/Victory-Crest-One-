"""Victory Crest One - Project Management & Professional Services (PSA) Models
Projects, Milestones, WBS Tasks, Timesheets, Project Expenses, and Milestone Invoicing.
"""

from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, Date, Integer
from backend.app.models.base import Base, BaseModelMixin


class Project(Base, BaseModelMixin):
    """Client professional services or capital infrastructure project."""
    __tablename__ = "pm_projects"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    project_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    customer_id = Column(String(36), nullable=True, index=True)
    customer_name = Column(String(255), nullable=False)

    project_manager_id = Column(String(36), nullable=True, index=True)
    project_manager_name = Column(String(255), nullable=False)

    billing_type = Column(String(30), default="MILESTONE_BASED", nullable=False)  # FIXED_PRICE, TIME_AND_MATERIALS, MILESTONE_BASED, NON_BILLABLE
    status = Column(String(30), default="ACTIVE", nullable=False, index=True)       # PLANNING, ACTIVE, ON_HOLD, COMPLETED, CANCELLED
    priority = Column(String(20), default="NORMAL", nullable=False, index=True)     # LOW, NORMAL, HIGH, URGENT

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    budget_amount = Column(Numeric(14, 2), default=0.00, nullable=False)
    billed_amount = Column(Numeric(14, 2), default=0.00, nullable=False)
    actual_cost = Column(Numeric(14, 2), default=0.00, nullable=False)
    progress_percent = Column(Numeric(5, 2), default=0.00, nullable=False)


class ProjectMilestone(Base, BaseModelMixin):
    """Contractual project milestone for progress tracking and progress invoicing."""
    __tablename__ = "pm_milestones"

    project_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    milestone_amount = Column(Numeric(14, 2), default=0.00, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, IN_PROGRESS, ACHIEVED, INVOICED, CANCELLED
    invoice_id = Column(String(36), nullable=True, index=True)
    achieved_at = Column(DateTime, nullable=True)


class ProjectTask(Base, BaseModelMixin):
    """Work Breakdown Structure (WBS) task assignment."""
    __tablename__ = "pm_tasks"

    project_id = Column(String(36), nullable=False, index=True)
    milestone_id = Column(String(36), nullable=True, index=True)

    task_code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    assigned_to_id = Column(String(36), nullable=True, index=True)
    assigned_to_name = Column(String(255), nullable=True)

    estimated_hours = Column(Numeric(8, 2), default=0.00, nullable=False)
    actual_hours = Column(Numeric(8, 2), default=0.00, nullable=False)

    status = Column(String(30), default="TODO", nullable=False, index=True)  # TODO, IN_PROGRESS, IN_REVIEW, DONE, BLOCKED
    priority = Column(String(20), default="NORMAL", nullable=False)           # LOW, NORMAL, HIGH, URGENT
    due_date = Column(Date, nullable=True)


class ProjectTimesheet(Base, BaseModelMixin):
    """Logged labor hours against a project and task."""
    __tablename__ = "pm_timesheets"

    project_id = Column(String(36), nullable=False, index=True)
    task_id = Column(String(36), nullable=True, index=True)

    employee_id = Column(String(36), nullable=True, index=True)
    employee_name = Column(String(255), nullable=False)

    work_date = Column(Date, nullable=False)
    hours = Column(Numeric(6, 2), nullable=False)

    is_billable = Column(Boolean, default=True, nullable=False)
    hourly_billing_rate = Column(Numeric(10, 2), default=0.00, nullable=False)
    hourly_cost_rate = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_billing_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_cost_amount = Column(Numeric(12, 2), default=0.00, nullable=False)

    status = Column(String(30), default="APPROVED", nullable=False, index=True)  # DRAFT, SUBMITTED, APPROVED, INVOICED
    description = Column(Text, nullable=True)


class ProjectExpense(Base, BaseModelMixin):
    """Direct out-of-pocket or subcontractor expense charged to a project."""
    __tablename__ = "pm_expenses"

    project_id = Column(String(36), nullable=False, index=True)
    category = Column(String(50), default="MISC", nullable=False)  # TRAVEL, SOFTWARE_LICENSE, EQUIPMENT, SUBCONTRACTOR, MATERIALS, MISC
    amount = Column(Numeric(12, 2), nullable=False)
    expense_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    is_billable = Column(Boolean, default=True, nullable=False)
    journal_entry_id = Column(String(36), nullable=True, index=True)
