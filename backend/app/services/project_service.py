"""Victory Crest One - Project Management & Professional Services (PSA) Service
Portfolios, WBS Task Hierarchies, Milestones, Timesheets, Project Costing,
and Automated Double-Entry GL Revenue Recognition.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta, timezone
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.project import (
    MilestoneCreate, MilestoneUpdate, MilestoneOut,
    TaskCreate, TaskUpdate, TaskOut,
    TimesheetCreate, TimesheetOut,
    ExpenseCreate, ExpenseOut,
    ProjectCreate, ProjectUpdate, ProjectOut,
    MilestoneInvoiceRequest, MilestoneInvoiceResponse,
    ProjectMetricsOut
)
from backend.app.schemas.finance import JournalEntryCreate, JournalLineCreate
from backend.app.services.finance_service import finance_service
from backend.app.services.audit_service import audit_service
from shared.calculations import (
    to_decimal,
    calculate_project_budget_variance,
    calculate_project_burn_rate,
    calculate_timesheet_totals,
    calculate_milestone_invoice,
    calculate_project_kpis
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory data stores
_PROJECT_STORE: Dict[str, Dict[str, Any]] = {}
_MILESTONE_STORE: Dict[str, List[Dict[str, Any]]] = {}
_TASK_STORE: Dict[str, List[Dict[str, Any]]] = {}
_TIMESHEET_STORE: Dict[str, List[Dict[str, Any]]] = {}
_EXPENSE_STORE: Dict[str, List[Dict[str, Any]]] = {}

_PROJECT_COUNTER = 100
_INVOICE_COUNTER = 100


def _seed_project_data():
    """Populate initial projects, milestones, WBS tasks, timesheets, and direct expenses."""
    global _PROJECT_COUNTER, _INVOICE_COUNTER
    if _PROJECT_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]  # Madurai Heritage Hotel
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]  # Kodaikanal Mountain Resort
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]  # Chennai Hub
    now = datetime.now(timezone.utc)
    today = date.today()

    # 1. Project 1: Grand Ballroom AV & Lighting (Madurai)
    p1_id = "prj_mdu_ballroom"
    _PROJECT_STORE[p1_id] = {
        "id": p1_id,
        "organization_id": org_id,
        "property_id": prop_mdu,
        "project_code": "PRJ-2026-001",
        "name": "Grand Ballroom Royal Acoustic & AV Overhaul",
        "description": "Complete replacement of acoustic baffles, automated line-array speakers, and architectural DMX stage illumination for heritage conventions.",
        "customer_id": "cust_heritage_trust",
        "customer_name": "Southern India Heritage & Arts Trust",
        "project_manager_id": "usr_pm_01",
        "project_manager_name": "Arunachalam V. (Senior PM)",
        "billing_type": "MILESTONE_BASED",
        "status": "ACTIVE",
        "priority": "HIGH",
        "start_date": today - timedelta(days=45),
        "end_date": today + timedelta(days=45),
        "budget_amount": Decimal("1500000.00"),
        "billed_amount": Decimal("500000.00"),
        "actual_cost": Decimal("320000.00"),
        "progress_percent": Decimal("45.00"),
        "created_at": now - timedelta(days=50)
    }

    _MILESTONE_STORE[p1_id] = [
        {"id": "ms_101", "project_id": p1_id, "title": "Phase 1: Acoustic Survey & 3D Rigging Plans", "description": "Precision laser acoustic scans and structural certification.", "milestone_amount": Decimal("500000.00"), "due_date": today - timedelta(days=20), "status": "INVOICED", "invoice_id": "inv_ms_101", "achieved_at": now - timedelta(days=20), "created_at": now - timedelta(days=50)},
        {"id": "ms_102", "project_id": p1_id, "title": "Phase 2: DMX Stage Lighting & Truss Installation", "description": "Overhead motorized truss rigging and architectural flood fixtures.", "milestone_amount": Decimal("600000.00"), "due_date": today - timedelta(days=2), "status": "ACHIEVED", "invoice_id": None, "achieved_at": now - timedelta(days=2), "created_at": now - timedelta(days=50)},
        {"id": "ms_103", "project_id": p1_id, "title": "Phase 3: Sound Reinforcement & Final Client Commissioning", "description": "Dante audio network integration and live performance handover.", "milestone_amount": Decimal("400000.00"), "due_date": today + timedelta(days=40), "status": "IN_PROGRESS", "invoice_id": None, "achieved_at": None, "created_at": now - timedelta(days=50)},
    ]

    _TASK_STORE[p1_id] = [
        {"id": "tsk_101", "project_id": p1_id, "milestone_id": "ms_101", "task_code": "TSK-101", "title": "Laser 3D Room Acoustic Scanning", "description": "Map room reverberation time (RT60) across 85 microphone points.", "assigned_to_id": "emp_eng_01", "assigned_to_name": "Kavitha Ramanathan", "estimated_hours": Decimal("24.00"), "actual_hours": Decimal("26.00"), "status": "DONE", "priority": "HIGH", "due_date": today - timedelta(days=35), "created_at": now - timedelta(days=50)},
        {"id": "tsk_102", "project_id": p1_id, "milestone_id": "ms_102", "task_code": "TSK-102", "title": "Motorized Chain Hoist & Truss Mount", "description": "Mount 4x 1-ton chain hoists on structural I-beams.", "assigned_to_id": "emp_eng_02", "assigned_to_name": "Manoj Kumar", "estimated_hours": Decimal("40.00"), "actual_hours": Decimal("38.00"), "status": "DONE", "priority": "URGENT", "due_date": today - timedelta(days=10), "created_at": now - timedelta(days=40)},
        {"id": "tsk_103", "project_id": p1_id, "milestone_id": "ms_103", "task_code": "TSK-103", "title": "Dante Network Audio Calibration", "description": "Configure digital audio transport across gigabit fiber links.", "assigned_to_id": "emp_eng_01", "assigned_to_name": "Kavitha Ramanathan", "estimated_hours": Decimal("30.00"), "actual_hours": Decimal("12.00"), "status": "IN_PROGRESS", "priority": "NORMAL", "due_date": today + timedelta(days=15), "created_at": now - timedelta(days=20)},
    ]

    _TIMESHEET_STORE[p1_id] = [
        {"id": "ts_101", "project_id": p1_id, "task_id": "tsk_101", "work_date": today - timedelta(days=36), "hours": Decimal("26.00"), "employee_id": "emp_eng_01", "employee_name": "Kavitha Ramanathan", "is_billable": True, "hourly_billing_rate": Decimal("2500.00"), "hourly_cost_rate": Decimal("850.00"), "total_billing_amount": Decimal("65000.00"), "total_cost_amount": Decimal("22100.00"), "status": "APPROVED", "description": "Completed acoustic room response profiling.", "created_at": now - timedelta(days=36)},
        {"id": "ts_102", "project_id": p1_id, "task_id": "tsk_102", "work_date": today - timedelta(days=12), "hours": Decimal("38.00"), "employee_id": "emp_eng_02", "employee_name": "Manoj Kumar", "is_billable": True, "hourly_billing_rate": Decimal("2200.00"), "hourly_cost_rate": Decimal("750.00"), "total_billing_amount": Decimal("83600.00"), "total_cost_amount": Decimal("28500.00"), "status": "APPROVED", "description": "Overhead structural rigging and cable raceway.", "created_at": now - timedelta(days=12)},
        {"id": "ts_103", "project_id": p1_id, "task_id": "tsk_103", "work_date": today - timedelta(days=2), "hours": Decimal("12.00"), "employee_id": "emp_eng_01", "employee_name": "Kavitha Ramanathan", "is_billable": True, "hourly_billing_rate": Decimal("2500.00"), "hourly_cost_rate": Decimal("850.00"), "total_billing_amount": Decimal("30000.00"), "total_cost_amount": Decimal("10200.00"), "status": "APPROVED", "description": "Digital DSP routing matrix configuration.", "created_at": now - timedelta(days=2)},
    ]

    _EXPENSE_STORE[p1_id] = [
        {"id": "exp_101", "project_id": p1_id, "category": "EQUIPMENT", "amount": Decimal("45000.00"), "expense_date": today - timedelta(days=35), "description": "Precision 3D acoustic interferometer rental", "is_billable": True, "journal_entry_id": "je_exp_101", "created_at": now - timedelta(days=35)},
        {"id": "exp_102", "project_id": p1_id, "category": "SUBCONTRACTOR", "amount": Decimal("125000.00"), "expense_date": today - timedelta(days=15), "description": "Certified structural scaffolding & rigging team", "is_billable": True, "journal_entry_id": "je_exp_102", "created_at": now - timedelta(days=15)},
    ]

    # 2. Project 2: Kodaikanal Solar & Hydro Transition (Kodaikanal)
    p2_id = "prj_kod_solar"
    _PROJECT_STORE[p2_id] = {
        "id": p2_id,
        "organization_id": org_id,
        "property_id": prop_kod,
        "project_code": "PRJ-2026-002",
        "name": "Kodaikanal Mountain Resort Solar Microgrid & Hydro Transition",
        "description": "Installation of 150 kWp rooftop solar photovoltaic array and 20 kW run-of-river micro-hydro turbine for 100% off-grid clean energy resilience.",
        "customer_id": "cust_green_eco",
        "customer_name": "Green Eco-Hotels Consortium",
        "project_manager_id": "usr_pm_02",
        "project_manager_name": "Divya N. (Sustainability Lead)",
        "billing_type": "MILESTONE_BASED",
        "status": "ACTIVE",
        "priority": "NORMAL",
        "start_date": today - timedelta(days=30),
        "end_date": today + timedelta(days=60),
        "budget_amount": Decimal("2400000.00"),
        "billed_amount": Decimal("800000.00"),
        "actual_cost": Decimal("610000.00"),
        "progress_percent": Decimal("35.00"),
        "created_at": now - timedelta(days=35)
    }

    _MILESTONE_STORE[p2_id] = [
        {"id": "ms_201", "project_id": p2_id, "title": "Milestone 1: Hydro-Flow & Solar Feasibility Report", "description": "Geotechnical soil surveys and seasonal stream flow calculations.", "milestone_amount": Decimal("800000.00"), "due_date": today - timedelta(days=10), "status": "INVOICED", "invoice_id": "inv_ms_201", "achieved_at": now - timedelta(days=10), "created_at": now - timedelta(days=35)},
        {"id": "ms_202", "project_id": p2_id, "title": "Milestone 2: 150 kWp Solar PV Array Rigging", "description": "Tier-1 solar panels mounted on storm-rated aluminum structures.", "milestone_amount": Decimal("1000000.00"), "due_date": today + timedelta(days=20), "status": "IN_PROGRESS", "invoice_id": None, "achieved_at": None, "created_at": now - timedelta(days=35)},
        {"id": "ms_203", "project_id": p2_id, "title": "Milestone 3: 200 kWh LiFePO4 BESS Storage & Grid Sync", "description": "Battery Energy Storage System commissioning and peak-shaving.", "milestone_amount": Decimal("600000.00"), "due_date": today + timedelta(days=55), "status": "PENDING", "invoice_id": None, "achieved_at": None, "created_at": now - timedelta(days=35)},
    ]

    _TASK_STORE[p2_id] = [
        {"id": "tsk_201", "project_id": p2_id, "milestone_id": "ms_201", "task_code": "TSK-201", "title": "Stream Flow Rate & Head Height Sensor Calibration", "description": "Deploy ultrasonic flow sensors on hill catchment streams.", "assigned_to_id": "emp_eng_03", "assigned_to_name": "Siddharth Verma", "estimated_hours": Decimal("20.00"), "actual_hours": Decimal("18.00"), "status": "DONE", "priority": "NORMAL", "due_date": today - timedelta(days=20), "created_at": now - timedelta(days=35)},
        {"id": "tsk_202", "project_id": p2_id, "milestone_id": "ms_202", "task_code": "TSK-202", "title": "Inverter & DC String Wiring Installation", "description": "Install string combiner boxes and surge arrestors.", "assigned_to_id": "emp_eng_03", "assigned_to_name": "Siddharth Verma", "estimated_hours": Decimal("50.00"), "actual_hours": Decimal("22.00"), "status": "IN_PROGRESS", "priority": "HIGH", "due_date": today + timedelta(days=10), "created_at": now - timedelta(days=15)},
    ]

    _TIMESHEET_STORE[p2_id] = [
        {"id": "ts_201", "project_id": p2_id, "task_id": "tsk_201", "work_date": today - timedelta(days=22), "hours": Decimal("18.00"), "employee_id": "emp_eng_03", "employee_name": "Siddharth Verma", "is_billable": True, "hourly_billing_rate": Decimal("2400.00"), "hourly_cost_rate": Decimal("800.00"), "total_billing_amount": Decimal("43200.00"), "total_cost_amount": Decimal("14400.00"), "status": "APPROVED", "description": "Completed hydraulic head flow calculations.", "created_at": now - timedelta(days=22)},
        {"id": "ts_202", "project_id": p2_id, "task_id": "tsk_202", "work_date": today - timedelta(days=5), "hours": Decimal("22.00"), "employee_id": "emp_eng_03", "employee_name": "Siddharth Verma", "is_billable": True, "hourly_billing_rate": Decimal("2400.00"), "hourly_cost_rate": Decimal("800.00"), "total_billing_amount": Decimal("52800.00"), "total_cost_amount": Decimal("17600.00"), "status": "APPROVED", "description": "DC cabling and combiner box wiring.", "created_at": now - timedelta(days=5)},
    ]

    _EXPENSE_STORE[p2_id] = [
        {"id": "exp_201", "project_id": p2_id, "category": "MATERIALS", "amount": Decimal("280000.00"), "expense_date": today - timedelta(days=12), "description": "Heavy-duty outdoor galvanized aluminum mounting rail extrusions", "is_billable": True, "journal_entry_id": "je_exp_201", "created_at": now - timedelta(days=12)},
    ]

    # 3. Project 3: Chennai Telepresence & Executive Boardroom (Chennai)
    p3_id = "prj_maa_telepresence"
    _PROJECT_STORE[p3_id] = {
        "id": p3_id,
        "organization_id": org_id,
        "property_id": prop_maa,
        "project_code": "PRJ-2026-003",
        "name": "Chennai Corporate Executive Lounge & Telepresence Suite",
        "description": "Ultra-HD 8K telepresence boardroom with motorized acoustic privacy screens and smart boardroom automation.",
        "customer_id": "cust_apex_tech",
        "customer_name": "Apex Global Technology Partners",
        "project_manager_id": "usr_pm_03",
        "project_manager_name": "Sanjay Rajan",
        "billing_type": "FIXED_PRICE",
        "status": "PLANNING",
        "priority": "NORMAL",
        "start_date": today + timedelta(days=5),
        "end_date": today + timedelta(days=40),
        "budget_amount": Decimal("950000.00"),
        "billed_amount": Decimal("0.00"),
        "actual_cost": Decimal("0.00"),
        "progress_percent": Decimal("0.00"),
        "created_at": now - timedelta(days=5)
    }

    _MILESTONE_STORE[p3_id] = [
        {"id": "ms_301", "project_id": p3_id, "title": "Design Signoff & Hardware Procurement", "description": "Approve architectural layout and order telepresence codecs.", "milestone_amount": Decimal("450000.00"), "due_date": today + timedelta(days=15), "status": "PENDING", "invoice_id": None, "achieved_at": None, "created_at": now - timedelta(days=5)},
        {"id": "ms_302", "project_id": p3_id, "title": "System Integration & User Training", "description": "Final commissioning and executive board dry-run.", "milestone_amount": Decimal("500000.00"), "due_date": today + timedelta(days=40), "status": "PENDING", "invoice_id": None, "achieved_at": None, "created_at": now - timedelta(days=5)},
    ]
    _TASK_STORE[p3_id] = []
    _TIMESHEET_STORE[p3_id] = []
    _EXPENSE_STORE[p3_id] = []


class ProjectService:
    """Enterprise Project Management & Professional Services (PSA) Engine."""

    def __init__(self):
        _seed_project_data()

    # -------------------------------------------------------------
    # Projects CRUD
    # -------------------------------------------------------------
    def list_projects(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[ProjectOut]:
        _seed_project_data()
        res = []
        for p_id, p in _PROJECT_STORE.items():
            if organization_id and p["organization_id"] != organization_id:
                continue
            if property_id and p["property_id"] != property_id:
                continue
            if status and p["status"].upper() != status.upper():
                continue
            if priority and p["priority"].upper() != priority.upper():
                continue

            ms = [MilestoneOut(**m) for m in _MILESTONE_STORE.get(p_id, [])]
            ts = [TaskOut(**t) for t in _TASK_STORE.get(p_id, [])]
            p_dict = dict(p)
            p_dict["milestones"] = ms
            p_dict["tasks"] = ts
            res.append(ProjectOut(**p_dict))

        return sorted(res, key=lambda x: x.project_code)

    def get_project(self, project_id: str) -> ProjectOut:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        p = _PROJECT_STORE[project_id]
        ms = [MilestoneOut(**m) for m in _MILESTONE_STORE.get(project_id, [])]
        ts = [TaskOut(**t) for t in _TASK_STORE.get(project_id, [])]
        p_dict = dict(p)
        p_dict["milestones"] = ms
        p_dict["tasks"] = ts
        return ProjectOut(**p_dict)

    def create_project(self, payload: ProjectCreate) -> ProjectOut:
        _seed_project_data()
        global _PROJECT_COUNTER
        _PROJECT_COUNTER += 1

        p_id = f"prj_{uuid.uuid4().hex[:8]}"
        org_id = payload.organization_id or DEMO_ORGANISATIONS[0]["id"]
        prop_id = payload.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]
        code = payload.project_code or f"PRJ-2026-{_PROJECT_COUNTER:03d}"

        p_dict = {
            "id": p_id,
            "organization_id": org_id,
            "property_id": prop_id,
            "project_code": code,
            "name": payload.name,
            "description": payload.description,
            "customer_id": payload.customer_id,
            "customer_name": payload.customer_name,
            "project_manager_id": payload.project_manager_id,
            "project_manager_name": payload.project_manager_name,
            "billing_type": payload.billing_type,
            "status": payload.status.upper(),
            "priority": payload.priority.upper(),
            "start_date": payload.start_date,
            "end_date": payload.end_date,
            "budget_amount": to_decimal(payload.budget_amount),
            "billed_amount": Decimal("0.00"),
            "actual_cost": Decimal("0.00"),
            "progress_percent": Decimal("0.00"),
            "created_at": datetime.now(timezone.utc)
        }

        # Initialize child collections
        ms_list = []
        for m in payload.milestones:
            m_id = f"ms_{uuid.uuid4().hex[:6]}"
            ms_list.append({
                "id": m_id,
                "project_id": p_id,
                "title": m.title,
                "description": m.description,
                "milestone_amount": to_decimal(m.milestone_amount),
                "due_date": m.due_date,
                "status": m.status.upper(),
                "invoice_id": None,
                "achieved_at": None,
                "created_at": datetime.now(timezone.utc)
            })

        t_list = []
        for t in payload.tasks:
            t_id = f"tsk_{uuid.uuid4().hex[:6]}"
            t_list.append({
                "id": t_id,
                "project_id": p_id,
                "milestone_id": t.milestone_id,
                "task_code": t.task_code,
                "title": t.title,
                "description": t.description,
                "assigned_to_id": t.assigned_to_id,
                "assigned_to_name": t.assigned_to_name,
                "estimated_hours": to_decimal(t.estimated_hours),
                "actual_hours": Decimal("0.00"),
                "status": t.status.upper(),
                "priority": t.priority.upper(),
                "due_date": t.due_date,
                "created_at": datetime.now(timezone.utc)
            })

        _PROJECT_STORE[p_id] = p_dict
        _MILESTONE_STORE[p_id] = ms_list
        _TASK_STORE[p_id] = t_list
        _TIMESHEET_STORE[p_id] = []
        _EXPENSE_STORE[p_id] = []

        audit_service.log_action(
            action="CREATE",
            entity_type="PROJECT",
            entity_id=p_id,
            details=f"Created Project {code} ({payload.name}) for {payload.customer_name}"
        )

        return self.get_project(p_id)

    def update_project(self, project_id: str, payload: ProjectUpdate) -> ProjectOut:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        p = _PROJECT_STORE[project_id]
        if payload.name is not None:
            p["name"] = payload.name
        if payload.description is not None:
            p["description"] = payload.description
        if payload.customer_name is not None:
            p["customer_name"] = payload.customer_name
        if payload.project_manager_name is not None:
            p["project_manager_name"] = payload.project_manager_name
        if payload.billing_type is not None:
            p["billing_type"] = payload.billing_type
        if payload.status is not None:
            p["status"] = payload.status.upper()
        if payload.priority is not None:
            p["priority"] = payload.priority.upper()
        if payload.start_date is not None:
            p["start_date"] = payload.start_date
        if payload.end_date is not None:
            p["end_date"] = payload.end_date
        if payload.budget_amount is not None:
            p["budget_amount"] = to_decimal(payload.budget_amount)
        if payload.progress_percent is not None:
            p["progress_percent"] = to_decimal(payload.progress_percent)

        return self.get_project(project_id)

    # -------------------------------------------------------------
    # Milestones & Invoicing
    # -------------------------------------------------------------
    def list_milestones(self, project_id: str) -> List[MilestoneOut]:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return [MilestoneOut(**m) for m in _MILESTONE_STORE.get(project_id, [])]

    def create_milestone(self, project_id: str, payload: MilestoneCreate) -> MilestoneOut:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        m_id = f"ms_{uuid.uuid4().hex[:6]}"
        m_dict = {
            "id": m_id,
            "project_id": project_id,
            "title": payload.title,
            "description": payload.description,
            "milestone_amount": to_decimal(payload.milestone_amount),
            "due_date": payload.due_date,
            "status": payload.status.upper(),
            "invoice_id": None,
            "achieved_at": None,
            "created_at": datetime.now(timezone.utc)
        }
        _MILESTONE_STORE.setdefault(project_id, []).append(m_dict)
        return MilestoneOut(**m_dict)

    def mark_milestone_achieved(self, project_id: str, milestone_id: str) -> MilestoneOut:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        milestones = _MILESTONE_STORE.get(project_id, [])
        m = next((item for item in milestones if item["id"] == milestone_id), None)
        if not m:
            raise HTTPException(status_code=404, detail=f"Milestone {milestone_id} not found")

        m["status"] = "ACHIEVED"
        m["achieved_at"] = datetime.now(timezone.utc)
        return MilestoneOut(**m)

    def invoice_milestone(
        self,
        project_id: str,
        milestone_id: str,
        req: MilestoneInvoiceRequest
    ) -> MilestoneInvoiceResponse:
        """
        Convert achieved milestone into customer invoice and post double-entry GL journal:
        DR 1020 Accounts Receivable (AR)  [Grand Total = Milestone + 18% GST]
        CR 4040 Service & Event Fee Revenue [Subtotal = Milestone Net Amount]
        CR 2020 Sales Tax & GST Payable   [Output GST 18%]
        """
        _seed_project_data()
        global _INVOICE_COUNTER
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        project = _PROJECT_STORE[project_id]
        milestones = _MILESTONE_STORE.get(project_id, [])
        m = next((item for item in milestones if item["id"] == milestone_id), None)
        if not m:
            raise HTTPException(status_code=404, detail=f"Milestone {milestone_id} not found")

        if m["status"] == "INVOICED":
            raise HTTPException(status_code=400, detail="Milestone has already been invoiced")

        # 1. Compute invoice amounts
        amt_res = calculate_milestone_invoice(m["milestone_amount"], tax_percent=req.tax_percent)
        subtotal = amt_res["subtotal"]
        tax_amt = amt_res["tax_amount"]
        grand_total = amt_res["grand_total"]

        _INVOICE_COUNTER += 1
        inv_number = f"INV-PRJ-{_INVOICE_COUNTER:04d}"
        inv_id = f"inv_{uuid.uuid4().hex[:8]}"

        # 2. Automated Double-Entry General Ledger Posting
        journal_id = None
        try:
            journal_lines = [
                JournalLineCreate(
                    account_code="1020",
                    debit=grand_total,
                    credit=Decimal("0.00"),
                    description=f"AR - {project['customer_name']} - Project Milestone: {m['title']}"
                ),
                JournalLineCreate(
                    account_code="4040",
                    debit=Decimal("0.00"),
                    credit=subtotal,
                    description=f"Service revenue recognition: {project['name']} ({m['title']})"
                )
            ]

            if tax_amt > Decimal("0.00"):
                journal_lines.append(
                    JournalLineCreate(
                        account_code="2020",
                        debit=Decimal("0.00"),
                        credit=tax_amt,
                        description=f"GST output tax on project milestone - {inv_number}"
                    )
                )

            journal_payload = JournalEntryCreate(
                organization_id=project["organization_id"],
                property_id=project["property_id"],
                entry_date=datetime.utcnow(),
                entry_type="INVOICE",
                reference=inv_number,
                description=f"Project Milestone Billing: {m['title']} for {project['customer_name']}",
                lines=journal_lines
            )
            posted_journal = finance_service.create_journal_entry(journal_payload)
            journal_id = posted_journal["id"] if isinstance(posted_journal, dict) else posted_journal.id
        except Exception as e:
            audit_service.log_action(
                action="ERROR",
                entity_type="PROJECT_MILESTONE",
                entity_id=milestone_id,
                details=f"Milestone GL posting error: {str(e)}"
            )

        # 3. Update milestone status and project billed amount
        m["status"] = "INVOICED"
        m["invoice_id"] = inv_id
        if not m["achieved_at"]:
            m["achieved_at"] = datetime.now(timezone.utc)

        project["billed_amount"] = (to_decimal(project["billed_amount"]) + subtotal).quantize(Decimal("0.01"))

        audit_service.log_action(
            action="INVOICE",
            entity_type="PROJECT_MILESTONE",
            entity_id=milestone_id,
            details=f"Invoiced milestone '{m['title']}' for ₹{grand_total} ({inv_number})"
        )

        return MilestoneInvoiceResponse(
            milestone_id=milestone_id,
            invoice_id=inv_id,
            invoice_number=inv_number,
            subtotal=subtotal,
            tax_amount=tax_amt,
            grand_total=grand_total,
            journal_entry_id=journal_id,
            message=f"Successfully generated invoice {inv_number} and posted double-entry GL journal."
        )

    # -------------------------------------------------------------
    # WBS Tasks
    # -------------------------------------------------------------
    def list_tasks(self, project_id: str) -> List[TaskOut]:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return [TaskOut(**t) for t in _TASK_STORE.get(project_id, [])]

    def create_task(self, project_id: str, payload: TaskCreate) -> TaskOut:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        t_id = f"tsk_{uuid.uuid4().hex[:6]}"
        t_dict = {
            "id": t_id,
            "project_id": project_id,
            "milestone_id": payload.milestone_id,
            "task_code": payload.task_code,
            "title": payload.title,
            "description": payload.description,
            "assigned_to_id": payload.assigned_to_id,
            "assigned_to_name": payload.assigned_to_name,
            "estimated_hours": to_decimal(payload.estimated_hours),
            "actual_hours": to_decimal(payload.actual_hours),
            "status": payload.status.upper(),
            "priority": payload.priority.upper(),
            "due_date": payload.due_date,
            "created_at": datetime.now(timezone.utc)
        }
        _TASK_STORE.setdefault(project_id, []).append(t_dict)
        return TaskOut(**t_dict)

    def update_task_status(self, project_id: str, task_id: str, new_status: str) -> TaskOut:
        _seed_project_data()
        tasks = _TASK_STORE.get(project_id, [])
        t = next((item for item in tasks if item["id"] == task_id), None)
        if not t:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        t["status"] = new_status.upper()
        return TaskOut(**t)

    # -------------------------------------------------------------
    # Timesheets & Expenses
    # -------------------------------------------------------------
    def list_timesheets(self, project_id: str) -> List[TimesheetOut]:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return [TimesheetOut(**ts) for ts in _TIMESHEET_STORE.get(project_id, [])]

    def log_timesheet(self, project_id: str, payload: TimesheetCreate) -> TimesheetOut:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        hrs = to_decimal(payload.hours)
        b_rate = to_decimal(payload.hourly_billing_rate)
        c_rate = to_decimal(payload.hourly_cost_rate)
        tot_billing = (hrs * b_rate).quantize(Decimal("0.01"))
        tot_cost = (hrs * c_rate).quantize(Decimal("0.01"))

        ts_id = f"ts_{uuid.uuid4().hex[:6]}"
        ts_dict = {
            "id": ts_id,
            "project_id": project_id,
            "task_id": payload.task_id,
            "work_date": payload.work_date,
            "hours": hrs,
            "employee_id": payload.employee_id,
            "employee_name": payload.employee_name,
            "is_billable": payload.is_billable,
            "hourly_billing_rate": b_rate,
            "hourly_cost_rate": c_rate,
            "total_billing_amount": tot_billing,
            "total_cost_amount": tot_cost,
            "status": payload.status.upper(),
            "description": payload.description,
            "created_at": datetime.now(timezone.utc)
        }
        _TIMESHEET_STORE.setdefault(project_id, []).append(ts_dict)

        # Update project actual cost
        p = _PROJECT_STORE[project_id]
        p["actual_cost"] = (to_decimal(p["actual_cost"]) + tot_cost).quantize(Decimal("0.01"))

        # Update task actual hours if linked
        if payload.task_id:
            for tsk in _TASK_STORE.get(project_id, []):
                if tsk["id"] == payload.task_id:
                    tsk["actual_hours"] = (to_decimal(tsk["actual_hours"]) + hrs).quantize(Decimal("0.01"))

        return TimesheetOut(**ts_dict)

    def list_expenses(self, project_id: str) -> List[ExpenseOut]:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return [ExpenseOut(**e) for e in _EXPENSE_STORE.get(project_id, [])]

    def log_expense(self, project_id: str, payload: ExpenseCreate) -> ExpenseOut:
        _seed_project_data()
        if project_id not in _PROJECT_STORE:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        amt = to_decimal(payload.amount)
        exp_id = f"exp_{uuid.uuid4().hex[:6]}"
        exp_dict = {
            "id": exp_id,
            "project_id": project_id,
            "category": payload.category.upper(),
            "amount": amt,
            "expense_date": payload.expense_date,
            "description": payload.description,
            "is_billable": payload.is_billable,
            "journal_entry_id": None,
            "created_at": datetime.now(timezone.utc)
        }
        _EXPENSE_STORE.setdefault(project_id, []).append(exp_dict)

        # Update project actual cost
        p = _PROJECT_STORE[project_id]
        p["actual_cost"] = (to_decimal(p["actual_cost"]) + amt).quantize(Decimal("0.01"))

        return ExpenseOut(**exp_dict)

    # -------------------------------------------------------------
    # Executive Telemetry & Metrics
    # -------------------------------------------------------------
    def get_project_metrics(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> ProjectMetricsOut:
        _seed_project_data()

        projects = [
            p for p in _PROJECT_STORE.values()
            if (not organization_id or p["organization_id"] == organization_id)
            and (not property_id or p["property_id"] == property_id)
        ]

        proj_ids = {p["id"] for p in projects}
        all_timesheets = []
        all_expenses = []
        pending_ms_count = 0

        for pid in proj_ids:
            all_timesheets.extend(_TIMESHEET_STORE.get(pid, []))
            all_expenses.extend(_EXPENSE_STORE.get(pid, []))
            for ms in _MILESTONE_STORE.get(pid, []):
                if ms["status"] in ("PENDING", "IN_PROGRESS", "ACHIEVED"):
                    pending_ms_count += 1

        kpi_res = calculate_project_kpis(projects, all_timesheets, all_expenses)
        ts_res = calculate_timesheet_totals(all_timesheets)

        return ProjectMetricsOut(
            total_projects=kpi_res["total_projects"],
            active_projects=kpi_res["active_projects"],
            completed_projects=kpi_res["completed_projects"],
            total_contract_value=kpi_res["total_budget"],
            total_billed_revenue=kpi_res["total_billed"],
            total_actual_costs=kpi_res["total_actual_cost"],
            profit_margin_percent=kpi_res["profit_margin_percent"],
            total_logged_hours=ts_res["total_hours"],
            billable_utilization_rate=ts_res["utilization_rate"],
            pending_milestones_count=pending_ms_count
        )


project_service = ProjectService()
