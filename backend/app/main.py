"""Victory Crest One - FastAPI Central Application
Modular enterprise backend serving REST APIs, database connectivity diagnostics,
and multi-tenant business services.
"""

from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import check_database_connection, check_local_database_connection
from backend.app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info(f"Starting {settings.APP_NAME} Backend Engine (v{settings.APP_VERSION})...")
    logger.info(f"Active Environment: {settings.APP_ENV} (DEBUG={settings.DEBUG})")
    
    # Check Central Database (PostgreSQL)
    db_status = check_database_connection()
    if db_status["is_connected"]:
        logger.info(f"Central Database: CONNECTED ({db_status['engine']} latency: {db_status['latency_ms']} ms)")
    else:
        logger.warning(f"Central Database: DISCONNECTED ({db_status['detail']})")
        logger.info(f"Troubleshooting: {db_status.get('troubleshooting')}")

    # Check Local SQLite Storage
    local_status = check_local_database_connection()
    logger.info(f"Local Storage: {local_status['status']} ({local_status['engine']})")
    
    yield
    logger.info(f"Shutting down {settings.APP_NAME} Backend...")


app = FastAPI(
    title=f"{settings.APP_NAME} - Enterprise Business Operating System",
    description=(
        "Central API powering sales, finance, ERP, hospitality, restaurant, "
        "and multi-tenant business operations for Victory Crest ONE."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_log(request: Request, call_next):
    """Middleware for request latency tracking and structured request logging."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms} ms)")
    return response


# Include Versioned API Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", summary="Root Entrypoint")
def root():
    """System welcome and operational metadata."""
    return {
        "product": settings.APP_NAME,
        "tagline": "One Platform. Every Business. Complete Control.",
        "version": settings.APP_VERSION,
        "api_docs": "/docs",
        "health_endpoint": f"{settings.API_V1_PREFIX}/health",
        "modules_endpoint": f"{settings.API_V1_PREFIX}/modules",
        "organizations_endpoint": f"{settings.API_V1_PREFIX}/organizations"
    }
