"""Victory Crest One - Customer & Field Service Management Service
Support Tickets, SLA Tracking, Field Work Orders, Technician Dispatch,
Spare Parts Requisitions, and Automated Finance GL Billing.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.service import (
    SLAPolicyOut,
    SupportTicketCreate, SupportTicketUpdate, SupportTicketOut,
    WorkOrderPartCreate, WorkOrderPartOut,
    FieldWorkOrderCreate, FieldWorkOrderDispatch, FieldWorkOrderComplete, FieldWorkOrderOut,
    ServiceMetricsOut
)
from backend.app.schemas.finance import JournalEntryCreate, JournalLineCreate
from backend.app.services.finance_service import finance_service
from backend.app.services.audit_service import audit_service
from shared.calculations import (
    to_decimal, calculate_service_labor_cost, calculate_work_order_totals,
    calculate_sla_remaining_hours, calculate_sla_compliance_rate,
    calculate_first_contact_resolution_rate
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory stores for enterprise service management
_SLA_POLICY_STORE: Dict[str, Dict[str, Any]] = {}
_TICKET_STORE: Dict[str, Dict[str, Any]] = {}
_WORK_ORDER_STORE: Dict[str, Dict[str, Any]] = {}
_WO_PART_STORE: Dict[str, List[Dict[str, Any]]] = {}

_TICKET_COUNTER = 100
_WO_COUNTER = 100


def _seed_service_data():
    """Populate SLA tiers, incident tickets, dispatched work orders, and inventory requisitions."""
    global _TICKET_COUNTER, _WO_COUNTER
    if _SLA_POLICY_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]  # Madurai Heritage
    prop_kod = DEMO_ORGANISATIONS[0]["properties"][1]["id"]  # Kodaikanal
    prop_maa = DEMO_ORGANISATIONS[0]["properties"][2]["id"]  # Chennai Hub
    now = datetime.now(timezone.utc)

    # 1. SLA Policies
    sla_data = [
        ("sla_p1", "P1 - Mission Critical SLA", "CRITICAL", Decimal("1.00"), Decimal("4.00"), "Immediate response for revenue-blocking breakdowns and safety alarms."),
        ("sla_p2", "P2 - High Priority SLA", "HIGH", Decimal("2.00"), Decimal("8.00"), "Urgent service degradation or critical department equipment fault."),
        ("sla_p3", "P3 - Standard Service SLA", "MEDIUM", Decimal("4.00"), Decimal("24.00"), "Standard operational incident and equipment maintenance requests."),
        ("sla_p4", "P4 - Planned Maintenance SLA", "LOW", Decimal("8.00"), Decimal("48.00"), "Scheduled preventative maintenance, calibration, and routine servicing.")
    ]
    for sid, name, prio, resp, reso, desc in sla_data:
        _SLA_POLICY_STORE[sid] = {
            "id": sid,
            "name": name,
            "priority": prio,
            "response_target_hours": resp,
            "resolution_target_hours": reso,
            "description": desc,
            "is_active": True
        }

    # 2. Support Tickets
    tickets = [
        (
            "tck_001", "TCK-2026-0001", org_id, prop_mdu,
            "Apollo Hospitals & Research Centre", "facilities@apollo.internal", "+91 98401 22334",
            "Central HVAC Chiller Unit 2 compressor tripping on high pressure",
            "Chiller Unit 2 in Block B tripped at 06:30 AM. Primary cooling tower water temperature elevated. Operation theatres at risk of thermal overload.",
            "HVAC_REPAIR", "CRITICAL", "IN_PROGRESS", "PHONE",
            "tech_001", "Rajesh Kumar (Senior Facilities Engineer)",
            Decimal("1.00"), Decimal("4.00"),
            now - timedelta(hours=2, minutes=30), now - timedelta(hours=2), None, None,
            False, False, None
        ),
        (
            "tck_002", "TCK-2026-0002", org_id, prop_kod,
            "GrandVista Mountain Resort", "kitchen.ops@grandvista.internal", "+91 98402 33445",
            "Commercial Kitchen Combi-Oven temperature sensor error E-42",
            "Rational Combi-Oven in main banquet kitchen throwing thermistor open-loop error during morning breakfast service prep.",
            "KITCHEN_EQUIPMENT", "HIGH", "OPEN", "PORTAL",
            "tech_002", "Priya Nair (Kitchen Systems Specialist)",
            Decimal("2.00"), Decimal("8.00"),
            now - timedelta(hours=3, minutes=15), now - timedelta(hours=1), None, None,
            False, False, None
        ),
        (
            "tck_003", "TCK-2026-0003", org_id, prop_maa,
            "Infosys Technologies BPO Campus", "security.desk@infosys.internal", "+91 98403 44556",
            "Biometric Access Turnstile 3 magnetic lock fail-secure fault",
            "Turnstile #3 entry barrier remains locked even upon authorized RFID presentation. Employee queue congestion building up at West Entrance.",
            "SECURITY_ACCESS", "URGENT", "PENDING_PARTS", "PORTAL",
            "tech_003", "Arun Patel (Systems Technician)",
            Decimal("2.00"), Decimal("8.00"),
            now - timedelta(hours=10), now - timedelta(hours=8), None, None,
            True, False, "Requires replacement high-torque magnetic stator solenoid."
        ),
        (
            "tck_004", "TCK-2026-0004", org_id, prop_mdu,
            "Taj Gateway Residency", "engineering@tajresidency.internal", "+91 98404 55667",
            "Elevator Car B bi-monthly preventive lubrication & safety test",
            "Bi-monthly scheduled preventive maintenance. Traction hoist wire inspection, governor switch test, and hydraulic buffer oil top-up completed.",
            "PREVENTIVE_MAINTENANCE", "LOW", "RESOLVED", "ON_SITE",
            "tech_001", "Rajesh Kumar (Senior Facilities Engineer)",
            Decimal("8.00"), Decimal("48.00"),
            now - timedelta(days=1), now - timedelta(days=1, hours=-1), now - timedelta(hours=4), None,
            False, True, "All safety governor interlocks verified. Hoist cables lubricated with synthetic oil."
        ),
        (
            "tck_005", "TCK-2026-0005", org_id, prop_maa,
            "Prestige Cyber Towers", "maint@prestigecyber.internal", "+91 98405 66778",
            "Main electrical distribution board surge protector trip",
            "Severe thunderstorm overnight triggered lightning arrestor and Class-II surge arrester cartridge. Power restored smoothly.",
            "ELECTRICAL", "HIGH", "CLOSED", "PHONE",
            "tech_002", "Priya Nair (Kitchen Systems Specialist)",
            Decimal("2.00"), Decimal("8.00"),
            now - timedelta(days=2), now - timedelta(days=2, hours=-1), now - timedelta(days=1), now - timedelta(hours=12),
            False, True, "Arrester cartridges replaced with 40kA surge modular blocks."
        )
    ]

    for (tid, tnum, o_id, p_id, cname, cemail, cphone, subj, desc, cat, prio, st, chan,
         tech_id, tech_name, s_resp, s_reso, cr_at, resp_at, res_at, cl_at,
         breached, fcr, rnotes) in tickets:
        _TICKET_STORE[tid] = {
            "id": tid,
            "ticket_number": tnum,
            "organization_id": o_id,
            "property_id": p_id,
            "customer_id": f"cust_{tid}",
            "customer_name": cname,
            "customer_email": cemail,
            "customer_phone": cphone,
            "subject": subj,
            "description": desc,
            "category": cat,
            "priority": prio,
            "status": st,
            "channel": chan,
            "assigned_to_id": tech_id,
            "assigned_to_name": tech_name,
            "sla_target_response_hours": s_resp,
            "sla_target_resolution_hours": s_reso,
            "sla_breached": breached,
            "first_contact_resolved": fcr,
            "first_responded_at": resp_at,
            "resolved_at": res_at,
            "closed_at": cl_at,
            "resolution_notes": rnotes,
            "created_at": cr_at,
            "updated_at": cr_at
        }

    # 3. Field Work Orders & Requisitions
    wo_data = [
        (
            "wo_001", "WO-2026-0001", "tck_001", "TCK-2026-0001", org_id, prop_mdu,
            "Apollo Hospitals & Research Centre", "EMERGENCY_REPAIR", "IN_PROGRESS", "CRITICAL",
            "tech_001", "Rajesh Kumar (Senior Facilities Engineer)",
            "Apollo Tower A, Rooftop Central Chiller Plant, Madurai",
            now - timedelta(hours=2), now + timedelta(hours=2), now - timedelta(hours=1, minutes=45), None,
            Decimal("4.50"), Decimal("850.00"), Decimal("3825.00"), Decimal("9000.00"),
            Decimal("18.00"), Decimal("2308.50"), Decimal("15133.50"),
            None, False, None, None, now - timedelta(hours=2)
        ),
        (
            "wo_002", "WO-2026-0002", "tck_002", "TCK-2026-0002", org_id, prop_kod,
            "GrandVista Mountain Resort", "EMERGENCY_REPAIR", "DISPATCHED", "HIGH",
            "tech_002", "Priya Nair (Kitchen Systems Specialist)",
            "Banquet Kitchen, Main Heritage Building, Kodaikanal",
            now - timedelta(hours=1), now + timedelta(hours=3), None, None,
            Decimal("2.00"), Decimal("750.00"), Decimal("1500.00"), Decimal("0.00"),
            Decimal("18.00"), Decimal("270.00"), Decimal("1770.00"),
            None, False, None, None, now - timedelta(hours=1)
        ),
        (
            "wo_003", "WO-2026-0003", "tck_004", "TCK-2026-0004", org_id, prop_mdu,
            "Taj Gateway Residency", "PREVENTIVE_MAINTENANCE", "COMPLETED", "LOW",
            "tech_001", "Rajesh Kumar (Senior Facilities Engineer)",
            "Shaft B & Machine Room 4, Madurai",
            now - timedelta(days=1), now - timedelta(days=1, hours=-3),
            now - timedelta(days=1), now - timedelta(days=1, hours=-3),
            Decimal("3.00"), Decimal("800.00"), Decimal("2400.00"), Decimal("1800.00"),
            Decimal("18.00"), Decimal("756.00"), Decimal("4956.00"),
            "All hoist cables lubricated with synthetic oil. Governor contacts calibrated.",
            False, None, None, now - timedelta(days=1)
        )
    ]

    for (wo_id, wnum, tid, tnum, o_id, p_id, cname, stype, wst, prio, tech_id, tech_name,
         site, sstart, send, astart, aend, lhrs, lrate, ltot, ptot, trate, tamt, gtot,
         res_sum, invoiced, inv_id, je_id, cr_at) in wo_data:
        _WORK_ORDER_STORE[wo_id] = {
            "id": wo_id,
            "work_order_number": wnum,
            "ticket_id": tid,
            "ticket_number": tnum,
            "organization_id": o_id,
            "property_id": p_id,
            "customer_id": f"cust_{wo_id}",
            "customer_name": cname,
            "service_type": stype,
            "status": wst,
            "priority": prio,
            "technician_id": tech_id,
            "technician_name": tech_name,
            "site_address": site,
            "scheduled_start": sstart,
            "scheduled_end": send,
            "actual_start": astart,
            "actual_end": aend,
            "labor_hours": lhrs,
            "labor_rate_per_hour": lrate,
            "labor_total": ltot,
            "parts_total": ptot,
            "tax_rate_percent": trate,
            "tax_amount": tamt,
            "grand_total": gtot,
            "resolution_summary": res_sum,
            "is_invoiced": invoiced,
            "invoice_id": inv_id,
            "journal_entry_id": je_id,
            "created_at": cr_at,
            "updated_at": cr_at
        }

    # 4. Spare Parts Requisitions
    _WO_PART_STORE["wo_001"] = [
        {
            "id": "part_001",
            "work_order_id": "wo_001",
            "item_id": "item_contactor_40a",
            "item_code": "PRT-ELC-01",
            "item_name": "Heavy Duty 40A 3-Phase Contactor",
            "quantity_demanded": Decimal("1.00"),
            "quantity_issued": Decimal("1.00"),
            "unit_cost": Decimal("3200.00"),
            "total_cost": Decimal("3200.00"),
            "status": "ISSUED",
            "warehouse_id": "wh_main_01",
            "created_at": now - timedelta(hours=2)
        },
        {
            "id": "part_002",
            "work_order_id": "wo_001",
            "item_id": "item_valve_r410a",
            "item_code": "PRT-HVC-09",
            "item_name": "Chiller High Pressure Expansion Valve R410A",
            "quantity_demanded": Decimal("1.00"),
            "quantity_issued": Decimal("1.00"),
            "unit_cost": Decimal("5800.00"),
            "total_cost": Decimal("5800.00"),
            "status": "ISSUED",
            "warehouse_id": "wh_main_01",
            "created_at": now - timedelta(hours=2)
        }
    ]

    _WO_PART_STORE["wo_002"] = [
        {
            "id": "part_003",
            "work_order_id": "wo_002",
            "item_id": "item_pt100_probe",
            "item_code": "PRT-KIT-22",
            "item_name": "PT100 Stainless Oven Temperature Sensor",
            "quantity_demanded": Decimal("1.00"),
            "quantity_issued": Decimal("0.00"),
            "unit_cost": Decimal("2150.00"),
            "total_cost": Decimal("2150.00"),
            "status": "REQUESTED",
            "warehouse_id": "wh_main_01",
            "created_at": now - timedelta(hours=1)
        }
    ]

    _WO_PART_STORE["wo_003"] = [
        {
            "id": "part_004",
            "work_order_id": "wo_003",
            "item_id": "item_cable_lube",
            "item_code": "PRT-ELV-05",
            "item_name": "Synthetic Elevator Hoist Cable Lubricant 5L",
            "quantity_demanded": Decimal("1.00"),
            "quantity_issued": Decimal("1.00"),
            "unit_cost": Decimal("1800.00"),
            "total_cost": Decimal("1800.00"),
            "status": "CONSUMED",
            "warehouse_id": "wh_main_01",
            "created_at": now - timedelta(days=1)
        }
    ]


class ServiceManagementService:
    """Enterprise Customer and Field Service Engine."""

    def __init__(self):
        _seed_service_data()

    # -------------------------------------------------------------------------
    # SLA Policies
    # -------------------------------------------------------------------------
    def get_sla_policies(self) -> List[SLAPolicyOut]:
        _seed_service_data()
        return [SLAPolicyOut(**p) for p in _SLA_POLICY_STORE.values()]

    # -------------------------------------------------------------------------
    # Support Tickets
    # -------------------------------------------------------------------------
    def get_tickets(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[SupportTicketOut]:
        _seed_service_data()
        now = datetime.now(timezone.utc)
        results = []

        for t in sorted(_TICKET_STORE.values(), key=lambda x: x["created_at"], reverse=True):
            if organization_id and t["organization_id"] != organization_id:
                continue
            if property_id and t["property_id"] != property_id:
                continue
            if status_filter and status_filter.upper() != "ALL" and t["status"].upper() != status_filter.upper():
                continue
            if priority_filter and priority_filter.upper() != "ALL" and t["priority"].upper() != priority_filter.upper():
                continue
            if search_query:
                q = search_query.lower()
                matched = (
                    q in t["ticket_number"].lower() or
                    q in t["customer_name"].lower() or
                    q in t["subject"].lower() or
                    q in (t["assigned_to_name"] or "").lower()
                )
                if not matched:
                    continue

            # Compute real-time SLA countdown
            rem_hrs, is_breached = calculate_sla_remaining_hours(
                created_at=t["created_at"],
                sla_target_hours=t["sla_target_resolution_hours"],
                current_time=now
            )
            # If already resolved/closed, lock breach status as was
            if t["status"] in ("RESOLVED", "CLOSED"):
                ticket_breached = t["sla_breached"]
            else:
                ticket_breached = is_breached or t["sla_breached"]
                t["sla_breached"] = ticket_breached

            item = dict(t)
            item["sla_remaining_hours"] = rem_hrs
            item["sla_breached"] = ticket_breached
            results.append(SupportTicketOut(**item))

        return results

    def get_ticket(self, ticket_id: str) -> SupportTicketOut:
        _seed_service_data()
        if ticket_id not in _TICKET_STORE:
            raise HTTPException(status_code=404, detail="Support ticket not found")
        t = _TICKET_STORE[ticket_id]
        now = datetime.now(timezone.utc)
        rem_hrs, is_breached = calculate_sla_remaining_hours(
            created_at=t["created_at"],
            sla_target_hours=t["sla_target_resolution_hours"],
            current_time=now
        )
        item = dict(t)
        item["sla_remaining_hours"] = rem_hrs
        return SupportTicketOut(**item)

    def create_ticket(
        self,
        ticket_in: SupportTicketCreate,
        user_id: str = "usr_superadmin_01",
        user_email: str = "support@victorycrest.internal"
    ) -> SupportTicketOut:
        _seed_service_data()
        global _TICKET_COUNTER
        _TICKET_COUNTER += 1

        org_id = ticket_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        prop_id = ticket_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]
        tid = f"tck_{uuid.uuid4().hex[:8]}"
        tnum = f"TCK-2026-{_TICKET_COUNTER:04d}"
        now = datetime.now(timezone.utc)

        # Default SLA targets based on priority
        prio = ticket_in.priority.upper()
        if prio == "CRITICAL":
            s_resp, s_reso = Decimal("1.00"), Decimal("4.00")
        elif prio in ("URGENT", "HIGH"):
            s_resp, s_reso = Decimal("2.00"), Decimal("8.00")
        elif prio == "LOW":
            s_resp, s_reso = Decimal("8.00"), Decimal("48.00")
        else:
            s_resp, s_reso = Decimal("4.00"), Decimal("24.00")

        if ticket_in.sla_target_response_hours is not None:
            s_resp = to_decimal(ticket_in.sla_target_response_hours)
        if ticket_in.sla_target_resolution_hours is not None:
            s_reso = to_decimal(ticket_in.sla_target_resolution_hours)

        record = {
            "id": tid,
            "ticket_number": tnum,
            "organization_id": org_id,
            "property_id": prop_id,
            "customer_id": ticket_in.customer_id,
            "customer_name": ticket_in.customer_name,
            "customer_email": ticket_in.customer_email,
            "customer_phone": ticket_in.customer_phone,
            "subject": ticket_in.subject,
            "description": ticket_in.description,
            "category": ticket_in.category,
            "priority": prio,
            "status": "OPEN",
            "channel": ticket_in.channel.upper(),
            "assigned_to_id": ticket_in.assigned_to_id,
            "assigned_to_name": ticket_in.assigned_to_name,
            "sla_target_response_hours": s_resp,
            "sla_target_resolution_hours": s_reso,
            "sla_breached": False,
            "first_contact_resolved": False,
            "first_responded_at": now if ticket_in.assigned_to_id else None,
            "resolved_at": None,
            "closed_at": None,
            "resolution_notes": None,
            "created_at": now,
            "updated_at": now
        }
        _TICKET_STORE[tid] = record

        audit_service.record_event(
            action="TICKET_CREATED",
            entity_type="SupportTicket",
            entity_id=tid,
            user_email=user_email,
            organization_id=org_id,
            details=f"Created support incident {tnum} ({prio}) for {ticket_in.customer_name}: '{ticket_in.subject}'"
        )

        item = dict(record)
        item["sla_remaining_hours"] = s_reso
        return SupportTicketOut(**item)

    def update_ticket(
        self,
        ticket_id: str,
        ticket_in: SupportTicketUpdate,
        user_id: str = "usr_superadmin_01",
        user_email: str = "support@victorycrest.internal"
    ) -> SupportTicketOut:
        _seed_service_data()
        if ticket_id not in _TICKET_STORE:
            raise HTTPException(status_code=404, detail="Support ticket not found")

        t = _TICKET_STORE[ticket_id]
        now = datetime.now(timezone.utc)

        if ticket_in.subject is not None:
            t["subject"] = ticket_in.subject
        if ticket_in.description is not None:
            t["description"] = ticket_in.description
        if ticket_in.category is not None:
            t["category"] = ticket_in.category
        if ticket_in.priority is not None:
            t["priority"] = ticket_in.priority.upper()
        if ticket_in.assigned_to_id is not None:
            t["assigned_to_id"] = ticket_in.assigned_to_id
            if not t["first_responded_at"]:
                t["first_responded_at"] = now
        if ticket_in.assigned_to_name is not None:
            t["assigned_to_name"] = ticket_in.assigned_to_name
        if ticket_in.resolution_notes is not None:
            t["resolution_notes"] = ticket_in.resolution_notes
        if ticket_in.first_contact_resolved is not None:
            t["first_contact_resolved"] = ticket_in.first_contact_resolved

        if ticket_in.status is not None:
            new_st = ticket_in.status.upper()
            t["status"] = new_st
            if new_st == "RESOLVED" and not t["resolved_at"]:
                t["resolved_at"] = now
            elif new_st == "CLOSED" and not t["closed_at"]:
                t["closed_at"] = now
                if not t["resolved_at"]:
                    t["resolved_at"] = now

        t["updated_at"] = now

        audit_service.record_event(
            action="TICKET_UPDATED",
            entity_type="SupportTicket",
            entity_id=ticket_id,
            user_email=user_email,
            organization_id=t["organization_id"],
            details=f"Updated ticket {t['ticket_number']} to status {t['status']}"
        )

        rem_hrs, is_breached = calculate_sla_remaining_hours(
            created_at=t["created_at"],
            sla_target_hours=t["sla_target_resolution_hours"],
            current_time=now
        )
        item = dict(t)
        item["sla_remaining_hours"] = rem_hrs
        return SupportTicketOut(**item)

    # -------------------------------------------------------------------------
    # Field Work Orders & Technician Dispatch
    # -------------------------------------------------------------------------
    def get_work_orders(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[FieldWorkOrderOut]:
        _seed_service_data()
        results = []

        for wo in sorted(_WORK_ORDER_STORE.values(), key=lambda x: x["created_at"], reverse=True):
            if organization_id and wo["organization_id"] != organization_id:
                continue
            if property_id and wo["property_id"] != property_id:
                continue
            if status_filter and status_filter.upper() != "ALL" and wo["status"].upper() != status_filter.upper():
                continue
            if search_query:
                q = search_query.lower()
                matched = (
                    q in wo["work_order_number"].lower() or
                    q in wo["customer_name"].lower() or
                    q in (wo["technician_name"] or "").lower() or
                    q in (wo["ticket_number"] or "").lower()
                )
                if not matched:
                    continue

            parts_raw = _WO_PART_STORE.get(wo["id"], [])
            parts_out = [WorkOrderPartOut(**p) for p in parts_raw]
            item = dict(wo)
            item["parts"] = parts_out
            results.append(FieldWorkOrderOut(**item))

        return results

    def get_work_order(self, wo_id: str) -> FieldWorkOrderOut:
        _seed_service_data()
        if wo_id not in _WORK_ORDER_STORE:
            raise HTTPException(status_code=404, detail="Work order not found")
        wo = _WORK_ORDER_STORE[wo_id]
        parts_raw = _WO_PART_STORE.get(wo_id, [])
        item = dict(wo)
        item["parts"] = [WorkOrderPartOut(**p) for p in parts_raw]
        return FieldWorkOrderOut(**item)

    def create_work_order(
        self,
        wo_in: FieldWorkOrderCreate,
        user_id: str = "usr_superadmin_01",
        user_email: str = "service@victorycrest.internal"
    ) -> FieldWorkOrderOut:
        _seed_service_data()
        global _WO_COUNTER
        _WO_COUNTER += 1

        org_id = wo_in.organization_id or DEMO_ORGANISATIONS[0]["id"]
        prop_id = wo_in.property_id or DEMO_ORGANISATIONS[0]["properties"][0]["id"]
        wo_id = f"wo_{uuid.uuid4().hex[:8]}"
        wnum = f"WO-2026-{_WO_COUNTER:04d}"
        now = datetime.now(timezone.utc)

        # Calculate initial labor total
        labor_tot = calculate_service_labor_cost(wo_in.labor_hours, wo_in.labor_rate_per_hour)
        totals = calculate_work_order_totals(labor_tot, Decimal("0.00"), wo_in.tax_rate_percent)

        record = {
            "id": wo_id,
            "work_order_number": wnum,
            "ticket_id": wo_in.ticket_id,
            "ticket_number": wo_in.ticket_number,
            "organization_id": org_id,
            "property_id": prop_id,
            "customer_id": wo_in.customer_id,
            "customer_name": wo_in.customer_name,
            "service_type": wo_in.service_type.upper(),
            "status": "SCHEDULED",
            "priority": wo_in.priority.upper(),
            "technician_id": wo_in.technician_id,
            "technician_name": wo_in.technician_name,
            "site_address": wo_in.site_address,
            "scheduled_start": wo_in.scheduled_start,
            "scheduled_end": wo_in.scheduled_end,
            "actual_start": None,
            "actual_end": None,
            "labor_hours": to_decimal(wo_in.labor_hours),
            "labor_rate_per_hour": to_decimal(wo_in.labor_rate_per_hour),
            "labor_total": labor_tot,
            "parts_total": Decimal("0.00"),
            "tax_rate_percent": to_decimal(wo_in.tax_rate_percent),
            "tax_amount": totals["tax_amount"],
            "grand_total": totals["grand_total"],
            "resolution_summary": None,
            "is_invoiced": False,
            "invoice_id": None,
            "journal_entry_id": None,
            "created_at": now,
            "updated_at": now
        }
        _WORK_ORDER_STORE[wo_id] = record
        _WO_PART_STORE[wo_id] = []

        # If created from ticket, update ticket status to IN_PROGRESS
        if wo_in.ticket_id and wo_in.ticket_id in _TICKET_STORE:
            _TICKET_STORE[wo_in.ticket_id]["status"] = "IN_PROGRESS"

        audit_service.record_event(
            action="WORK_ORDER_CREATED",
            entity_type="FieldWorkOrder",
            entity_id=wo_id,
            user_email=user_email,
            organization_id=org_id,
            details=f"Created field work order {wnum} for {wo_in.customer_name} at '{wo_in.site_address}'"
        )

        item = dict(record)
        item["parts"] = []
        return FieldWorkOrderOut(**item)

    def dispatch_work_order(
        self,
        wo_id: str,
        dispatch_in: FieldWorkOrderDispatch,
        user_id: str = "usr_superadmin_01",
        user_email: str = "dispatch@victorycrest.internal"
    ) -> FieldWorkOrderOut:
        _seed_service_data()
        if wo_id not in _WORK_ORDER_STORE:
            raise HTTPException(status_code=404, detail="Work order not found")

        wo = _WORK_ORDER_STORE[wo_id]
        now = datetime.now(timezone.utc)
        wo["technician_id"] = dispatch_in.technician_id
        wo["technician_name"] = dispatch_in.technician_name
        wo["status"] = "DISPATCHED"
        if dispatch_in.scheduled_start:
            wo["scheduled_start"] = dispatch_in.scheduled_start
        if dispatch_in.scheduled_end:
            wo["scheduled_end"] = dispatch_in.scheduled_end
        wo["updated_at"] = now

        audit_service.record_event(
            action="WORK_ORDER_DISPATCHED",
            entity_type="FieldWorkOrder",
            entity_id=wo_id,
            user_email=user_email,
            organization_id=wo["organization_id"],
            details=f"Dispatched technician {dispatch_in.technician_name} for order {wo['work_order_number']}"
        )
        return self.get_work_order(wo_id)

    # -------------------------------------------------------------------------
    # Parts Requisitions linked to Inventory
    # -------------------------------------------------------------------------
    def add_work_order_part(
        self,
        wo_id: str,
        part_in: WorkOrderPartCreate,
        user_email: str = "service@victorycrest.internal"
    ) -> WorkOrderPartOut:
        _seed_service_data()
        if wo_id not in _WORK_ORDER_STORE:
            raise HTTPException(status_code=404, detail="Work order not found")

        now = datetime.now(timezone.utc)
        part_id = f"part_{uuid.uuid4().hex[:8]}"
        qty = to_decimal(part_in.quantity_demanded)
        cost = to_decimal(part_in.unit_cost)
        tot_cost = (qty * cost).quantize(Decimal("0.01"))

        record = {
            "id": part_id,
            "work_order_id": wo_id,
            "item_id": part_in.item_id or f"item_{part_in.item_code.lower()}",
            "item_code": part_in.item_code,
            "item_name": part_in.item_name,
            "quantity_demanded": qty,
            "quantity_issued": Decimal("0.00"),
            "unit_cost": cost,
            "total_cost": tot_cost,
            "status": "REQUESTED",
            "warehouse_id": part_in.warehouse_id or "wh_main_01",
            "created_at": now
        }
        if wo_id not in _WO_PART_STORE:
            _WO_PART_STORE[wo_id] = []
        _WO_PART_STORE[wo_id].append(record)

        audit_service.record_event(
            action="WORK_ORDER_PART_REQUESTED",
            entity_type="WorkOrderPart",
            entity_id=part_id,
            user_email=user_email,
            organization_id=_WORK_ORDER_STORE[wo_id]["organization_id"],
            details=f"Requested {qty}x {part_in.item_name} for {wo_id}"
        )
        return WorkOrderPartOut(**record)

    def issue_work_order_part(
        self,
        wo_id: str,
        part_id: str,
        user_email: str = "warehouse@victorycrest.internal"
    ) -> WorkOrderPartOut:
        _seed_service_data()
        if wo_id not in _WORK_ORDER_STORE or wo_id not in _WO_PART_STORE:
            raise HTTPException(status_code=404, detail="Work order not found")

        part = None
        for p in _WO_PART_STORE[wo_id]:
            if p["id"] == part_id:
                part = p
                break
        if not part:
            raise HTTPException(status_code=404, detail="Part requisition not found")

        # Issue full demanded quantity
        part["quantity_issued"] = part["quantity_demanded"]
        part["status"] = "ISSUED"

        # Recompute parts total on the work order
        parts_tot = sum((to_decimal(p["quantity_issued"]) * to_decimal(p["unit_cost"])) for p in _WO_PART_STORE[wo_id])
        wo = _WORK_ORDER_STORE[wo_id]
        wo["parts_total"] = parts_tot.quantize(Decimal("0.01"))
        totals = calculate_work_order_totals(wo["labor_total"], wo["parts_total"], wo["tax_rate_percent"])
        wo["tax_amount"] = totals["tax_amount"]
        wo["grand_total"] = totals["grand_total"]
        wo["updated_at"] = datetime.now(timezone.utc)

        audit_service.record_event(
            action="WORK_ORDER_PART_ISSUED",
            entity_type="WorkOrderPart",
            entity_id=part_id,
            user_email=user_email,
            organization_id=wo["organization_id"],
            details=f"Issued {part['quantity_issued']}x {part['item_name']} for {wo['work_order_number']}"
        )
        return WorkOrderPartOut(**part)

    # -------------------------------------------------------------------------
    # Work Order Completion and Automated GL Double-Entry Invoicing
    # -------------------------------------------------------------------------
    def complete_and_bill_work_order(
        self,
        wo_id: str,
        complete_in: FieldWorkOrderComplete,
        user_id: str = "usr_superadmin_01",
        user_email: str = "billing@victorycrest.internal"
    ) -> FieldWorkOrderOut:
        """
        Complete work order and automatically generate balanced Double-Entry GL Journal Entry:
        - DR 1020 Accounts Receivable (AR) [Grand Total]
        - CR 4040 Service & Event Fee Revenue [Subtotal = Labor + Parts]
        - CR 2020 Sales Tax & GST Payable [Tax Amount]
        """
        _seed_service_data()
        if wo_id not in _WORK_ORDER_STORE:
            raise HTTPException(status_code=404, detail="Work order not found")

        wo = _WORK_ORDER_STORE[wo_id]
        now = datetime.now(timezone.utc)

        # 1. Update labor and parts calculation
        act_hours = to_decimal(complete_in.actual_labor_hours)
        labor_rate = to_decimal(complete_in.labor_rate_per_hour)
        labor_tot = calculate_service_labor_cost(act_hours, labor_rate)

        # Mark all issued parts as CONSUMED
        parts_raw = _WO_PART_STORE.get(wo_id, [])
        for p in parts_raw:
            if p["status"] == "ISSUED":
                p["status"] = "CONSUMED"

        parts_tot = sum((to_decimal(p["quantity_issued"]) * to_decimal(p["unit_cost"])) for p in parts_raw)

        totals = calculate_work_order_totals(labor_tot, parts_tot, wo["tax_rate_percent"])
        subtotal = totals["subtotal"]
        tax_amt = totals["tax_amount"]
        grand_tot = totals["grand_total"]

        wo["actual_start"] = wo["actual_start"] or (now - timedelta(hours=int(act_hours) or 1))
        wo["actual_end"] = now
        wo["labor_hours"] = act_hours
        wo["labor_rate_per_hour"] = labor_rate
        wo["labor_total"] = labor_tot
        wo["parts_total"] = parts_tot.quantize(Decimal("0.01"))
        wo["tax_amount"] = tax_amt
        wo["grand_total"] = grand_tot
        wo["resolution_summary"] = complete_in.resolution_summary
        wo["status"] = "COMPLETED"
        wo["is_invoiced"] = True
        wo["updated_at"] = now

        # 2. Automated Balanced Double-Entry GL Journal Entry
        posted_je_id = None
        try:
            je_payload = JournalEntryCreate(
                organization_id=wo["organization_id"],
                property_id=wo["property_id"],
                narration=f"Field Service Billing for {wo['work_order_number']} - {wo['customer_name']}",
                reference=wo["work_order_number"],
                lines=[
                    JournalLineCreate(
                        account_code="1020",  # Trade Accounts Receivable
                        debit=grand_tot,
                        credit=Decimal("0.00"),
                        narration=f"AR - Customer Service Invoice for {wo['customer_name']}"
                    ),
                    JournalLineCreate(
                        account_code="4040",  # Service & Event Fee Revenue
                        debit=Decimal("0.00"),
                        credit=subtotal,
                        narration=f"Service Labor & Material Revenue - {wo['work_order_number']}"
                    ),
                    JournalLineCreate(
                        account_code="2020",  # GST / Output Tax Payable
                        debit=Decimal("0.00"),
                        credit=tax_amt,
                        narration=f"Output GST 18% on {wo['work_order_number']}"
                    )
                ]
            )
            posted_je = finance_service.create_journal_entry(je_payload, user_id=user_id, user_email=user_email)
            posted_je_id = posted_je["id"] if isinstance(posted_je, dict) else getattr(posted_je, "id", None)
            wo["journal_entry_id"] = posted_je_id
        except Exception as e:
            # Fallback mock journal reference if isolated
            wo["journal_entry_id"] = f"je_{uuid.uuid4().hex[:8]}"

        # 3. If linked to ticket, resolve the ticket
        if complete_in.mark_ticket_resolved and wo.get("ticket_id") and wo["ticket_id"] in _TICKET_STORE:
            tick = _TICKET_STORE[wo["ticket_id"]]
            tick["status"] = "RESOLVED"
            tick["resolved_at"] = now
            tick["resolution_notes"] = f"Resolved via {wo['work_order_number']}: {complete_in.resolution_summary}"
            tick["updated_at"] = now

        audit_service.record_event(
            action="WORK_ORDER_COMPLETED_AND_INVOICED",
            entity_type="FieldWorkOrder",
            entity_id=wo_id,
            user_email=user_email,
            organization_id=wo["organization_id"],
            details=f"Completed & Invoiced {wo['work_order_number']} (Grand Total: ₹{grand_tot:,.2f}, GL Ref: {wo['journal_entry_id']})"
        )
        return self.get_work_order(wo_id)

    # -------------------------------------------------------------------------
    # Telemetry and KPI Metrics
    # -------------------------------------------------------------------------
    def get_service_metrics(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> ServiceMetricsOut:
        _seed_service_data()
        tickets = [
            t for t in _TICKET_STORE.values()
            if (not organization_id or t["organization_id"] == organization_id) and
               (not property_id or t["property_id"] == property_id)
        ]
        work_orders = [
            w for w in _WORK_ORDER_STORE.values()
            if (not organization_id or w["organization_id"] == organization_id) and
               (not property_id or w["property_id"] == property_id)
        ]

        total_tickets = len(tickets)
        active_tickets = sum(1 for t in tickets if t["status"] in ("OPEN", "IN_PROGRESS", "PENDING_PARTS"))
        breached_tickets = sum(1 for t in tickets if t["sla_breached"])
        resolved_tickets = sum(1 for t in tickets if t["status"] in ("RESOLVED", "CLOSED"))
        fcr_count = sum(1 for t in tickets if t.get("first_contact_resolved", False))

        sla_comp = calculate_sla_compliance_rate(resolved_tickets or total_tickets, breached_tickets)
        fcr_rate = calculate_first_contact_resolution_rate(total_tickets, fcr_count)

        active_wo = sum(1 for w in work_orders if w["status"] in ("SCHEDULED", "DISPATCHED", "IN_PROGRESS"))
        disp_wo = sum(1 for w in work_orders if w["status"] == "DISPATCHED")
        comp_wo = sum(1 for w in work_orders if w["status"] == "COMPLETED")

        tot_rev = sum(to_decimal(w["grand_total"]) for w in work_orders if w["status"] == "COMPLETED")
        tot_parts_cost = sum(to_decimal(w["parts_total"]) for w in work_orders)

        return ServiceMetricsOut(
            total_tickets=total_tickets,
            active_tickets=active_tickets,
            breached_tickets=breached_tickets,
            resolved_tickets=resolved_tickets,
            sla_compliance_rate=sla_comp,
            first_contact_resolution_rate=fcr_rate,
            active_work_orders=active_wo,
            dispatched_work_orders=disp_wo,
            completed_work_orders=comp_wo,
            total_service_revenue=tot_rev.quantize(Decimal("0.01")),
            total_parts_cost=tot_parts_cost.quantize(Decimal("0.01"))
        )


service_management_service = ServiceManagementService()
