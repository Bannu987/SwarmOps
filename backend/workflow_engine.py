"""
DAG Workflow Engine for SwarmOps v3.
Code controls which agents run. LLM only generates text.
"""
import re
import time
import logging
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Make sure backend dir is on path so quality_gate is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


# ============================================================
# WORKFLOW BLUEPRINTS
# ============================================================

WORKFLOWS = {
    "keyword_research": {
        "agents": ["seo"],
        "parallel": False,
        "sub_prompts": {
            "seo": "Find the top keyword opportunities for this business. Include search intent, competition level, and priority ranking.",
        },
        "synthesis_instruction": None,
    },
    "content_strategy": {
        "agents": ["research", "seo", "content"],
        "parallel": True,
        "sub_prompts": {
            "research": "Research the competitive content landscape. What topics do competitors cover? What content gaps exist?",
            "seo": "Identify top keywords and content opportunities based on search volume and competition.",
            "content": "Suggest specific blog post titles, formats, and angles that would resonate with this audience.",
        },
        "synthesis_instruction": "Combine competitive research, keyword data, and content ideas into ONE unified content strategy. For each recommended article: include title, target keyword, and a 40-word inverted pyramid intro (answer first, context second). Suggest 3 FAQ pairs that should be added as JSON-LD schema. Prioritize by impact. Give 5 specific article recommendations.",
    },
    "lead_generation": {
        "agents": ["cro", "ppc", "content", "crm"],
        "parallel": True,
        "sub_prompts": {
            "cro": "Identify top 3 conversion friction points. Recommend fixes. Keep under 150 words.",
            "ppc": "Recommend paid lead gen strategy: channels, budget, targeting. Keep under 150 words.",
            "content": "Suggest 3 lead magnet ideas with landing page copy hooks. Keep under 150 words.",
            "crm": "Design 3-email nurture sequence for new leads. Include subjects. Keep under 150 words.",
        },
        "synthesis_instruction": "Create a lead generation plan combining funnel optimization, paid ads, content, and email nurture. Top 5 actions ranked by impact. Keep under 400 words.",
    },
    "marketing_audit": {
        "agents": ["seo", "content", "cro", "analytics", "research", "brand"],
        "parallel": True,
        "sub_prompts": {
            "seo": "Audit SEO: meta tags, keyword optimization, technical issues. Score 0-100. List top 3 issues. Keep under 150 words.",
            "content": "Audit content: quality, gaps, frequency. Score 0-100. List top 3 issues. Keep under 150 words.",
            "cro": "Audit conversions: CTAs, forms, trust signals, friction. Score 0-100. Use MECLABS equation. Keep under 150 words.",
            "analytics": "Audit analytics setup and data quality. Score 0-100. List top 3 issues. Keep under 150 words.",
            "research": "Identify top 3 competitors and key market gaps. Keep under 150 words.",
            "brand": "Audit brand positioning, messaging clarity, differentiation. Score 0-100. Keep under 150 words.",
        },
        "synthesis_instruction": "Create a marketing audit with: 1) Overall grade (A+ through F), 2) Score for each section (0-100), 3) Top 3 strengths, 4) Top 3 weaknesses, 5) Top 5 priority actions ranked by impact. Keep total response under 500 words.",
    },
    "competitor_analysis": {
        "agents": ["research", "seo", "content"],
        "parallel": True,
        "sub_prompts": {
            "research": "Identify top 3-5 competitors. Analyze their strengths, weaknesses, and market positioning.",
            "seo": "Compare keyword rankings and SEO strategies against competitors.",
            "content": "Analyze competitor content: topics, formats, frequency, and gaps we can exploit.",
        },
        "synthesis_instruction": "Create a competitive intelligence briefing: competitive landscape overview, our advantages, our vulnerabilities, and 5 specific actions to gain market share.",
    },
    "growth_plan": {
        "agents": ["seo", "content", "ppc", "crm", "analytics"],
        "parallel": True,
        "sub_prompts": {
            "seo": "Recommend top 3 organic growth actions for the next 3 months. Include keywords. Keep under 150 words.",
            "content": "Recommend 3 content initiatives: pillar pages, blog posts. Include titles. Keep under 150 words.",
            "ppc": "Recommend paid strategy: channels, budget split, targeting. Keep under 150 words.",
            "crm": "Design email nurture sequence for new leads. 3 emails with subjects. Keep under 150 words.",
            "analytics": "Identify the 3 highest-impact growth levers from available data. Keep under 150 words.",
        },
        "synthesis_instruction": "Create a 3-month growth plan: Month 1 (quick wins), Month 2 (building), Month 3 (scaling). Separate organic vs paid. Include budget estimates. Keep total under 500 words.",
    },
    "social_strategy": {
        "agents": ["smm", "content", "brand"],
        "parallel": True,
        "sub_prompts": {
            "smm": "Recommend social media strategy: platforms, posting frequency, content types, engagement tactics.",
            "content": "Suggest specific post ideas, captions, and content themes for social media.",
            "brand": "Ensure social strategy aligns with brand positioning and voice.",
        },
        "synthesis_instruction": "Create a unified social media strategy. Include platform priorities, content calendar framework, and 5 specific post ideas with captions.",
    },
    "paid_campaign": {
        "agents": ["ppc", "analytics", "cro"],
        "parallel": True,
        "sub_prompts": {
            "ppc": "Design a paid advertising campaign: keywords, ad copy, targeting, budget allocation.",
            "analytics": "Analyze available performance data to inform campaign targeting and budget.",
            "cro": "Recommend landing page optimizations to maximize campaign conversion rate.",
        },
        "synthesis_instruction": "Create a complete paid campaign plan: ad strategy, landing page recommendations, budget breakdown, and expected performance.",
    },
    "aeo_optimization": {
        "agents": ["aeo", "seo", "content"],
        "parallel": True,
        "sub_prompts": {
            "aeo": "Analyze the content/website for AI search optimization. Score AEO readiness 0-100. Identify top 3 improvements. Generate FAQ schema pairs. Keep under 200 words.",
            "seo": "Identify the top entity-building opportunities. What topics need topical authority clusters? What Schema.org markup is missing? Keep under 150 words.",
            "content": "Suggest 3 content pieces optimized for AI citation. Each must use inverted pyramid structure, include citable stats, and target a specific AI query. Keep under 150 words.",
        },
        "synthesis_instruction": "Create an AEO optimization plan: 1) AEO readiness score, 2) Top 5 changes to get cited by AI search engines, 3) Content to create, 4) Schema markup to add. Include the actual JSON-LD code for FAQ schema. Keep under 500 words.",
    },
    "publish_content": {
        "agents": ["content", "seo", "aeo"],
        "parallel": True,
        "sub_prompts": {
            "content": "Write a complete blog post based on the user's request. Include title, intro (inverted pyramid — answer first), body with H2 sections, and conclusion with CTA. Keep under 400 words.",
            "seo": "For this blog post topic, provide: target keyword, meta description (under 155 chars), 3 internal link suggestions, and Schema.org Article markup. Keep under 100 words.",
            "aeo": "Optimize this blog post for AI search: rewrite the intro as inverted pyramid (answer first), suggest 3 FAQ pairs for JSON-LD, and inject one citable statistic. Keep under 150 words.",
        },
        "synthesis_instruction": "Combine into a complete, ready-to-publish blog post. Include the SEO-optimized title, inverted pyramid intro, body content, and end with an FAQ section. Add the JSON-LD schema as a code block at the end. Keep under 600 words.",
    },
    "create_campaign": {
        "agents": ["ppc", "content", "cro"],
        "parallel": True,
        "sub_prompts": {
            "ppc": "Design a Google Ads search campaign: recommend keywords (10 max), daily budget, bidding strategy, targeting. Keep under 150 words.",
            "content": "Write 3 responsive search ad variants. Each must have 3 headlines (30 chars max each) and 2 descriptions (90 chars max each). Keep under 200 words.",
            "cro": "Recommend landing page structure for this campaign: headline, subheadline, 3 bullet points, CTA text, trust signals. Score with MECLABS. Keep under 150 words.",
        },
        "synthesis_instruction": "Create a complete Google Ads campaign plan: keywords, budget, 3 ad variants with headlines/descriptions, and landing page recommendations. Include MECLABS score for the landing page. Format as a deployable campaign brief.",
    },
    "create_email_sequence": {
        "agents": ["crm", "content", "cro"],
        "parallel": True,
        "sub_prompts": {
            "crm": "Design a 3-email nurture sequence: timing (day 1, day 4, day 7), subject lines, purpose of each email, and segment targeting. Keep under 150 words.",
            "content": "Write the body copy for each of the 3 nurture emails. Each under 100 words. Include personalization tokens and clear CTAs. Keep total under 350 words.",
            "cro": "For each email's CTA: recommend button text, placement, and urgency element. Score the sequence's overall conversion probability. Keep under 100 words.",
        },
        "synthesis_instruction": "Create a complete 3-email nurture sequence ready to deploy. For each email include: subject line, send day, full body copy, CTA button text. End with conversion optimization notes.",
    },
    "create_social_posts": {
        "agents": ["smm", "content", "brand"],
        "parallel": True,
        "sub_prompts": {
            "smm": "Recommend which platform to post on and when. Suggest content format (carousel, video, text) and engagement strategy. Keep under 100 words.",
            "content": "Write 3 social media posts for the recommended platform. Each must have a hook in the first line, value in the body, and a CTA. Include hashtags. Keep under 250 words total.",
            "brand": "Review the posts for brand voice consistency and messaging alignment. Flag any issues. Keep under 80 words.",
        },
        "synthesis_instruction": "Present 3 ready-to-post social media posts. For each: platform, content, hashtags, best time to post, and expected engagement. Format so the user can copy-paste directly.",
    },
}


# ============================================================
# SCHEMA HINTS — concise format guidance for single-pass agents
# ============================================================

_SCHEMA_HINTS = {
    "seo": "Format: Start with top 3 keyword opportunities (keyword, intent, competition). Then 3 specific recommendations with expected impact.",
    "content": "Format: Start with content gap analysis. Then suggest 3 specific articles with titles, target keywords, and angles.",
    "ppc": "Format: Recommend channels and budget split. Include 3 specific campaign ideas with targeting and expected ROI.",
    "analytics": "Format: List key metrics to track. Identify 3 data-driven insights. Recommend measurement framework.",
    "cro": "Format: Score using MECLABS (C=4m+3v+2(i-f)-2a). Identify weakest LIFT factor. Give 3 specific conversion fixes.",
    "crm": "Format: Design 3-email nurture sequence with subjects and timing. Recommend lifecycle optimization.",
    "smm": "Format: Recommend top 2 platforms with posting frequency. Give 3 specific post ideas with hooks.",
    "brand": "Format: Evaluate positioning clarity, differentiation, and voice consistency. Give 3 specific improvements.",
    "research": "Format: Identify 3-5 competitors. Compare strengths/weaknesses. Identify 3 market opportunities.",
    "web_ux": "Format: Evaluate load speed, mobile UX, navigation. Identify 3 friction points with fixes.",
    "aeo": "Format: AEO readiness score (0-100), citation probability, top 3 improvements, inverted pyramid intro rewrite, 5 FAQ pairs for JSON-LD schema.",
}


def _get_concise_schema_hint(agent_id: str) -> str:
    return _SCHEMA_HINTS.get(agent_id, "Format: Summary, 3 recommendations with impact, 2 next steps.")


# ============================================================
# INTENT → WORKFLOW MAPPING
# ============================================================

INTENT_WORKFLOW_MAP = [
    (["write a blog", "write an article", "create a blog post", "publish content",
      "write content", "draft a post", "create an article", "write a post"], "publish_content"),
    (["create a campaign", "launch ads", "set up google ads", "create google ads",
      "build a campaign", "ad campaign setup", "launch a campaign", "google ads campaign"], "create_campaign"),
    (["create email sequence", "email nurture", "drip campaign", "email campaign",
      "create emails", "write emails", "email automation", "email drip"], "create_email_sequence"),
    (["create social posts", "write social media", "create linkedin post",
      "write a tweet", "instagram post", "social media posts",
      "draft social posts", "write social posts"], "create_social_posts"),
    (["aeo", "answer engine", "ai search", "ai overviews", "get cited",
      "optimize for ai", "optimize for chatgpt", "perplexity optimization",
      "ai citation", "zero click", "ai answer", "generative engine",
      "geo optimization"], "aeo_optimization"),
    (["audit", "grade my", "review my site", "analyze my site", "full analysis", "website analysis", "site audit"], "marketing_audit"),
    (["3 month plan", "three month plan", "growth plan", "marketing plan", "full strategy", "complete strategy", "quarterly plan", "budget plan"], "growth_plan"),
    (["generate leads", "get leads", "more leads", "lead generation", "lead gen", "capture leads", "get more leads"], "lead_generation"),
    (["competitor", "competition", "compare us", "competitive", " vs ", "beat my competitors", "competitive analysis"], "competitor_analysis"),
    (["content strategy", "content plan", "blog strategy", "content calendar", "what to write", "blog ideas", "article ideas", "content ideas"], "content_strategy"),
    (["social media strategy", "social strategy", "social plan", "instagram strategy", "linkedin strategy", "social media plan", "social content"], "social_strategy"),
    (["paid campaign", "google ads", "ppc campaign", "ad campaign", "advertising campaign", "paid advertising", "ad strategy"], "paid_campaign"),
    (["keyword", "keywords", "find keywords", "keyword research", "keyword opportunities", "seo keywords"], "keyword_research"),
]


def match_workflow(message: str):
    """Match user message to a workflow blueprint. Returns workflow name or None."""
    msg_lower = message.lower()
    for patterns, workflow_name in INTENT_WORKFLOW_MAP:
        for pattern in patterns:
            if pattern in msg_lower:
                return workflow_name
    return None


def get_workflow(name: str):
    """Get a workflow blueprint by name."""
    return WORKFLOWS.get(name)


def execute_workflow(workflow_name, user_message, brand_context, call_agent_fn, call_synthesis_fn):
    """
    Execute a DAG workflow.

    Args:
        workflow_name: key in WORKFLOWS dict
        user_message: the user's original message
        brand_context: brand context string to inject into agent prompts
        call_agent_fn: function(agent_id, full_prompt) -> str
        call_synthesis_fn: function(synthesis_prompt) -> str

    Returns:
        dict with response, agents_used, agent_timings, multi_agent
    """
    workflow = WORKFLOWS.get(workflow_name)
    if not workflow:
        return None

    agents = workflow["agents"]
    sub_prompts = workflow["sub_prompts"]
    parallel = workflow.get("parallel", True)
    synthesis_instruction = workflow.get("synthesis_instruction")
    agent_count = len(agents)

    start_time = time.time()
    agent_results = {}
    agent_timings = {}

    logger.info(f"[WORKFLOW] Starting '{workflow_name}' with {agent_count} agents (parallel={parallel})")

    # Lazy-load quality gate (avoids circular import at module load time)
    try:
        from quality_gate import get_quality_gate
        _qg = get_quality_gate()
    except Exception:
        _qg = None

    def run_agent(agent_id):
        agent_start = time.time()
        sub_prompt = sub_prompts.get(agent_id, user_message)
        full_prompt = f"{brand_context}\n\nUser request: {user_message}\n\nYour specific task: {sub_prompt}"

        # Determine if two-step is worth the extra API call:
        # Skip for: large parallel workflows (4+ agents) OR simple queries
        use_two_step = True
        if agent_count >= 4:
            use_two_step = False  # Large workflows: single-pass to save API calls

        if use_two_step:
            try:
                from difficulty_scorer import score_difficulty
                difficulty, _ = score_difficulty(user_message)
                if difficulty <= 3:
                    use_two_step = False
            except Exception:
                pass

        try:
            if use_two_step:
                # Complex, small workflow (2-3 agents): two-step for better quality
                try:
                    from two_step_generator import two_step_generate, get_schema_template
                    from response_schemas import format_structured_response
                    schema_template = get_schema_template(agent_id)
                    structured = two_step_generate(
                        reasoning_fn=lambda p: str(call_agent_fn(agent_id, p) or ""),
                        formatting_fn=lambda p: str(call_agent_fn("nexus", p) or ""),
                        reasoning_prompt=full_prompt,
                        schema_template=schema_template,
                        brand_context=brand_context,
                    )
                    formatted = format_structured_response(structured)
                    result = (
                        formatted if formatted and len(formatted.strip()) > 50
                        else structured.get("_raw_analysis", structured.get("summary", ""))
                    )
                    if not result or len(str(result).strip()) < 20:
                        raise ValueError("two-step produced empty result")
                except Exception as ts_err:
                    logger.warning(f"Two-step failed for {agent_id}: {ts_err} — falling back to single-pass")
                    use_two_step = False  # fall through to single-pass below

            if not use_two_step:
                # Single-pass with concise schema hint (fast path for large workflows)
                schema_hint = _get_concise_schema_hint(agent_id)
                augmented_prompt = (
                    f"{full_prompt}\n\n{schema_hint}\n\n"
                    "Keep your response under 200 words. Be specific and actionable. "
                    "Reference the brand by name. Include metrics where possible."
                )
                if _qg:
                    gate_result = _qg.gate_with_retry(
                        generator_fn=lambda: str(call_agent_fn(agent_id, augmented_prompt) or ""),
                        agent_id=agent_id,
                        min_words=25,
                    )
                    result = gate_result["response"]
                    if not gate_result["passed"]:
                        logger.warning(f"QualityGate: {agent_id} did not pass after {gate_result['attempts']} attempt(s). Warnings: {gate_result['quality'].get('warnings', [])}")
                else:
                    result = str(call_agent_fn(agent_id, augmented_prompt) or "")

            elapsed = round(time.time() - agent_start, 1)
            return agent_id, result, elapsed
        except Exception as e:
            logger.error(f"Workflow agent {agent_id} failed: {e}")
            return agent_id, "", round(time.time() - agent_start, 1)

    if parallel and len(agents) > 1:
        with ThreadPoolExecutor(max_workers=min(len(agents), 6)) as executor:
            futures = {executor.submit(run_agent, aid): aid for aid in agents}
            for future in as_completed(futures, timeout=55):
                try:
                    agent_id, result, elapsed = future.result(timeout=55)
                    agent_results[agent_id] = result
                    agent_timings[agent_id] = elapsed
                except Exception as e:
                    logger.error(f"Future failed: {e}")
    else:
        for aid in agents:
            agent_id, result, elapsed = run_agent(aid)
            agent_results[agent_id] = result
            agent_timings[agent_id] = elapsed

    total_time = round(time.time() - start_time, 1)
    valid_results = {k: v for k, v in agent_results.items() if v and len(v.strip()) > 20}

    logger.info(f"[WORKFLOW] Completed '{workflow_name}' in {total_time}s. Agent timings: {agent_timings}")

    # Single agent or no synthesis needed — return best result directly
    if not synthesis_instruction or len(valid_results) <= 1:
        best = max(valid_results.values(), key=len) if valid_results else (
            "I wasn't able to complete that analysis. Could you rephrase your request?"
        )
        return {
            "response": best,
            "workflow": workflow_name,
            "agents_used": list(agent_results.keys()),
            "agent_timings": agent_timings,
            "multi_agent": len(agents) > 1,
            "latency_seconds": total_time,
        }

    # Multi-agent — synthesize (400-char truncation per agent to save tokens)
    agent_findings = ""
    for agent_id, result in valid_results.items():
        truncated = result[:400].strip()
        if len(result) > 400:
            truncated += "..."
        agent_findings += f"\n--- {agent_id.upper()} ---\n{truncated}\n"

    synthesis_prompt = f"""You are SwarmOps, synthesizing findings from multiple specialist agents.

User asked: {user_message}
{brand_context}

Specialist findings:{agent_findings}

{synthesis_instruction}

PRIORITIZE BY IMPACT (RICE thinking):
Rank ALL recommendations by: Reach × Impact × Confidence / Effort.
Lead with QUICK WINS — high impact, low effort actions first.
For each recommendation include: what to do, expected outcome, and timeline.
Put the 2-3 highest-RICE actions at the top. Save complex long-term items for last.

RULES:
- Combine ALL specialist findings into ONE unified response
- Do NOT list each agent's output separately
- Do NOT repeat agent findings verbatim — synthesize and prioritize
- Write as one voice — you are the strategist presenting a complete plan
- Be specific to the brand — reference their name and industry
- Every recommendation must have a concrete expected outcome and timeline
- Keep under 500 words
- End with "Would you like me to..." and 2-3 specific next steps
"""

    try:
        synthesized = call_synthesis_fn(synthesis_prompt)
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        synthesized = ""

    if not synthesized or len(synthesized.strip()) < 30:
        synthesized = max(valid_results.values(), key=len) if valid_results else (
            "I analyzed your request but couldn't synthesize a complete response. Please try again."
        )

    return {
        "response": synthesized,
        "workflow": workflow_name,
        "agents_used": list(agent_results.keys()),
        "agent_timings": agent_timings,
        "multi_agent": True,
        "latency_seconds": total_time,
    }
