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
    """Run a multi-agent workflow."""
    if workflow_name not in WORKFLOWS:
        return {"error": f"Unknown workflow: {workflow_name}"}

    config = WORKFLOWS[workflow_name]
    agents = config["agents"]

    ctx = get_context(conversation_id)
    memory = get_memory(conversation_id)

    memory.store(message, role="user", mem_type="conversation")

    context_header = ctx.context_header()
    relevant_memory = memory.recall_as_context(message, top_k=3)
    if relevant_memory:
        context_header = f"{context_header}\n\n{relevant_memory}"

    start = time.time()

    # Run all specialist agents in parallel
    specialist_results = []
    with ThreadPoolExecutor(max_workers=min(len(agents), 5)) as executor:
        futures = {
            executor.submit(run_agent, agent, message, context_header): agent
            for agent in agents
        }
        for future in as_completed(futures):
            result = future.result()
            specialist_results.append(result)

    # Synthesize via Nexus
    synthesis_input = f"User asked: {message}\n\nSpecialist agent outputs:\n\n"
    for r in specialist_results:
        synthesis_input += f"--- {r['agent'].upper()} ---\n{r['response']}\n\n"

    synthesis_input += (
        "\nSynthesize these into ONE cohesive, actionable response for the user.\n"
        "- Lead with the most important insight (Pyramid Principle)\n"
        "- Integrate findings naturally (don't list 'SEO says X, Content says Y')\n"
        "- Be direct and specific\n"
        "- Include concrete next actions\n"
        "- Acknowledge data limitations honestly\n"
    )

    nexus_result = run_agent("nexus", synthesis_input, context_header)

    memory.store(
        nexus_result["response"][:500],
        role="assistant",
        mem_type="workflow",
        importance=0.7,
    )

    total_elapsed = time.time() - start

    return {
        "workflow": workflow_name,
        "response": nexus_result["response"],
        "agents_used": agents,
        "specialist_outputs": [
            {"agent": r["agent"], "elapsed": r["elapsed"]}
            for r in specialist_results
        ],
        "latency_ms": int(total_elapsed * 1000),
    }


def run_single_agent(agent_id: str, message: str, conversation_id: str = "default") -> Dict:
    """Run a single specific agent (used for slash commands)."""
    ctx = get_context(conversation_id)
    memory = get_memory(conversation_id)

    memory.store(message, role="user", mem_type="conversation")

    context_header = ctx.context_header()
    relevant_memory = memory.recall_as_context(message, top_k=3)
    if relevant_memory:
        context_header = f"{context_header}\n\n{relevant_memory}"

    result = run_agent(agent_id, message, context_header)

    memory.store(
        result["response"][:500],
        role="assistant",
        mem_type="conversation",
        importance=0.5,
    )

    return {
        "agent": agent_id,
        "response": result["response"],
        "agents_used": [agent_id],
        "latency_ms": int(result["elapsed"] * 1000),
    }
