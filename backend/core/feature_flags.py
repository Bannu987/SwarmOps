import os
import logging
from typing import Optional, Dict, Any, List
from core.supabase_client import get_admin_client, is_available as supabase_available

logger = logging.getLogger("swarmops.feature_flags")

# Default values for standard system flags if not specified
DEFAULT_FLAGS = {
    "ENABLE_ACTION_PLAN_CREATION": True,
    "ENABLE_AUTO_VERIFICATION": True,
    "ENABLE_DETERMINISTIC_SIGNAL_RULES": True,
    "ENABLE_STREAMING_BOARDROOM": True,
    "ENABLE_MODEL_FALLBACK": True,
    "ENABLE_TRACE_LOGGING": True,
    "ENABLE_PROJECT_MEMORY": False,
    "ENABLE_RAG_CONTEXT": False,
    "ENABLE_MEMORY_CAPTURE": False,
    "ENABLE_MEMORY_DEBUG_PANEL": False,
}

def get_env_override(key: str) -> Optional[bool]:
    """Check environment variable override for a feature flag."""
    val = os.environ.get(key)
    if val is None:
        return None
    return val.lower() in ("true", "1", "yes", "on")

def _fetch_db_flag(key: str, scope_type: str, scope_id: Optional[str]) -> Optional[bool]:
    """Query a specific feature flag scope in the database."""
    if not supabase_available():
        return None
    try:
        admin = get_admin_client()
        query = admin.table("feature_flags").select("enabled").eq("key", key).eq("scope_type", scope_type)
        if scope_id:
            query = query.eq("scope_id", scope_id)
        else:
            query = query.is_("scope_id", "null")
        
        res = query.execute()
        if res.data and len(res.data) > 0:
            return bool(res.data[0]["enabled"])
    except Exception as e:
        logger.warning(f"Failed to fetch feature flag '{key}' from DB (scope={scope_type}, id={scope_id}): {e}")
    return None

def _get_project_workspace_id(project_id: str) -> Optional[str]:
    """Fetch workspace_id for a project to check workspace scope."""
    if not supabase_available():
        return None
    try:
        admin = get_admin_client()
        res = admin.table("projects").select("workspace_id").eq("id", project_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("workspace_id")
    except Exception as e:
        logger.warning(f"Failed to fetch workspace_id for project {project_id}: {e}")
    return None

def get_feature_flag(key: str, user_id: Optional[str] = None, project_id: Optional[str] = None, default: Optional[bool] = None) -> bool:
    """
    Resolve feature flag value based on priority:
    1. Environment variable override
    2. DB project scope
    3. DB user scope
    4. DB workspace scope
    5. DB global scope
    6. Default value (passed parameter, or fallback standard default)
    """
    # 1. Env Override
    env_val = get_env_override(key)
    if env_val is not None:
        return env_val

    # Resolve actual default if not provided
    resolved_default = default if default is not None else DEFAULT_FLAGS.get(key, False)

    # If DB is not available, fail-safe to default
    if not supabase_available():
        return resolved_default

    # 2. Project Scope
    if project_id:
        val = _fetch_db_flag(key, "project", project_id)
        if val is not None:
            return val

    # 3. User Scope
    if user_id:
        val = _fetch_db_flag(key, "user", user_id)
        if val is not None:
            return val

    # 4. Workspace Scope
    if project_id:
        workspace_id = _get_project_workspace_id(project_id)
        if workspace_id:
            val = _fetch_db_flag(key, "workspace", workspace_id)
            if val is not None:
                return val

    # 5. Global Scope
    val = _fetch_db_flag(key, "global", None)
    if val is not None:
        return val

    # 6. Default
    return resolved_default

def is_enabled(key: str, user_id: Optional[str] = None, project_id: Optional[str] = None, default: bool = False) -> bool:
    """Convenience function checking if flag is enabled."""
    return get_feature_flag(key, user_id=user_id, project_id=project_id, default=default)

def get_active_flags(user_id: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, bool]:
    """Retrieve state of all registered and overridden flags."""
    active = {}
    # Scan environment variables for any ENABLE_ flags
    for env_k in os.environ:
        if env_k.startswith("ENABLE_"):
            val = get_env_override(env_k)
            if val is not None:
                active[env_k] = val

    # Fetch all flags defined in DB
    db_flags = []
    if supabase_available():
        try:
            admin = get_admin_client()
            res = admin.table("feature_flags").select("key, scope_type, scope_id, enabled").execute()
            if res.data:
                db_flags = res.data
        except Exception as e:
            logger.warning(f"Failed to fetch active flag registry from DB: {e}")

    # Gather workspace_id if project_id is provided
    workspace_id = _get_project_workspace_id(project_id) if project_id else None

    # Helper to check if a DB flag rule applies to the context
    def rule_applies(flag_rule) -> bool:
        scope = flag_rule.get("scope_type")
        sid = flag_rule.get("scope_id")
        if scope == "global":
            return True
        if scope == "project" and project_id and sid == project_id:
            return True
        if scope == "user" and user_id and sid == user_id:
            return True
        if scope == "workspace" and workspace_id and sid == workspace_id:
            return True
        return False

    # Apply database flag rules sorted by precedence: global -> workspace -> user -> project
    # This ensures higher precedence scopes overwrite lower precedence scopes.
    scope_precedence = {"global": 1, "workspace": 2, "user": 3, "project": 4}
    sorted_db_rules = sorted(
        [r for r in db_flags if rule_applies(r)],
        key=lambda r: scope_precedence.get(r.get("scope_type"), 0)
    )

    # Apply defaults first
    for k, default_val in DEFAULT_FLAGS.items():
        active[k] = default_val

    # Apply DB rules
    for rule in sorted_db_rules:
        active[rule["key"]] = bool(rule["enabled"])

    # Re-apply environment overrides (which have highest precedence)
    for env_k in os.environ:
        if env_k.startswith("ENABLE_"):
            val = get_env_override(env_k)
            if val is not None:
                active[env_k] = val

    return active

def snapshot_active_flags(user_id: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, bool]:
    """Create a dictionary snapshot of active flags to store in trace metadata."""
    return get_active_flags(user_id=user_id, project_id=project_id)
