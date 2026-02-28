"""
Revenue Attribution Tracker — SwarmOps
Logs every agent recommendation with predicted impact.
Tracks accuracy over time to build an agent performance leaderboard.
"""

import os
import re
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Shared DB — same marketingos.db as memory_store.py / brand_dna.py
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marketingos.db")
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Thread-local connection to marketingos.db."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


def _init_tables():
    """Create recommendation_log and agent_performance tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS recommendation_log (
            id              TEXT PRIMARY KEY,
            agent           TEXT NOT NULL,
            recommendation_text  TEXT NOT NULL,
            predicted_impact     TEXT,
            predicted_metric     TEXT,
            predicted_value      REAL,
            status          TEXT DEFAULT 'pending',
            actual_impact   REAL,
            accuracy_score  REAL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            measured_at     TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_performance (
            agent                   TEXT PRIMARY KEY,
            total_recommendations   INTEGER DEFAULT 0,
            implemented_count       INTEGER DEFAULT 0,
            measured_count          INTEGER DEFAULT 0,
            avg_accuracy            REAL DEFAULT 0.0,
            best_recommendation_id  TEXT,
            worst_recommendation_id TEXT,
            updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_rec_log_agent ON recommendation_log(agent);
        CREATE INDEX IF NOT EXISTS idx_rec_log_status ON recommendation_log(status);
    """)
    conn.commit()


_init_tables()


# ---------------------------------------------------------------------------
# Recommendation Parser — extracts predicted impacts from agent response text
# ---------------------------------------------------------------------------

# Patterns that signal a recommendation with a predicted numeric impact
_IMPACT_PATTERNS = [
    r"(?:expected|predicted|estimated|projected|could|should|may|might|will)\s+"
    r"(?:increase|improve|boost|reduce|decrease|drop|grow|raise|lower|drive)\s+"
    r"[\w\s]+?(?:by|to)\s+(\d+(?:\.\d+)?)\s*%",
    r"\+(\d+(?:\.\d+)?)\s*%\s*(?:conversion|revenue|traffic|click|open|engagement|roas|roi|cac|ltv)",
    r"(\d+(?:\.\d+)?)\s*%\s*(?:increase|improvement|boost|reduction|decrease)\s+in",
    r"(?:revenue|traffic|conversions?|sales?|leads?|engagement)\s+(?:up|increase|grow)\s+(?:by\s+)?(\d+(?:\.\d+)?)%",
]

_METRIC_KEYWORDS = {
    "conversion": "conversion_rate",
    "traffic": "traffic_volume",
    "revenue": "revenue",
    "click": "click_through_rate",
    "open": "email_open_rate",
    "engagement": "engagement_rate",
    "roas": "roas",
    "roi": "roi",
    "cac": "cac",
    "ltv": "ltv",
    "lead": "lead_volume",
    "sale": "sales_volume",
    "bounce": "bounce_rate",
}


def _parse_recommendations(agent: str, response_text: str) -> list[dict]:
    """
    Scan agent response text for recommendations with predicted numeric impacts.
    Returns list of dicts: {text, predicted_impact, predicted_metric, predicted_value}
    """
    found = []
    if not response_text:
        return found

    lines = response_text.split("\n")
    for line in lines:
        for pattern in _IMPACT_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                value_str = match.group(1)
                try:
                    predicted_value = float(value_str) / 100.0  # Store as decimal (0.15 not 15%)
                except (ValueError, IndexError):
                    continue

                # Detect which metric this is about
                predicted_metric = "general"
                line_lower = line.lower()
                for keyword, metric in _METRIC_KEYWORDS.items():
                    if keyword in line_lower:
                        predicted_metric = metric
                        break

                # Format the impact label
                predicted_impact = f"+{value_str}% {predicted_metric.replace('_', ' ')}"

                # Trim the line to a clean recommendation text
                rec_text = line.strip()[:500]

                found.append({
                    "text": rec_text,
                    "predicted_impact": predicted_impact,
                    "predicted_metric": predicted_metric,
                    "predicted_value": predicted_value,
                })
                break  # One match per line is enough

    return found[:5]  # Cap at 5 auto-parsed recs per response


# ---------------------------------------------------------------------------
# RevenueTracker Class
# ---------------------------------------------------------------------------

class RevenueTracker:
    """
    Logs, tracks, and measures the accuracy of agent recommendations.
    All methods are safe — they silently continue on error to never block responses.
    """

    def log_recommendation(
        self,
        agent: str,
        text: str,
        predicted_impact: str,
        predicted_metric: str,
        predicted_value: float,
    ) -> str:
        """
        Log a recommendation with its predicted impact.
        Returns the recommendation_id for later tracking.
        """
        rec_id = str(uuid.uuid4())
        try:
            conn = _get_conn()
            conn.execute(
                """INSERT INTO recommendation_log
                   (id, agent, recommendation_text, predicted_impact,
                    predicted_metric, predicted_value, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
                (rec_id, agent, text[:500], predicted_impact, predicted_metric, predicted_value),
            )
            # Update total count in agent_performance
            conn.execute(
                """INSERT INTO agent_performance (agent, total_recommendations, updated_at)
                   VALUES (?, 1, CURRENT_TIMESTAMP)
                   ON CONFLICT(agent) DO UPDATE SET
                     total_recommendations = total_recommendations + 1,
                     updated_at = CURRENT_TIMESTAMP""",
                (agent,),
            )
            conn.commit()
            print(f"[revenue_tracker] Logged rec {rec_id[:8]}… for {agent}: {predicted_impact}")
        except Exception as e:
            print(f"[revenue_tracker] log_recommendation error: {e}")
        return rec_id

    def auto_log_from_response(self, agent: str, response_text: str) -> list[str]:
        """
        Parse an agent response for recommendations and auto-log them.
        Returns list of recommendation IDs created.
        """
        ids = []
        try:
            recs = _parse_recommendations(agent, response_text)
            for rec in recs:
                rec_id = self.log_recommendation(
                    agent=agent,
                    text=rec["text"],
                    predicted_impact=rec["predicted_impact"],
                    predicted_metric=rec["predicted_metric"],
                    predicted_value=rec["predicted_value"],
                )
                ids.append(rec_id)
        except Exception as e:
            print(f"[revenue_tracker] auto_log error: {e}")
        return ids

    def update_status(self, recommendation_id: str, status: str):
        """
        Update the status of a recommendation.
        Valid statuses: pending / implemented / skipped / measured
        """
        try:
            valid = {"pending", "implemented", "skipped", "measured"}
            if status not in valid:
                return
            conn = _get_conn()
            conn.execute(
                "UPDATE recommendation_log SET status = ? WHERE id = ?",
                (status, recommendation_id),
            )
            if status == "implemented":
                # Get agent name to update implemented_count
                row = conn.execute(
                    "SELECT agent FROM recommendation_log WHERE id = ?",
                    (recommendation_id,)
                ).fetchone()
                if row:
                    conn.execute(
                        """UPDATE agent_performance SET
                           implemented_count = implemented_count + 1,
                           updated_at = CURRENT_TIMESTAMP
                           WHERE agent = ?""",
                        (row["agent"],),
                    )
            conn.commit()
        except Exception as e:
            print(f"[revenue_tracker] update_status error: {e}")

    def record_outcome(self, recommendation_id: str, actual_impact: float):
        """
        Record the actual measured impact for a recommendation.
        Computes accuracy_score = 1 - |predicted - actual| / max(|predicted|, |actual|)
        Updates the agent_performance leaderboard.
        """
        try:
            conn = _get_conn()
            row = conn.execute(
                "SELECT agent, predicted_value FROM recommendation_log WHERE id = ?",
                (recommendation_id,)
            ).fetchone()
            if not row:
                return

            predicted = row["predicted_value"] or 0.0
            agent = row["agent"]

            # Accuracy formula: 1 - normalized absolute error (clamped 0-1)
            denom = max(abs(predicted), abs(actual_impact), 0.0001)
            accuracy = max(0.0, 1.0 - abs(predicted - actual_impact) / denom)

            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                """UPDATE recommendation_log SET
                   actual_impact = ?, accuracy_score = ?,
                   status = 'measured', measured_at = ?
                   WHERE id = ?""",
                (actual_impact, round(accuracy, 4), now, recommendation_id),
            )

            # Recalculate agent_performance stats
            stats = conn.execute(
                """SELECT
                     COUNT(*) as measured_count,
                     AVG(accuracy_score) as avg_accuracy,
                     MAX(accuracy_score) as best_acc,
                     MIN(accuracy_score) as worst_acc
                   FROM recommendation_log
                   WHERE agent = ? AND status = 'measured'""",
                (agent,)
            ).fetchone()

            best_row = conn.execute(
                "SELECT id FROM recommendation_log WHERE agent = ? AND accuracy_score = ? LIMIT 1",
                (agent, stats["best_acc"] or 0)
            ).fetchone()
            worst_row = conn.execute(
                "SELECT id FROM recommendation_log WHERE agent = ? AND accuracy_score = ? LIMIT 1",
                (agent, stats["worst_acc"] or 0)
            ).fetchone()

            conn.execute(
                """UPDATE agent_performance SET
                   measured_count = ?,
                   avg_accuracy = ?,
                   best_recommendation_id = ?,
                   worst_recommendation_id = ?,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE agent = ?""",
                (
                    stats["measured_count"],
                    round(stats["avg_accuracy"] or 0.0, 4),
                    best_row["id"] if best_row else None,
                    worst_row["id"] if worst_row else None,
                    agent,
                ),
            )
            conn.commit()
            print(f"[revenue_tracker] Outcome recorded: {agent} accuracy={accuracy:.2%}")
        except Exception as e:
            print(f"[revenue_tracker] record_outcome error: {e}")

    def get_agent_accuracy(self, agent: str) -> dict:
        """Return accuracy stats for a specific agent."""
        try:
            conn = _get_conn()
            perf = conn.execute(
                "SELECT * FROM agent_performance WHERE agent = ?", (agent,)
            ).fetchone()
            if not perf:
                return {"agent": agent, "total_recommendations": 0, "avg_accuracy": None}
            return dict(perf)
        except Exception as e:
            print(f"[revenue_tracker] get_agent_accuracy error: {e}")
            return {"agent": agent, "error": str(e)}

    def get_recommendation_history(
        self, agent: Optional[str] = None, limit: int = 50
    ) -> list[dict]:
        """Return past recommendations, optionally filtered by agent."""
        try:
            conn = _get_conn()
            if agent:
                rows = conn.execute(
                    """SELECT * FROM recommendation_log WHERE agent = ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (agent, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM recommendation_log ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[revenue_tracker] get_recommendation_history error: {e}")
            return []

    def get_all_agent_performance(self) -> list[dict]:
        """Return the full agent performance leaderboard, sorted by accuracy."""
        try:
            conn = _get_conn()
            rows = conn.execute(
                "SELECT * FROM agent_performance ORDER BY avg_accuracy DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[revenue_tracker] get_all_agent_performance error: {e}")
            return []


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_tracker_instance: Optional[RevenueTracker] = None


def get_revenue_tracker() -> RevenueTracker:
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = RevenueTracker()
    return _tracker_instance
