"""
Wraps the LLM call with structured output enforcement.
Every agent now returns AgentOutput, never raw markdown.
"""
import json
import logging
from typing import Dict, List, Optional

from .model_router import call_model
from .prompts import get_prompt
from .schemas import AgentOutput, Evidence, Recommendation
from .confidence import compute_confidence
from .context import get_context
from .tier_router import classify_task

logger = logging.getLogger(__name__)


def _build_structured_prompt(agent_id: str, user_message: str, context_header: str = "") -> str:
    """Wrap the user message with structured output instructions."""
    return f"""{context_header}

USER ASKED:
{user_message}

YOU MUST respond with a single JSON object matching this exact schema:

{{
  "conclusion": "1-2 sentence top-line answer to the user's question",
  "summary": "2-4 paragraph elaboration in markdown",
  "evidence": [
    {{
      "claim": "specific thing this evidence supports",
      "source": "user_input | uploaded_file | ga4 | gsc | hubspot | google_ads | web_search | benchmark | framework | inferred",
      "source_detail": "specifics like 'GA4 last 30 days' or null",
      "weight": 0.0_to_1.0
    }}
  ],
  "assumptions": ["list of assumptions you had to make"],
  "data_gaps": ["what data would make this analysis stronger"],
  "recommendations": [
    {{
      "action": "specific action to take",
      "rationale": "why this action",
      "expected_impact": "high | medium | low",
      "effort": "low | medium | high",
      "timeframe": "this week | next 30 days | Q1 | etc"
    }}
  ],
  "used_real_data": true_or_false,
  "used_benchmarks": true_or_false,
  "used_frameworks": true_or_false
}}

CRITICAL RULES:
1. If you don't have real data, say so in data_gaps. Don't fabricate numbers.
2. Every claim in evidence MUST have an honest source. "inferred" is fine if that's the truth.
3. Be specific in recommendations. Vague advice is useless.
4. Return ONLY the JSON object. No prose before or after. No markdown code fences."""


def run_agent_structured(
    agent_id: str,
    user_message: str,
    conversation_id: str = "default",
    other_agent_outputs: Optional[List[AgentOutput]] = None,
    is_synthesis: bool = False,
) -> AgentOutput:
    """
    Run an agent and parse structured output. Falls back gracefully if
    JSON parsing fails — agent still returns AgentOutput, just with lower
    confidence and conclusion = raw text.
    """
    ctx = get_context(conversation_id)
    context_header = ctx.context_header()

    system = get_prompt(agent_id)
    structured_prompt = _build_structured_prompt(agent_id, user_message, context_header)

    # Classify which tier this call lands on (for the response)
    tier = classify_task(user_message, agent_id, is_synthesis)

    raw_response = call_model(
        prompt=structured_prompt,
        agent_id=agent_id,
        system=system + "\n\nALWAYS return JSON only. No markdown fences.",
        max_tokens=2500,
        temperature=0.5,
        json_mode=True,
        user_message=user_message,
        is_synthesis=is_synthesis,
    )

    parsed = _safe_parse_json(raw_response)

    if parsed:
        try:
            output = AgentOutput(
                agent_id=agent_id,
                conclusion=parsed.get("conclusion", ""),
                summary=parsed.get("summary", ""),
                evidence=[Evidence(**e) for e in parsed.get("evidence", [])],
                assumptions=parsed.get("assumptions", []),
                data_gaps=parsed.get("data_gaps", []),
                recommendations=[Recommendation(**r) for r in parsed.get("recommendations", [])],
                used_real_data=parsed.get("used_real_data", False),
                used_benchmarks=parsed.get("used_benchmarks", False),
                used_frameworks=parsed.get("used_frameworks", False),
                tier_used=tier,
            )
        except Exception as e:
            logger.warning(f"[{agent_id}] schema validation failed: {e}")
            output = _fallback_output(agent_id, raw_response, tier)
    else:
        logger.warning(f"[{agent_id}] could not parse JSON, falling back to text")
        output = _fallback_output(agent_id, raw_response, tier)

    output.confidence = compute_confidence(output, other_agent_outputs or [])

    return output


def _safe_parse_json(raw: str) -> Optional[Dict]:
    """Try multiple strategies to extract JSON."""
    if not raw:
        return None

    raw = raw.strip()

    # Strip common markdown fences
    if raw.startswith("```"):
        parts = raw.split("```", 2)
        if len(parts) >= 2:
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        else:
            return None

    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try finding the first { and last }
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _fallback_output(agent_id: str, raw: str, tier: int = 1) -> AgentOutput:
    """When JSON parsing fails, salvage what we can."""
    text = raw if raw and not raw.startswith("[") else "Agent could not generate a structured response."

    return AgentOutput(
        agent_id=agent_id,
        conclusion=text[:200] if len(text) > 200 else text,
        summary=text,
        evidence=[Evidence(claim="Unstructured response", source="inferred", weight=0.3)],
        assumptions=["Response could not be parsed as structured data"],
        data_gaps=["Agent did not provide evidence trail"],
        used_real_data=False,
        used_benchmarks=False,
        used_frameworks=False,
        tier_used=tier,
    )
