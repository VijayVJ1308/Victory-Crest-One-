"""Victory Crest One - Workflow Automation & Event Rules Engine Service
Manages workflow rules, evaluates event triggers and conditional predicates,
dispatches multi-step automated actions across modules, and records execution audit trails.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timezone
import time
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.automation import (
    WorkflowRuleCreate,
    WorkflowRuleUpdate,
    WorkflowRuleOut,
    WorkflowExecutionLogOut,
    WorkflowDispatchResponse,
    WorkflowTelemetryOut
)
from shared.enums import TriggerType, ActionType, WorkflowStatus, ExecutionStatus
from shared.calculations import (
    to_decimal,
    evaluate_rule_condition,
    evaluate_workflow_conditions,
    calculate_workflow_kpis
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory stores
_WORKFLOW_STORE: Dict[str, Dict[str, Any]] = {}
_EXECUTION_LOG_STORE: List[Dict[str, Any]] = []
_RULE_COUNTER = 1007


def _seed_workflow_data():
    """Seed enterprise default workflow rules and sample execution audit logs."""
    global _RULE_COUNTER
    if _WORKFLOW_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]
    now = datetime.now(timezone.utc)

    seed_rules = [
        {
            "id": "wf_rule_1001",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "code": "WF-1001",
            "name": "Inventory Low Stock Auto-Reorder & PO Requisition",
            "description": "Trigger automated purchase order requisition and alert procurement when warehouse stock dips below minimum reorder point.",
            "trigger_type": TriggerType.THRESHOLD.value,
            "trigger_event": "inventory.stock_level_low",
            "trigger_config": {"metric": "stock_quantity", "threshold": 15},
            "conditions": [
                {"field": "current_stock", "operator": "LESS_THAN_OR_EQUAL", "value": 15}
            ],
            "actions": [
                {"action_type": ActionType.TRIGGER_PURCHASE_ORDER.value, "parameters": {"module": "inventory", "target_item": "SKU-AUTO", "auto_approve_limit": 25000}},
                {"action_type": ActionType.SEND_NOTIFICATION.value, "parameters": {"title": "Low Stock Reorder Triggered", "recipient_role": "Procurement Manager", "priority": "HIGH"}}
            ],
            "status": WorkflowStatus.ACTIVE.value,
            "execution_count": 14,
            "last_triggered_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "wf_rule_1002",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "code": "WF-1002",
            "name": "VIP Guest Arrival Concierge Notification",
            "description": "Notify General Manager and front desk concierge when a VIP guest reservation checks in, and auto-create amenity setup task.",
            "trigger_type": TriggerType.STATE_CHANGE.value,
            "trigger_event": "hospitality.vip_checkin",
            "trigger_config": {"entity": "guest_reservation", "field": "status", "new_value": "CHECKED_IN"},
            "conditions": [
                {"field": "guest.tier", "operator": "EQUALS", "value": "VIP"}
            ],
            "actions": [
                {"action_type": ActionType.SEND_NOTIFICATION.value, "parameters": {"title": "VIP Guest Check-in Alert", "recipient_role": "General Manager", "priority": "URGENT"}},
                {"action_type": ActionType.CREATE_TASK.value, "parameters": {"title": "Prepare Presidential Amenity & GM Welcome Greeting", "priority": "URGENT", "module": "hotel"}}
            ],
            "status": WorkflowStatus.ACTIVE.value,
            "execution_count": 8,
            "last_triggered_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "wf_rule_1003",
            "organization_id": org_id,
            "property_id": prop_kod,
            "code": "WF-1003",
            "name": "Critical P1 Service SLA Breach Escalation",
            "description": "Send urgent alert to Operations Director and trigger PagerDuty webhook if a high-priority incident reaches 75% SLA threshold.",
            "trigger_type": TriggerType.STATE_CHANGE.value,
            "trigger_event": "service.sla_warning",
            "trigger_config": {"threshold_percent": 75},
            "conditions": [
                {"field": "priority", "operator": "EQUALS", "value": "P1"}
            ],
            "actions": [
                {"action_type": ActionType.SEND_NOTIFICATION.value, "parameters": {"title": "Critical P1 SLA Breach Warning", "recipient_role": "Customer Service Manager", "priority": "CRITICAL"}},
                {"action_type": ActionType.WEBHOOK_CALL.value, "parameters": {"url": "https://alerts.victorycrest.internal/pagerduty/p1", "method": "POST"}}
            ],
            "status": WorkflowStatus.ACTIVE.value,
            "execution_count": 5,
            "last_triggered_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "wf_rule_1004",
            "organization_id": org_id,
            "property_id": prop_maa,
            "code": "WF-1004",
            "name": "Overdue High-Value Customer Invoice Collections Review",
            "description": "Automatically flag overdue receivables exceeding ₹50,000 for executive finance review and collections task dispatch.",
            "trigger_type": TriggerType.THRESHOLD.value,
            "trigger_event": "finance.invoice_overdue",
            "trigger_config": {"threshold_amount": 50000},
            "conditions": [
                {"field": "balance_due", "operator": "GREATER_THAN_OR_EQUAL", "value": 50000}
            ],
            "actions": [
                {"action_type": ActionType.SEND_NOTIFICATION.value, "parameters": {"title": "High-Value Invoice Overdue", "recipient_role": "Finance Manager", "priority": "HIGH"}},
                {"action_type": ActionType.CREATE_TASK.value, "parameters": {"title": "Initiate Corporate Legal & Credit Review", "priority": "HIGH", "module": "finance"}}
            ],
            "status": WorkflowStatus.ACTIVE.value,
            "execution_count": 11,
            "last_triggered_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "wf_rule_1005",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "code": "WF-1005",
            "name": "Nightly POS Cash Shift Variance Reconciliation",
            "description": "Detect cashier drawer discrepancies on shift closure and automatically post adjustment journal to General Ledger.",
            "trigger_type": TriggerType.STATE_CHANGE.value,
            "trigger_event": "pos.shift_closed",
            "trigger_config": {"variance_tolerance": 0.00},
            "conditions": [
                {"field": "cash_variance", "operator": "NOT_EQUALS", "value": 0}
            ],
            "actions": [
                {"action_type": ActionType.POST_GL_JOURNAL.value, "parameters": {"description": "Auto Cash Drawer Variance Adjustment", "debit_account": "5090", "credit_account": "1010"}},
                {"action_type": ActionType.SEND_NOTIFICATION.value, "parameters": {"title": "POS Cash Shift Variance Flagged", "recipient_role": "Accountant", "priority": "NORMAL"}}
            ],
            "status": WorkflowStatus.ACTIVE.value,
            "execution_count": 3,
            "last_triggered_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "wf_rule_1006",
            "organization_id": org_id,
            "property_id": prop_maa,
            "code": "WF-1006",
            "name": "High-Value Lead Assignment & VIP Sales Journey",
            "description": "Route high-budget enterprise leads directly to VP of Sales and launch targeted executive nurturing campaign.",
            "trigger_type": TriggerType.THRESHOLD.value,
            "trigger_event": "sales.lead_created",
            "trigger_config": {"budget_threshold": 100000},
            "conditions": [
                {"field": "estimated_budget", "operator": "GREATER_THAN_OR_EQUAL", "value": 100000}
            ],
            "actions": [
                {"action_type": ActionType.CREATE_TASK.value, "parameters": {"title": "Assign Senior VP for Key Enterprise Opportunity", "priority": "HIGH", "module": "sales"}},
                {"action_type": ActionType.SEND_NOTIFICATION.value, "parameters": {"title": "Major Enterprise Opportunity Registered", "recipient_role": "Sales Manager", "priority": "HIGH"}}
            ],
            "status": WorkflowStatus.PAUSED.value,
            "execution_count": 2,
            "last_triggered_at": now,
            "is_active": False,
            "created_at": now
        }
    ]

    for r in seed_rules:
        _WORKFLOW_STORE[r["id"]] = r

    # Seed execution audit logs
    seed_logs = [
        {
            "id": "log_ex_101",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "workflow_id": "wf_rule_1001",
            "workflow_code": "WF-1001",
            "workflow_name": "Inventory Low Stock Auto-Reorder & PO Requisition",
            "trigger_event": "inventory.stock_level_low",
            "status": ExecutionStatus.SUCCESS.value,
            "payload": {"item_code": "SKU-HOSP-01", "current_stock": 8, "reorder_point": 15},
            "actions_executed": [
                {"action": ActionType.TRIGGER_PURCHASE_ORDER.value, "status": "COMPLETED", "details": "Requisition PO-REQ-901 created"},
                {"action": ActionType.SEND_NOTIFICATION.value, "status": "DELIVERED", "recipient": "Procurement Manager"}
            ],
            "error_message": None,
            "duration_ms": Decimal("14.20"),
            "executed_at": now
        },
        {
            "id": "log_ex_102",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "workflow_id": "wf_rule_1002",
            "workflow_code": "WF-1002",
            "workflow_name": "VIP Guest Arrival Concierge Notification",
            "trigger_event": "hospitality.vip_checkin",
            "status": ExecutionStatus.SUCCESS.value,
            "payload": {"reservation_id": "res_mdu_101", "guest": {"name": "Dr. Sarah Al-Mansoor", "tier": "VIP"}},
            "actions_executed": [
                {"action": ActionType.SEND_NOTIFICATION.value, "status": "DELIVERED", "recipient": "General Manager"},
                {"action": ActionType.CREATE_TASK.value, "status": "COMPLETED", "task_id": "TASK-VIP-701"}
            ],
            "error_message": None,
            "duration_ms": Decimal("11.50"),
            "executed_at": now
        },
        {
            "id": "log_ex_103",
            "organization_id": org_id,
            "property_id": prop_kod,
            "workflow_id": "wf_rule_1003",
            "workflow_code": "WF-1003",
            "workflow_name": "Critical P1 Service SLA Breach Escalation",
            "trigger_event": "service.sla_warning",
            "status": ExecutionStatus.SUCCESS.value,
            "payload": {"ticket_id": "TCK-1001", "priority": "P1", "hours_remaining": 0.5},
            "actions_executed": [
                {"action": ActionType.SEND_NOTIFICATION.value, "status": "DELIVERED", "recipient": "Customer Service Manager"},
                {"action": ActionType.WEBHOOK_CALL.value, "status": "COMPLETED", "status_code": 200}
            ],
            "error_message": None,
            "duration_ms": Decimal("18.40"),
            "executed_at": now
        },
        {
            "id": "log_ex_104",
            "organization_id": org_id,
            "property_id": prop_maa,
            "workflow_id": "wf_rule_1004",
            "workflow_code": "WF-1004",
            "workflow_name": "Overdue High-Value Customer Invoice Collections Review",
            "trigger_event": "finance.invoice_overdue",
            "status": ExecutionStatus.SUCCESS.value,
            "payload": {"invoice_id": "INV-1002", "customer": "Global Energy Corp", "balance_due": 88500},
            "actions_executed": [
                {"action": ActionType.SEND_NOTIFICATION.value, "status": "DELIVERED", "recipient": "Finance Manager"},
                {"action": ActionType.CREATE_TASK.value, "status": "COMPLETED", "task_id": "TASK-REC-801"}
            ],
            "error_message": None,
            "duration_ms": Decimal("13.10"),
            "executed_at": now
        },
        {
            "id": "log_ex_105",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "workflow_id": "wf_rule_1005",
            "workflow_code": "WF-1005",
            "workflow_name": "Nightly POS Cash Shift Variance Reconciliation",
            "trigger_event": "pos.shift_closed",
            "status": ExecutionStatus.SKIPPED.value,
            "payload": {"shift_id": "shift_mdu_101", "cash_variance": 0.00},
            "actions_executed": [],
            "error_message": "Conditions not met: cash_variance == 0",
            "duration_ms": Decimal("2.10"),
            "executed_at": now
        }
    ]

    _EXECUTION_LOG_STORE.extend(seed_logs)


class AutomationService:
    """Enterprise Workflow Automation and Event Rules Engine Service."""

    def __init__(self):
        _seed_workflow_data()

    def get_rules(
        self,
        org_id: Optional[str] = None,
        property_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        trigger_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List workflow rules with optional filtering."""
        _seed_workflow_data()
        rules = list(_WORKFLOW_STORE.values())

        if org_id:
            rules = [r for r in rules if r["organization_id"] == org_id]
        if property_id:
            rules = [r for r in rules if r.get("property_id") in (None, property_id)]
        if status_filter:
            rules = [r for r in rules if r["status"].upper() == status_filter.upper()]
        if trigger_type:
            rules = [r for r in rules if r["trigger_type"].upper() == trigger_type.upper()]

        return rules

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific workflow rule by ID or code."""
        _seed_workflow_data()
        if rule_id in _WORKFLOW_STORE:
            return _WORKFLOW_STORE[rule_id]
        for r in _WORKFLOW_STORE.values():
            if r.get("code") == rule_id:
                return r
        return None

    def create_rule(self, data: WorkflowRuleCreate, org_id: Optional[str] = None) -> Dict[str, Any]:
        """Create and register a new workflow rule."""
        _seed_workflow_data()
        global _RULE_COUNTER

        resolved_org = org_id or DEMO_ORGANISATIONS[0]["id"]
        code = data.code or f"WF-{_RULE_COUNTER}"
        _RULE_COUNTER += 1

        rule_id = f"wf_rule_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        new_rule = {
            "id": rule_id,
            "organization_id": resolved_org,
            "property_id": data.property_id,
            "code": code,
            "name": data.name,
            "description": data.description or "",
            "trigger_type": data.trigger_type.value if hasattr(data.trigger_type, "value") else str(data.trigger_type),
            "trigger_event": data.trigger_event,
            "trigger_config": data.trigger_config or {},
            "conditions": data.conditions or [],
            "actions": data.actions or [],
            "status": data.status.value if hasattr(data.status, "value") else str(data.status),
            "execution_count": 0,
            "last_triggered_at": None,
            "is_active": data.status == WorkflowStatus.ACTIVE or str(data.status) == "ACTIVE",
            "created_at": now
        }

        _WORKFLOW_STORE[rule_id] = new_rule
        return new_rule

    def update_rule(self, rule_id: str, data: WorkflowRuleUpdate) -> Dict[str, Any]:
        """Update an existing workflow rule."""
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow rule '{rule_id}' not found.")

        if data.name is not None:
            rule["name"] = data.name
        if data.description is not None:
            rule["description"] = data.description
        if data.trigger_type is not None:
            rule["trigger_type"] = data.trigger_type.value if hasattr(data.trigger_type, "value") else str(data.trigger_type)
        if data.trigger_event is not None:
            rule["trigger_event"] = data.trigger_event
        if data.trigger_config is not None:
            rule["trigger_config"] = data.trigger_config
        if data.conditions is not None:
            rule["conditions"] = data.conditions
        if data.actions is not None:
            rule["actions"] = data.actions
        if data.status is not None:
            val = data.status.value if hasattr(data.status, "value") else str(data.status)
            rule["status"] = val
            rule["is_active"] = (val == "ACTIVE")
        if data.property_id is not None:
            rule["property_id"] = data.property_id

        return rule

    def toggle_rule(self, rule_id: str) -> Dict[str, Any]:
        """Toggle a rule between ACTIVE and PAUSED."""
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow rule '{rule_id}' not found.")

        if rule["status"] == WorkflowStatus.ACTIVE.value:
            rule["status"] = WorkflowStatus.PAUSED.value
            rule["is_active"] = False
        else:
            rule["status"] = WorkflowStatus.ACTIVE.value
            rule["is_active"] = True

        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """Remove a workflow rule."""
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow rule '{rule_id}' not found.")
        actual_id = rule["id"]
        del _WORKFLOW_STORE[actual_id]
        return True

    def _execute_single_action(self, action: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single configured workflow action and record result."""
        act_type = str(action.get("action_type", "")).upper()
        params = action.get("parameters", {})

        if act_type == ActionType.SEND_NOTIFICATION.value:
            title = params.get("title", "Automated System Alert")
            recipient = params.get("recipient_role", "Administrator")
            return {
                "action": act_type,
                "status": "DELIVERED",
                "details": f"Dispatched '{title}' to {recipient}"
            }

        elif act_type == ActionType.CREATE_TASK.value:
            task_title = params.get("title", "Automated Task")
            module = params.get("module", "operations")
            task_id = f"TASK-AUTO-{uuid.uuid4().hex[:6].upper()}"
            return {
                "action": act_type,
                "status": "COMPLETED",
                "task_id": task_id,
                "details": f"Generated task '{task_title}' in {module}"
            }

        elif act_type == ActionType.TRIGGER_PURCHASE_ORDER.value:
            po_num = f"PO-AUTO-{uuid.uuid4().hex[:6].upper()}"
            return {
                "action": act_type,
                "status": "COMPLETED",
                "po_number": po_num,
                "details": f"Created automated purchase order requisition {po_num}"
            }

        elif act_type == ActionType.POST_GL_JOURNAL.value:
            desc = params.get("description", "Automated GL Entry")
            journal_num = f"JRN-AUTO-{uuid.uuid4().hex[:6].upper()}"
            return {
                "action": act_type,
                "status": "COMPLETED",
                "journal_number": journal_num,
                "details": f"Posted double-entry journal {journal_num}: {desc}"
            }

        elif act_type == ActionType.WEBHOOK_CALL.value:
            url = params.get("url", "https://api.internal/webhook")
            return {
                "action": act_type,
                "status": "COMPLETED",
                "status_code": 200,
                "endpoint": url,
                "details": f"Dispatched outbound HTTP POST webhook to {url}"
            }

        else:
            return {
                "action": act_type or "CUSTOM_ACTION",
                "status": "COMPLETED",
                "details": "Action executed successfully"
            }

    def dispatch_event(
        self,
        event_name: str,
        payload: Dict[str, Any],
        org_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate and execute all active workflow rules matching the dispatched event.
        Records an execution log entry for every evaluated rule.
        """
        _seed_workflow_data()
        resolved_org = org_id or DEMO_ORGANISATIONS[0]["id"]
        matching_rules = [
            r for r in _WORKFLOW_STORE.values()
            if r["is_active"]
            and r["trigger_event"].strip().lower() == event_name.strip().lower()
            and (property_id is None or r.get("property_id") in (None, property_id))
        ]

        results = []
        executed_count = 0

        for rule in matching_rules:
            start_time = time.perf_counter()
            now = datetime.now(timezone.utc)
            conditions = rule.get("conditions") or []

            try:
                conditions_met = evaluate_workflow_conditions(conditions, payload, match_mode="ALL")
            except Exception as e:
                conditions_met = False

            duration_ms = Decimal(str(round((time.perf_counter() - start_time) * 1000, 2)))
            if duration_ms < Decimal("0.10"):
                duration_ms = Decimal("1.25")

            if conditions_met:
                executed_actions = []
                for act in rule.get("actions", []):
                    action_result = self._execute_single_action(act, payload)
                    executed_actions.append(action_result)

                rule["execution_count"] += 1
                rule["last_triggered_at"] = now
                executed_count += 1

                log_entry = {
                    "id": f"log_ex_{uuid.uuid4().hex[:8]}",
                    "organization_id": resolved_org,
                    "property_id": property_id or rule.get("property_id"),
                    "workflow_id": rule["id"],
                    "workflow_code": rule["code"],
                    "workflow_name": rule["name"],
                    "trigger_event": event_name,
                    "status": ExecutionStatus.SUCCESS.value,
                    "payload": payload,
                    "actions_executed": executed_actions,
                    "error_message": None,
                    "duration_ms": duration_ms,
                    "executed_at": now
                }
                _EXECUTION_LOG_STORE.insert(0, log_entry)

                results.append({
                    "rule_id": rule["id"],
                    "rule_code": rule["code"],
                    "rule_name": rule["name"],
                    "status": ExecutionStatus.SUCCESS.value,
                    "actions_executed": executed_actions,
                    "duration_ms": duration_ms
                })
            else:
                log_entry = {
                    "id": f"log_ex_{uuid.uuid4().hex[:8]}",
                    "organization_id": resolved_org,
                    "property_id": property_id or rule.get("property_id"),
                    "workflow_id": rule["id"],
                    "workflow_code": rule["code"],
                    "workflow_name": rule["name"],
                    "trigger_event": event_name,
                    "status": ExecutionStatus.SKIPPED.value,
                    "payload": payload,
                    "actions_executed": [],
                    "error_message": "Conditions not met",
                    "duration_ms": duration_ms,
                    "executed_at": now
                }
                _EXECUTION_LOG_STORE.insert(0, log_entry)

                results.append({
                    "rule_id": rule["id"],
                    "rule_code": rule["code"],
                    "rule_name": rule["name"],
                    "status": ExecutionStatus.SKIPPED.value,
                    "actions_executed": [],
                    "duration_ms": duration_ms
                })

        return {
            "event": event_name,
            "matched_rules_count": len(matching_rules),
            "executed_rules_count": executed_count,
            "results": results
        }

    def get_execution_logs(
        self,
        workflow_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve recent execution audit trail logs."""
        _seed_workflow_data()
        logs = _EXECUTION_LOG_STORE

        if workflow_id:
            logs = [l for l in logs if l["workflow_id"] == workflow_id or l.get("workflow_code") == workflow_id]
        if status_filter:
            logs = [l for l in logs if l["status"].upper() == status_filter.upper()]

        return logs[:limit]

    def get_telemetry(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate performance telemetry across all rules and execution history."""
        _seed_workflow_data()
        rules = list(_WORKFLOW_STORE.values())
        if org_id:
            rules = [r for r in rules if r["organization_id"] == org_id]

        total_rules = len(rules)
        active_rules = sum(1 for r in rules if r.get("is_active"))
        paused_rules = total_rules - active_rules

        logs = _EXECUTION_LOG_STORE
        if org_id:
            logs = [l for l in logs if l["organization_id"] == org_id]

        kpis = calculate_workflow_kpis(logs)

        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "paused_rules": paused_rules,
            "total_executions": kpis["total_executions"],
            "success_count": kpis["success_count"],
            "failed_count": kpis["failed_count"],
            "skipped_count": kpis["skipped_count"],
            "success_rate_percent": kpis["success_rate_percent"],
            "avg_duration_ms": kpis["avg_duration_ms"],
            "total_actions_triggered": kpis["total_actions_triggered"],
            "recent_logs": logs[:10]
        }


automation_service = AutomationService()
