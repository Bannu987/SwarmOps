import logging
import json
import re
from typing import Optional, Dict, Any, List
from core.supabase_client import get_admin_client, is_available as supabase_available
from core.feature_flags import get_feature_flag

logger = logging.getLogger("swarmops.memory_service")

ALLOWED_MEMORY_TYPES = {
    "brand_profile",
    "website_summary",
    "target_audience",
    "offers_services",
    "previous_signal_summary",
    "approved_decision",
    "resolved_action",
    "verification_history",
    "user_preference",
    "curated_playbook"
}

# Regex to detect API keys, tokens, secrets
SECRET_PATTERNS = [
    re.compile(r"(?:api_key|apikey|secret|password|token|auth|bearer|jwt|sk_live|sbp_)[a-zA-Z0-9_\-\.\=\+\/]{8,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.\=\+\/]{20,}", re.IGNORECASE),
    re.compile(r"AIzaSy[a-zA-Z0-9_\-]{35}", re.IGNORECASE)  # Google API key
]

def sanitize_value(val: Any) -> Any:
    """Recursively strip secret-like content from strings, dicts, lists."""
    if isinstance(val, str):
        # Redact matching secrets
        for pattern in SECRET_PATTERNS:
            if pattern.search(val):
                val = pattern.sub("[REDACTED_SECRET]", val)
        return val
    elif isinstance(val, dict):
        sanitized = {}
        for k, v in val.items():
            # Drop keys that sound like secrets
            kl = k.lower()
            if any(s in kl for s in ["key", "secret", "password", "token", "auth", "credential", "private"]):
                sanitized[k] = "[REDACTED_SECRET]"
            else:
                sanitized[k] = sanitize_value(v)
        return sanitized
    elif isinstance(val, list):
        return [sanitize_value(item) for item in val]
    return val

def save_project_memory(
    user_id: str,
    project_id: str,
    memory_type: str,
    title: str,
    summary: Optional[str] = None,
    content: Optional[Dict[str, Any]] = None,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    confidence: float = 0.8,
    trust_level: str = "system"
) -> Optional[Dict[str, Any]]:
    """Save a project memory to the database, enforcing validation and secret filters."""
    # Check flags
    if not get_feature_flag("ENABLE_PROJECT_MEMORY", user_id=user_id, project_id=project_id, default=False):
        logger.info(f"Skipping memory capture: ENABLE_PROJECT_MEMORY is False")
        return None
    if not get_feature_flag("ENABLE_MEMORY_CAPTURE", user_id=user_id, project_id=project_id, default=False):
        logger.info(f"Skipping memory capture: ENABLE_MEMORY_CAPTURE is False")
        return None

    if memory_type not in ALLOWED_MEMORY_TYPES:
        logger.warning(f"Invalid memory type skipped: {memory_type}")
        return None

    # Sanitize content
    title = sanitize_value(title)
    summary = sanitize_value(summary) if summary else ""
    content = sanitize_value(content) if content else {}

    if not supabase_available():
        logger.warning("Supabase not available, unable to save memory.")
        return None

    try:
        admin = get_admin_client()
        memory_row = {
            "user_id": user_id,
            "project_id": project_id,
            "memory_type": memory_type,
            "title": title,
            "summary": summary,
            "content": content,
            "source_type": source_type,
            "source_id": source_id,
            "trace_id": trace_id,
            "confidence": confidence,
            "trust_level": trust_level
        }
        res = admin.table("project_memory").insert(memory_row).execute()
        if res.data:
            logger.info(f"Saved project memory: {res.data[0]['id']} (type={memory_type})")
            return res.data[0]
    except Exception as e:
        logger.error(f"Failed to save project memory: {e}")
    return None

def get_project_memory(project_id: str, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all memories for a specific project."""
    if not supabase_available():
        return []
    try:
        admin = get_admin_client()
        query = admin.table("project_memory").select("*").eq("project_id", project_id)
        if memory_type:
            query = query.eq("memory_type", memory_type)
        res = query.order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to retrieve project memory: {e}")
    return []

def retrieve_relevant_memory(
    project_id: str,
    user_id: str,
    query: Optional[str] = None,
    limit: int = 5,
    memory_types: Optional[List[str]] = None,
    trace_id: Optional[str] = None,
    retrieval_reason: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant memories scoped by project_id and user_id.
    Performs python-side filtering/keyword matching for simplicity and stability.
    """
    memories = get_project_memory(project_id)
    
    # Filter by user_id to prevent cross-user leakage
    memories = [m for m in memories if m.get("user_id") == user_id]

    # Filter by memory types
    if memory_types:
        memories = [m for m in memories if m.get("memory_type") in memory_types]

    # Keyword matching
    if query:
        words = [w.lower() for w in re.split(r"\s+", query.strip()) if len(w) > 2]
        if words:
            matched_memories = []
            for m in memories:
                title_l = (m.get("title") or "").lower()
                summary_l = (m.get("summary") or "").lower()
                score = 0
                for w in words:
                    if w in title_l:
                        score += 3
                    if w in summary_l:
                        score += 1
                if score > 0:
                    m["_retrieval_score"] = score
                    matched_memories.append(m)
            # Sort by retrieval score descending, then by created_at descending
            memories = sorted(matched_memories, key=lambda x: (-x["_retrieval_score"], x.get("created_at", "")))
    
    # Limit
    retrieved = memories[:limit]
    retrieved_ids = [m["id"] for m in retrieved]
    retrieved_types = list(set([m["memory_type"] for m in retrieved]))

    # Log retrieval to retrieval_logs
    if supabase_available():
        try:
            admin = get_admin_client()
            log_row = {
                "user_id": user_id,
                "project_id": project_id,
                "trace_id": trace_id,
                "query": query or "",
                "retrieved_memory_ids": retrieved_ids,
                "memory_types": retrieved_types,
                "retrieval_reason": retrieval_reason or ""
            }
            admin.table("retrieval_logs").insert(log_row).execute()
        except Exception as e:
            logger.warning(f"Failed to write retrieval log: {e}")

    # Remove temporary retrieval score keys
    for m in retrieved:
        m.pop("_retrieval_score", None)

    return retrieved

def summarize_memory_for_boardroom(project_id: str, user_id: str, trace_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve and construct a short memory context block for injection into Boardroom context.
    Strictly enforces maximum limits:
    - max 5 memories
    - max 1500 characters total
    - no long logs or untrusted content as instructions
    """
    if not get_feature_flag("ENABLE_RAG_CONTEXT", user_id=user_id, project_id=project_id, default=False):
        return {"context_str": "", "retrieved_memories": []}

    types_to_fetch = [
        "brand_profile",
        "website_summary",
        "previous_signal_summary",
        "approved_decision",
        "resolved_action",
        "verification_history"
    ]
    
    memories = retrieve_relevant_memory(
        project_id=project_id,
        user_id=user_id,
        limit=5,
        memory_types=types_to_fetch,
        trace_id=trace_id,
        retrieval_reason="Boardroom context injection"
    )

    if not memories:
        return {"context_str": "", "retrieved_memories": []}

    lines = ["\n=== RELEVANT PROJECT MEMORY CONTEXT ==="]
    current_len = len(lines[0])

    for m in memories:
        m_type = m.get("memory_type", "memory")
        title = m.get("title", "")
        summary = m.get("summary", "")
        
        # Build block
        block = f"\n- [{m_type.upper()}] {title}: {summary}"
        if current_len + len(block) > 1450: # Leave room for closing line
            break
        lines.append(block)
        current_len += len(block)

    lines.append("\n========================================\n")
    context_str = "".join(lines)
    
    return {
        "context_str": context_str,
        "retrieved_memories": [
            {
                "id": m["id"],
                "memory_type": m["memory_type"],
                "title": m["title"],
                "source_id": m.get("source_id")
            } for m in memories
        ]
    }

def memory_from_boardroom_decision(
    user_id: str,
    project_id: str,
    signal_title: str,
    final_decision: str,
    priority: str,
    checklist: List[str],
    trace_id: str,
    source_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Save boardroom decision to memory."""
    checklist_str = ", ".join(checklist) if checklist else "None"
    summary = f"Decision: {final_decision}. Priority: {priority}. Checklist: {checklist_str}"
    content = {
        "signal_title": signal_title,
        "final_decision": final_decision,
        "priority": priority,
        "checklist": checklist
    }
    return save_project_memory(
        user_id=user_id,
        project_id=project_id,
        memory_type="approved_decision",
        title=f"Boardroom Decision: {signal_title}",
        summary=summary,
        content=content,
        source_type="boardroom_decision",
        source_id=source_id,
        trace_id=trace_id
    )

def memory_from_action_plan(
    user_id: str,
    project_id: str,
    action_title: str,
    action_description: str,
    owner: str,
    priority: str,
    checklist: List[str],
    source_signal_id: str,
    trace_id: Optional[str] = None,
    action_plan_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Save action plan approval to memory."""
    checklist_str = ", ".join(checklist) if checklist else "None"
    summary = f"Action: {action_description}. Owner: {owner}. Priority: {priority}. Checklist: {checklist_str}"
    content = {
        "action_title": action_title,
        "action_description": action_description,
        "owner": owner,
        "priority": priority,
        "checklist": checklist,
        "source_signal_id": source_signal_id
    }
    return save_project_memory(
        user_id=user_id,
        project_id=project_id,
        memory_type="approved_decision",
        title=f"Action Plan Approved: {action_title}",
        summary=summary,
        content=content,
        source_type="action_plan",
        source_id=action_plan_id,
        trace_id=trace_id
    )

def memory_from_verification(
    user_id: str,
    project_id: str,
    action_title: str,
    verification_status: str,
    verification_method: str,
    result_message: str,
    action_plan_id: str,
    trace_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Save verification completion to memory."""
    summary = f"Status: {verification_status}. Method: {verification_method}. Result: {result_message}"
    content = {
        "verification_status": verification_status,
        "verification_method": verification_method,
        "result_message": result_message,
        "action_plan_id": action_plan_id
    }
    # Save as resolved_action if passed, otherwise verification_history
    m_type = "resolved_action" if verification_status.lower() in ("passed", "success", "verified") else "verification_history"
    return save_project_memory(
        user_id=user_id,
        project_id=project_id,
        memory_type=m_type,
        title=f"Verification Result: {action_title}",
        summary=summary,
        content=content,
        source_type="verification_history",
        source_id=action_plan_id,
        trace_id=trace_id
    )
