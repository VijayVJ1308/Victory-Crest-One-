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
    finance
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

