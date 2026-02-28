"""
Memory Store - SwarmOps
Persistent SQLite memory so agents learn from past work.
"""

import sqlite3
import json
import os
import threading
from datetime import datetime, timedelta, timezone
from db import get_connection as _db_get_connection, DB_PATH


class MemoryStore:
    """Persistent memory for all SwarmOps agents using SQLite."""

    def __init__(self, db_path=None):
        # db_path param kept for backwards compatibility but ignored —
        # all modules share the single DB_PATH from db.py
        self.db_path = DB_PATH
        self._local = threading.local()
        self._init_tables()

    def _get_conn(self):
        """Get a thread-local SQLite connection via centralized db.py."""
        return _db_get_connection()

    def _init_tables(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS task_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT NOT NULL,
                task_input TEXT NOT NULL,
                task_output TEXT NOT NULL,
                model TEXT,
                provider TEXT,
                confidence REAL,
                latency_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Business Profile: persistent key/value store for user's business data
            CREATE TABLE IF NOT EXISTS business_profile (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Agent Insights: meaningful insights saved per department
            CREATE TABLE IF NOT EXISTS agent_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL DEFAULT 0.8,
                source TEXT DEFAULT 'agent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            );

            -- Recommendation Tracking: track what was recommended and outcome
            CREATE TABLE IF NOT EXISTS recommendation_tracking (
                id TEXT PRIMARY KEY,
                department TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                predicted_impact TEXT,
                status TEXT DEFAULT 'pending',
                actual_impact TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_memory_dept ON agent_memory(department);
            CREATE INDEX IF NOT EXISTS idx_memory_type ON agent_memory(memory_type);
            CREATE INDEX IF NOT EXISTS idx_tasklog_dept ON task_log(department);
            CREATE INDEX IF NOT EXISTS idx_tasklog_date ON task_log(created_at);
            CREATE INDEX IF NOT EXISTS idx_insights_dept ON agent_insights(department);
        """)
        conn.commit()

    # ------------------------------------------------------------------
    # Agent Memory
    # ------------------------------------------------------------------

    def save_memory(self, department: str, memory_type: str, content: str, metadata: dict = None):
        """Store a memory for an agent department."""
        conn = self._get_conn()
        meta_json = json.dumps(metadata, default=str) if metadata else None
        conn.execute(
            "INSERT INTO agent_memory (department, memory_type, content, metadata) VALUES (?, ?, ?, ?)",
            (department, memory_type, content, meta_json),
        )
        conn.commit()

    def recall_memories(self, department: str, limit: int = 5) -> list:
        """Get most recent memories for a department."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT content, metadata, created_at FROM agent_memory WHERE department = ? ORDER BY created_at DESC LIMIT ?",
            (department, limit),
        ).fetchall()
        return [
            {
                "content": r["content"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def search_memories(self, department: str, query: str, limit: int = 3) -> list:
        """Simple text search across memories for a department."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT content, metadata, created_at FROM agent_memory WHERE department = ? AND content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (department, f"%{query}%", limit),
        ).fetchall()
        return [
            {
                "content": r["content"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Task Log
    # ------------------------------------------------------------------

    def log_task(self, department: str, task_input: str, task_output: str,
                 model: str = "", provider: str = "", confidence: float = 0.0, latency_ms: int = 0):
        """Log a completed task."""
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO task_log (department, task_input, task_output, model, provider, confidence, latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (department, task_input, task_output[:500], model, provider, confidence, latency_ms),
        )
        conn.commit()

    def get_task_history(self, department: str = None, days: int = 7, limit: int = 20) -> list:
        """Get recent tasks, optionally filtered by department."""
        conn = self._get_conn()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        if department:
            rows = conn.execute(
                "SELECT department, task_input, task_output, model, provider, confidence, latency_ms, created_at "
                "FROM task_log WHERE department = ? AND created_at >= ? ORDER BY created_at DESC LIMIT ?",
                (department, cutoff, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT department, task_input, task_output, model, provider, confidence, latency_ms, created_at "
                "FROM task_log WHERE created_at >= ? ORDER BY created_at DESC LIMIT ?",
                (cutoff, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Aggregate stats across all tasks."""
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) as c FROM task_log").fetchone()["c"]
        today_cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        today = conn.execute("SELECT COUNT(*) as c FROM task_log WHERE created_at >= ?", (today_cutoff,)).fetchone()["c"]
        avg_conf = conn.execute("SELECT AVG(confidence) as a FROM task_log WHERE confidence > 0").fetchone()["a"]

        models = {}
        for r in conn.execute("SELECT provider, COUNT(*) as c FROM task_log GROUP BY provider").fetchall():
            if r["provider"]:
                models[r["provider"]] = r["c"]

        departments = {}
        for r in conn.execute("SELECT department, COUNT(*) as c FROM task_log GROUP BY department").fetchall():
            departments[r["department"]] = r["c"]

        return {
            "total_tasks": total,
            "tasks_today": today,
            "avg_confidence": round(avg_conf, 3) if avg_conf else 0.0,
            "models_used": models,
            "department_usage": departments,
        }

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def export_all(self) -> dict:
        """Export all data as JSON-serializable dict."""
        conn = self._get_conn()
        memories = [
            dict(r) for r in conn.execute(
                "SELECT department, memory_type, content, metadata, created_at FROM agent_memory ORDER BY id"
            ).fetchall()
        ]
        tasks = [
            dict(r) for r in conn.execute(
                "SELECT department, task_input, task_output, model, provider, confidence, latency_ms, created_at FROM task_log ORDER BY id"
            ).fetchall()
        ]
        return {"agent_memory": memories, "task_log": tasks}

    def import_all(self, data: dict) -> dict:
        """Import data from an export. Appends to existing data."""
        conn = self._get_conn()
        mem_count = 0
        task_count = 0
        for m in data.get("agent_memory", []):
            conn.execute(
                "INSERT INTO agent_memory (department, memory_type, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                (m["department"], m["memory_type"], m["content"], m.get("metadata"), m.get("created_at")),
            )
            mem_count += 1
        for t in data.get("task_log", []):
            conn.execute(
                "INSERT INTO task_log (department, task_input, task_output, model, provider, confidence, latency_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (t["department"], t["task_input"], t["task_output"], t.get("model", ""), t.get("provider", ""), t.get("confidence", 0), t.get("latency_ms", 0), t.get("created_at")),
            )
            task_count += 1
        conn.commit()
        return {"memories_imported": mem_count, "tasks_imported": task_count}

    def clear_all(self):
        """Delete all memories and task logs."""
        conn = self._get_conn()
        conn.execute("DELETE FROM agent_memory")
        conn.execute("DELETE FROM task_log")
        conn.execute("DELETE FROM agent_insights")
        # Don't clear business_profile — user had to type that data
        conn.commit()

    # ------------------------------------------------------------------
    # Business Profile (persistent key/value for user's business data)
    # ------------------------------------------------------------------

    def set_profile_key(self, key: str, value: str):
        """Upsert a business profile key."""
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO business_profile (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
            (key.lower().strip(), str(value)),
        )
        conn.commit()

    def get_profile_key(self, key: str) -> str:
        """Get a single business profile value."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT value FROM business_profile WHERE key = ?",
            (key.lower().strip(),),
        ).fetchone()
        return row["value"] if row else None

    def get_all_profile_keys(self) -> dict:
        """Get entire business profile as dict."""
        conn = self._get_conn()
        rows = conn.execute("SELECT key, value FROM business_profile").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def clear_profile(self):
        """Clear the business profile (user reset)."""
        conn = self._get_conn()
        conn.execute("DELETE FROM business_profile")
        conn.commit()

    # ------------------------------------------------------------------
    # Brand Context (Nexus Context Injection)
    # ------------------------------------------------------------------

    def get_brand_context(self) -> dict:
        """Get the core Brand Context for Nexus."""
        keys = ["company_name", "industry", "target_audience", "budget_constraints", "current_funnel_bottleneck"]
        conn = self._get_conn()
        placeholders = ",".join("?" for _ in keys)
        rows = conn.execute(f"SELECT key, value FROM business_profile WHERE key IN ({placeholders})", keys).fetchall()
        context = {k: "Unknown" for k in keys}
        for r in rows:
            context[r["key"]] = r["value"]
        return context

    def update_brand_context(self, updates: dict):
        """Update the Brand Context values via dictionary."""
        allowed_keys = {"company_name", "industry", "target_audience", "budget_constraints", "current_funnel_bottleneck"}
        for k, v in updates.items():
            k_lower = k.lower().strip()
            if k_lower in allowed_keys and v:
                self.set_profile_key(k_lower, str(v))

    # ------------------------------------------------------------------
    # Agent Insights
    # ------------------------------------------------------------------

    def save_insight(self, department: str, insight_type: str, content: str,
                     confidence: float = 0.8, source: str = "agent",
                     expires_days: int = None):
        """Save a meaningful insight from an agent or the user."""
        conn = self._get_conn()
        expires_at = None
        if expires_days:
            from datetime import timedelta
            expires_at = (datetime.now(timezone.utc) + timedelta(days=expires_days)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO agent_insights (department, insight_type, content, confidence, source, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (department, insight_type, content, confidence, source, expires_at),
        )
        conn.commit()

    def get_insights(self, department: str = None, limit: int = 10) -> list:
        """Get non-expired insights, optionally filtered by department."""
        conn = self._get_conn()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        if department:
            rows = conn.execute(
                "SELECT department, insight_type, content, confidence, source, created_at "
                "FROM agent_insights "
                "WHERE department = ? AND (expires_at IS NULL OR expires_at > ?) "
                "ORDER BY created_at DESC LIMIT ?",
                (department, now, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT department, insight_type, content, confidence, source, created_at "
                "FROM agent_insights "
                "WHERE expires_at IS NULL OR expires_at > ? "
                "ORDER BY created_at DESC LIMIT ?",
                (now, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Recommendation Tracking
    # ------------------------------------------------------------------

    def track_recommendation(self, rec_id: str, department: str, recommendation: str,
                              predicted_impact: str = ""):
        """Record a recommendation for tracking."""
        conn = self._get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO recommendation_tracking "
            "(id, department, recommendation, predicted_impact) VALUES (?, ?, ?, ?)",
            (rec_id, department, recommendation, predicted_impact),
        )
        conn.commit()

    def update_recommendation_status(self, rec_id: str, status: str, actual_impact: str = ""):
        """Update the outcome of a recommendation."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE recommendation_tracking SET status=?, actual_impact=? WHERE id=?",
            (status, actual_impact, rec_id),
        )
        conn.commit()

    def get_recommendations(self, department: str = None, status: str = None) -> list:
        """Get tracked recommendations with optional filters."""
        conn = self._get_conn()
        query = "SELECT * FROM recommendation_tracking WHERE 1=1"
        params = []
        if department:
            query += " AND department = ?"
            params.append(department)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT 20"
        return [dict(r) for r in conn.execute(query, params).fetchall()]


# Singleton for easy import
_store = None

def get_memory_store() -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store
