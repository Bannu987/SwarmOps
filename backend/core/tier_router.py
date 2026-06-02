"""
Task-tier router. Picks the model based on task complexity, not agent.

Tier 1 (Execution, free): drafting copy, listing keywords, formatting schema
Tier 2 (Analysis, free):  reasoning on data, attribution, MECLABS scoring
Tier 3 (Strategy, paid):  orchestration, roadmaps, cross-channel decisions

The agent doesn't know which tier it runs on. Router decides at call time.
"""
import os
from typing import Optional


# Models per tier — easy to swap
TIER_1_MODELS = {
    "primary":  "meta-llama/llama-3-8b-instruct:free",
    "fast":     "meta-llama/llama-3-8b-instruct:free",
    "fallback": "qwen/qwen-2-7b-instruct:free",
}

TIER_2_MODELS = {
    "primary":   "meta-llama/llama-3-8b-instruct:free",
    "reasoning": "google/gemma-2-9b-it:free",
    "fallback":  "qwen/qwen-2-7b-instruct:free",
}

TIER_3_MODELS = {
    "primary":  "anthropic/claude-sonnet-4-20250514",  # paid, premium
    "fallback": "anthropic/claude-3.5-sonnet",         # cheaper backup
}


# Keywords that signal each tier
TIER_3_SIGNALS = [
    "strategy", "strategic", "roadmap", "plan", "synthesi", "synthesize",
    "reallocate", "budget", "positioning", "go to market", "go-to-market",
    "quarterly", "annual", "q1", "q2", "q3", "q4", "fiscal",
    "executive", "report", "audit", "competitive analysis",
    "decision", "prioritize", "recommend",
]

TIER_2_SIGNALS = [
    "analyze", "analyse", "attribution", "funnel", "conversion rate",
    "cohort", "retention", "churn", "ltv", "cac", "roas", "ctr",
    "statistical", "significance", "a/b test", "ab test", "experiment",
    "meclabs", "lift", "rice", "ice", "pie",
    "mmm", "marketing mix", "multi-touch", "shapley", "markov",
    "ga4", "search console", "gsc", "hubspot",
]

# Agents whose default is Tier 3 (orchestration)
TIER_3_AGENTS = {"nexus"}

# Agents whose default is Tier 2 (analytical specialists)
TIER_2_AGENTS = {"analytics", "cro"}

# Everything else defaults to Tier 1 (execution)


def classify_task(
    user_message: str,
    agent_id: str,
    is_synthesis: bool = False,
) -> int:
    """
    Returns 1, 2, or 3. Synthesis calls (Nexus combining specialist
    outputs into final answer) are always Tier 3.
    """
    if is_synthesis or agent_id == "nexus":
        return 3

    if agent_id in TIER_3_AGENTS:
        return 3

    msg = (user_message or "").lower()

    # Strong signals override the agent default
    if any(s in msg for s in TIER_3_SIGNALS):
        return 3

    if any(s in msg for s in TIER_2_SIGNALS):
        return 2

    if agent_id in TIER_2_AGENTS:
        return 2

    # Long messages tend to need more reasoning
    if len(msg) > 800:
        return 2

    return 1


def select_model(tier: int) -> str:
    """Pick the primary model for a given tier. Support env override."""
    env_model = os.environ.get("OPENROUTER_MODEL")
    if env_model:
        return env_model

    if tier == 3:
        # Only use paid Claude if user explicitly opted in via env var
        # (avoids surprise bills during dev)
        if os.environ.get("ENABLE_PAID_TIER", "false").lower() == "true":
            return TIER_3_MODELS["primary"]
        return TIER_2_MODELS["primary"]  # free fallback

    if tier == 2:
        return TIER_2_MODELS["primary"]

    return TIER_1_MODELS["primary"]



def fallback_chain(tier: int) -> list:
    """Get the fallback chain for a tier (in order of preference)."""
    if tier == 3:
        chain = []
        if os.environ.get("ENABLE_PAID_TIER", "false").lower() == "true":
            chain.append(TIER_3_MODELS["primary"])
            chain.append(TIER_3_MODELS["fallback"])
        chain.extend([
            TIER_2_MODELS["primary"],
            TIER_2_MODELS["reasoning"],
            TIER_1_MODELS["primary"],
        ])
        return chain

    if tier == 2:
        return [
            TIER_2_MODELS["primary"],
            TIER_2_MODELS["reasoning"],
            TIER_2_MODELS["fallback"],
            TIER_1_MODELS["primary"],
        ]

    return [
        TIER_1_MODELS["primary"],
        TIER_1_MODELS["fast"],
        TIER_1_MODELS["fallback"],
    ]
