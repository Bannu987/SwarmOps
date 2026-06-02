"""
Opportunity engine. Reads recent signals + brand context, generates
ranked opportunities using the agent runner. Runs every 6 hours.

This is what populates the Operations Floor's Opportunities column.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta

from .agent_runner import run_agent_structured
from .schemas import Recommendation
from .supabase_client import get_admin_client

logger = logging.getLogger(__name__)


# Which agents propose opportunities for which categories
AGENT_CATEGORIES = {
    "seo": "seo",
    "content": "content",
    "cro": "cro",
    "aeo": "aeo",
    "analytics": "analytics",
}


def compute_rice_score(rec: Recommendation, confidence: float) -> float:
    """RICE: (Reach × Impact × Confidence) / Effort"""
    reach_score = 1.0

    impact_map = {"high": 3.0, "medium": 2.0, "low": 1.0}
    impact = impact_map.get(rec.expected_impact, 2.0)

    effort_map = {"low": 1.0, "medium": 2.0, "high": 3.0}
    effort = effort_map.get(rec.effort, 2.0)

    return round((reach_score * impact * confidence) / effort, 2)


def generate_opportunities_for_user(user_id: str, project: Dict) -> int:
    """
    For one user/project: read recent signals, run each specialist,
    persist ranked opportunities.
    Returns number of opportunities created.
    """
    admin = get_admin_client()
    if not admin:
        return 0

    # Read recent active signals
    try:
        signals_result = admin.table("signals") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("status", "active") \
            .order("detected_at", desc=True) \
            .limit(20) \
            .execute()

        recent_signals = signals_result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch signals: {e}")
        return 0

    if not recent_signals:
        logger.info(f"[opportunity_engine] no signals for {user_id}, skipping")
        return 0

    signal_summary = _build_signal_summary(recent_signals)
    project_context = _build_project_context(project)

    opportunities_created = 0

    for agent_id, category in AGENT_CATEGORIES.items():
        prompt = f"""{project_context}

RECENT SIGNALS (last 7 days):
{signal_summary}

Based on these signals + the project context, propose 1-3 specific
opportunities the user should act on. For each opportunity:
- What action to take (be specific, not generic)
- Which signals triggered this opportunity (reference signal IDs)
- Expected impact (high/medium/low)
- Effort required (low/medium/high)
- Timeframe (this week / next 30 days / Q1)

Return the standard JSON schema. Each recommendation in the
recommendations[] array becomes one opportunity."""

        try:
            output = run_agent_structured(agent_id, prompt, conversation_id=f"opportunity-engine-{user_id}")

            for rec in output.recommendations[:3]:  # max 3 per agent
                rice = compute_rice_score(rec, output.confidence)
                relevant_signal_ids = _match_signals_to_recommendation(rec, recent_signals)

                opportunity = {
                    "user_id": user_id,
                    "project_id": project.get("id"),
                    "title": rec.action[:200],
                    "description": rec.rationale,
                    "category": category,
                    "signal_ids": relevant_signal_ids,
                    "recommended_action": rec.action,
                    "expected_impact": rec.expected_impact,
                    "effort": rec.effort,
                    "timeframe": rec.timeframe,
                    "rice_score": rice,
                    "confidence": output.confidence,
                    "proposed_by": agent_id,
                    "endorsed_by": [agent_id],
                    "status": "active",
                    "expires_at": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
                }

                try:
                    # Robust duplicate active opportunity check
                    existing = admin.table("opportunities") \
                        .select("id") \
                        .eq("project_id", project.get("id")) \
                        .eq("title", rec.action[:200]) \
                        .in_("status", ["active", "in_progress"]) \
                        .execute()
                    
                    if existing.data:
                        opp_id = existing.data[0]["id"]
                        logger.info(f"[opportunity_engine] Deduplication matched active opportunity '{rec.action[:200]}' (ID: {opp_id}). Updating in-place...")
                        admin.table("opportunities").update({
                            "description": rec.rationale,
                            "recommended_action": rec.action,
                            "expected_impact": rec.expected_impact,
                            "effort": rec.effort,
                            "timeframe": rec.timeframe,
                            "rice_score": rice,
                            "confidence": output.confidence,
                            "expires_at": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
                        }).eq("id", opp_id).execute()
                        continue

                    # Insert new opportunity if no active duplicate was found
                    admin.table("opportunities").insert(opportunity).execute()
                    opportunities_created += 1
                except Exception as e:
                    logger.warning(f"Failed to persist/update opportunity: {e}")


        except Exception as e:
            logger.error(f"[{agent_id}] opportunity generation failed: {e}")
            continue

    logger.info(f"[opportunity_engine] created {opportunities_created} opportunities for {user_id}")
    return opportunities_created


def _build_signal_summary(signals: List[Dict]) -> str:
    """Format signals for the prompt."""
    lines = []
    for sig in signals[:15]:
        ts = sig.get("detected_at", "")[:10]
        sev = sig.get("severity", "medium").upper()
        title = sig.get("title", "")
        cat = sig.get("category", "")
        source = sig.get("source_agent", "")
        lines.append(f"[{sev}] [{cat}] {title} (by {source}, {ts})")
        if sig.get("description"):
            lines.append(f"  → {sig['description'][:200]}")
        lines.append(f"  signal_id: {sig['id']}")
    return "\n".join(lines)


def _build_project_context(project: Dict) -> str:
    """Format project context for the prompt."""
    parts = ["PROJECT CONTEXT:"]

    if project.get("name"):
        parts.append(f"Brand: {project['name']}")
    if project.get("website_url"):
        parts.append(f"Website: {project['website_url']}")
    if project.get("description"):
        parts.append(f"About: {project['description'][:300]}")

    brand_data = project.get("brand_data") or {}
    if isinstance(brand_data, dict):
        if brand_data.get("industry"):
            parts.append(f"Industry: {brand_data['industry']}")
        if brand_data.get("audience"):
            parts.append(f"Audience: {brand_data['audience']}")

    return "\n".join(parts)


def _match_signals_to_recommendation(rec: Recommendation, signals: List[Dict]) -> List[str]:
    """
    Match signals to a recommendation by keyword overlap.
    Returns list of signal UUIDs that likely triggered the rec.
    """
    rec_words = set((rec.action + " " + rec.rationale).lower().split())
    matched = []

    for sig in signals:
        sig_words = set((sig.get("title", "") + " " + sig.get("description", "")).lower().split())
        overlap = len(rec_words & sig_words) / max(len(rec_words), 1)
        if overlap > 0.15:
            matched.append(sig["id"])
        if len(matched) >= 3:
            break

    return matched
