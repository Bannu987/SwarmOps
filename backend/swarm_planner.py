"""
SwarmOps — Swarm Planner
Plan → Execute → Score → Synthesize

Replaces keyword-based routing with LLM-powered intelligent orchestration.
Every nexus query now goes through a 4-step pipeline:
  1. build_execution_plan()  — decide which agents should run
  2. run_agents()            — execute them in parallel
  3. rank_agent_results()    — sort by confidence
  4. synthesize_results()    — Nexus CMO synthesizes into one response
"""

import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Agent registry — describes what each agent specializes in
# ---------------------------------------------------------------------------

AGENT_DESCRIPTIONS = {
    "seo":      "SEO analysis, keyword research, search rankings, organic traffic optimization",
    "content":  "Content strategy, copywriting, blog posts, messaging architecture",
    "ppc":      "Paid advertising, Google/Facebook Ads, campaign strategy, ad copy, budget optimization",
    "analytics":"Performance metrics, data analysis, ROI calculation, conversion rate trends",
    "cro":      "Conversion rate optimization, A/B testing, funnel analysis, landing page improvement",
    "research": "Market research, competitor analysis, industry trends, customer insights",
    "smm":      "Social media strategy, platform content, engagement, community building",
    "crm":      "Email marketing, customer retention, nurture sequences, lifecycle campaigns",
    "brand":    "Brand strategy, positioning, brand voice, identity, messaging framework",
    "web_ux":   "Website UX, page design, navigation architecture, user experience",
}

# Fast keyword fallback — no LLM needed for clear-cut queries
_KEYWORD_MAP = [
    (["traffic",   "seo",        "keyword",  "search rank", "organic",   "serp"],       ["seo", "content", "research"]),
    (["ads",       "ppc",        "campaign", "google ads",  "facebook ads", "paid", "cpc", "roas"], ["ppc", "analytics"]),
    (["conversion","cro",        "funnel",   "checkout",    "cart",      "landing page", "a/b test"], ["cro", "analytics", "ppc"]),
    (["sales",     "revenue",    "more sales","grow revenue","increase sales"],                       ["cro", "crm", "analytics"]),
    (["leads",     "lead gen",   "lead generation", "pipeline", "prospects"],                         ["cro", "ppc", "crm"]),
    (["competitor","competition","competitive","vs "],                                                ["research", "seo"]),
    (["brand",     "messaging",  "positioning","voice",       "identity"],                            ["brand", "content"]),
    (["social",    "instagram",  "twitter",   "linkedin",    "tiktok",   "facebook", "social media"], ["smm", "content"]),
    (["email",     "retention",  "churn",     "nurture",     "sequence", "lifecycle"],               ["crm", "analytics"]),
    (["analytics", "data",       "metrics",   "numbers",     "performance", "roi", "kpi"],            ["analytics"]),
    (["website",   "landing",    "ux",        "design",      "page speed","navigation","wireframe"],  ["web_ux", "cro"]),
    (["content",   "blog",       "article",   "copy",        "write",    "post"],                     ["content", "seo"]),
]


# ---------------------------------------------------------------------------
# STEP 1: Planner
# ---------------------------------------------------------------------------

def build_execution_plan(user_message: str, brand_name: str = "") -> list:
    """
    LLM-powered planner: decides which specialist agents should run.
    Falls back to keyword matching if LLM call fails or returns invalid output.
    Returns a list of 1–4 agent names, or ["nexus"] for conversational queries.
    """
    from model_router import call_model_sync

    agent_list_str = "\n".join(f"- {k}: {v}" for k, v in AGENT_DESCRIPTIONS.items())
    brand_hint = f" (brand: {brand_name})" if brand_name and brand_name != "your brand" else ""

    prompt = f"""You are an AI orchestrator for a marketing platform{brand_hint}. \
Analyze the user's question and select the most relevant specialist agents.

Available agents:
{agent_list_str}

User question: "{user_message}"

Rules:
- Return 1-4 agent names most relevant to this question
- If the question is conversational, a greeting, or general chat, return ["nexus"]
- Traffic/SEO → ["seo", "content", "research"]
- Ads/paid → ["ppc", "analytics"]
- Conversions/sales → ["cro", "analytics", "ppc"]
- Competitors → ["research", "seo"]
- Brand/messaging → ["brand", "content"]
- Analytics/numbers → ["analytics"]
- Unknown/vague → ["research"]

Return ONLY a valid JSON array of agent names. No explanation. No other text.
Example: ["seo", "content", "research"]"""

    try:
        response = call_model_sync(
            prompt=prompt,
            system_prompt="Return only a valid JSON array of agent names. No other text.",
            tier=1,
            max_tokens=60,
        )
        match = re.search(r'\[.*?\]', str(response), re.DOTALL)
        if match:
            agents = json.loads(match.group())
            valid = [a for a in agents if a in AGENT_DESCRIPTIONS or a == "nexus"]
            if valid:
                print(f"  🧠 LLM Plan: {valid}")
                return valid[:4]
    except Exception:
        pass

    # Keyword fallback
    plan = _keyword_plan(user_message)
    print(f"  🔑 Keyword Plan: {plan}")
    return plan


def _keyword_plan(user_message: str) -> list:
    """Fast keyword-based fallback — no LLM call."""
    msg = user_message.lower()
    for keywords, agents in _KEYWORD_MAP:
        if any(kw in msg for kw in keywords):
            return agents
    return ["research"]


# ---------------------------------------------------------------------------
# STEP 2: Agent executor
# ---------------------------------------------------------------------------

def call_agent(agent_name: str, prompt: str) -> dict:
    """
    Call a single agent with a fully-formed prompt (already includes brand context).
    Returns {"insight": str, "confidence": float}.
    """
    try:
        result_text = ""

        if agent_name == "seo":
            from seo_agent import find_keyword_opportunities, find_keywords
            result_text = find_keyword_opportunities(prompt) or find_keywords(prompt) or ""

        elif agent_name == "content":
            from content_agent import generate_content
            result_text = generate_content(prompt) or ""

        elif agent_name == "ppc":
            from ppc_agent import create_campaign_strategy
            result_text = create_campaign_strategy(prompt) or ""

        elif agent_name == "analytics":
            from analytics_agent import analyze_performance
            result_text = analyze_performance(prompt, prompt) or ""

        elif agent_name == "cro":
            from cro_agent import analyze_funnel
            result_text = analyze_funnel(
                funnel_steps=prompt, conversion_data="", goal="increase conversions"
            ) or ""

        elif agent_name == "research":
            from research_agent import research_topic
            result_text = research_topic(prompt) or ""

        elif agent_name == "smm":
            from smm_agent import create_social_calendar
            result_text = create_social_calendar(
                industry="General", brand_voice="Professional", target_audience="General audience"
            ) or ""

        elif agent_name == "crm":
            from crm_agent import create_email_sequence
            result_text = create_email_sequence(prompt, num_emails=3) or ""

        elif agent_name == "brand":
            from brand_strategist_agent import create_brand_strategy
            result_text = create_brand_strategy(
                company_name="Company", industry="General",
                target_audience="General audience", unique_value=prompt
            ) or ""

        elif agent_name == "web_ux":
            from web_ux_agent import design_landing_page
            result_text = design_landing_page(
                product=prompt, target_audience="General audience", goal="conversions"
            ) or ""

        else:
            return {"insight": "Agent not found.", "confidence": 0.0}

        confidence = _score_result(result_text)
        return {"insight": result_text, "confidence": confidence}

    except Exception as e:
        return {"insight": f"Agent unavailable: {str(e)[:120]}", "confidence": 0.0}


def _score_result(text: str) -> float:
    """Score agent result quality as a confidence proxy (0.0–1.0)."""
    score = 0.5
    if len(text) > 200:  score += 0.1
    if len(text) > 500:  score += 0.1
    if re.search(r'\d+%|\$\d+|\d+x', text): score += 0.15
    if any(w in text.lower() for w in ['recommend', 'suggest', 'priority', 'action', 'should']):
        score += 0.1
    return min(score, 1.0)


def run_agents(agent_list: list, prompt: str, max_workers: int = 5, timeout: int = 30) -> dict:
    """
    Run agents in parallel via ThreadPoolExecutor.
    Returns {agent_name: {"insight": str, "confidence": float}}.
    prompt should already include brand context (augmented msg from main.py).
    """
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(call_agent, agent, prompt): agent
            for agent in agent_list
        }
        for future in as_completed(futures, timeout=timeout):
            agent = futures[future]
            try:
                results[agent] = future.result(timeout=timeout)
            except Exception as e:
                results[agent] = {
                    "insight": f"Timed out or failed: {str(e)[:80]}",
                    "confidence": 0.0,
                }
    return results


# ---------------------------------------------------------------------------
# STEP 3: Ranker
# ---------------------------------------------------------------------------

def rank_agent_results(agent_results: dict) -> list:
    """
    Sort agent results by confidence descending.
    Returns list of (agent_name, result_dict) tuples.
    """
    return sorted(
        agent_results.items(),
        key=lambda x: x[1].get("confidence", 0.0),
        reverse=True,
    )


# ---------------------------------------------------------------------------
# STEP 4: Synthesis
# ---------------------------------------------------------------------------

def synthesize_results(user_message: str, ranked_results: list, brand_name: str = "your brand") -> str:
    """
    Nexus CMO synthesizes all ranked agent insights into one strategic response.
    Structured output: Title → Explanation → Priority Actions → Expected Impact → Next Steps.
    """
    from model_router import call_model_sync

    if not ranked_results:
        return (
            "I need a bit more context to give you a precise recommendation. "
            "What's the main marketing challenge you're facing right now?"
        )

    # Build findings block — top 4 agents, highest confidence first
    findings_block = ""
    for agent_name, result in ranked_results[:4]:
        confidence = result.get("confidence", 0.0)
        insight = str(result.get("insight", ""))[:500]
        findings_block += f"\n### {agent_name.upper()} Agent (confidence: {confidence:.1f})\n{insight}\n"

    synthesis_prompt = f"""You are The Nexus — CMO of SwarmOps. You just received intelligence from {len(ranked_results)} specialist agent(s).

User's question: "{user_message}"
Brand: {brand_name}

Agent findings (ranked by confidence — higher = more reliable):
{findings_block}

Synthesize this into ONE strategic response. Use EXACTLY this structure:

**[Strategy Name]**

[2–3 sentence explanation of the core opportunity or problem. Reference {brand_name} by name.]

**Top Priority Actions:**
1. [Specific, actionable step with expected outcome]
2. [Specific, actionable step with expected outcome]
3. [Specific, actionable step with expected outcome]

**Expected Impact:**
[1–2 sentences on the realistic growth or improvement potential. Be specific, not generic.]

---

**What would you like to explore next?**
1. [Follow-up option]
2. [Follow-up option]
3. [Follow-up option]

Rules:
- 150–250 words total
- Conversational and strategic — never a data dump
- Never show agent names, JSON, or internal labels in the output
- Weight insights from higher-confidence agents more heavily
- Every action must be specific to {brand_name}'s context"""

    try:
        from nexus import NEXUS_MASTER_PROMPT
        return call_model_sync(
            prompt=synthesis_prompt,
            system_prompt=NEXUS_MASTER_PROMPT,
            tier=2,
            max_tokens=600,
        )
    except Exception:
        # Fallback: surface the top insight cleanly
        top_insight = str(ranked_results[0][1].get("insight", ""))[:400]
        return (
            f"**Strategic Recommendation for {brand_name}**\n\n"
            f"{top_insight}\n\n"
            "**What would you like to explore next?**\n"
            "1. Dive deeper into this strategy\n"
            "2. Run a full marketing audit\n"
            "3. Compare against competitors"
        )
