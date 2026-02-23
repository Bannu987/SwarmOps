"""
Response Formatter - SwarmOps
Structures all agent responses with consistent metadata.
Backwards-compatible with the existing frontend response shape.
"""

import time
from typing import Optional, List, Dict, Any


def format_response(
    agent: str,
    result_text: str,
    model: str = "unknown",
    provider: str = "unknown",
    latency_ms: int = 0,
    quality: Optional[Dict] = None,
    integrations_used: Optional[List[str]] = None,
    data_sources: Optional[List[str]] = None,
    follow_up_suggestions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a fully-structured response dict.
    Backwards-compatible: always includes result, model, provider, latency_ms.

    Args:
        agent: Agent name ("seo", "content", etc.)
        result_text: The agent's response text
        model: Model used (e.g., "llama-3.3-70b-versatile")
        provider: Provider (e.g., "groq")
        latency_ms: Response time
        quality: Skeptic quality dict (optional)
        integrations_used: List of connected integrations used
        data_sources: List of data sources consulted
        follow_up_suggestions: Suggested next actions

    Returns:
        Full response dict that the frontend can consume
    """
    response = {
        "success": True,
        "agent": agent,
        "result": result_text,
        "model": model,
        "provider": provider,
        "latency_ms": latency_ms,
    }

    # Build metadata block
    metadata: Dict[str, Any] = {}

    if quality:
        response["quality"] = quality
        metadata["confidence"] = quality.get("confidence", 0.0)
        metadata["revised"] = quality.get("revised", False)

        # Add confidence breakdown if present
        breakdown = quality.get("breakdown")
        if breakdown:
            metadata["confidence_breakdown"] = breakdown

    if integrations_used:
        metadata["integrations_used"] = integrations_used
    if data_sources:
        metadata["data_sources"] = data_sources
    if follow_up_suggestions:
        metadata["follow_up_suggestions"] = follow_up_suggestions

    if metadata:
        response["metadata"] = metadata

    return response


def generate_follow_up_suggestions(agent: str, result_text: str) -> List[str]:
    """
    Generate intelligent follow-up suggestions based on what the agent produced.
    Used to guide the user to the next logical step.
    """
    # Map of agent → natural follow-up agents
    follow_up_map = {
        "seo": [
            "Create content targeting these keywords",
            "Build a PPC campaign around high-intent keywords",
            "Set up Google Search Console tracking",
        ],
        "content": [
            "Distribute content on social media",
            "Set up email campaign promoting this content",
            "Analyze SEO performance of this content",
        ],
        "ppc": [
            "Analyze campaign performance after 2 weeks",
            "Create matching landing page for these ads",
            "Set up conversion tracking in Google Analytics",
        ],
        "analytics": [
            "Identify CRO opportunities from this data",
            "Create a weekly reporting dashboard",
            "Set up anomaly alerts for key metrics",
        ],
        "crm": [
            "Analyze email performance after sending",
            "Segment list for more targeted campaigns",
            "Connect email data to ad retargeting",
        ],
        "smm": [
            "Schedule posts and track engagement",
            "Run a paid amplification campaign on top posts",
            "Analyze which content performs best",
        ],
        "brand": [
            "Apply brand guidelines to website copy",
            "Audit existing marketing materials for consistency",
            "Create brand messaging framework",
        ],
        "cro": [
            "Implement A/B tests and track results",
            "Analyze funnel data after optimization",
            "Run heatmap analysis on key pages",
        ],
        "research": [
            "Create content strategy based on research findings",
            "Build a competitive analysis report",
            "Use research to inform your PPC keyword strategy",
        ],
        "webux": [
            "A/B test the new design vs current",
            "Measure conversion impact after changes",
            "Get user feedback via surveys",
        ],
    }

    suggestions = follow_up_map.get(agent, [
        "Run a full marketing pipeline analysis",
        "Check analytics for performance insights",
    ])

    return suggestions[:3]
