"""Victory Crest One - Health & Diagnostics Service
Monitors backend operational health, database connectivity, and environment status.
"""

from typing import Dict, Any
from datetime import datetime
import platform
import sys

from backend.app.core.config import settings
from backend.app.core.database import check_database_connection, check_local_database_connection
from backend.app.schemas.health import SystemHealthSchema, DatabaseHealthSchema


class HealthService:
    """Service to evaluate system health, database readiness, and operational status."""

    @staticmethod
    def get_system_health() -> SystemHealthSchema:
        db_info = check_database_connection()
        local_db_info = check_local_database_connection()

        db_health = DatabaseHealthSchema(
            status=db_info["status"],
            engine=db_info["engine"],
            url_masked=db_info["url_masked"],
            is_connected=db_info["is_connected"],
            latency_ms=db_info.get("latency_ms"),
            detail=db_info.get("detail"),
            troubleshooting=db_info.get("troubleshooting")
        )

        overall_status = "healthy" if db_health.is_connected else "degraded"

        diagnostics = {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "local_storage": local_db_info,
            "ai_assistant_enabled": settings.AI_ASSISTANT_ENABLED,
            "payment_sandbox_mode": settings.PAYMENT_SANDBOX_MODE,
            "database_engine_mode": "PostgreSQL (Production/Target)" if settings.is_postgres else "SQLite"
        }

        return SystemHealthSchema(
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
            timestamp=datetime.utcnow(),
            status=overall_status,
            database=db_health,
            offline_sync_available=local_db_info.get("is_connected", False),
            diagnostics=diagnostics
        )


health_service = HealthService()
