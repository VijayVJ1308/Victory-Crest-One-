"""Victory Crest One - Integration Tests for Database Connections & Diagnostics
"""

from backend.app.core.database import check_database_connection, check_local_database_connection


def test_database_connection_diagnostics():
    """Verify check_database_connection provides honest diagnostic output and troubleshooting."""
    result = check_database_connection()
    assert "status" in result
    assert "engine" in result
    assert "is_connected" in result
    assert "url_masked" in result
    # Make sure passwords are not exposed
    assert "postgres:postgres@" not in result["url_masked"]
    
    if not result["is_connected"]:
        assert result["troubleshooting"] is not None
        assert "docker compose up -d" in result["troubleshooting"] or "5432" in result["troubleshooting"]


def test_local_sqlite_connection():
    """Verify local SQLite storage is operational for offline queue and caching."""
    result = check_local_database_connection()
    assert result["is_connected"] is True
    assert result["engine"] == "SQLite"
