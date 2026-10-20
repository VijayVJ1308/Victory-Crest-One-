"""Victory Crest One - Database Configuration & Connection Management
Central PostgreSQL connection pool with connection diagnostics, latency telemetry,
safe error reporting, and local SQLite offline database support.
"""

import time
import os
from pathlib import Path
from typing import Generator, Dict, Any, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from backend.app.core.config import settings
from backend.app.core.logging import logger

Base = declarative_base()

# Configure Primary Central Engine (PostgreSQL)
try:
    if settings.is_postgres:
        primary_engine = create_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3}
        )
    else:
        primary_engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
except Exception as e:
    logger.warning(f"Error initializing primary engine: {e}")
    primary_engine = None

PrimarySessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=primary_engine
) if primary_engine else None

# Ensure local data directory for offline SQLite database exists
local_db_path = Path(settings.LOCAL_DB_PATH)
local_db_path.parent.mkdir(parents=True, exist_ok=True)
sqlite_url = f"sqlite:///{local_db_path}"

local_engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False}
)
LocalSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=local_engine)


def check_database_connection() -> Dict[str, Any]:
    """
    Test connectivity to the central PostgreSQL database.
    Provides execution latency and explicit troubleshooting instructions if unreachable.
    Does NOT silently pretend the central database is connected.
    """
    if not primary_engine:
        return {
            "status": "disconnected",
            "engine": "PostgreSQL",
            "url_masked": settings.masked_database_url,
            "is_connected": False,
            "latency_ms": None,
            "detail": "Engine failed to initialize",
            "troubleshooting": (
                "PostgreSQL database service is unreachable or driver configuration error. "
                "To start PostgreSQL via Docker, run: `docker compose up -d` (port 5432). "
                "Verify psycopg2-binary is installed and DATABASE_URL is valid in .env."
            )
        }

    start_time = time.perf_counter()
    try:
        with primary_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            val = result.scalar()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            if val == 1:
                return {
                    "status": "connected",
                    "engine": "PostgreSQL",
                    "url_masked": settings.masked_database_url,
                    "is_connected": True,
                    "latency_ms": latency_ms,
                    "detail": "Connection active and responsive",
                    "troubleshooting": None
                }
    except OperationalError as oe:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        err_msg = str(oe.orig) if hasattr(oe, "orig") else str(oe)
        return {
            "status": "disconnected",
            "engine": "PostgreSQL",
            "url_masked": settings.masked_database_url,
            "is_connected": False,
            "latency_ms": latency_ms,
            "detail": f"OperationalError: {err_msg}",
            "troubleshooting": (
                "PostgreSQL service is not reachable at 5432. "
                "To start PostgreSQL via Docker, run: `docker compose up -d` in the project root. "
                "Alternatively, start your local PostgreSQL service or set DATABASE_URL in .env."
            )
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "error",
            "engine": "PostgreSQL",
            "url_masked": settings.masked_database_url,
            "is_connected": False,
            "latency_ms": latency_ms,
            "detail": f"Database error: {str(e)}",
            "troubleshooting": "Check PostgreSQL logs and connection credentials in .env file."
        }


def check_local_database_connection() -> Dict[str, Any]:
    """Check connectivity to the local SQLite database."""
    try:
        with local_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return {
                "status": "connected",
                "engine": "SQLite",
                "path": str(settings.LOCAL_DB_PATH),
                "is_connected": True,
                "detail": "Local SQLite storage operational"
            }
    except Exception as e:
        return {
            "status": "error",
            "engine": "SQLite",
            "path": str(settings.LOCAL_DB_PATH),
            "is_connected": False,
            "detail": str(e)
        }


def get_db() -> Generator[Session, None, None]:
    """FastAPI database dependency with session management."""
    if not PrimarySessionLocal:
        raise RuntimeError("Primary database session factory is not available")
    db = PrimarySessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_local_db() -> Generator[Session, None, None]:
    """FastAPI/Desktop local offline SQLite database dependency."""
    db = LocalSessionLocal()
    try:
        yield db
    finally:
        db.close()
