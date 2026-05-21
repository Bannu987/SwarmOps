"""
Calculate confidence from actual signals — never hallucinate it.

Inputs:
- data_availability: how much real data did the agent have?
- evidence_quality: how strong is each piece of evidence?
- assumption_count: how many assumptions did the agent make?
- cross_agent_agreement: do other agents agree?

Output: float in [0.0, 1.0]
"""
from typing import List
from .schemas import AgentOutput, Evidence


# Higher weight = more confidence-boosting
SOURCE_WEIGHTS = {
    "ga4": 1.0,
    "gsc": 1.0,
    "hubspot": 1.0,
    "google_ads": 1.0,
    "uploaded_file": 0.85,
    "user_input": 0.75,
    "web_search": 0.65,
    "benchmark": 0.45,
    "framework": 0.35,
    "inferred": 0.20,
}


def compute_confidence(
    output: AgentOutput,
    other_agent_outputs: List[AgentOutput] = None,
) -> float:
    """Calculate confidence from evidence + assumptions + cross-agent agreement."""
    other_agent_outputs = other_agent_outputs or []

    # 1. Evidence score (0.0 to 1.0)
    if output.evidence:
        weighted_sum = sum(
            SOURCE_WEIGHTS.get(e.source, 0.3) * e.weight
            for e in output.evidence
        )
        evidence_score = min(weighted_sum / len(output.evidence), 1.0)
    else:
        evidence_score = 0.2

    # 2. Assumption penalty (each unsupported assumption hurts)
    assumption_penalty = min(len(output.assumptions) * 0.05, 0.3)

    # 3. Data gap penalty
    gap_penalty = min(len(output.data_gaps) * 0.03, 0.2)

    # 4. Cross-agent agreement bonus (keyword overlap heuristic for v1)
    agreement_bonus = 0.0
    if other_agent_outputs:
        my_words = set(output.conclusion.lower().split())
        agree_count = sum(
            1 for other in other_agent_outputs
            if len(my_words & set(other.conclusion.lower().split())) / max(len(my_words), 1) > 0.3
        )
        agreement_bonus = (agree_count / len(other_agent_outputs)) * 0.15

    # 5. Real data bonus
    real_data_bonus = 0.1 if output.used_real_data else 0.0

    confidence = (
        evidence_score * 0.55
        + agreement_bonus
        + real_data_bonus
        - assumption_penalty
        - gap_penalty
    )

    return max(0.05, min(0.99, round(confidence, 2)))


def calibrate_to_label(confidence: float) -> str:
    """Convert numeric confidence to a human label."""
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.65:
        return "medium"
    if confidence >= 0.40:
        return "low"
    return "speculative"
