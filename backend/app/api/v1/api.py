"""Victory Crest One - API v1 Router Aggregator
Combines health, organization, and module catalog endpoints under /api/v1.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, organizations, modules, auth, users, audit

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & Diagnostics"])
api_router.include_router(organizations.router, tags=["Organizations & Multi-Tenancy"])
api_router.include_router(modules.router, tags=["Module Catalog"])
api_router.include_router(auth.router, tags=["Identity & Authentication"])
api_router.include_router(users.router, tags=["User Management & RBAC"])
api_router.include_router(audit.router, tags=["Audit & Compliance"])
