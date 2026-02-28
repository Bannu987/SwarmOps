"""
LearningEngine — SwarmOps
Learns user preferences over time from interaction patterns.
Personalizes all agent responses without any manual configuration.
"""

import os
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Optional
from db import get_connection as _get_conn, DB_PATH


def _init_tables():
    """Create user_preferences and interaction_feedback tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT NOT NULL UNIQUE,
            preference  TEXT NOT NULL,
            confidence  REAL DEFAULT 0.5,
            signal_count INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS interaction_feedback (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            agent       TEXT NOT NULL,
            query_summary  TEXT,
            response_quality TEXT DEFAULT 'good',
            modification_notes TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_feedback_agent ON interaction_feedback(agent);
        CREATE INDEX IF NOT EXISTS idx_feedback_quality ON interaction_feedback(response_quality);
    """)
    conn.commit()


_init_tables()


# ---------------------------------------------------------------------------
# Preference Categories and Detection Logic
# ---------------------------------------------------------------------------

# Maps query/response signals to preference categories and values
_LENGTH_LONG_SIGNALS = [
    "more detail", "expand on", "elaborate", "comprehensive", "in depth",
    "full breakdown", "thorough", "detailed analysis", "everything about"
]
_LENGTH_SHORT_SIGNALS = [
    "shorter", "brief", "concise", "tldr", "summary only", "just the",
    "quick", "simple", "just give me", "bullet points only"
]
_FORMAL_SIGNALS = [
    "formal", "professional", "corporate", "business tone", "b2b",
    "enterprise", "executive", "boardroom"
]
_CASUAL_SIGNALS = [
    "casual", "friendly", "conversational", "like a friend", "informal",
    "relaxed", "simple language"
]
_DETAIL_HIGH_SIGNALS = [
    "why", "explain", "how does", "what causes", "reasoning", "strategy behind",
    "rationale", "break down"
]

# Topic frequency tracking (which agents/topics the user visits most)
_AGENT_TOPIC_MAP = {
    "seo": "seo_optimization",
    "content": "content_creation",
    "ppc": "paid_advertising",
    "analytics": "data_analytics",
    "crm": "email_marketing",
    "smm": "social_media",
    "brand": "brand_strategy",
    "cro": "conversion_optimization",
    "web_ux": "web_design",
    "research": "market_research",
    "nexus": "general_strategy",
}


def _detect_signals(text: str) -> dict:
    """
    Scan text for preference signals.
    Returns dict of {category: detected_preference} for all signals found.
    """
    text_lower = text.lower()
    signals = {}

    # Response length preference
    if any(s in text_lower for s in _LENGTH_LONG_SIGNALS):
        signals["response_length"] = "long"
    elif any(s in text_lower for s in _LENGTH_SHORT_SIGNALS):
        signals["response_length"] = "short"

    # Formality preference
    if any(s in text_lower for s in _FORMAL_SIGNALS):
        signals["tone_formality"] = "formal"
    elif any(s in text_lower for s in _CASUAL_SIGNALS):
        signals["tone_formality"] = "casual"

    # Detail level
    if any(s in text_lower for s in _DETAIL_HIGH_SIGNALS):
        signals["detail_level"] = "high"

    return signals


# ---------------------------------------------------------------------------
# LearningEngine Class
# ---------------------------------------------------------------------------

class LearningEngine:
    """
    Passively learns user preferences from interaction patterns.
    All writes are silent — never blocks or crashes a response.
    """

    def record_interaction(
        self,
        agent: str,
        query: str,
        response_quality: str = "good",
        notes: Optional[str] = None,
    ):
        """
        Record an interaction for learning.
        response_quality: 'good' | 'modified' | 'rejected'
        notes: what the user changed or why it was modified/rejected
        """
        try:
            conn = _get_conn()
            query_summary = query[:200] if query else ""
            conn.execute(
                """INSERT INTO interaction_feedback
                   (agent, query_summary, response_quality, modification_notes)
                   VALUES (?, ?, ?, ?)""",
                (agent, query_summary, response_quality, notes),
            )
            conn.commit()

            # Immediately extract and update signals from this interaction
            self._update_signals_from_text(query + " " + (notes or ""), agent)

        except Exception as e:
            print(f"[learning_engine] record_interaction error: {e}")

    def _update_signals_from_text(self, text: str, agent: str):
        """Extract preference signals from text and update user_preferences table."""
        try:
            signals = _detect_signals(text)

            # Track which agents/topics user frequents
            topic = _AGENT_TOPIC_MAP.get(agent, agent)
            signals[f"frequent_topic_{topic}"] = "yes"

            conn = _get_conn()
            for category, preference in signals.items():
                existing = conn.execute(
                    "SELECT signal_count, confidence FROM user_preferences WHERE category = ?",
                    (category,)
                ).fetchone()

                if existing:
                    new_count = existing["signal_count"] + 1
                    # Confidence increases with more consistent signals, caps at 0.95
                    new_confidence = min(0.95, 0.5 + (new_count * 0.05))
                    conn.execute(
                        """UPDATE user_preferences SET
                           preference = ?, signal_count = ?, confidence = ?,
                           last_updated = CURRENT_TIMESTAMP
                           WHERE category = ?""",
                        (preference, new_count, round(new_confidence, 2), category),
                    )
                else:
                    conn.execute(
                        """INSERT INTO user_preferences
                           (category, preference, confidence, signal_count)
                           VALUES (?, ?, 0.5, 1)""",
                        (category, preference),
                    )
            conn.commit()
        except Exception as e:
            print(f"[learning_engine] _update_signals error: {e}")

    def learn_preferences(self):
        """
        Analyze ALL past interactions and rebuild preference model.
        Call this periodically (e.g., every 50 interactions) for a full re-learn.
        Typically called by the scheduler — not per-request.
        """
        try:
            conn = _get_conn()
            rows = conn.execute(
                """SELECT agent, query_summary, response_quality, modification_notes
                   FROM interaction_feedback ORDER BY created_at DESC LIMIT 200"""
            ).fetchall()

            # Aggregate all text signals
            combined_text = " ".join(
                (r["query_summary"] or "") + " " + (r["modification_notes"] or "")
                for r in rows
            )

            # Rebuild preference signals from combined history
            signals = _detect_signals(combined_text)

            # Count agent frequency
            agent_counts = Counter(r["agent"] for r in rows)
            top_agents = [a for a, _ in agent_counts.most_common(3)]
            for agent in top_agents:
                topic = _AGENT_TOPIC_MAP.get(agent, agent)
                signals[f"frequent_topic_{topic}"] = "yes"

            # Count rejection/modification rates to detect quality issues
            total = len(rows)
            if total > 0:
                bad = sum(1 for r in rows if r["response_quality"] in ("modified", "rejected"))
                bad_rate = bad / total
                if bad_rate > 0.3:  # >30% modification rate → user wants something different
                    signals["response_satisfaction"] = "low"
                else:
                    signals["response_satisfaction"] = "high"

            # Upsert all learned preferences
            for category, preference in signals.items():
                existing = conn.execute(
                    "SELECT signal_count FROM user_preferences WHERE category = ?", (category,)
                ).fetchone()
                count = (existing["signal_count"] if existing else 0) + 1
                confidence = min(0.95, 0.5 + count * 0.05)
                conn.execute(
                    """INSERT INTO user_preferences (category, preference, confidence, signal_count)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(category) DO UPDATE SET
                         preference = excluded.preference,
                         confidence = excluded.confidence,
                         signal_count = excluded.signal_count,
                         last_updated = CURRENT_TIMESTAMP""",
                    (category, preference, round(confidence, 2), count),
                )
            conn.commit()
            print(f"[learning_engine] Preferences rebuilt from {total} interactions")
        except Exception as e:
            print(f"[learning_engine] learn_preferences error: {e}")

    def get_context_boost(self, agent: str) -> str:
        """
        Returns a personalization string for injection into agent system prompts.
        Returns empty string if no preferences learned yet.
        """
        try:
            conn = _get_conn()
            rows = conn.execute(
                "SELECT category, preference, confidence FROM user_preferences ORDER BY confidence DESC"
            ).fetchall()

            if not rows:
                return ""

            prefs = {r["category"]: (r["preference"], r["confidence"]) for r in rows}

            parts = []

            # Response length
            if "response_length" in prefs:
                val, conf = prefs["response_length"]
                if conf >= 0.6:
                    label = "detailed and comprehensive" if val == "long" else "concise and brief"
                    parts.append(f"{label} responses")

            # Formality
            if "tone_formality" in prefs:
                val, conf = prefs["tone_formality"]
                if conf >= 0.6:
                    parts.append(f"{val} tone")

            # Detail level
            if "detail_level" in prefs:
                val, conf = prefs["detail_level"]
                if conf >= 0.6 and val == "high":
                    parts.append("high detail with reasoning explained")

            # Top topics the user cares about
            topic_prefs = [
                cat.replace("frequent_topic_", "").replace("_", " ")
                for cat, (val, conf) in prefs.items()
                if cat.startswith("frequent_topic_") and conf >= 0.55
            ]

            if not parts and not topic_prefs:
                return ""

            context = "USER PREFERENCES:"
            if parts:
                context += f" This user prefers {', '.join(parts)}."
            if topic_prefs:
                context += f" They frequently focus on: {', '.join(topic_prefs[:3])}."

            return context

        except Exception as e:
            print(f"[learning_engine] get_context_boost error: {e}")
            return ""

    def get_agent_insights(self, agent: str) -> dict:
        """
        What has the system learned about how this user interacts with this agent?
        Returns a dict of insights.
        """
        try:
            conn = _get_conn()
            rows = conn.execute(
                """SELECT response_quality, query_summary, modification_notes
                   FROM interaction_feedback WHERE agent = ?
                   ORDER BY created_at DESC LIMIT 50""",
                (agent,)
            ).fetchall()

            if not rows:
                return {"agent": agent, "interactions": 0, "insights": []}

            total = len(rows)
            good = sum(1 for r in rows if r["response_quality"] == "good")
            modified = sum(1 for r in rows if r["response_quality"] == "modified")
            rejected = sum(1 for r in rows if r["response_quality"] == "rejected")

            satisfaction_rate = round(good / total, 2) if total else 0.0

            insights = []
            if modified + rejected > total * 0.3:
                insights.append("User frequently modifies or rejects responses — may prefer a different style")
            if satisfaction_rate >= 0.8:
                insights.append("High satisfaction rate with this agent")

            # Sample recent queries to show topic trends
            recent_topics = [r["query_summary"] for r in rows[:5] if r["query_summary"]]

            return {
                "agent": agent,
                "interactions": total,
                "satisfaction_rate": satisfaction_rate,
                "good": good,
                "modified": modified,
                "rejected": rejected,
                "insights": insights,
                "recent_queries": recent_topics,
            }
        except Exception as e:
            print(f"[learning_engine] get_agent_insights error: {e}")
            return {"agent": agent, "error": str(e)}

    def get_all_preferences(self) -> list[dict]:
        """Return all learned user preferences."""
        try:
            conn = _get_conn()
            rows = conn.execute(
                "SELECT * FROM user_preferences ORDER BY confidence DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[learning_engine] get_all_preferences error: {e}")
            return []

    def reset(self):
        """Clear all learned preferences and interaction history."""
        try:
            conn = _get_conn()
            conn.execute("DELETE FROM user_preferences")
            conn.execute("DELETE FROM interaction_feedback")
            conn.commit()
            print("[learning_engine] All preferences and feedback reset")
        except Exception as e:
            print(f"[learning_engine] reset error: {e}")


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_engine_instance: Optional[LearningEngine] = None


def get_learning_engine() -> LearningEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = LearningEngine()
    return _engine_instance
