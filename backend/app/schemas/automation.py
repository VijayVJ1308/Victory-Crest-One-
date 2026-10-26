"""Victory Crest One - Workflow Automation Pydantic Schemas
DTOs for Rules Configuration, Condition Evaluation, Event Dispatching,
and Execution Audit Telemetry.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

from shared.enums import TriggerType, ActionType, WorkflowStatus, ExecutionStatus, ComparisonOperator


class WorkflowCondition(BaseModel):
    """Single condition predicate evaluated against dynamic event context."""
    field: str = Field(..., description="Target property name or dot-notated path e.g. 'guest.tier'")
    operator: str = Field(default="EQUALS", description="Comparison operator e.g. EQUALS, GREATER_THAN, CONTAINS")
    value: Any = Field(..., description="Target literal or threshold value")


class WorkflowActionSchema(BaseModel):
    """Action step executed when workflow trigger condition matches."""
    action_type: str = Field(..., description="Action type: SEND_NOTIFICATION, CREATE_TASK, etc.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")


class WorkflowRuleCreate(BaseModel):
    """Payload to create a new workflow rule."""
    code: Optional[str] = Field(default=None, description="Unique code e.g. 'WF-1007'. Auto-generated if omitted.")
    name: str = Field(..., description="Descriptive rule title")
    description: Optional[str] = Field(default=None, description="Detailed explanation of the workflow")
    trigger_type: TriggerType = Field(default=TriggerType.STATE_CHANGE)
    trigger_event: str = Field(..., description="Event name e.g. 'inventory.stock_level_low'")
    trigger_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(..., min_length=1, description="At least one action required")
    status: WorkflowStatus = Field(default=WorkflowStatus.ACTIVE)
    property_id: Optional[str] = None


class WorkflowRuleUpdate(BaseModel):
    """Payload to modify an existing workflow rule."""
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[TriggerType] = None
    trigger_event: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    status: Optional[WorkflowStatus] = None
    property_id: Optional[str] = None


class WorkflowRuleOut(BaseModel):
    """Complete workflow rule response representation."""
    id: str
    organization_id: str
    property_id: Optional[str] = None
    code: str
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_event: str
    trigger_config: Optional[Dict[str, Any]] = None
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    execution_count: int = 0
    last_triggered_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


class WorkflowExecutionLogOut(BaseModel):
    """Audit log entry for an executed or evaluated workflow."""
    id: str
    organization_id: str
    property_id: Optional[str] = None
    workflow_id: str
    workflow_code: str
    workflow_name: str
    trigger_event: str
    status: str
    payload: Optional[Dict[str, Any]] = None
    actions_executed: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None
    duration_ms: Decimal = Field(default=Decimal("0.00"))
    executed_at: datetime


class WorkflowDispatchEventRequest(BaseModel):
    """Request to dispatch or simulate an event into the rules engine."""
    event: str = Field(..., description="Canonical event name e.g. 'inventory.stock_level_low'")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event context payload")
    property_id: Optional[str] = None


class WorkflowDispatchResponse(BaseModel):
    """Response summarizing event processing outcome."""
    event: str
    matched_rules_count: int
    executed_rules_count: int
    results: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowTelemetryOut(BaseModel):
    """Comprehensive performance and health telemetry for workflow automation."""
    total_rules: int
    active_rules: int
    paused_rules: int
    total_executions: int
    success_count: int
    failed_count: int
    skipped_count: int
    success_rate_percent: Decimal
    avg_duration_ms: Decimal
    total_actions_triggered: int
    recent_logs: List[WorkflowExecutionLogOut] = Field(default_factory=list)
