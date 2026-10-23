"""Victory Crest One - Project Management & Professional Services (PSA) REST API Endpoints
Portfolios, Milestones, WBS Task Lists, Timesheets, Project Costing,
and Automated Double-Entry GL Milestone Invoicing.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Path, Body
from backend.app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    MilestoneCreate, MilestoneOut, MilestoneInvoiceRequest, MilestoneInvoiceResponse,
    TaskCreate, TaskOut,
    TimesheetCreate, TimesheetOut,
    ExpenseCreate, ExpenseOut,
    ProjectMetricsOut
)
from backend.app.services.project_service import project_service

router = APIRouter(prefix="/projects")


# -------------------------------------------------------------
# Projects
# -------------------------------------------------------------
@router.get("", response_model=List[ProjectOut])
def list_projects(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by property ID"),
    status: Optional[str] = Query(None, description="Filter by status (PLANNING, ACTIVE, ON_HOLD, COMPLETED, CANCELLED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, NORMAL, HIGH, URGENT)")
):
    """Retrieve client professional services and capital infrastructure projects."""
    return project_service.list_projects(
        organization_id=organization_id,
        property_id=property_id,
        status=status,
        priority=priority
    )


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str = Path(..., description="Project ID")):
    """Get detailed project profile with milestone schedule and WBS tasks."""
    return project_service.get_project(project_id)


@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate):
    """Register a new project portfolio and baseline scope."""
    return project_service.create_project(payload)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str = Path(..., description="Project ID"),
    payload: ProjectUpdate = Body(...)
):
    """Update project status, timeline dates, or budget parameters."""
    return project_service.update_project(project_id, payload)


# -------------------------------------------------------------
# Milestones & Milestone Invoicing
# -------------------------------------------------------------
@router.get("/{project_id}/milestones", response_model=List[MilestoneOut])
def list_milestones(project_id: str = Path(..., description="Project ID")):
    """List milestones for a project."""
    return project_service.list_milestones(project_id)


@router.post("/{project_id}/milestones", response_model=MilestoneOut)
def create_milestone(
    project_id: str = Path(..., description="Project ID"),
    payload: MilestoneCreate = Body(...)
):
    """Add a milestone deliverable to a project."""
    return project_service.create_milestone(project_id, payload)


@router.post("/{project_id}/milestones/{milestone_id}/achieve", response_model=MilestoneOut)
def mark_milestone_achieved(
    project_id: str = Path(..., description="Project ID"),
    milestone_id: str = Path(..., description="Milestone ID")
):
    """Sign off milestone as achieved and ready for progress invoicing."""
    return project_service.mark_milestone_achieved(project_id, milestone_id)


@router.post("/{project_id}/milestones/{milestone_id}/invoice", response_model=MilestoneInvoiceResponse)
def invoice_milestone(
    project_id: str = Path(..., description="Project ID"),
    milestone_id: str = Path(..., description="Milestone ID"),
    req: MilestoneInvoiceRequest = Body(...)
):
    """Generate customer invoice for achieved milestone and post double-entry GL revenue."""
    return project_service.invoice_milestone(project_id, milestone_id, req)


# -------------------------------------------------------------
# WBS Tasks
# -------------------------------------------------------------
@router.get("/{project_id}/tasks", response_model=List[TaskOut])
def list_tasks(project_id: str = Path(..., description="Project ID")):
    """List work breakdown structure (WBS) tasks for a project."""
    return project_service.list_tasks(project_id)


@router.post("/{project_id}/tasks", response_model=TaskOut)
def create_task(
    project_id: str = Path(..., description="Project ID"),
    payload: TaskCreate = Body(...)
):
    """Create a new task assignment under a project."""
    return project_service.create_task(project_id, payload)


@router.put("/{project_id}/tasks/{task_id}/status", response_model=TaskOut)
def update_task_status(
    project_id: str = Path(..., description="Project ID"),
    task_id: str = Path(..., description="Task ID"),
    new_status: str = Query(..., description="Status (TODO, IN_PROGRESS, IN_REVIEW, DONE, BLOCKED)")
):
    """Update task execution status."""
    return project_service.update_task_status(project_id, task_id, new_status)


# -------------------------------------------------------------
# Timesheets & Expenses
# -------------------------------------------------------------
@router.get("/{project_id}/timesheets", response_model=List[TimesheetOut])
def list_timesheets(project_id: str = Path(..., description="Project ID")):
    """Retrieve logged labor timesheets for a project."""
    return project_service.list_timesheets(project_id)


@router.post("/{project_id}/timesheets", response_model=TimesheetOut)
def log_timesheet(
    project_id: str = Path(..., description="Project ID"),
    payload: TimesheetCreate = Body(...)
):
    """Log staff labor hours and billable time against a project."""
    return project_service.log_timesheet(project_id, payload)


@router.get("/{project_id}/expenses", response_model=List[ExpenseOut])
def list_expenses(project_id: str = Path(..., description="Project ID")):
    """List out-of-pocket and subcontractor expenses incurred on a project."""
    return project_service.list_expenses(project_id)


@router.post("/{project_id}/expenses", response_model=ExpenseOut)
def log_expense(
    project_id: str = Path(..., description="Project ID"),
    payload: ExpenseCreate = Body(...)
):
    """Charge a direct project expense."""
    return project_service.log_expense(project_id, payload)


# -------------------------------------------------------------
# PSA Executive Telemetry & KPIs
# -------------------------------------------------------------
@router.get("/metrics/summary", response_model=ProjectMetricsOut)
def get_project_metrics(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by property ID")
):
    """Retrieve executive PSA portfolio metrics, burn rates, and billable utilization."""
    return project_service.get_project_metrics(
        organization_id=organization_id,
        property_id=property_id
    )
