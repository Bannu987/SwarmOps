"""
Workflow engine. Code controls routing, not the LLM.
6 blueprints for v1.
"""
import time
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .model_router import call_model
from .prompts import get_prompt
from .memory import get_memory
from .context import get_context

logger = logging.getLogger(__name__)


# 6 workflow blueprints
WORKFLOWS = {
    "keyword_research": {
        "agents": ["seo"],
        "triggers": ["keyword", "keywords", "search term", "rank for"],
    },
    "content_creation": {
        "agents": ["content", "seo", "aeo"],
        "triggers": ["write a blog", "create content", "blog post", "article"],
    },
    "marketing_audit": {
        "agents": ["seo", "content", "analytics", "cro", "aeo"],
        "triggers": ["audit", "review my site", "analyze my site"],
    },
    "conversion_optimization": {
        "agents": ["cro", "analytics"],
        "triggers": ["conversion", "cro", "improve conversions", "funnel"],
    },
    "ai_search_optimization": {
        "agents": ["aeo", "seo", "content"],
        "triggers": ["aeo", "ai search", "chatgpt search", "perplexity", "ai overview"],
    },
    "growth_strategy": {
        "agents": ["seo", "content", "analytics", "cro"],
        "triggers": ["growth", "strategy", "plan", "roadmap"],
    },
}


def detect_workflow(message: str) -> Optional[str]:
    """Detect which workflow matches the user message."""
    low = message.lower()
    best_match = None
    best_score = 0

    for name, config in WORKFLOWS.items():
        score = sum(1 for trigger in config["triggers"] if trigger in low)
        if score > best_score:
            best_score = score
            best_match = name

    return best_match if best_score > 0 else None


def run_agent(agent_id: str, prompt: str, context_header: str = "") -> Dict:
    """Run a single agent."""
    start = time.time()

    system = get_prompt(agent_id)
    full_prompt = f"{context_header}\n\n{prompt}" if context_header else prompt

    response = call_model(
        prompt=full_prompt,
        agent_id=agent_id,
        system=system,
        max_tokens=2000,
        temperature=0.7,
    )

    elapsed = time.time() - start
    return {
        "agent": agent_id,
        "response": response,
        "elapsed": round(elapsed, 1),
    }


def run_workflow(workflow_name: str, message: str, conversation_id: str = "default") -> Dict:
    """Run a multi-agent workflow with structured output."""
    from .agent_runner import run_agent_structured
    from .schemas import SwarmDecision

    if workflow_name not in WORKFLOWS:
        return {"error": f"Unknown workflow: {workflow_name}"}

    config = WORKFLOWS[workflow_name]
    agents = config["agents"]

    ctx = get_context(conversation_id)
    memory = get_memory(conversation_id)
    memory.store(message, role="user", mem_type="conversation")

    start = time.time()

    # Phase 1: All specialists respond in parallel with structured output
    specialist_outputs = []
    with ThreadPoolExecutor(max_workers=min(len(agents), 5)) as executor:
        futures = {
            executor.submit(run_agent_structured, agent, message, conversation_id): agent
            for agent in agents
        }
        for future in as_completed(futures):
            output = future.result()
            specialist_outputs.append(output)

    # Phase 2: Recalculate confidence with cross-agent agreement
    from .confidence import compute_confidence
    for output in specialist_outputs:
        others = [o for o in specialist_outputs if o.agent_id != output.agent_id]
        output.confidence = compute_confidence(output, others)

    # Phase 3: Nexus synthesizes
    synthesis_input = _build_synthesis_input(message, specialist_outputs)
    nexus_output = run_agent_structured("nexus", synthesis_input, conversation_id, specialist_outputs)

    avg_confidence = sum(o.confidence for o in specialist_outputs) / len(specialist_outputs)
    agreed = [o.agent_id for o in specialist_outputs if o.confidence > 0.5]
    dissented = [o.agent_id for o in specialist_outputs if o.confidence <= 0.5]

    swarm_decision = SwarmDecision(
        decision=nexus_output.conclusion,
        rationale=nexus_output.summary,
        agents_consulted=[o.agent_id for o in specialist_outputs],
        agents_agreed=agreed,
        agents_dissented=dissented,
        confidence=round((nexus_output.confidence + avg_confidence) / 2, 2),
        next_action=nexus_output.recommendations[0] if nexus_output.recommendations else None,
    )

    memory.store(nexus_output.conclusion[:500], role="assistant", mem_type="workflow", importance=0.7)

    total_elapsed = time.time() - start

    return {
        # OLD shape (keeps existing UI working)
        "workflow": workflow_name,
        "response": nexus_output.summary or nexus_output.conclusion,
        "agents_used": [o.agent_id for o in specialist_outputs],
        "latency_ms": int(total_elapsed * 1000),
        "confidence": swarm_decision.confidence,

        # NEW structured shape (for future UI)
        "structured": {
            "decision": swarm_decision.dict(),
            "specialists": [o.dict() for o in specialist_outputs],
            "nexus": nexus_output.dict(),
        },
    }


def run_single_agent(agent_id: str, message: str, conversation_id: str = "default") -> Dict:
    """Run a single specific agent with structured output."""
    from .agent_runner import run_agent_structured

    ctx = get_context(conversation_id)
    memory = get_memory(conversation_id)
    memory.store(message, role="user", mem_type="conversation")

    start = time.time()
    output = run_agent_structured(agent_id, message, conversation_id)
    elapsed = time.time() - start

    memory.store(output.conclusion[:500], role="assistant", mem_type="conversation", importance=0.5)

    return {
        # OLD shape
        "agent": agent_id,
        "response": output.summary or output.conclusion,
        "agents_used": [agent_id],
        "latency_ms": int(elapsed * 1000),
        "confidence": output.confidence,

        # NEW shape
        "structured": {
            "specialist": output.dict(),
        },
    }


def _build_synthesis_input(user_message: str, outputs: List) -> str:
    """Build Nexus's synthesis prompt from specialist outputs."""
    lines = [f"USER ASKED: {user_message}\n"]
    lines.append("SPECIALIST OUTPUTS:\n")

    for o in outputs:
        lines.append(f"--- {o.agent_id.upper()} (confidence: {int(o.confidence * 100)}%) ---")
        lines.append(f"CONCLUSION: {o.conclusion}")
        if o.evidence:
            lines.append(f"EVIDENCE: {len(o.evidence)} items, sources: {', '.join(set(e.source for e in o.evidence))}")
        if o.recommendations:
            lines.append(f"TOP REC: {o.recommendations[0].action}")
        if o.assumptions:
            lines.append(f"ASSUMPTIONS: {'; '.join(o.assumptions[:2])}")
        lines.append("")

    lines.append(
        "SYNTHESIZE these specialist outputs into ONE cohesive decision for the user.\n"
        "\n"
        "Your response should:\n"
        "- Lead with the most important insight (Pyramid Principle)\n"
        "- Integrate findings naturally (don't list 'SEO says X, Content says Y')\n"
        "- Be honest about confidence and data gaps\n"
        "- Recommend specific next actions\n"
        "- If specialists disagreed, briefly note the dissent\n"
        "\n"
        "Return your response as the standard JSON schema."
    )

    return "\n".join(lines)
