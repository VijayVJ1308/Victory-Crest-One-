"""Victory Crest One - Workflow Automation & Event Rules Engine Models
Persistent Workflow Rules, Condition Filters, Action Sequences, and Audit Execution Logs.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, Integer
from backend.app.models.base import Base, BaseModelMixin


class WorkflowRule(Base, BaseModelMixin):
    """Event-driven automation rule or scheduled task definition."""
    __tablename__ = "wf_rules"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    trigger_type = Column(String(50), nullable=False, index=True)  # TriggerType enum
    trigger_event = Column(String(100), nullable=False, index=True) # e.g. inventory.stock_level_low

    trigger_config_json = Column(Text, nullable=True)
    conditions_json = Column(Text, nullable=True)                  # JSON list of conditions
    actions_json = Column(Text, nullable=False)                     # JSON list of actions

    status = Column(String(30), default="ACTIVE", nullable=False, index=True)  # WorkflowStatus enum
    execution_count = Column(Integer, default=0, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class WorkflowExecutionLog(Base, BaseModelMixin):
    """Historical audit trail of workflow triggers and pipeline executions."""
    __tablename__ = "wf_execution_logs"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    workflow_id = Column(String(36), nullable=False, index=True)
    workflow_code = Column(String(50), nullable=False)
    workflow_name = Column(String(255), nullable=False)
    trigger_event = Column(String(100), nullable=False, index=True)

    status = Column(String(30), nullable=False, index=True)        # ExecutionStatus enum
    payload_json = Column(Text, nullable=True)
    actions_executed_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Numeric(10, 2), default=0.00, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
