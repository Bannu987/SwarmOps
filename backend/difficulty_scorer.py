"""
Query difficulty scorer.
Returns a difficulty score (1-10) and selects the appropriate model tier.
Higher score → more complex query → premium model.
"""
import re


# Signal lists for difficulty estimation
_SIMPLE_SIGNALS = [
    "what is", "what are", "how do i", "help me with", "tips for",
    "explain", "define", "tell me about", "quick", "simple", "basic",
    "get started", "overview", "intro", "beginner",
]

_MEDIUM_SIGNALS = [
    "strategy", "plan", "recommend", "analyze", "compare", "optimize",
    "improve", "build", "create", "develop", "review my", "audit",
    "how to grow", "increase", "generate", "funnel", "campaign",
    "email sequence", "content calendar", "keyword research",
]

_COMPLEX_SIGNALS = [
    "comprehensive", "complete", "full", "detailed", "end-to-end",
    "multi-channel", "across all", "3 month", "6 month", "quarterly",
    "market entry", "go-to-market", "gtm", "p&l", "roi projection",
    "competitive landscape", "cohort", "attribution", "multi-touch",
    "segmentation analysis", "predictive", "machine learning",
    "international", "enterprise", "scale to", "growth model",
]

_QUESTION_WORDS_SIMPLE = {"what", "who", "when", "where"}
_QUESTION_WORDS_COMPLEX = {"how", "why", "which", "should"}


def score_difficulty(message: str) -> tuple[int, str]:
    """
    Score query difficulty from 1 (trivial) to 10 (deeply complex).

    Returns:
        (score: int, category: str)
        category: "simple" | "medium" | "complex"
    """
    msg = message.lower().strip()
    score = 3  # baseline

    # Word count contributes to complexity
    word_count = len(msg.split())
    if word_count > 30:
        score += 1
    if word_count > 60:
        score += 1

    # Signal scanning
    for signal in _SIMPLE_SIGNALS:
        if signal in msg:
            score -= 1
            break  # only deduct once

    for signal in _MEDIUM_SIGNALS:
        if signal in msg:
            score += 1
            break

    complex_hits = sum(1 for s in _COMPLEX_SIGNALS if s in msg)
    score += min(complex_hits * 2, 4)

    # Multi-part questions (contains "and" + "also" pattern, or multiple "?")
    question_count = msg.count("?")
    if question_count >= 2:
        score += 1
    if question_count >= 3:
        score += 1

    # Asks for numbers/projections
    if re.search(r'\b(roi|budget|cost|price|revenue|cac|ltv|roas|cpc|ctr|cvr)\b', msg):
        score += 1

    # Multi-agent workflows always complex
    multi_agent_keywords = ["audit", "full strategy", "growth plan", "lead generation", "competitor analysis"]
    if any(k in msg for k in multi_agent_keywords):
        score = max(score, 6)

    # Clamp
    score = max(1, min(score, 10))

    if score <= 3:
        category = "simple"
    elif score <= 6:
        category = "medium"
    else:
        category = "complex"

    return score, category


def get_model_tier(difficulty_score: int) -> str:
    """
    Map difficulty score to model tier for call_model_sync().

    Returns:
        "fast" (tier 1) | "standard" (tier 2) | "premium" (tier 3)
    """
    if difficulty_score <= 3:
        return "fast"
    elif difficulty_score <= 6:
        return "standard"
    else:
        return "premium"


def get_tier_number(difficulty_score: int) -> int:
    """Return numeric tier (1/2/3) for call_model_sync tier param."""
    tier = get_model_tier(difficulty_score)
    return {"fast": 1, "standard": 2, "premium": 3}[tier]
