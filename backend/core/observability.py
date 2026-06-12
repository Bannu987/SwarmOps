import logging
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict

logger = logging.getLogger("swarmops.observability")

# 5. VERSION CONSTANTS
BOARDROOM_PROMPT_VERSION = "1.1.0"
SIGNAL_RULES_VERSION = "1.1.0"
ACTION_PLAN_SCHEMA_VERSION = "1.1.0"
VERIFICATION_RULES_VERSION = "1.1.0"
WORKFLOW_VERSION = "1.5.0"

# 8. FEATURE FLAGS
def get_feature_flag(name: str, default: bool = True) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes", "on")

def log_structured_event(
    event_name: str,
    trace_id: str,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    signal_id: Optional[str] = None,
    action_plan_id: Optional[str] = None,
    status: str = "success",
    latency_ms: Optional[int] = None,
    model_name: Optional[str] = None,
    fallback_reason: Optional[str] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict] = None
):
    """
    Produce a clean structured JSON log for observability.
    Does NOT log secrets/API keys.
    """
    log_data = {
        "event_name": event_name,
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "project_id": project_id,
        "signal_id": signal_id,
        "action_plan_id": action_plan_id,
        "status": status,
        "latency_ms": latency_ms,
        "model_name": model_name,
        "fallback_reason": fallback_reason,
        "error_type": error_type,
        "error_message": error_message,
        "workflow_version": WORKFLOW_VERSION,
        "prompt_version": BOARDROOM_PROMPT_VERSION,
        "metadata": metadata or {}
    }
    
    cleaned_log = {k: v for k, v in log_data.items() if v is not None}
    logger.info(f"[STRUCTURED_EVENT] {json.dumps(cleaned_log)}")


def create_run_trace_db(
    trace_id: str,
    user_id: Optional[str],
    project_id: Optional[str],
    run_type: str,
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Optional[str]:
    """Insert run trace into database defensively."""
    if not get_feature_flag("ENABLE_TRACE_LOGGING", True):
        return None
        
    try:
        from .supabase_client import get_admin_client
        admin = get_admin_client()
        if not admin:
            return None
            
        res = admin.table("run_traces").insert({
            "trace_id": trace_id,
            "user_id": user_id,
            "project_id": project_id,
            "run_type": run_type,
            "workflow_version": WORKFLOW_VERSION,
            "prompt_version": BOARDROOM_PROMPT_VERSION,
            "model_name": model_name,
            "provider": provider,
            "status": "running",
            "metadata": metadata or {}
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        logger.debug(f"Defensive run trace insertion failed: {e}")
        return None


def update_run_trace_db(
    trace_id: str,
    status: str,
    latency_ms: Optional[int] = None,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict] = None
):
    """Update run trace in database defensively."""
    if not get_feature_flag("ENABLE_TRACE_LOGGING", True):
        return
        
    try:
        from .supabase_client import get_admin_client
        admin = get_admin_client()
        if not admin:
            return
            
        update_data = {
            "status": status,
            "ended_at": datetime.now(timezone.utc).isoformat()
        }
        if latency_ms is not None:
            update_data["latency_ms"] = latency_ms
        if tokens_in is not None:
            update_data["tokens_in"] = tokens_in
        if tokens_out is not None:
            update_data["tokens_out"] = tokens_out
        if error_type is not None:
            update_data["error_type"] = error_type
        if error_message is not None:
            update_data["error_message"] = error_message
        if metadata:
            update_data["metadata"] = metadata
            
        admin.table("run_traces").update(update_data).eq("trace_id", trace_id).execute()
    except Exception as e:
        logger.debug(f"Defensive run trace update failed: {e}")


def log_agent_step_db(
    trace_id: str,
    step_name: str,
    agent_name: str,
    input_snapshot: Dict,
    output_snapshot: Dict,
    schema_valid: bool = True,
    tool_used: Optional[str] = None,
    fallback_used: bool = False,
    started_at: Optional[str] = None,
    latency_ms: Optional[int] = None,
    error_type: Optional[str] = None,
    metadata: Optional[Dict] = None
):
    """Log an agent execution step defensively."""
    if not get_feature_flag("ENABLE_TRACE_LOGGING", True):
        return
        
    try:
        from .supabase_client import get_admin_client
        admin = get_admin_client()
        if not admin:
            return
            
        admin.table("agent_step_logs").insert({
            "trace_id": trace_id,
            "step_name": step_name,
            "agent_name": agent_name,
            "input_snapshot": input_snapshot,
            "output_snapshot": output_snapshot,
            "schema_valid": schema_valid,
            "tool_used": tool_used,
            "fallback_used": fallback_used,
            "error_type": error_type,
            "started_at": started_at or datetime.now(timezone.utc).isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "latency_ms": latency_ms,
            "metadata": metadata or {}
        }).execute()
    except Exception as e:
        logger.debug(f"Defensive step logging failed: {e}")


def get_run_trace_db(
    trace_id: str,
    user_id: Optional[str] = None
) -> Optional[Dict]:
    """Fetch a run trace by trace_id. Optionally filter by user_id for ownership."""
    if not get_feature_flag("ENABLE_TRACE_LOGGING", True):
        return None

    try:
        from .supabase_client import get_admin_client
        admin = get_admin_client()
        if not admin:
            return None

        query = admin.table("run_traces").select("*").eq("trace_id", trace_id)
        if user_id:
            query = query.eq("user_id", user_id)

        res = query.execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        logger.debug(f"Defensive run trace fetch failed: {e}")
        return None
