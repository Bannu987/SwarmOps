"""
Master runner. Loops through all users/projects, runs scanners that
are due, then generates opportunities. Called by cron or on-demand.
"""
import logging
from typing import Dict

from .signals.website_health import WebsiteHealthScanner
from .opportunity_engine import generate_opportunities_for_user
from .supabase_client import get_admin_client

logger = logging.getLogger(__name__)


# Register all available scanners here
ALL_SCANNERS = [
    WebsiteHealthScanner(),
    # Future: GA4Scanner, GSCScanner, CompetitorPricingScanner, ContentDecayScanner
]


def run_all_scans() -> Dict:
    """
    Run all scanners for all active users.
    Designed to be called by a cron job every hour.
    Each scanner respects its own interval, so scanners that ran recently
    are skipped automatically.
    """
    admin = get_admin_client()
    if not admin:
        return {"error": "Supabase not configured"}

    try:
        projects_result = admin.table("projects") \
            .select("*") \
            .eq("archived", False) \
            .execute()

        projects = projects_result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch projects: {e}")
        return {"error": str(e)}

    if not projects:
        return {"status": "no_active_projects", "scanners_run": 0}

    total_signals = 0
    total_opportunities = 0
    scanners_run = 0

    for project in projects:
        user_id = project["user_id"]

        for scanner in ALL_SCANNERS:
            try:
                signals_created = scanner.run_for_user(user_id, project)
                total_signals += signals_created
                scanners_run += 1
            except Exception as e:
                logger.error(f"Scanner {scanner.name} failed for user {user_id}: {e}")

        try:
            ops = generate_opportunities_for_user(user_id, project)
            total_opportunities += ops
        except Exception as e:
            logger.error(f"Opportunity engine failed for {user_id}: {e}")

    summary = {
        "status": "success",
        "projects_scanned": len(projects),
        "scanners_run": scanners_run,
        "signals_created": total_signals,
        "opportunities_created": total_opportunities,
    }
    logger.info(f"[scanner_runner] {summary}")
    return summary


def run_scans_for_user(user_id: str, project_id: str = None) -> Dict:
    """
    Run scanners for a specific user/project. Used by on-demand
    endpoint (e.g. when user adds website URL, scan immediately).
    """
    admin = get_admin_client()
    if not admin:
        return {"error": "Supabase not configured"}

    query = admin.table("projects").select("*").eq("user_id", user_id).eq("archived", False)
    if project_id:
        query = query.eq("id", project_id)

    try:
        projects = query.execute().data or []
    except Exception as e:
        return {"error": str(e)}

    total_signals = 0
    total_opportunities = 0

    for project in projects:
        for scanner in ALL_SCANNERS:
            try:
                signals_created = scanner.run_for_user(user_id, project)
                total_signals += signals_created
            except Exception as e:
                logger.error(f"Scanner failed: {e}")

        try:
            ops = generate_opportunities_for_user(user_id, project)
            total_opportunities += ops
        except Exception as e:
            logger.error(f"Opportunity engine failed: {e}")

    return {
        "status": "success",
        "signals_created": total_signals,
        "opportunities_created": total_opportunities,
    }
