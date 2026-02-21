"""
Memory Store - SwarmOps
Persistent SQLite memory so agents learn from past work.
"""

import sqlite3
import json
import os
import threading
from datetime import datetime, timedelta, timezone


class MemoryStore:
    """Persistent memory for all SwarmOps agents using SQLite."""

    def __init__(self, db_path="marketingos.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
        self._local = threading.local()
        self._init_tables()

    def _get_conn(self):
        """Get a thread-local SQLite connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

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

            CREATE INDEX IF NOT EXISTS idx_memory_dept ON agent_memory(department);
            CREATE INDEX IF NOT EXISTS idx_memory_type ON agent_memory(memory_type);
            CREATE INDEX IF NOT EXISTS idx_tasklog_dept ON task_log(department);
            CREATE INDEX IF NOT EXISTS idx_tasklog_date ON task_log(created_at);
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
        conn.commit()


# Singleton for easy import
_store = None

def get_memory_store() -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store
