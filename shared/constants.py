"""Victory Crest One - System Constants
Canonical constants, module catalog metadata, demo entity configurations, and UI constants.
"""

from typing import Dict, List, Any

PRODUCT_NAME = "Victory Crest One"
TAGLINE = "One Platform. Every Business. Complete Control."
APP_VERSION = "0.1.0"

# Module Categories
CATEGORY_CORE = "Core & Executive"
CATEGORY_REVENUE = "Sales & Revenue"
CATEGORY_OPERATIONS = "Operations & ERP"
CATEGORY_HOSPITALITY = "Hospitality & Dining"
CATEGORY_PEOPLE = "People & Administration"

# Canonical Module Catalog
MODULE_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "dashboard",
        "name": "Executive Dashboard",
        "category": CATEGORY_CORE,
        "icon": "📊",
        "description": "Unified business metrics, live revenue telemetry, KPIs, and operational health.",
        "phase": 1,
        "status": "active"
    },
    {
        "id": "sales",
        "name": "Sales & CRM",
        "category": CATEGORY_REVENUE,
        "icon": "💼",
        "description": "Leads, deals, pipelines, quotes, customer accounts, and sales team quotas.",
        "phase": 5,
        "status": "active"
    },
    {
        "id": "marketing",
        "name": "Marketing Automation",
        "category": CATEGORY_REVENUE,
        "icon": "📣",
        "description": "Campaigns, audience segmentation, customer journeys, and conversion attribution.",
        "phase": 7,
        "status": "active"
    },

    {
        "id": "commerce",
        "name": "E-Commerce",
        "category": CATEGORY_REVENUE,
        "icon": "🛒",
        "description": "Multi-channel catalog, online storefront, inventory reservation, and cart.",
        "phase": 6,
        "status": "active"
    },
    {
        "id": "pos",
        "name": "Point of Sale (POS)",
        "category": CATEGORY_REVENUE,
        "icon": "💳",
        "description": "Multi-register cashier terminals, barcode scanning, drawer reconciliation, and receipts.",
        "phase": 6,
        "status": "active"
    },

    {
        "id": "finance",
        "name": "Finance & Banking",
        "category": CATEGORY_OPERATIONS,
        "icon": "💰",
        "description": "Receivables, payables, expenses, bank reconciliations, cash-flow, and budgets.",
        "phase": 4,
        "status": "active"
    },
    {
        "id": "accounting",
        "name": "General Accounting",
        "category": CATEGORY_OPERATIONS,
        "icon": "📑",
        "description": "Double-entry general ledger, chart of accounts, journal entries, and trial balance.",
        "phase": 4,
        "status": "active"
    },
    {
        "id": "erp",
        "name": "Supply Chain & ERP",
        "category": CATEGORY_OPERATIONS,
        "icon": "📦",
        "description": "Procurement, purchase orders, vendor evaluation, and replenishment planning.",
        "phase": 8,
        "status": "active"
    },
    {
        "id": "inventory",
        "name": "Warehouse & Inventory",
        "category": CATEGORY_OPERATIONS,
        "icon": "🏭",
        "description": "Multi-warehouse stock movements, lot/batch tracking, valuation, and stocktaking.",
        "phase": 8,
        "status": "active"
    },
    {
        "id": "manufacturing",
        "name": "Manufacturing & Assets",
        "category": CATEGORY_OPERATIONS,
        "icon": "⚙️",
        "description": "Bill of materials (BOM), production runs, quality checks, and maintenance schedules.",
        "phase": 12,
        "status": "active"
    },
    {
        "id": "service",
        "name": "Customer & Field Service",
        "category": CATEGORY_OPERATIONS,
        "icon": "🛠️",
        "description": "Support tickets, SLA tracking, field work orders, technician scheduling, and parts.",
        "phase": 10,
        "status": "active"
    },
    {
        "id": "hotel",
        "name": "Hotel & Resort PMS",
        "category": CATEGORY_HOSPITALITY,
        "icon": "🏨",
        "description": "Room inventory, rate plans, reservations, check-in/out, folios, and housekeeping.",
        "phase": 11,
        "status": "active"
    },
    {
        "id": "restaurant",
        "name": "Restaurant & Dining",
        "category": CATEGORY_HOSPITALITY,
        "icon": "🍽️",
        "description": "Table management, KDS kitchen tickets, menu recipes, wastage, and folio billing.",
        "phase": 11,
        "status": "active"
    },
    {
        "id": "hr",
        "name": "Human Resources",
        "category": CATEGORY_PEOPLE,
        "icon": "👥",
        "description": "Employee directory, recruitment pipeline, shift attendance, and leave management.",
        "phase": 9,
        "status": "active"
    },
    {
        "id": "payroll",
        "name": "Payroll Management",
        "category": CATEGORY_PEOPLE,
        "icon": "💵",
        "description": "Salary structures, statutory earnings, deductions, payslip generation, and disbursements.",
        "phase": 9,
        "status": "active"
    },
    {
        "id": "projects",
        "name": "Project Management",
        "category": CATEGORY_OPERATIONS,
        "icon": "📋",
        "description": "Portfolios, milestones, task dependencies, resource allocation, and billable time.",
        "phase": 13,
        "status": "active"
    },
    {
        "id": "bi",
        "name": "Business Intelligence",
        "category": CATEGORY_CORE,
        "icon": "📈",
        "description": "Star-schema analytical cubes, cross-module data extraction, and executive reports.",
        "phase": 14,
        "status": "active"
    },
    {
        "id": "automation",
        "name": "Workflow Automation",
        "category": CATEGORY_CORE,
        "icon": "⚡",
        "description": "Event-driven triggers, approval escalations, scheduled tasks, and webhook actions.",
        "phase": 15,
        "status": "active"
    },
    {
        "id": "ai_assistant",
        "name": "AI Business Assistant",
        "category": CATEGORY_CORE,
        "icon": "🤖",
        "description": "Permission-aware query engine, safe semantic summaries, and executive Q&A.",
        "phase": 16,
        "status": "active"
    },
    {
        "id": "iot_gateways",
        "name": "IoT & Smart Devices",
        "category": CATEGORY_OPERATIONS,
        "icon": "📡",
        "description": "Smart energy meters, guestroom automation, kitchen sensors, and asset telemetry.",
        "phase": 17,
        "status": "active"
    },
    {
        "id": "analytics_lake",
        "name": "Data Lakehouse & Predictive ML",
        "category": CATEGORY_CORE,
        "icon": "🔮",
        "description": "Distributed parquet data lake, cross-enterprise machine learning models, and automated forecasting.",
        "phase": 18,
        "status": "active"
    },
    {
        "id": "cybersecurity_governance",
        "name": "Zero-Trust Security & Audit",
        "category": CATEGORY_CORE,
        "icon": "🛡️",
        "description": "Continuous automated audit posture, zero-trust cryptographic verification, and security governance.",
        "phase": 19,
        "status": "active"
    },
    {
        "id": "multi_cloud_dr",
        "name": "Multi-Cloud Resiliency & Autonomous DR",
        "category": CATEGORY_CORE,
        "icon": "🌐",
        "description": "Continuous cross-cloud standby replication, automated failover drills, and zero-RPO disaster recovery.",
        "phase": 20,
        "status": "planned"
    },


    {
        "id": "documents",
        "name": "Shared Documents",
        "category": CATEGORY_PEOPLE,
        "icon": "📁",
        "description": "Document vault, version history, retention compliance, and cross-record attachments.",
        "phase": 3,
        "status": "planned"
    },
    {
        "id": "settings",
        "name": "Administration & Security",
        "category": CATEGORY_PEOPLE,
        "icon": "⚙️",
        "description": "Multi-tenant configuration, RBAC permissions, audit trail, and integration hub.",
        "phase": 2,
        "status": "active"
    }
]

# Standard Demo Organisations and Properties
DEMO_ORGANISATIONS = [
    {
        "id": "org_victory_crest_group",
        "code": "VCG",
        "name": "Victory Crest Enterprise Group",
        "legal_name": "Victory Crest Enterprises Private Limited",
        "currency": "INR",
        "is_simulated": True,
        "properties": [
            {
                "id": "prop_madurai_heritage",
                "code": "VCH-MDU",
                "name": "GrandVista Heritage Hotel — Madurai",
                "type": "hotel",
                "city": "Madurai",
                "state": "Tamil Nadu",
                "country": "India",
                "rooms_count": 85,
                "is_simulated": True
            },
            {
                "id": "prop_kodai_mountain",
                "code": "VCR-KOD",
                "name": "GrandVista Mountain Resort — Kodaikanal",
                "type": "resort",
                "city": "Kodaikanal",
                "state": "Tamil Nadu",
                "country": "India",
                "rooms_count": 64,
                "is_simulated": True
            },
            {
                "id": "prop_chennai_business",
                "code": "VCB-MAA",
                "name": "GrandVista Business Hotel — Chennai",
                "type": "hotel",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "country": "India",
                "rooms_count": 120,
                "is_simulated": True
            },
            {
                "id": "prop_central_hq",
                "code": "VC-HQ",
                "name": "Victory Crest Corporate HQ & Central Services",
                "type": "corporate_office",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "country": "India",
                "rooms_count": 0,
                "is_simulated": True
            }
        ]
    }
]
