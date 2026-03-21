"""
DAG Workflow Engine for SwarmOps v3.
Code controls which agents run. LLM only generates text.
"""
import re
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        "synthesis_instruction": "Combine competitive research, keyword data, and content ideas into ONE unified content strategy. Give 5 specific article recommendations with titles and target keywords.",
    },
    "lead_generation": {
        "agents": ["cro", "ppc", "content", "crm"],
        "parallel": True,
        "sub_prompts": {
            "cro": "Analyze the conversion funnel. Where are the friction points? What would improve lead capture rate?",
            "ppc": "Recommend a paid advertising strategy for lead generation. Include channel, budget, and targeting approach.",
            "content": "Suggest lead magnet ideas and landing page copy that would attract qualified leads.",
            "crm": "Design an email nurture sequence for new leads. Include subject lines and send timing.",
        },
        "synthesis_instruction": "Create a unified lead generation plan. Combine funnel optimization, paid ads, content, and email nurture. Prioritize the 5 highest-impact actions with implementation order.",
    },
    "marketing_audit": {
        "agents": ["seo", "content", "cro", "analytics", "research", "brand"],
        "parallel": True,
        "sub_prompts": {
            "seo": "Audit SEO: meta tags, keyword optimization, technical issues, backlink profile.",
            "content": "Audit content strategy: quality, gaps, frequency, formats, readability.",
            "cro": "Audit conversion optimization: CTAs, forms, trust signals, user flow, friction.",
            "analytics": "Analyze performance data. Compute key metrics and identify trends.",
            "research": "Research competitive landscape. How does this brand compare to top competitors?",
            "brand": "Evaluate brand positioning, messaging clarity, and differentiation.",
        },
        "synthesis_instruction": "Create a comprehensive marketing audit: 1) Overall grade (A+ through F), 2) Score for each section (0-100), 3) Top 3 strengths, 4) Top 3 weaknesses, 5) Top 5 priority actions with expected impact and timeline.",
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
            "seo": "Recommend organic growth strategies: keywords to target, technical fixes, link building.",
            "content": "Recommend content initiatives: pillar pages, blog strategy, content calendar.",
            "ppc": "Recommend paid strategies: channels, budget allocation, targeting, expected ROI.",
            "crm": "Recommend lifecycle marketing: email sequences, lead nurturing, retention.",
            "analytics": "Identify the highest-impact growth levers based on available data.",
        },
        "synthesis_instruction": "Create a 3-month growth plan: Month 1 (quick wins), Month 2 (building momentum), Month 3 (scaling). Separate organic vs paid. Include budget estimates.",
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
}


# ============================================================
# INTENT → WORKFLOW MAPPING
# ============================================================

INTENT_WORKFLOW_MAP = [
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

    start_time = time.time()
    agent_results = {}
    agent_timings = {}

    def run_agent(agent_id):
        agent_start = time.time()
        sub_prompt = sub_prompts.get(agent_id, user_message)
        full_prompt = f"{brand_context}\n\nUser request: {user_message}\n\nYour specific task: {sub_prompt}"
        try:
            result = call_agent_fn(agent_id, full_prompt)
            elapsed = round(time.time() - agent_start, 1)
            return agent_id, str(result or ""), elapsed
        except Exception as e:
            logger.error(f"Workflow agent {agent_id} failed: {e}")
            return agent_id, "", round(time.time() - agent_start, 1)

    if parallel and len(agents) > 1:
        with ThreadPoolExecutor(max_workers=min(len(agents), 5)) as executor:
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

    # Multi-agent — synthesize
    agent_findings = ""
    for agent_id, result in valid_results.items():
        agent_findings += f"\n--- {agent_id.upper()} SPECIALIST ---\n{result[:600]}\n"

    synthesis_prompt = f"""You are SwarmOps, synthesizing findings from multiple specialist agents.

User asked: {user_message}
{brand_context}

Specialist findings:{agent_findings}

{synthesis_instruction}

RULES:
- Combine ALL specialist findings into ONE unified response
- Do NOT list each agent's output separately
- Write as one voice — you are the strategist presenting a complete plan
- Be specific to the brand — reference their name and industry
- Keep under 400 words unless the user asked for detailed/comprehensive
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
