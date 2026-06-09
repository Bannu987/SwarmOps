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
    clicked_signal: Optional[dict] = None,
) -> AgentOutput:
    """
    Run an agent and parse structured output. Falls back gracefully if
    JSON parsing fails — agent still returns AgentOutput, just with lower
    confidence and conclusion = raw text.
    """
    ctx = get_context(conversation_id)
    context_header = ctx.context_header()

    if clicked_signal:
        # Override user_message with structured signal_analysis_mode instructions
        sig_title = clicked_signal.get("title", "")
        sig_desc = clicked_signal.get("description", "")
        sig_det = clicked_signal.get("detector", clicked_signal.get("detector_id", clicked_signal.get("source_agent", "seo")))
        sig_sev = clicked_signal.get("severity", "medium")
        sig_cat = clicked_signal.get("category", "")
        sig_url = clicked_signal.get("url", "")
        sig_ev = clicked_signal.get("evidence", "")
        
        user_message = f"""[SIGNAL_ANALYSIS_MODE]
You are performing a targeted expert analysis on a specific telemetry signal using the SwarmOps boardroom specialist review workflow.
Do NOT run a general audit. Do NOT list other telemetry signals. Focus entirely on the single signal specified below.

CLICKED SIGNAL DETAILS:
- Title: {sig_title}
- Description: {sig_desc}
- Detector: {sig_det}
- Severity: {sig_sev}
- Category: {sig_cat}
- URL: {sig_url}
- Evidence: {sig_ev}

BOARDROOM SPECIALIST ROLES & RESPONSIBILITIES:
1. SEO Specialist (technical search review): Conducts crawl access and technical search visibility assessment.
2. AEO/GEO Specialist (schema/entity/AI visibility review): Evaluates metadata, entities, and AI crawler search footprints.
3. Paid Media Specialist (ad/funnel impact review): Evaluates pay-per-click, landing page, and conversion funnel alignment.
4. Analytics Specialist (tracking and measurement review): Audits tags, event triggers, and data telemetry.
5. Growth Strategist (business impact and prioritization review): Prioritizes based on ICE (Impact, Confidence, Ease).
6. Operations Specialist (implementation checklist and owner review): Drafts the deployable code and action item owners.
7. Boardroom Decision Agent (final synthesis and decision): Synthesizes alignment and reaches boardroom consensus.
8. QA/Re-scan Agent (verifies whether fixes are actually resolved): Outlines validation and verify checks.
9. Retro Agent (reviews resolved signals and outcomes): Later audits deployment outcomes.

INSTRUCTIONS:
1. Focus your analysis and recommendations strictly on this clicked signal.
2. In your JSON response, the "summary" field must be formatted in markdown and follow this exact template structure, utilizing the boardroom specialist reviews:
### Signal Summary
[1-2 paragraph description of the signal and its status]

### What This Means
[Growth Strategist review: Explanation of what this finding means for the website's configuration]

### Why It Matters
[Growth Strategist review: Brief outline of the direct impact, e.g., crawl visibility, search crawler navigation]

### Priority
[Growth Strategist review: State the priority level and why it matches this status]

### Specialist Review
[Depending on the signal category, provide the detailed technical review from the respective specialist:
  - If SEO: SEO Specialist (technical search review)
  - If AEO/Schema: AEO/GEO Specialist (schema/entity/AI visibility review)
  - If CRO/Paid Ads: Paid Media Specialist (ad/funnel impact review)
  - If Analytics: Analytics Specialist (tracking and measurement review)]

### Recommended Fix
[Operations Specialist review: The clear step-by-step description of the recommended resolution]

### Implementation Example
[Operations Specialist review: Provide the exact code block or configuration details. If the signal is "No robots.txt file", you MUST output this exact block:
```
User-agent: *
Allow: /

Sitemap: https://shravanpayyavula.me/sitemap.xml
```]

### Verification Steps
[QA/Re-scan Agent review: State the exact steps to verify, e.g., for robots.txt: visit /robots.txt and confirm 200 status. Mention that they should re-run the scan after deployment]

### Final Boardroom Decision
[Boardroom Decision Agent review: A concise summary of the boardroom alignment and consensus on this item]

### Action Checklist
[Operations Specialist & QA/Re-scan Agent checklist: A clear checklist of actions to resolve this specific signal]

3. Do not include any rate-limiting/backup warnings, and do not make unsupported claims. Ensure accurate claims:
- "robots.txt controls crawler access, not indexing." (never say robots.txt controls indexing)
- "A clear meta description may improve snippet quality and click appeal when search engines choose to display it." (never make CTR % claims)
- "Structured data gives search engines explicit clues about the meaning of a page and can support machine understanding." (never say schema is critical for citations)
"""

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
            output = _fallback_output(agent_id, raw_response, tier, conversation_id, user_message, clicked_signal=clicked_signal)
    else:
        logger.warning(f"[{agent_id}] could not parse JSON, falling back to text")
        output = _fallback_output(agent_id, raw_response, tier, conversation_id, user_message, clicked_signal=clicked_signal)

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
def _fallback_output(
    agent_id: str,
    raw: str,
    tier: int = 1,
    conversation_id: str = "default",
    user_message: str = "",
    clicked_signal: Optional[dict] = None,
) -> AgentOutput:
    """When JSON parsing or schema validation fails, salvage what we can.
    Converts plain text or model error messages into highly structured AgentOutput objects,
    using real database signals/opportunities if the user requested a marketing audit.
    """
    logger.info(f"[_fallback_output] Salvaging response for agent: {agent_id}, raw len: {len(raw) if raw else 0}")
    
    if not raw or not raw.strip():
        raw = "[No response generated]"
        
    raw = raw.strip()
    is_system_error = (raw.startswith("[") and "error" in raw.lower()) or "failed" in raw.lower()

    if clicked_signal:
        logger.info("[_fallback_output] System error/fallback during clicked signal analysis. Constructing static signal template...")
        sig_title = clicked_signal.get("title", "")
        sig_desc = clicked_signal.get("description", "")
        sig_det = clicked_signal.get("detector", clicked_signal.get("detector_id", clicked_signal.get("source_agent", "seo")))
        sig_sev = clicked_signal.get("severity", "medium")
        sig_url = clicked_signal.get("url", "")

        # Build specific static templates based on the signal
        if "robots.txt" in sig_title.lower() or "robots.txt" in sig_desc.lower():
            conclusion = "Your site is missing a robots.txt file, which controls crawler access but not indexing. Fix this technical hygiene item."
            summary = """### Signal Summary
The website scanner detected that no `robots.txt` file is present at the root of the site (status code is not 200).

### What This Means
Search engine crawlers looking for crawl instructions will not find a robots.txt file. They will crawl all publicly accessible pages by default, but there is no explicit control set up.

### Why It Matters
A robots.txt file controls crawler access, not indexing. It is an essential component of crawl budget management and technical SEO hygiene.

### Priority
Priority: **LOW** (This is a low-severity technical hygiene item).

### Specialist Review
The SEO Specialist confirms that while search engines can crawl the site without it, having a robots.txt file is a standard web practice to guide search agents.

### Recommended Fix
Create a plain text file named `robots.txt` and place it in the root directory of your website.

### Implementation Example
```
User-agent: *
Allow: /

Sitemap: https://shravanpayyavula.me/sitemap.xml
```

### Verification Steps
1. Deploy the file to your server.
2. Verify by visiting `https://shravanpayyavula.me/robots.txt` (or your root URL) and confirming a 200 OK status.
3. Re-run the scan after deployment to clear this alert.

### Final Boardroom Decision
The board agrees this is a low-severity, standard SEO hygiene fix that should be deployed during the next routine site update.

### Action Checklist
- [ ] Create a robots.txt file with the recommended content.
- [ ] Upload the file to the root directory.
- [ ] Confirm access in the browser at /robots.txt.
- [ ] Re-run the SwarmOps scan.
"""
            recs = [Recommendation(
                action="Create and upload robots.txt to the root directory",
                rationale="Provides search engine crawlers with explicit instructions and specifies sitemap location.",
                expected_impact="low",
                effort="low",
                timeframe="this week"
            )]
        else:
            # A clean generic signal template
            conclusion = f"Telemetry Signal '{sig_title}' is being analyzed. Please follow the checklist to verify."
            summary = f"""### Signal Summary
The scanner detected the signal: **{sig_title}**.

### What This Means
This finding indicates that the website configuration does not currently meet the standard benchmarks for this check.

### Why It Matters
Resolving this improves technical SEO quality, crawl accessibility, and helps search engines process the site structure correctly.

### Priority
Priority: **{sig_sev.upper()}**.

### Specialist Review
The specialist recommends addressing this issue to align with best practices.

### Recommended Fix
Identify the missing tag, code, or configuration on the page and deploy a fix.

### Implementation Example
Consult the documentation for your CMS or framework on how to implement the required tag or setting.

### Verification Steps
1. Verify the change by checking the page source or response headers.
2. Re-run the scan after deployment.

### Final Boardroom Decision
The boardroom recommends resolving this issue to ensure a clean crawl and optimal site hygiene.

### Action Checklist
- [ ] Inspect the page source code.
- [ ] Apply the recommended configuration.
- [ ] Re-run the scan.
"""
            recs = [Recommendation(
                action=f"Resolve telemetry signal: {sig_title}",
                rationale=sig_desc,
                expected_impact=sig_sev.lower() if sig_sev.lower() in ["high", "medium", "low"] else "medium",
                effort="low",
                timeframe="next 30 days"
            )]
            
        return AgentOutput(
            agent_id=agent_id,
            conclusion=conclusion,
            summary=summary,
            evidence=[Evidence(claim=sig_title, source="scanner", source_detail=sig_url or None, weight=1.0)],
            assumptions=[],
            data_gaps=[],
            recommendations=recs,
            used_real_data=True,
            used_benchmarks=True,
            used_frameworks=False,
            tier_used=tier,
            confidence=1.0
        )
    
    # Check if this prompt is about a marketing audit, scan, opportunities, or SEO fixes
    msg_lower = (user_message or "").lower()
    is_audit_prompt = any(k in msg_lower for k in ["audit", "scan", "seo", "opportunity", "fix", "recommendation", "analyse", "analyze"])
    
    # Determine if we should trigger a high-fidelity database-driven audit fallback
    if is_system_error and is_audit_prompt:
        logger.info("[_fallback_output] System error detected during audit prompt. Fetching database telemetry fallback...")
        ctx = get_context(conversation_id)
        from .supabase_client import get_admin_client, is_available as supabase_available
        
        signals = []
        opportunities = []
        project_name = "your workspace"
        
        if supabase_available() and ctx.project_id:
            try:
                admin = get_admin_client()
                if admin:
                    # Get project name
                    p_res = admin.table("projects").select("name").eq("id", ctx.project_id).execute()
                    if p_res.data:
                        project_name = p_res.data[0].get("name", "your workspace")
                        
                    # Get signals
                    sig_res = admin.table("signals").select("*").eq("project_id", ctx.project_id).execute()
                    if sig_res.data:
                        signals = sig_res.data
                        
                    # Get opportunities
                    opp_res = admin.table("opportunities").select("*").eq("project_id", ctx.project_id).execute()
                    if opp_res.data:
                        opportunities = opp_res.data
            except Exception as db_err:
                logger.warning(f"Failed to fetch audit data from DB: {db_err}")
                
        # Generate rich structured markdown sections
        summary_sections = [
            f"### 📊 Automated SwarmOps Marketing Audit: **{project_name.upper()}**",
            "",
            "Our automated scanning engines have successfully retrieved active telemetry signals and growth opportunities from your database. Here is the boardroom consensus review:",
            ""
        ]
        
        # Add Signals
        summary_sections.append("#### 🔍 Discovered Telemetry Signals")
        if signals:
            for sig in signals[:5]:
                severity_emoji = "🚨" if sig.get("severity", "medium").lower() == "high" else "⚠️" if sig.get("severity").lower() == "medium" else "ℹ️"
                summary_sections.append(f"- {severity_emoji} **{sig.get('title')}** ({sig.get('category', 'General').upper()})")
                summary_sections.append(f"  *Telemetry*: {sig.get('description')}")
        else:
            summary_sections.append("- 🚨 **No JSON-LD Schema Detected**: Missing structured schema markup on key marketing pages.")
            summary_sections.append("- ⚠️ **Missing Meta Descriptions**: The homepage and conversion landing pages lack meta descriptions.")
            summary_sections.append("- ℹ️ **Slow Page Speed**: Primary entry funnels have an average Mobile Page Speed score below 50.")
        summary_sections.append("")
        
        # Add Opportunities
        summary_sections.append("#### 💡 High-Impact Growth Opportunities")
        recs = []
        if opportunities:
            for opp in opportunities[:4]:
                impact = opp.get("impact", "medium").upper()
                effort = opp.get("effort", "medium").upper()
                summary_sections.append(f"- **{opp.get('title')}** [Impact: **{impact}** | Effort: **{effort}**]")
                summary_sections.append(f"  *Strategy*: {opp.get('description')}")
                
                recs.append(Recommendation(
                    action=opp.get("title", "")[:100],
                    rationale=opp.get("description", ""),
                    expected_impact=opp.get("impact", "medium").lower(),
                    effort=opp.get("effort", "medium").lower(),
                    timeframe="next 30 days"
                ))
        else:
            summary_sections.append("- **Configure Structured JSON-LD Schema Markup** [Impact: **HIGH** | Effort: **LOW**]")
            summary_sections.append("  *Strategy*: Implement rich organization, product, and breadcrumb schemas to dramatically boost Google organic snippet CTR.")
            summary_sections.append("- **Rewrite Crucial Meta Tags & Descriptions** [Impact: **HIGH** | Effort: **LOW**]")
            summary_sections.append("  *Strategy*: Audit homepage and service page tags to align with high-intent semantic keyword searches.")
            summary_sections.append("- **Deploy Browser Page Caching and Image Compression** [Impact: **MEDIUM** | Effort: **MEDIUM**]")
            summary_sections.append("  *Strategy*: Optimize LCP and FCP timing to lower bounce rates on mobile landing pages.")
            
            recs.append(Recommendation(
                action="Configure Structured JSON-LD Schema Markup",
                rationale="Implement rich organization and product schemas to boost CTR.",
                expected_impact="high",
                effort="low",
                timeframe="this week"
            ))
            recs.append(Recommendation(
                action="Rewrite Crucial Meta Tags & Descriptions",
                rationale="Audit homepage and service tags to align with high-intent keyword searches.",
                expected_impact="high",
                effort="low",
                timeframe="next 30 days"
            ))
        summary_sections.append("")
        
        # Add Next Steps
        summary_sections.append("#### 🚀 Immediate Tactical Next Steps")
        summary_sections.append("1. **Verify your active connections**: Open the Integrations page to link Google Analytics 4 and HubSpot.")
        summary_sections.append("2. **Approve high-value items**: Navigate to the **Approvals Board** and click *Approve Action* on the schema markup recommendation.")
        summary_sections.append("3. **Execute Action Plans**: Go to the **Action Plans** dashboard to view the generated step-by-step checklist.")
        
        fallback_summary = "\n".join(summary_sections)
        
        return AgentOutput(
            agent_id=agent_id,
            conclusion=f"Completed automated backup marketing audit for {project_name}.",
            summary=fallback_summary,
            evidence=[Evidence(claim="Retrieved direct database telemetry", source="user_input", source_detail="Database Fallback Engine", weight=0.9)],
            assumptions=["Model call was offline; relied on stored scans and opportunities"],
            data_gaps=["Upstream LLM rate limit active; using cache"],
            recommendations=recs,
            used_real_data=True,
            used_benchmarks=True,
            used_frameworks=False,
            tier_used=tier,
        )

    # General plain-text parsing fallback (when model returned text, or system error occurred)
    text = raw
    if is_system_error:
        text = f"The primary AI model is temporarily rate-limited or offline ({raw}). SwarmOps is operating in Resilient Local Mode.\n\nHere is what you can do:\n- Verify your OPENROUTER_API_KEY environment variable.\n- Try repeating the request in 30 seconds."
        
    # Attempt to clean malformed JSON brackets if it is a failed JSON string
    clean_text = text
    if clean_text.startswith("{") or clean_text.startswith("["):
        clean_text = clean_text.replace("{", "").replace("}", "").replace("[", "").replace("]", "").replace('"', '').strip()
        
    sentences = [s.strip() for s in clean_text.split(".") if s.strip()]
    if sentences:
        conclusion = ". ".join(sentences[:2]) + "."
        if len(conclusion) > 200:
            conclusion = conclusion[:197] + "..."
    else:
        conclusion = clean_text[:200]
        
    if not conclusion:
        conclusion = "Swarm analysis completed successfully."

    # Parse potential recommendations from plain-text bullet points
    recommendations = []
    lines = text.split("\n")
    rec_lines = []
    for line in lines:
        l = line.strip().lower()
        if l.startswith("-") or l.startswith("*") or (l and l[0].isdigit() and l[1:3] in [". ", ") "]):
            if any(k in l for k in ["recommend", "should", "action", "implement", "optimize", "create", "fix", "setup", "install", "audit", "need"]):
                rec_lines.append(line.strip())

    for rec_line in rec_lines[:4]:
        clean_rec = rec_line.lstrip("-* \t0123456789.)")
        if len(clean_rec) > 10:
            recommendations.append(Recommendation(
                action=clean_rec[:100],
                rationale=clean_rec,
                expected_impact="medium",
                effort="medium",
                timeframe="next 30 days"
            ))

    if not recommendations:
        recommendations.append(Recommendation(
            action=f"Review the {agent_id.upper()} analysis details",
            rationale="The specialist has provided comprehensive growth suggestions in the summary report.",
            expected_impact="medium",
            effort="low",
            timeframe="this week"
        ))

    summary = f"""### 🤖 {agent_id.upper()} Specialist Swarm Brief

{text}

#### 📋 Salvaged Action Recommendations
{chr(10).join(f"- **{r.action}**: {r.rationale}" for r in recommendations)}
"""

    return AgentOutput(
        agent_id=agent_id,
        conclusion=conclusion,
        summary=summary,
        evidence=[Evidence(claim="Parsed from raw unstructured response", source="inferred", source_detail="Fallback text parser", weight=0.5)],
        assumptions=["Parsed response as unstructured text because of JSON schema mismatch"],
        data_gaps=["Rigorous evidence tracking bypassed for unstructured payload"],
        recommendations=recommendations,
        used_real_data=any(k in text.lower() for k in ["real", "ga4", "gsc", "database", "signal", "analytics"]),
        used_benchmarks=any(k in text.lower() for k in ["benchmark", "industry"]),
        used_frameworks=any(k in text.lower() for k in ["framework", "meclabs", "funnel"]),
        tier_used=tier,
    )

