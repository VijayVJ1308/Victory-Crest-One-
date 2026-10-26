"""Victory Crest One - API v1 Router Aggregator
Combines health, organization, and module catalog endpoints under /api/v1.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    organizations,
    modules,
    auth,
    users,
    audit,
    customers,
    suppliers,
    products,
    documents,
    notifications,
    finance,
    crm,
    pos,
    marketing,
    inventory,
    hr,
    service,
    hospitality,
    manufacturing,
    projects,
    bi,
    automation,
    ai_assistant,
    iot,
    lakehouse,
    security,
    dr
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & Diagnostics"])
api_router.include_router(organizations.router, tags=["Organizations & Multi-Tenancy"])
api_router.include_router(modules.router, tags=["Module Catalog"])
api_router.include_router(auth.router, tags=["Identity & Authentication"])
api_router.include_router(users.router, tags=["User Management & RBAC"])
api_router.include_router(audit.router, tags=["Audit & Compliance"])
api_router.include_router(customers.router, tags=["Customer Master"])
api_router.include_router(suppliers.router, tags=["Supplier Master"])
api_router.include_router(products.router, tags=["Product Master"])
api_router.include_router(documents.router, tags=["Document Vault"])
api_router.include_router(notifications.router, tags=["In-App Notifications"])
api_router.include_router(finance.router, tags=["Finance & General Accounting"])
api_router.include_router(crm.router, tags=["Sales CRM & Revenue Pipeline"])
api_router.include_router(pos.router, tags=["Point of Sale & Commerce"])
api_router.include_router(marketing.router, tags=["Marketing Automation"])
api_router.include_router(inventory.router, tags=["Supply Chain, ERP & Inventory"])
api_router.include_router(hr.router, tags=["Human Resources & Payroll"])
api_router.include_router(service.router, tags=["Customer & Field Service"])
api_router.include_router(hospitality.router, tags=["Hospitality PMS & Restaurant Dining"])
api_router.include_router(manufacturing.router, tags=["Manufacturing & Production Orders"])
api_router.include_router(projects.router, tags=["Project Management & PSA"])
api_router.include_router(bi.router, tags=["Business Intelligence & Analytics"])
api_router.include_router(automation.router, prefix="/automation", tags=["Workflow Automation & Rules Engine"])
api_router.include_router(ai_assistant.router, prefix="/ai", tags=["AI Business Assistant & Semantic Q&A"])
api_router.include_router(iot.router, prefix="/iot", tags=["IoT & Smart Device Gateways"])
api_router.include_router(lakehouse.router, prefix="/lakehouse", tags=["Data Lakehouse & Predictive ML"])
api_router.include_router(security.router, prefix="/security", tags=["Zero-Trust Security & Compliance Auditor"])
api_router.include_router(dr.router, prefix="/dr", tags=["Multi-Cloud Resiliency & Autonomous DR"])









