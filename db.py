"""
db.py — Centralized Database Access for SwarmOps
Single source of truth for the SQLite connection.

Configuration:
  - Local dev:  uses ./marketingos.db (relative to this file)
  - Railway:    set DB_PATH=/data/marketingos.db (persistent volume mount)

All modules import from here instead of hardcoding their own path.
"""

import os
import sqlite3
import threading

# ---------------------------------------------------------------------------
# DB_PATH — controlled by environment variable for Railway volume support
# ---------------------------------------------------------------------------
# Default: marketingos.db in the same directory as this file (project root).
# On Railway: set DB_PATH=/data/marketingos.db in environment variables,
# then mount a Railway Volume at /data to persist across deploys.
_DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marketingos.db")
DB_PATH = os.environ.get("DB_PATH", _DEFAULT_DB)

# Log which path is being used on startup
print(f"[db] Using database: {DB_PATH}")

# ---------------------------------------------------------------------------
# Thread-local connection pool
# One connection per thread — safe for FastAPI's async threadpool workers.
# ---------------------------------------------------------------------------
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """
    Get a thread-local SQLite connection.
    Creates the connection (and parent directory) on first use per thread.
    WAL mode enabled for better concurrent read/write performance.
    """
    if not hasattr(_local, "conn") or _local.conn is None:
        # Ensure parent directory exists (important for Railway volume paths like /data/)
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row

        # WAL mode: readers don't block writers, writers don't block readers
        _local.conn.execute("PRAGMA journal_mode=WAL")
        # Wait up to 5s if the DB is locked instead of immediately raising
        _local.conn.execute("PRAGMA busy_timeout=5000")

    return _local.conn


def get_db_path() -> str:
    """Return the active database file path."""
    return DB_PATH


def get_db_size_mb() -> float:
    """Return the database file size in megabytes. Returns 0.0 if file not found."""
    try:
        return round(os.path.getsize(DB_PATH) / (1024 * 1024), 3)
    except OSError:
        return 0.0


def get_table_count() -> int:
    """Return the number of tables in the database."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) as c FROM sqlite_master WHERE type='table'"
        ).fetchone()
        return row["c"] if row else 0
    except Exception:
        return 0
