"""Victory Crest One - Workflow Automation & Event Rules Engine REST API Endpoints
Endpoints for workflow rule CRUD, status toggling, cross-module event dispatching,
execution audit logs, and performance telemetry.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status

from backend.app.schemas.automation import (
    WorkflowRuleCreate,
    WorkflowRuleUpdate,
    WorkflowRuleOut,
    WorkflowExecutionLogOut,
    WorkflowDispatchEventRequest,
    WorkflowDispatchResponse,
    WorkflowTelemetryOut
)
from backend.app.services.automation_service import automation_service

router = APIRouter()


@router.get("/rules", response_model=List[WorkflowRuleOut])
def list_workflow_rules(
    property_id: Optional[str] = Query(None, description="Filter rules by operating property"),
    status: Optional[str] = Query(None, description="Filter rules by status (ACTIVE, PAUSED)"),
    trigger_type: Optional[str] = Query(None, description="Filter by trigger type (STATE_CHANGE, THRESHOLD, etc.)")
):
    """Retrieve all workflow rules matching filter criteria."""
    return automation_service.get_rules(
        property_id=property_id,
        status_filter=status,
        trigger_type=trigger_type
    )


@router.get("/rules/{rule_id}", response_model=WorkflowRuleOut)
def get_workflow_rule(rule_id: str):
    """Retrieve a single workflow rule by ID or code."""
    rule = automation_service.get_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow rule '{rule_id}' not found."
        )
    return rule


@router.post("/rules", response_model=WorkflowRuleOut, status_code=status.HTTP_201_CREATED)
def create_workflow_rule(rule_in: WorkflowRuleCreate):
    """Create and register a new event-driven workflow rule."""
    return automation_service.create_rule(rule_in)


@router.put("/rules/{rule_id}", response_model=WorkflowRuleOut)
def update_workflow_rule(rule_id: str, rule_in: WorkflowRuleUpdate):
    """Update an existing workflow rule's conditions, actions, or configuration."""
    return automation_service.update_rule(rule_id, rule_in)


@router.post("/rules/{rule_id}/toggle", response_model=WorkflowRuleOut)
def toggle_workflow_rule(rule_id: str):
    """Toggle a workflow rule between ACTIVE and PAUSED status."""
    return automation_service.toggle_rule(rule_id)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow_rule(rule_id: str):
    """Delete a workflow rule."""
    automation_service.delete_rule(rule_id)
    return None


@router.post("/dispatch", response_model=WorkflowDispatchResponse)
def dispatch_event(request: WorkflowDispatchEventRequest):
    """
    Dispatch an event into the rules engine to evaluate active conditions
    and execute triggered workflow action pipelines.
    """
    return automation_service.dispatch_event(
        event_name=request.event,
        payload=request.payload,
        property_id=request.property_id
    )


@router.get("/logs", response_model=List[WorkflowExecutionLogOut])
def list_execution_logs(
    workflow_id: Optional[str] = Query(None, description="Filter logs by workflow ID or code"),
    status: Optional[str] = Query(None, description="Filter logs by execution status (SUCCESS, SKIPPED, FAILED)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of logs to return")
):
    """Retrieve recent workflow execution audit logs."""
    return automation_service.get_execution_logs(
        workflow_id=workflow_id,
        status_filter=status,
        limit=limit
    )


@router.get("/telemetry", response_model=WorkflowTelemetryOut)
def get_automation_telemetry():
    """Retrieve aggregated performance metrics, execution counts, success rates, and recent logs."""
    return automation_service.get_telemetry()
