"""
Pydantic response schemas for structured agent outputs.
Used to enforce valid JSON structure from agent LLM calls.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class KeywordItem(BaseModel):
    keyword: str
    search_intent: str  # informational / commercial / transactional / navigational
    competition: str    # low / medium / high
    priority: str       # quick-win / medium-term / long-term


class SEOResponse(BaseModel):
    summary: str = Field(..., description="1-2 sentence summary of the SEO opportunity")
    top_keywords: List[KeywordItem] = Field(default_factory=list, max_items=5)
    technical_issues: List[str] = Field(default_factory=list, max_items=5)
    quick_wins: List[str] = Field(default_factory=list, max_items=3)


class ContentItem(BaseModel):
    title: str
    format: str        # blog / video / infographic / case-study / email
    target_keyword: Optional[str] = None
    angle: str


class ContentResponse(BaseModel):
    summary: str
    recommendations: List[ContentItem] = Field(default_factory=list, max_items=5)
    content_gaps: List[str] = Field(default_factory=list, max_items=3)


class PPCResponse(BaseModel):
    summary: str
    recommended_channels: List[str]
    budget_split: dict  # {"Google Ads": "60%", "Meta": "40%"}
    ad_copy_hooks: List[str] = Field(default_factory=list, max_items=3)
    expected_cpc_range: str


class AnalyticsResponse(BaseModel):
    summary: str
    key_metrics: dict  # {"bounce_rate": "65%", "avg_session": "2:10"}
    trends: List[str] = Field(default_factory=list, max_items=3)
    opportunities: List[str] = Field(default_factory=list, max_items=3)


class CRMResponse(BaseModel):
    summary: str
    email_sequence: List[dict]  # [{"subject": "...", "timing": "Day 1", "goal": "..."}]
    segmentation_tips: List[str] = Field(default_factory=list, max_items=3)


class SMMResponse(BaseModel):
    summary: str
    platform_priorities: List[str]  # ["LinkedIn (primary)", "Instagram (secondary)"]
    post_ideas: List[dict]  # [{"platform": "LinkedIn", "caption": "...", "format": "carousel"}]
    posting_frequency: str


class AuditSection(BaseModel):
    name: str
    score: int  # 0-100
    findings: List[str] = Field(default_factory=list, max_items=3)


class AuditResponse(BaseModel):
    overall_grade: str  # A+, B, C-, etc.
    sections: List[AuditSection] = Field(default_factory=list, max_items=6)
    strengths: List[str] = Field(default_factory=list, max_items=3)
    weaknesses: List[str] = Field(default_factory=list, max_items=3)
    priority_actions: List[str] = Field(default_factory=list, max_items=5)


class GenericResponse(BaseModel):
    summary: str
    recommendations: List[str] = Field(default_factory=list, max_items=5)
    next_steps: List[str] = Field(default_factory=list, max_items=3)


# --------------------------------------------------------
# Schema registry — maps agent_id to schema class
# --------------------------------------------------------

AGENT_SCHEMAS = {
    "seo": SEOResponse,
    "content": ContentResponse,
    "ppc": PPCResponse,
    "analytics": AnalyticsResponse,
    "crm": CRMResponse,
    "smm": SMMResponse,
    "brand": GenericResponse,
    "cro": GenericResponse,
    "web_ux": GenericResponse,
    "research": GenericResponse,
}


def get_schema_prompt(agent_id: str) -> str:
    """Return a JSON schema instruction to append to agent prompts."""
    schema = AGENT_SCHEMAS.get(agent_id)
    if not schema:
        return ""
    fields = list(schema.__fields__.keys())
    example = {f: "..." for f in fields}
    import json
    return (
        f"\n\nIMPORTANT: Respond ONLY with valid JSON matching this structure:\n"
        f"{json.dumps(example, indent=2)}\n"
        f"Do not include any text outside the JSON object."
    )


def parse_agent_response(agent_id: str, text: str):
    """Try to parse agent response as the agent's schema. Returns model instance or None."""
    import json, re
    schema = AGENT_SCHEMAS.get(agent_id)
    if not schema:
        return None

    # Extract JSON from markdown fences or raw
    json_str = text.strip()
    fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_str, re.DOTALL)
    if fence_match:
        json_str = fence_match.group(1)
    elif not json_str.startswith('{'):
        brace_match = re.search(r'\{.*\}', json_str, re.DOTALL)
        if brace_match:
            json_str = brace_match.group(0)

    try:
        data = json.loads(json_str)
        return schema(**data)
    except Exception:
        return None


def _rice_sort_key(rec) -> float:
    """Sort recommendations by RICE proxy (high impact + low effort first)."""
    if not isinstance(rec, dict):
        return 0.0
    effort_map = {"trivial": 5, "low": 4, "medium": 3, "high": 2, "massive": 1}
    impact_keywords = {
        "significant": 3, "major": 3, "substantial": 3,
        "increase": 2, "improve": 2, "boost": 2, "drive": 2,
        "optimize": 1, "enhance": 1, "reduce": 1, "minor": 0,
    }
    effort_score = effort_map.get(str(rec.get("effort", "medium")).lower(), 3)
    impact_text = str(rec.get("impact", "")).lower()
    impact_score = max((v for k, v in impact_keywords.items() if k in impact_text), default=1)
    return float(effort_score * impact_score)


def format_structured_response(model_instance) -> str:
    """
    Convert a structured response (Pydantic model OR plain dict) to readable markdown.
    Recommendations are sorted by RICE proxy (quick wins first).
    """
    if model_instance is None:
        return ""

    # Handle plain dict (from two_step_generator)
    if isinstance(model_instance, dict):
        return _format_dict_response(model_instance)


    cls_name = type(model_instance).__name__
    lines = []

    if cls_name == "SEOResponse":
        lines.append(model_instance.summary)
        if model_instance.top_keywords:
            lines.append("\n**Top Keyword Opportunities:**")
            for kw in model_instance.top_keywords:
                lines.append(f"- **{kw.keyword}** ({kw.search_intent}, {kw.competition} competition) — {kw.priority}")
        if model_instance.technical_issues:
            lines.append("\n**Technical Issues:**")
            for issue in model_instance.technical_issues:
                lines.append(f"- {issue}")
        if model_instance.quick_wins:
            lines.append("\n**Quick Wins:**")
            for win in model_instance.quick_wins:
                lines.append(f"- {win}")

    elif cls_name == "ContentResponse":
        lines.append(model_instance.summary)
        if model_instance.recommendations:
            lines.append("\n**Content Recommendations:**")
            for item in model_instance.recommendations:
                kw_str = f" | Keyword: {item.target_keyword}" if item.target_keyword else ""
                lines.append(f"- **{item.title}** ({item.format}){kw_str}\n  {item.angle}")
        if model_instance.content_gaps:
            lines.append("\n**Content Gaps:**")
            for gap in model_instance.content_gaps:
                lines.append(f"- {gap}")

    elif cls_name == "PPCResponse":
        lines.append(model_instance.summary)
        lines.append(f"\n**Recommended Channels:** {', '.join(model_instance.recommended_channels)}")
        if model_instance.budget_split:
            lines.append("\n**Budget Split:**")
            for channel, pct in model_instance.budget_split.items():
                lines.append(f"- {channel}: {pct}")
        lines.append(f"\n**Expected CPC:** {model_instance.expected_cpc_range}")
        if model_instance.ad_copy_hooks:
            lines.append("\n**Ad Copy Hooks:**")
            for hook in model_instance.ad_copy_hooks:
                lines.append(f"- {hook}")

    elif cls_name == "AuditResponse":
        lines.append(f"**Overall Grade: {model_instance.overall_grade}**")
        if model_instance.sections:
            lines.append("\n**Section Scores:**")
            for sec in model_instance.sections:
                lines.append(f"- {sec.name}: {sec.score}/100")
        if model_instance.strengths:
            lines.append("\n**Strengths:**")
            for s in model_instance.strengths:
                lines.append(f"- {s}")
        if model_instance.weaknesses:
            lines.append("\n**Weaknesses:**")
            for w in model_instance.weaknesses:
                lines.append(f"- {w}")
        if model_instance.priority_actions:
            lines.append("\n**Priority Actions:**")
            for i, action in enumerate(model_instance.priority_actions, 1):
                lines.append(f"{i}. {action}")

    else:
        # GenericResponse and others
        if hasattr(model_instance, 'summary'):
            lines.append(model_instance.summary)
        if hasattr(model_instance, 'recommendations') and model_instance.recommendations:
            lines.append("\n**Recommendations:**")
            for rec in model_instance.recommendations:
                if isinstance(rec, str):
                    lines.append(f"- {rec}")
        if hasattr(model_instance, 'next_steps') and model_instance.next_steps:
            lines.append("\n**Next Steps:**")
            for step in model_instance.next_steps:
                lines.append(f"- {step}")

    return "\n".join(lines)


def _format_dict_response(data: dict) -> str:
    """Format a plain dict response (from two_step_generator) to markdown."""
    lines = []

    if data.get("summary"):
        lines.append(data["summary"])

    # Keywords (SEO)
    if data.get("keywords"):
        lines.append("\n**Top Keywords:**")
        for kw in data["keywords"][:5]:
            if isinstance(kw, dict):
                lines.append(f"- **{kw.get('keyword', kw)}** — {kw.get('reasoning', kw.get('intent', ''))}")
            else:
                lines.append(f"- {kw}")

    # Content ideas
    if data.get("ideas"):
        lines.append("\n**Content Ideas:**")
        for idea in data["ideas"][:5]:
            if isinstance(idea, dict):
                kw_str = f" | `{idea['target_keyword']}`" if idea.get("target_keyword") else ""
                lines.append(f"- **{idea.get('title', idea)}** ({idea.get('format', '')}){kw_str}")
            else:
                lines.append(f"- {idea}")

    # Email sequence (CRM)
    if data.get("email_sequence"):
        lines.append("\n**Email Sequence:**")
        for email in data["email_sequence"][:5]:
            if isinstance(email, dict):
                lines.append(f"- **{email.get('timing', '')}** — {email.get('subject', email.get('purpose', ''))}")
            else:
                lines.append(f"- {email}")

    # MECLABS score (CRO)
    if data.get("meclabs_score"):
        ms = data["meclabs_score"]
        lines.append(f"\n**MECLABS Score:** {ms.get('total', '?')}/86 ({ms.get('grade', '?')})")

    # Post ideas (SMM)
    if data.get("post_ideas"):
        lines.append("\n**Post Ideas:**")
        for post in data["post_ideas"][:4]:
            if isinstance(post, dict):
                lines.append(f"- **{post.get('platform', '')}** ({post.get('format', '')}): {post.get('content', '')}")
            else:
                lines.append(f"- {post}")

    # Recommendations — RICE sorted (quick wins first)
    recs = data.get("recommendations", [])
    if recs:
        if isinstance(recs[0], dict):
            recs = sorted(recs, key=_rice_sort_key, reverse=True)
        lines.append("\n**Recommendations:**")
        for rec in recs[:5]:
            if isinstance(rec, dict):
                action = rec.get("action", str(rec))
                impact = rec.get("impact", "")
                effort = rec.get("effort", "")
                timeline = rec.get("timeline", "")
                meta = " | ".join(filter(None, [effort and f"{effort} effort", timeline]))
                lines.append(f"- {action}" + (f" → {impact}" if impact else "") + (f" _{meta}_" if meta else ""))
            else:
                lines.append(f"- {rec}")

    # Next steps
    if data.get("next_steps"):
        lines.append("\n**Would you like me to:**")
        for step in data["next_steps"][:3]:
            lines.append(f"- {step}")

    # Raw fallback
    if not lines and data.get("_raw_analysis"):
        return data["_raw_analysis"]

    return "\n".join(lines)
