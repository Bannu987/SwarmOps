"""
Two-Step Generation Pattern for SwarmOps agents.

Step 1: LLM reasons freely (no JSON constraint) — better analysis quality.
Step 2: Fast model extracts structured data from the free text.

Research shows two-pass generation outperforms single-pass structured
generation because the LLM doesn't have to simultaneously think AND format.
"""
import json
import re
import logging

logger = logging.getLogger(__name__)


def two_step_generate(reasoning_fn, formatting_fn, reasoning_prompt,
                      schema_template, brand_context=""):
    """
    Execute two-step generation.

    Args:
        reasoning_fn: function(prompt) -> str  (primary LLM, free reasoning)
        formatting_fn: function(prompt) -> str  (fast model for JSON extraction)
        reasoning_prompt: full prompt for step 1
        schema_template: dict showing the expected JSON structure
        brand_context: brand context string to inject

    Returns:
        dict: parsed structured data, or fallback with raw text
    """
    # STEP 1: Free reasoning — no JSON constraint
    step1_prompt = (
        f"{brand_context}\n\n{reasoning_prompt}"
        if brand_context
        else reasoning_prompt
    )
    step1_prompt += (
        "\n\nThink through this carefully. Provide your complete analysis with "
        "specific recommendations. Be detailed and reference the brand specifically. "
        "Do NOT format as JSON. Write naturally."
    )

    try:
        raw_analysis = reasoning_fn(step1_prompt)
    except Exception as e:
        logger.error(f"Two-step step 1 failed: {e}")
        return {"summary": "Analysis could not be completed.", "recommendations": [], "next_steps": []}

    if not raw_analysis or len(str(raw_analysis).strip()) < 30:
        return {"summary": "Analysis produced insufficient results.", "recommendations": [], "next_steps": []}

    raw_analysis = str(raw_analysis)

    # STEP 2: Extract structured data from the free text
    schema_json = json.dumps(schema_template, indent=2)

    step2_prompt = (
        f"Extract structured data from this analysis.\n"
        f"Return ONLY valid JSON matching this exact schema:\n\n"
        f"{schema_json}\n\n"
        f"Analysis to extract from:\n---\n{raw_analysis[:3000]}\n---\n\n"
        f"Rules:\n"
        f"- Extract real data from the analysis above. Do NOT invent new information.\n"
        f"- Every field must be populated. Use empty lists [] if no items found.\n"
        f"- Keep text concise — summaries under 100 words, recs under 30 words each.\n"
        f"- Return ONLY the JSON object. No markdown fences. No commentary."
    )

    try:
        formatted = formatting_fn(step2_prompt)
        text = str(formatted).strip()
        # Strip markdown fences
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Two-step step 2 failed: {e}")

    # Fallback: return raw analysis in generic wrapper
    return {
        "summary": raw_analysis[:500],
        "recommendations": [],
        "next_steps": ["Ask me to elaborate on any specific area"],
        "_raw_analysis": raw_analysis,
    }


# -----------------------------------------------------------------------
# Schema templates for each agent type
# -----------------------------------------------------------------------

AGENT_SCHEMA_TEMPLATES = {
    "seo": {
        "summary": "2-3 sentence SEO overview",
        "keywords": [
            {"keyword": "example", "intent": "commercial", "competition": "medium",
             "priority": "high", "reasoning": "why this matters"}
        ],
        "recommendations": [
            {"action": "specific action", "impact": "expected result",
             "effort": "low", "timeline": "2-4 weeks"}
        ],
        "next_steps": ["suggested follow-up 1", "suggested follow-up 2"],
    },

    "content": {
        "summary": "2-3 sentence content strategy overview",
        "ideas": [
            {"title": "Article Title", "format": "blog post",
             "target_keyword": "keyword", "angle": "unique hook"}
        ],
        "recommendations": [
            {"action": "specific action", "impact": "expected result",
             "effort": "low", "timeline": "2-4 weeks"}
        ],
        "next_steps": ["suggested follow-up 1", "suggested follow-up 2"],
    },

    "ppc": {
        "summary": "2-3 sentence PPC strategy overview",
        "recommended_channels": ["Google Ads", "LinkedIn Ads"],
        "budget_recommendation": "$X/month split across channels",
        "keywords_to_target": ["keyword 1", "keyword 2"],
        "ad_copy_ideas": ["headline idea 1", "headline idea 2"],
        "recommendations": [
            {"action": "specific action", "impact": "expected result",
             "effort": "low", "timeline": "2-4 weeks"}
        ],
        "next_steps": ["suggested follow-up 1"],
    },

    "analytics": {
        "summary": "2-3 sentence analysis overview",
        "computed_metrics": {"metric_name": "value"},
        "insights": ["insight 1", "insight 2"],
        "recommendations": [
            {"action": "specific action", "impact": "expected result",
             "effort": "low", "timeline": "2-4 weeks"}
        ],
        "next_steps": ["suggested follow-up 1"],
    },

    "cro": {
        "summary": "2-3 sentence CRO overview",
        "meclabs_score": {
            "motivation": 7, "value_proposition": 6, "incentive": 5,
            "friction": 4, "anxiety": 3, "total": 52, "grade": "Moderate",
        },
        "lift_model": {
            "weakest_driver": "clarity",
            "strongest_inhibitor": "anxiety",
            "priority_fix": "Improve headline clarity",
        },
        "recommendations": [
            {"action": "specific action", "impact": "expected result",
             "effort": "low", "timeline": "2-4 weeks"}
        ],
        "next_steps": ["suggested follow-up 1"],
    },

    "crm": {
        "summary": "2-3 sentence CRM/email strategy overview",
        "email_sequence": [
            {"subject": "Email subject", "timing": "Day 1", "purpose": "Introduction"}
        ],
        "recommendations": [
            {"action": "specific action", "impact": "expected result",
             "effort": "low", "timeline": "2-4 weeks"}
        ],
        "next_steps": ["suggested follow-up 1"],
    },

    "smm": {
        "summary": "2-3 sentence social strategy overview",
        "platform_priorities": ["LinkedIn", "Twitter"],
        "post_ideas": [
            {"platform": "LinkedIn", "content": "Post idea", "format": "carousel"}
        ],
        "recommendations": [
            {"action": "specific action", "impact": "expected result",
             "effort": "low", "timeline": "2-4 weeks"}
        ],
        "next_steps": ["suggested follow-up 1"],
    },

    "generic": {
        "summary": "2-3 sentence overview",
        "recommendations": [
            {"action": "specific action", "impact": "expected result",
             "effort": "low", "timeline": "2-4 weeks"}
        ],
        "next_steps": ["suggested follow-up 1"],
    },
}


def get_schema_template(agent_id: str) -> dict:
    """Get the appropriate schema template for an agent."""
    return AGENT_SCHEMA_TEMPLATES.get(agent_id, AGENT_SCHEMA_TEMPLATES["generic"])
