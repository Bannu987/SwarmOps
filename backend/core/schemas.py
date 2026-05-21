"""
Structured output schemas for every agent.
Confidence is REAL — calculated from data availability and agreement.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """A single piece of evidence backing a conclusion."""
    claim: str
    source: Literal["user_input", "uploaded_file", "ga4", "gsc", "hubspot",
                    "google_ads", "web_search", "benchmark", "framework", "inferred"]
    source_detail: Optional[str] = None  # e.g. "GA4 last 30 days"
    weight: float = Field(default=0.5, ge=0.0, le=1.0)


class Recommendation(BaseModel):
    """A single recommended action."""
    action: str
    rationale: str
    expected_impact: Literal["high", "medium", "low"]
    effort: Literal["low", "medium", "high"]
    timeframe: str  # e.g. "this week", "next 30 days", "Q1"
    rice_score: Optional[float] = None  # Reach × Impact × Confidence / Effort


class AgentOutput(BaseModel):
    """
    Standard return shape for every specialist agent.
    Confidence is CALCULATED, not hallucinated.
    """
    agent_id: str
    conclusion: str  # 1-2 sentence top-line answer
    summary: str     # 2-4 paragraph elaboration (markdown OK)

    # Real data trail
    evidence: List[Evidence] = []
    assumptions: List[str] = []   # what the agent had to assume
    data_gaps: List[str] = []     # what would make this better

    # Recommendations
    recommendations: List[Recommendation] = []

    # CALCULATED confidence (see compute_confidence)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Honesty flags
    used_real_data: bool = False
    used_benchmarks: bool = False
    used_frameworks: bool = False
    tier_used: int = 1  # which routing tier this ran on


class DebateRound(BaseModel):
    """One agent's contribution to a multi-agent debate."""
    agent_id: str
    position: str
    confidence: float = Field(ge=0.0, le=1.0)
    agrees_with: List[str] = []
    disagrees_with: List[str] = []
    reasoning: str


class SwarmDecision(BaseModel):
    """The final output after specialists run + Nexus synthesizes."""
    decision: str
    rationale: str
    agents_consulted: List[str]
    agents_agreed: List[str]
    agents_dissented: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    next_action: Optional[Recommendation] = None
    dissent_notes: Optional[str] = None
