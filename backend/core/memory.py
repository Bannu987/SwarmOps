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
