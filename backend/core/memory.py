"""
Composite memory system.
Each memory scored by: semantic similarity + recency + importance.
"""
import math
import time
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class Memory:
    def __init__(self, content: str, role: str = "assistant",
                 importance: float = 0.5, mem_type: str = "conversation"):
        self.content = content[:1000]
        self.role = role
        self.importance = max(0.0, min(1.0, importance))
        self.mem_type = mem_type
        self.timestamp = time.time()
        self.access_count = 0

    def age_seconds(self) -> float:
        return time.time() - self.timestamp


class CompositeMemory:
    """In-memory store with composite scoring."""

    SEMANTIC_WEIGHT = 0.4
    RECENCY_WEIGHT = 0.3
    IMPORTANCE_WEIGHT = 0.3
    RECENCY_HALF_LIFE = 300  # 5 min
    MAX_MEMORIES = 100

    def __init__(self):
        self.memories: List[Memory] = []

    def store(self, content: str, role: str = "assistant",
              importance: float = 0.5, mem_type: str = "conversation"):
        """Store a memory with auto-scored importance if 0.5."""
        if importance == 0.5:
            importance = self._auto_score(content, mem_type)

        mem = Memory(content, role, importance, mem_type)
        self.memories.append(mem)

        if len(self.memories) > self.MAX_MEMORIES:
            self._evict()

        return mem

    def recall(self, query: str, top_k: int = 5) -> List[Tuple[Memory, float]]:
        """Recall memories ranked by composite score."""
        if not self.memories:
            return []

        scored = []
        for mem in self.memories:
            sem = self._similarity(query, mem.content)
            age = mem.age_seconds()
            rec = math.exp(-0.693 * age / self.RECENCY_HALF_LIFE)

            score = (
                self.SEMANTIC_WEIGHT * sem +
                self.RECENCY_WEIGHT * rec +
                self.IMPORTANCE_WEIGHT * mem.importance
            )

            if score >= 0.1:
                scored.append((mem, round(score, 3)))
                mem.access_count += 1

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def recall_as_context(self, query: str, top_k: int = 5) -> str:
        """Format recalled memories as context string."""
        results = self.recall(query, top_k)
        if not results:
            return ""

        lines = ["=== RELEVANT MEMORY ==="]
        for mem, score in results:
            role = "User" if mem.role == "user" else "SwarmOps"
            tag = f"[{mem.mem_type}]" if mem.mem_type != "conversation" else ""
            lines.append(f"{role} {tag}: {mem.content[:250]}")
        lines.append("=== END MEMORY ===")
        return "\n".join(lines)

    def _auto_score(self, content: str, mem_type: str) -> float:
        type_scores = {
            "brand": 0.9, "decision": 0.8, "audit": 0.8,
            "tool_result": 0.7, "workflow": 0.6,
            "conversation": 0.4, "greeting": 0.1,
        }
        score = type_scores.get(mem_type, 0.5)

        low = content.lower()
        if any(w in low for w in ["url", "https://", "brand name", "company"]):
            score = max(score, 0.8)
        if any(w in low for w in ["goal", "objective", "budget", "revenue"]):
            score = max(score, 0.7)
        if any(w in low for w in ["hello", "hi ", "thanks", "ok"]):
            score = min(score, 0.2)
        if len(content) < 20:
            score = min(score, 0.3)

        return round(score, 2)

    def _similarity(self, query: str, content: str) -> float:
        """Simple word overlap. Real implementations use embeddings."""
        q_words = set(query.lower().split())
        c_words = set(content.lower().split())
        if not q_words or not c_words:
            return 0.0
        overlap = len(q_words & c_words)
        return overlap / max(len(q_words), 1)

    def _evict(self):
        """Remove low-scored memories when over capacity."""
        scored = []
        for i, mem in enumerate(self.memories):
            rec = math.exp(-0.693 * mem.age_seconds() / self.RECENCY_HALF_LIFE)
            score = 0.5 * rec + 0.5 * mem.importance
            scored.append((i, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        keep = set(idx for idx, _ in scored[:self.MAX_MEMORIES])
        self.memories = [m for i, m in enumerate(self.memories) if i in keep]


# Per-conversation memory store (in-memory; production would use Redis/DB)
_stores = {}


def get_memory(conversation_id: str = "default") -> CompositeMemory:
    if conversation_id not in _stores:
        _stores[conversation_id] = CompositeMemory()
    return _stores[conversation_id]


# ============================================================
# PERSISTENT PROJECT MEMORY (Supabase-backed)
# ============================================================

from .supabase_client import get_admin_client, is_available as supabase_available

def create_project_memory(
    user_id: str,
    project_id: str,
    memory_type: str,
    title: str,
    summary: str,
    source: str = "user",
    confidence: float = 0.5,
    tags: list = None
) -> dict:
    """Persist a new memory to the project_memories database table."""
    admin = get_admin_client()
    if not admin:
        return {"error": "Supabase not configured"}
    try:
        res = admin.table("project_memories").insert({
            "user_id": user_id,
            "project_id": project_id,
            "memory_type": memory_type,
            "title": title[:200],
            "summary": summary,
            "source": source,
            "confidence": confidence,
            "tags": tags or []
        }).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        logger.error(f"Failed to create project memory: {e}")
        return {"error": str(e)}

def list_project_memories(project_id: str, memory_type: str = None) -> list:
    """Retrieve all memories for a project, optionally filtered by type."""
    admin = get_admin_client()
    if not admin:
        return []
    try:
        query = admin.table("project_memories").select("*").eq("project_id", project_id)
        if memory_type:
            query = query.eq("memory_type", memory_type)
        res = query.order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to list project memories: {e}")
        return []

def delete_project_memory(memory_id: str) -> bool:
    """Delete a memory from the project_memories table."""
    admin = get_admin_client()
    if not admin:
        return False
    try:
        admin.table("project_memories").delete().eq("id", memory_id).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to delete project memory: {e}")
        return False

def retrieve_relevant_memories(project_id: str, query_text: str = None, limit: int = 6) -> list:
    """
    Retrieve project memories for context injection.
    Groups by type and retrieves up to `limit` total records.
    """
    memories = list_project_memories(project_id)
    if not memories:
        return []
    
    if query_text:
        low_query = query_text.lower().split()
        scored = []
        for mem in memories:
            text = (mem.get("title", "") + " " + mem.get("summary", "") + " " + " ".join(mem.get("tags", []))).lower()
            match_score = sum(1 for w in low_query if w in text)
            scored.append((mem, match_score))
        scored.sort(key=lambda x: x[1], reverse=True)
        memories = [item[0] for item in scored]
        
    return memories[:limit]

def extract_and_persist_memories_from_decision(user_id: str, project_id: str, decision_text: str, rationale_text: str):
    """
    Extract durable insights from the final swarm decision and persist them.
    """
    from .model_router import call_model
    import json
    
    prompt = f"""You are the boardroom memory extraction specialist.
Analyze this finalized swarm decision:

DECISION:
{decision_text}

RATIONALE:
{rationale_text}

Extract up to 3 durable, high-value strategic facts or memories from this decision that should be remembered for future campaign brief creations.
For each memory, you MUST classify it into one of these types:
- 'campaign_goal' (specific goals to achieve)
- 'icp' (audience persona traits)
- 'competitor' (insights about competitors)
- 'channel_strategy' (channel selections and priorities)
- 'previous_decision' (concrete strategic shifts agreed upon)
- 'brand_voice' (brand style details)
- 'experiment' (A/B testing plans)
- 'data_gap' (flaws or missing logs)

You MUST respond with a single JSON array of objects matching this schema:
[
  {{
    "memory_type": "type",
    "title": "Short title (<60 chars)",
    "summary": "1-2 sentence descriptive fact",
    "tags": ["tag1", "tag2"]
  }}
]

Return ONLY the JSON array. No markdown code fences, no prose."""

    try:
        raw_response = call_model(
            prompt=prompt,
            agent_id="nexus",
            system="Always return JSON array only. No markdown fences.",
            max_tokens=800,
            temperature=0.3,
            json_mode=True
        )
        
        # Try to parse
        from .agent_runner import _safe_parse_json
        parsed = _safe_parse_json(raw_response)
        
        if not parsed:
            # Try parsing direct list if _safe_parse_json expects dictionary
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                parts = cleaned.split("```", 2)
                if len(parts) >= 2:
                    cleaned = parts[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
            parsed = json.loads(cleaned)
            
        if parsed and isinstance(parsed, list):
            for item in parsed:
                memory_type = item.get("memory_type")
                title = item.get("title")
                summary = item.get("summary")
                tags = item.get("tags", [])
                
                if memory_type and title and summary:
                    create_project_memory(
                        user_id=user_id,
                        project_id=project_id,
                        memory_type=memory_type,
                        title=title,
                        summary=summary,
                        source="swarm_decision",
                        confidence=0.85,
                        tags=tags
                    )
            logger.info(f"Successfully extracted and saved {len(parsed)} persistent memories for project {project_id}")
    except Exception as e:
        logger.error(f"Failed to extract memories from decision: {e}")

