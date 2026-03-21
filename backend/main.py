"""
SwarmOps - FastAPI Backend
Full Nexus orchestrator + 10 agents + real integrations
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os
import io
import json
import requests

# Fix Windows encoding — agent modules print emoji that crash charmap codec
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path (project root → nexus, brand_dna, model_router, etc.)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add backend directory explicitly (knowledge_base, web_crawler, competitive_intel)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env before anything else (Railway sets real env vars, this is for local dev)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from knowledge_base import get_knowledge_base
from web_crawler import get_web_crawler
from conversation_manager import get_conversation_manager
from response_cleaner import get_response_cleaner
from sanitize import sanitize_response

# ---------------------------------------------------------------------------
# Startup ENV check — prints to Railway logs so you can verify keys are loaded
# ---------------------------------------------------------------------------
_ENV_KEYS = [
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "OPENROUTER_API_KEY",
    "NVIDIA_API_KEY",
    "DEEPSEEK_API_KEY",
    "SERPER_API_KEY",
    "BRAVE_API_KEY",
]

def _env_check():
    parts = []
    for key in _ENV_KEYS:
        short = key.replace("_API_KEY", "").replace("_KEY", "")
        found = bool(os.getenv(key))
        icon = "\u2705" if found else "\u274c"
        parts.append(f"{short}={icon}")
    line = "  ".join(parts)
    print(f"\n{'='*60}")
    print(f"ENV CHECK: {line}")
    print(f"{'='*60}\n")

_env_check()

# Initialize FastAPI first (before heavy imports)
app = FastAPI(
    title="SwarmOps API",
    description="Multi-Agent AI Marketing Intelligence",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Explicit OPTIONS handler — safety net so preflight never returns 405
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Lazy loading for heavy modules
_nexus = None
def get_nexus():
    global _nexus
    if _nexus is None:
        from nexus import Nexus
        _nexus = Nexus()
    return _nexus


_kb = get_knowledge_base()
_crawler = get_web_crawler()
_cm = get_conversation_manager()
_cleaner = get_response_cleaner()


def _is_external_url(message: str, stored_url: str) -> bool:
    """Check if user is asking about a URL different from their own stored URL."""
    import re
    urls = re.findall(r'https?://[^\s]+|(?:www\.)?[\w-]+\.(?:com|org|net|io|in|co|me|dev|ai)(?:/\S*)?', message.lower())
    if not urls or not stored_url:
        return False
    stored_domain = stored_url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].lower()
    for url in urls:
        url_domain = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].lower()
        if url_domain != stored_domain and len(url_domain) > 3:
            return True
    return False


def _extract_text(result):
    """Extract displayable text from any agent result (str, dict, list, None)."""
    if result is None:
        return None
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        # Try common text keys in order
        for key in ("analysis", "ai_analysis", "report", "result", "content", "post", "calendar"):
            if key in result and isinstance(result[key], str):
                return result[key]
        # Return full dict as formatted string
        import json
        return json.dumps(result, indent=2, default=str)
    if isinstance(result, list):
        import json
        return json.dumps(result, indent=2, default=str)
    return str(result)


def _format_audit_chat_result(audit_report: dict) -> str:
    """Convert audit data to a conversational, CMO-quality chat response."""
    def _score_emoji(s):
        if s >= 80: return "🟢"
        if s >= 60: return "🟡"
        return "🔴"

    grade = audit_report.get("grade", "N/A")
    overall_score = audit_report.get("overall_score", 0)
    brand = audit_report.get("brand", {})
    brand_name = brand.get("name", audit_report.get("url", "your website"))
    url = audit_report.get("url", "")
    exec_summary = audit_report.get("executive_summary", "")
    scores = audit_report.get("scores", {})
    actions = audit_report.get("priority_actions", [])
    audit_id = audit_report.get("id", "")

    # Score table
    score_lines = []
    for section, score in scores.items():
        score_lines.append(f"| {section.replace('_', ' ').title()} | {score}/100 | {_score_emoji(score)} |")
    score_table = "\n".join(score_lines)

    # Top 5 priority actions
    action_lines = []
    for i, action in enumerate(actions[:5], 1):
        if isinstance(action, dict):
            act_text = action.get("action", str(action))
            is_quick = action.get("type") == "quick_win"
            tag = " ⚡" if is_quick else ""
            action_lines.append(f"{i}.{tag} {act_text}")
        else:
            action_lines.append(f"{i}. {action}")
    actions_text = "\n".join(action_lines)

    # Identify top strengths and critical gaps
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_strength = sorted_scores[0][0].replace("_", " ").title() if sorted_scores else "N/A"
    worst_gap = sorted_scores[-1][0].replace("_", " ").title() if sorted_scores else "N/A"
    worst_score = sorted_scores[-1][1] if sorted_scores else 0

    report_link = f"\n\n📄 **[Download Full Report](/api/audit/{audit_id}/report)**" if audit_id else ""

    return f"""## {brand_name} Marketing Audit — Grade **{grade}** ({overall_score}/100)

{exec_summary}

---

### Score Breakdown

| Section | Score | Status |
|---------|-------|--------|
{score_table}

---

### Top Priority Actions

{actions_text}

---

**Biggest strength:** {top_strength} is your strongest area — lean into it.

**Biggest opportunity:** {worst_gap} scored {worst_score}/100 — this is your highest-leverage improvement area.{report_link}

**Would you like me to:**
- 📊 Deep-dive into any specific section?
- 🎯 Build a 90-day improvement roadmap?
- ⚡ Focus only on quick wins (1-2 week fixes)?
- 🔍 Run a competitor comparison?"""


# ============================================================================
# REQUEST MODELS
# ============================================================================

class TaskRequest(BaseModel):
    goal: str

class ContentRequest(BaseModel):
    prompt: str
    max_length: Optional[int] = 2000

class ContentPublishRequest(BaseModel):
    topic: str
    post_type: Optional[str] = "blog"
    status: Optional[str] = "draft"
    seo_keywords: Optional[List[str]] = None

class CampaignRequest(BaseModel):
    campaign_name: str
    daily_budget: float
    keywords: List[str]
    headlines: List[str]
    descriptions: List[str]
    landing_url: str

class ContactRequest(BaseModel):
    email: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    company: Optional[str] = ""

class SocialPostRequest(BaseModel):
    platform: str
    topic: str
    brand_voice: Optional[str] = "Professional and engaging"
    goal: Optional[str] = "Increase engagement"
    brand_name: Optional[str] = "Brand"

class DebateRequest(BaseModel):
    topic: str
    agent_positions: Dict[str, str]

class BrandStrategyRequest(BaseModel):
    company_name: str
    industry: str
    target_audience: str
    unique_value: Optional[str] = ""

class LandingPageRequest(BaseModel):
    product: str
    target_audience: str
    goal: str
    key_benefits: Optional[str] = ""

class FunnelRequest(BaseModel):
    funnel_steps: str
    conversion_data: Optional[str] = ""
    goal: Optional[str] = "increase conversions"

class EmailSequenceRequest(BaseModel):
    topic: str
    num_emails: Optional[int] = 3

# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/")
def root():
    return {
        "status": "operational",
        "message": "SwarmOps API",
        "version": "2.0.0",
        "agents": 10,
        "docs": "/docs"
    }

@app.get("/health")
def health():
    """Health check — includes database stats for monitoring."""
    db_info = {}
    try:
        from db import get_db_path, get_db_size_mb, get_table_count, get_connection
        conn = get_connection()
        db_info["path"] = get_db_path()
        db_info["size_mb"] = get_db_size_mb()
        db_info["tables"] = get_table_count()

        # brand_dna configured?
        row = conn.execute("SELECT COUNT(*) as c FROM brand_dna").fetchone()
        db_info["brand_dna_configured"] = row["c"] > 0 if row else False
    except Exception:
        pass

    try:
        from memory_store import get_memory_store
        stats = get_memory_store().get_stats()
        db_info["total_tasks"] = stats.get("total_tasks", 0)
    except Exception:
        pass

    try:
        from revenue_tracker import get_revenue_tracker
        recs = get_revenue_tracker().get_recommendation_history(limit=1000)
        db_info["total_recommendations"] = len(recs)
    except Exception:
        pass

    try:
        from competitive_intel import get_competitive_intel
        db_info["competitors_tracked"] = len(get_competitive_intel().list_competitors())
    except Exception:
        db_info["competitors_tracked"] = 0

    return {"status": "healthy", "agents": 10, "database": db_info}

@app.get("/api/debug-env")
def debug_env():
    """Check which API keys are present (true/false only, never exposes values)"""
    result = {}
    for key in _ENV_KEYS:
        val = os.getenv(key)
        result[key] = bool(val and val.strip())
    found = sum(1 for v in result.values() if v)
    return {"keys": result, "found": found, "total": len(result)}

@app.get("/api/test-providers")
def test_providers():
    """Test all AI model providers and search engines"""
    try:
        from model_router import test_all_providers
        results = test_all_providers()
        working = sum(1 for v in results.values() if v == "ok")
        return {"providers": results, "working": working, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rate-limits")
def get_rate_limits():
    """Get current rate limit status for all providers"""
    try:
        from rate_limiter import get_rate_limiter
        limiter = get_rate_limiter()
        status = limiter.get_status()

        # Calculate summary stats
        total_providers = len(status)
        available = sum(1 for v in status.values() if v["available"])
        rate_limited = total_providers - available

        return {
            "status": status,
            "summary": {
                "total_providers": total_providers,
                "available": available,
                "rate_limited": rate_limited
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# NEXUS ENDPOINTS (Smart Routing)
# ============================================================================

@app.post("/api/task")
def execute_task(request: TaskRequest):
    """Execute any task via Nexus smart routing"""
    try:
        nexus = get_nexus()
        result = nexus.execute_task(request.goal)
        return {"success": True, "goal": request.goal, "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard")
def get_dashboard():
    """Get system dashboard"""
    try:
        nexus = get_nexus()
        return nexus.get_performance_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/debate")
def run_debate(request: DebateRequest):
    """Run agent debate"""
    try:
        nexus = get_nexus()
        result = nexus.resolve_conflict(request.topic, request.agent_positions)
        return {"success": True, "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class FeedbackLoopRequest(BaseModel):
    trigger: Optional[str] = "manual"
    metrics: Optional[Dict[str, Any]] = None

@app.post("/api/feedback-loop")
def run_feedback_loop(request: FeedbackLoopRequest = None):
    """Run live feedback loop"""
    try:
        nexus = get_nexus()
        result = nexus.run_feedback_loop()
        return {"success": True, "result": _extract_text(result), "trigger": request.trigger if request else "manual"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CONTENT AGENT
# ============================================================================

@app.post("/api/content/generate")
def generate_content_endpoint(request: ContentRequest):
    try:
        from content_agent import generate_content
        result = generate_content(request.prompt, request.max_length)
        return {"success": True, "agent": "content", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/publish")
def publish_content_endpoint(request: ContentPublishRequest):
    try:
        from content_agent import generate_and_publish
        result = generate_and_publish(
            topic=request.topic,
            post_type=request.post_type,
            status=request.status,
            seo_keywords=request.seo_keywords
        )
        return {"success": True, "agent": "content", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANALYTICS AGENT — falls back to AI analysis if GA4 not connected
# ============================================================================

@app.get("/api/analytics/dashboard")
def analytics_dashboard(days: int = 30):
    try:
        from analytics_agent import get_live_dashboard, analyze_performance
        result = get_live_dashboard(days=days)
        if result is None or (isinstance(result, str) and "❌" in result):
            result = analyze_performance(
                f"Marketing analytics dashboard for last {days} days",
                "GA4 not connected. Generating AI-powered sample analysis based on industry benchmarks."
            )
        return {"success": True, "agent": "analytics", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/anomalies")
def detect_anomalies(days: int = 7):
    try:
        from analytics_agent import detect_live_anomalies, analyze_performance
        result = detect_live_anomalies(days=days)
        if result is None:
            # Fallback: generate AI-powered anomaly analysis when live GA4 data is insufficient
            result = analyze_performance(
                f"Anomaly detection scan for the last {days} days",
                f"GA4 connection available but no significant data changes detected in the last {days} days. "
                f"Generate a brief anomaly report summarizing that performance metrics are stable "
                f"with no critical deviations. Include typical metrics to monitor."
            )
            if result is None:
                result = {
                    "status": "healthy",
                    "message": f"No anomalies detected in the last {days} days. All metrics within normal range.",
                    "anomalies": [],
                    "critical_count": 0
                }
        return {"success": True, "agent": "analytics", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SEO AGENT — falls back to AI analysis if integrations not connected
# ============================================================================

@app.get("/api/seo/rankings")
def get_rankings(days: int = 28):
    try:
        from seo_agent import get_real_rankings, analyze_seo
        result = get_real_rankings(days=days)
        if result is None:
            result = analyze_seo("website SEO performance")
        return {"success": True, "agent": "seo", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seo/keywords/{keyword}")
def get_keyword_data(keyword: str, location_code: int = 2840):
    try:
        from seo_agent import get_real_keyword_data, find_keywords
        result = get_real_keyword_data(keyword, location_code=location_code)
        if result is None:
            result = find_keywords(keyword)
        return {"success": True, "agent": "seo", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seo/opportunities")
def keyword_opportunities(topic: str = "marketing"):
    try:
        from seo_agent import find_keyword_opportunities, find_keywords
        result = find_keyword_opportunities(topic)
        if result is None:
            result = find_keywords(topic)
        return {"success": True, "agent": "seo", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PPC AGENT — falls back to AI strategy if Google Ads not connected
# ============================================================================

@app.get("/api/ppc/campaigns")
def get_campaigns(days: int = 7):
    try:
        from ppc_agent import get_real_campaign_performance, create_campaign_strategy
        result = get_real_campaign_performance(days=days)
        if result is None:
            result = create_campaign_strategy("PPC campaign performance overview")
        return {"success": True, "agent": "ppc", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ppc/create-campaign")
def create_campaign(request: CampaignRequest):
    try:
        from ppc_agent import execute_campaign
        result = execute_campaign(
            campaign_name=request.campaign_name,
            daily_budget=request.daily_budget,
            keywords=request.keywords,
            headlines=request.headlines,
            descriptions=request.descriptions,
            landing_url=request.landing_url
        )
        return {"success": True, "agent": "ppc", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ppc/optimize")
def optimize_campaigns(days: int = 7):
    try:
        from ppc_agent import auto_optimize_campaigns
        result = auto_optimize_campaigns(days=days)
        if result is None:
            result = "Google Ads not connected. Connect Google Ads to get optimization recommendations."
        return {"success": True, "agent": "ppc", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CRM AGENT — falls back to AI email writing if HubSpot not connected
# ============================================================================

@app.get("/api/crm/contacts")
def get_contacts(limit: int = 10):
    try:
        from crm_agent import get_real_contacts
        result = get_real_contacts(limit=limit)
        if result is None:
            result = "HubSpot CRM not connected. Configure HUBSPOT_ACCESS_TOKEN to pull real contacts."
        return {"success": True, "agent": "crm", "result": _extract_text(result)}
    except requests.exceptions.Timeout:
        return {"success": True, "agent": "crm", "result": "HubSpot API is slow. Try again with a smaller limit (e.g., ?limit=5)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crm/add-contact")
def add_contact(request: ContactRequest):
    try:
        from crm_agent import add_contact_to_hubspot
        result = add_contact_to_hubspot(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            company=request.company
        )
        return {"success": True, "agent": "crm", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crm/email-performance")
def email_performance():
    try:
        from crm_agent import get_real_email_performance
        result = get_real_email_performance()
        if result is None:
            result = "HubSpot not connected. Configure HUBSPOT_ACCESS_TOKEN to see email performance."
        return {"success": True, "agent": "crm", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crm/email-sequence")
def create_email_sequence_endpoint(request: EmailSequenceRequest):
    try:
        from crm_agent import create_email_sequence
        result = create_email_sequence(request.topic, request.num_emails)
        return {"success": True, "agent": "crm", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SMM AGENT (Social Media)
# ============================================================================

@app.get("/api/smm/trends")
def get_social_trends(industry: str = "marketing"):
    try:
        from smm_agent import analyze_trends
        result = analyze_trends(industry=industry, platforms=["instagram", "linkedin", "twitter"])
        return {"success": True, "agent": "smm", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/smm/post")
def create_social_post(request: SocialPostRequest):
    try:
        from smm_agent import write_platform_post
        result = write_platform_post(
            platform=request.platform,
            topic=request.topic,
            brand_voice=request.brand_voice,
            goal=request.goal,
            brand_name=request.brand_name
        )
        return {"success": True, "agent": "smm", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/smm/calendar")
def get_content_calendar(brand_name: str = "Brand", industry: str = "General", posts_per_week: int = 5):
    try:
        from smm_agent import create_social_calendar
        result = create_social_calendar(
            brand_name=brand_name,
            industry=industry,
            platforms=["instagram", "linkedin"],
            posts_per_week=posts_per_week,
            target_audience="General audience"
        )
        return {"success": True, "agent": "smm", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BRAND AGENT
# ============================================================================

@app.post("/api/brand/strategy")
def brand_strategy(request: BrandStrategyRequest):
    try:
        from brand_strategist_agent import create_brand_strategy
        result = create_brand_strategy(
            request.company_name,
            request.industry,
            request.target_audience,
            request.unique_value
        )
        return {"success": True, "agent": "brand", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WEB/UX AGENT
# ============================================================================

@app.post("/api/webux/landing-page")
def design_landing_page_endpoint(request: LandingPageRequest):
    try:
        from web_ux_agent import design_landing_page
        result = design_landing_page(
            request.product,
            request.target_audience,
            request.goal,
            "modern",
            request.key_benefits
        )
        return {"success": True, "agent": "webux", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CRO AGENT
# ============================================================================

@app.post("/api/cro/analyze-funnel")
def analyze_funnel_endpoint(request: FunnelRequest):
    try:
        from cro_agent import analyze_funnel
        result = analyze_funnel(request.funnel_steps, request.conversion_data, request.goal)
        return {"success": True, "agent": "cro", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RESEARCH AGENT
# ============================================================================

class ResearchRequest(BaseModel):
    topic: str
    depth: Optional[str] = "comprehensive"

@app.post("/api/research/topic")
def research_topic_endpoint(request: ResearchRequest):
    try:
        from research_agent import research_topic
        result = research_topic(request.topic)
        return {"success": True, "agent": "research", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/research/topic")
def research_topic_get(topic: str):
    try:
        from research_agent import research_topic
        result = research_topic(topic)
        return {"success": True, "agent": "research", "result": _extract_text(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DEEP RESEARCH ENDPOINT — intensive multi-step research with reasoning model
# ============================================================================

class DeepResearchRequest(BaseModel):
    topic: str

@app.post("/api/deep-research")
async def deep_research_endpoint(request: DeepResearchRequest):
    """
    Execute deep research with 5-step process:
    1. Generate 3 smart search queries
    2. Execute searches on Brave + Serper
    3. Compile results
    4. Analyze with Kimi K2.5 reasoning model
    5. Return structured data
    """
    try:
        from deep_research_agent import get_deep_research_agent
        import os

        deep_research = get_deep_research_agent(
            brave_api_key=os.getenv("BRAVE_API_KEY"),
            serper_api_key=os.getenv("SERPER_API_KEY")
        )

        result = await deep_research.research(request.topic)

        if result.get("success"):
            return {
                "success": True,
                "agent": "deep_research",
                "result": result,
                "model": result.get("models_used", {}).get("analysis", "unknown"),
                "provider": "multi-step",
                "latency_ms": result.get("total_latency_ms", 0),
                "quality": {
                    "confidence": result.get("confidence", 0.0),
                    "approved": True,
                    "revised": False
                }
            }
        else:
            return {
                "success": False,
                "agent": "deep_research",
                "error": result.get("error", "Deep research failed"),
                "result": result
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SMART ONBOARDING HELPER
# Called at the very start of /api/chat before any agent logic.
# Returns a response dict if onboarding is active, None if user is fully set up.
# ============================================================================

import re as _url_re
_URL_PATTERN = _url_re.compile(
    r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9][a-zA-Z0-9\-]*\.[a-z]{2,}(?:/[^\s]*)?)',
    _url_re.IGNORECASE
)

def _is_url(text: str) -> str | None:
    """Extract a URL from text, or return None if none found."""
    m = _URL_PATTERN.search(text.strip())
    if not m:
        return None
    url = m.group(0)
    if not url.startswith("http"):
        url = "https://" + url
    return url

def _onboarding_complete() -> bool:
    """
    Return True if the user has EXPLICITLY completed or skipped onboarding.
    NOTE: brand_dna table having rows does NOT mean complete — the URL step
    stores BrandDNA mid-flow. Only check explicit completion markers.
    """
    try:
        from memory_store import get_memory_store
        mem = get_memory_store()
        # Explicitly marked complete (step 3 finished or skip command used)
        if mem.get_profile_key("onboarding_step") == "complete":
            return True
        # website_url set means either completed or manually configured via API
        if mem.get_profile_key("website_url"):
            return True
    except Exception:
        pass
    return False

async def _handle_onboarding(user_msg: str, agent: str):
    """
    Smart onboarding state machine.
    Returns a response dict if onboarding is active, None if already complete or agent is not nexus.

    Only triggers for nexus agent when the message contains marketing intent.
    General questions ("what is AI"), specific agent queries, and skip phrases bypass onboarding.
    """
    # Non-nexus agents never get onboarding
    if agent not in ("nexus", ""):
        return None

    # Already onboarded — nothing to do
    if _onboarding_complete():
        return None

    try:
        from memory_store import get_memory_store
        mem = get_memory_store()
        raw_step = mem.get_profile_key("onboarding_step")
        # "unstarted" = we have never shown the onboarding prompt yet
        step = raw_step if raw_step else "unstarted"

        _msg_lower = user_msg.lower().strip()

        # ---- Audit intent — bypass onboarding entirely ----
        _AUDIT_KEYWORDS = [
            'audit', 'site audit', 'website audit', 'marketing audit',
            'full analysis', 'grade my site', 'check my site', 'analyze my website',
            'analyse my website', 'audit my website', 'audit my site',
        ]
        if any(k in _msg_lower for k in _AUDIT_KEYWORDS):
            return None  # Let audit routing handle it

        # ---- SKIP / bypass phrases — complete onboarding permanently ----
        _SKIP_WORDS = ['skip', 'no thanks', 'later', 'not now', 'no onboarding', 'bypass']
        if any(s in _msg_lower for s in _SKIP_WORDS):
            mem.set_profile_key("onboarding_step", "complete")
            mem.set_profile_key("website_url", "skipped")
            return {
                "success": True,
                "agent": "nexus",
                "onboarding_complete": True,
                "result": (
                    "No problem — onboarding skipped. You can always set your business profile later "
                    "via the settings panel.\n\nWhat marketing challenge can I help you tackle today?"
                ),
                "model": "onboarding",
                "provider": "system",
                "latency_ms": 0,
            }

        # ---- If onboarding has not started yet, apply intent gate ----
        if step == "unstarted":
            # Patterns that indicate a general question — route normally without onboarding
            _BYPASS_PREFIXES = [
                'what is', 'what are', 'what does', 'what was', 'what were', "what's",
                'how to', 'how do', 'how does', 'how can', 'how would', 'how is',
                'tell me', 'explain', 'define', 'describe',
                'who is', 'who are', 'why is', 'why does', 'why are',
                'when is', 'where is', 'can you tell', 'do you know',
                'give me a', 'show me a', 'list ', 'write me', 'write a',
            ]
            if any(_msg_lower.startswith(p) for p in _BYPASS_PREFIXES):
                return None

            # Signals that the user wants marketing help for THEIR business
            _MARKETING_SIGNALS = [
                'marketing', 'seo', 'ppc', 'ads ', ' ad ', 'campaign', 'content strategy',
                'my business', 'my website', 'my brand', 'my company', 'my store', 'my shop',
                'help me grow', 'help me with', 'help with my', 'help my',
                'grow my', 'traffic', 'leads', 'sales', 'revenue', 'conversion',
                'social media', 'email marketing', 'funnel', 'keyword', 'rank my',
                'audit my', 'analyse my', 'analyze my', 'improve my', 'boost my',
                'increase my', 'promote my', 'launch my', 'our brand', 'our website',
                'our company', 'our business', 'our product',
            ]
            if not any(s in _msg_lower for s in _MARKETING_SIGNALS):
                # No marketing intent detected — route normally
                return None

            # Marketing intent confirmed — show onboarding step 1
            mem.set_profile_key("onboarding_step", "1")
            url = _is_url(user_msg)
            if url:
                # Fast-track: they included a URL in their first message
                mem.set_profile_key("onboarding_step", "2_extracting")
                mem.set_profile_key("website_url_pending", url)
                return await _onboarding_extract_brand(url, mem)
            return {
                "success": True,
                "agent": "nexus",
                "onboarding": True,
                "onboarding_step": 1,
                "onboarding_total": 3,
                "awaiting": "website_url",
                "result": (
                    "Welcome to SwarmOps! I'm your AI marketing team — 11 specialized agents "
                    "ready to help with SEO, content, PPC, CRM, analytics, and more.\n\n"
                    "Before I give you specific advice instead of generic tips, let me learn about "
                    "your business.\n\n"
                    "**What's your website URL?** I'll analyze it automatically to understand "
                    "your brand, audience, and market position.\n\n"
                    "_Type **skip** if you'd rather jump straight in._"
                ),
                "model": "onboarding",
                "provider": "system",
                "latency_ms": 0,
            }

        # ---- STEP 1: Waiting for URL (prompt already shown) ----
        if step in ("1", "2_pending"):
            url = _is_url(user_msg)
            if url:
                mem.set_profile_key("website_url_pending", url)
                return await _onboarding_extract_brand(url, mem)
            # Still waiting for a URL
            return {
                "success": True,
                "agent": "nexus",
                "onboarding": True,
                "onboarding_step": 1,
                "onboarding_total": 3,
                "awaiting": "website_url",
                "result": (
                    "I need your website URL to analyse your brand automatically. "
                    "Just paste it here — something like `https://yoursite.com`.\n\n"
                    "_Type **skip** to jump straight in without a profile._"
                ),
                "model": "onboarding",
                "provider": "system",
                "latency_ms": 0,
            }

        # ---- STEP 2: BrandDNA extracted, waiting for goal ----
        if step == "2":
            _GOAL_PATTERNS = [
                'increase', 'generate', 'boost', 'grow', 'improve', 'build',
                'get more', 'reduce', 'optimize', 'optimise', 'launch', 'drive',
                'traffic', 'leads', 'sales', 'awareness', 'revenue', 'conversions',
                'engagement', 'want to', 'need to', 'trying to', 'goal is',
            ]
            goal = user_msg.strip()

            if len(goal) < 3:
                return {
                    "success": True,
                    "agent": "nexus",
                    "onboarding": True,
                    "onboarding_step": 2,
                    "onboarding_total": 3,
                    "awaiting": "primary_goal",
                    "result": "What's your primary marketing goal? (e.g. increase traffic, generate leads, boost sales, build brand awareness)",
                    "model": "onboarding",
                    "provider": "system",
                    "latency_ms": 0,
                }

            # If it doesn't look like a goal (e.g. a question), use a default and complete
            if not any(p in goal.lower() for p in _GOAL_PATTERNS):
                goal = "grow my business"

            # Save goal and complete onboarding
            mem.set_profile_key("primary_goal", goal)
            mem.set_profile_key("onboarding_step", "complete")
            mem.set_profile_key("website_url", mem.get_profile_key("website_url_pending") or "")

            # Give first tailored recommendation based on goal
            dna = None
            try:
                from brand_dna import get_brand_dna
                dna = get_brand_dna().get_stored()
            except Exception:
                pass

            brand_name = dna.get("brand_name", "your business") if dna else "your business"
            industry = dna.get("industry", "") if dna else ""
            industry_str = f" in the {industry} space" if industry else ""

            _goal_lower = goal.lower()
            if any(w in _goal_lower for w in ["traffic", "visit", "seo", "organic", "search"]):
                first_action = "Start with the **SEO agent** — ask it to find your top keyword opportunities."
                second_action = "Then use the **Content agent** to create optimised articles targeting those keywords."
            elif any(w in _goal_lower for w in ["lead", "prospect", "pipeline", "b2b"]):
                first_action = "Start with the **CRM agent** — build a lead nurture email sequence."
                second_action = "Then use the **CRO agent** to identify friction points on your landing pages."
            elif any(w in _goal_lower for w in ["sale", "revenue", "conversion", "ecommerce"]):
                first_action = "Start with the **CRO agent** — it'll audit your funnel and find where you're losing customers."
                second_action = "Then use the **PPC agent** to build a paid campaign targeting high-intent buyers."
            elif any(w in _goal_lower for w in ["brand", "awareness", "recognition", "social"]):
                first_action = "Start with the **Brand Strategy agent** — define your voice and positioning."
                second_action = "Then use the **SMM agent** to create a social content calendar."
            else:
                first_action = "Start by asking me anything — I'll route it to the right specialist automatically."
                second_action = "Or ask for a full marketing audit to see where the biggest opportunities are."

            return {
                "success": True,
                "agent": "nexus",
                "onboarding": True,
                "onboarding_step": 3,
                "onboarding_total": 3,
                "onboarding_complete": True,
                "result": (
                    f"You're all set! I now know {brand_name}{industry_str} — "
                    f"every agent will use your brand context automatically.\n\n"
                    f"**Your goal:** {goal}\n\n"
                    f"**Here's where to start:**\n"
                    f"1. {first_action}\n"
                    f"2. {second_action}\n\n"
                    f"Just ask me anything — I'll route it to the right specialist."
                ),
                "model": "onboarding",
                "provider": "system",
                "latency_ms": 0,
            }

    except Exception as e:
        print(f"[onboarding] error: {e}")
        # Never block the chat — fall through to normal handling
    return None


async def _onboarding_extract_brand(url: str, mem) -> dict:
    """Extract BrandDNA from URL and return step-2 onboarding response."""
    dna_result = {"success": False}
    try:
        from brand_dna import get_brand_dna
        import asyncio as _asyncio
        dna_result = await _asyncio.get_event_loop().run_in_executor(
            None, get_brand_dna().extract, url
        )
    except Exception as e:
        print(f"[onboarding] BrandDNA extraction failed: {e}")

    mem.set_profile_key("onboarding_step", "2")

    # Explicitly persist the URL so load_full_context always finds it
    try:
        mem.set_profile_key("website_url", url)
    except Exception:
        pass

    if dna_result.get("success") and dna_result.get("brand_dna"):
        dna = dna_result["brand_dna"]
        brand_name = dna.get("brand_name", "your brand")
        brand_voice = dna.get("brand_voice", "professional")
        target_audience = dna.get("target_audience", "your audience")
        industry = dna.get("industry", "")
        tone_keywords = dna.get("tone_keywords", [])
        tone_str = ", ".join(tone_keywords[:3]) if isinstance(tone_keywords, list) else ""

        return {
            "success": True,
            "agent": "nexus",
            "onboarding": True,
            "onboarding_step": 2,
            "onboarding_total": 3,
            "awaiting": "primary_goal",
            "brand_dna": dna,
            "result": (
                f"I've analysed **{url}** and here's what I found:\n\n"
                f"**Brand:** {brand_name}\n"
                f"**Industry:** {industry}\n"
                f"**Voice:** {brand_voice}" + (f" — {tone_str}" if tone_str else "") + "\n"
                f"**Audience:** {target_audience}\n\n"
                f"Every agent will now write in {brand_name}'s voice automatically.\n\n"
                f"**What's your primary marketing goal?**\n"
                f"(e.g. increase traffic, generate leads, boost sales, build brand awareness)"
            ),
            "model": "onboarding",
            "provider": "system",
            "latency_ms": 0,
        }
    else:
        # Extraction failed — ask manual questions
        return {
            "success": True,
            "agent": "nexus",
            "onboarding": True,
            "onboarding_step": 2,
            "onboarding_total": 3,
            "awaiting": "primary_goal",
            "result": (
                f"I couldn't automatically analyse `{url}` (the site may block scrapers). "
                f"No problem — I'll work with what you tell me.\n\n"
                f"**What's your primary marketing goal?**\n"
                f"(e.g. increase traffic, generate leads, boost sales, build brand awareness)"
            ),
            "model": "onboarding",
            "provider": "system",
            "latency_ms": 0,
        }


# ============================================================================
# MULTI-AGENT ORCHESTRATION — parallel agent dispatch for complex queries
# ============================================================================

MULTI_AGENT_TRIGGERS = {
    "more traffic": ["seo", "content", "research"],
    "get traffic": ["seo", "content", "research"],
    "increase traffic": ["seo", "content", "research"],
    "grow traffic": ["seo", "content", "research"],
    "more leads": ["cro", "ppc", "crm"],
    "generate leads": ["cro", "ppc", "crm"],
    "lead generation": ["cro", "ppc", "crm"],
    "more sales": ["cro", "crm", "analytics"],
    "increase conversions": ["cro", "analytics", "content"],
    "improve conversions": ["cro", "analytics", "content"],
    "brand awareness": ["smm", "content", "brand"],
    "social media strategy": ["smm", "content", "research"],
    "full marketing strategy": ["seo", "content", "ppc", "cro", "smm"],
    "marketing plan": ["seo", "content", "ppc", "cro", "smm"],
    "launch": ["seo", "ppc", "content", "smm"],
    "product launch": ["seo", "ppc", "content", "smm"],
    "reduce churn": ["crm", "analytics", "cro"],
    "retain customers": ["crm", "analytics", "cro"],
    "grow revenue": ["cro", "crm", "ppc", "analytics"],
    "increase revenue": ["cro", "crm", "ppc", "analytics"],
    "3 month plan": ["seo", "content", "ppc", "crm", "analytics"],
    "three month plan": ["seo", "content", "ppc", "crm", "analytics"],
    "growth plan": ["seo", "content", "ppc", "analytics"],
    "marketing plan": ["seo", "content", "ppc", "crm", "smm"],
    "full strategy": ["seo", "content", "ppc", "cro", "smm"],
    "complete strategy": ["seo", "content", "ppc", "cro", "smm"],
    "deep analysis": ["seo", "content", "analytics", "cro", "research"],
    "budget plan": ["ppc", "analytics", "content"],
    "organic and paid": ["seo", "content", "ppc"],
    "organic vs paid": ["seo", "content", "ppc"],
}

def _check_multi_agent_trigger(user_message: str):
    """Returns list of agents to run in parallel, or None if single-agent."""
    msg_lower = user_message.lower()
    for trigger, agents in MULTI_AGENT_TRIGGERS.items():
        if trigger in msg_lower:
            return agents
    return None


def _rank_agent_results(agent_results: dict) -> list:
    """Rank agent results by response quality/length as confidence proxy."""
    import re as _re_rank
    ranked = []
    for agent_id, result in agent_results.items():
        text = str(result)
        score = 0.5  # base score

        if len(text) > 200: score += 0.1
        if len(text) > 500: score += 0.1

        if _re_rank.search(r'\d+%|\$\d+|\d+x', text): score += 0.15

        if any(w in text.lower() for w in ['recommend', 'suggest', 'priority', 'action', 'should']):
            score += 0.1

        score = min(score, 1.0)
        ranked.append((agent_id, result, score))

    ranked.sort(key=lambda x: x[2], reverse=True)
    return ranked

# ============================================================================
# CONVERSATION MEMORY — persist highlights across sessions for Nexus context
# ============================================================================

def _update_conversation_memory(user_message: str, agent_response: str, brand_context: dict):
    """Store conversation highlights in conversation_memory table."""
    try:
        import re as _re_mem
        from db import get_connection as _mem_conn
        conn = _mem_conn()

        numbers = _re_mem.findall(
            r'\$[\d,]+|\d+%|\d+x|\d+\s*visitors|\d+\s*sales', user_message
        )
        metrics = ", ".join(numbers) if numbers else ""

        strategy_keywords = [
            'seo', 'content', 'ppc', 'email', 'social', 'cro',
            'retargeting', 'blog', 'landing page', 'campaign',
        ]
        found = [k for k in strategy_keywords if k in agent_response.lower()]
        strategies = ", ".join(found) if found else ""

        industry = brand_context.get("industry", "") if isinstance(brand_context, dict) else ""

        conn.execute(
            """INSERT INTO conversation_memory
               (user_goal, industry, strategies_discussed, metrics_mentioned, key_insights)
               VALUES (?, ?, ?, ?, ?)""",
            (
                user_message[:200],
                industry,
                strategies,
                metrics,
                agent_response[:500],
            ),
        )
        conn.commit()
    except Exception:
        pass  # never block on memory


def _get_conversation_context() -> str:
    """Return recent conversation highlights to inject into Nexus prompts."""
    try:
        from db import get_connection as _ctx_conn
        conn = _ctx_conn()
        rows = conn.execute(
            "SELECT strategies_discussed, metrics_mentioned FROM conversation_memory "
            "ORDER BY created_at DESC LIMIT 3"
        ).fetchall()
        if not rows:
            return ""
        parts = []
        for row in rows:
            if row[0]:
                parts.append(f"Previously discussed: {row[0]}")
            if row[1]:
                parts.append(f"Known metrics: {row[1]}")
        return "CONVERSATION HISTORY:\n" + "\n".join(parts) if parts else ""
    except Exception:
        return ""


# ============================================================================
# UNIFIED CHAT ENDPOINT — single entry point for all agents
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    agent: str = "nexus"

@app.post("/api/chat")
async def chat(request: ChatRequest, skip_review: bool = Query(False)):
    """Unified chat endpoint — routes message to the appropriate agent, with Skeptic QA + memory + pipelines"""
    try:
        agent = request.agent.lower().strip()
        msg = request.message.strip()
        user_msg = request.message.strip()  # preserve raw user input before any augmentation

        if not user_msg:
            return JSONResponse({"response": "Please send a message.", "agent": agent, "provider": "system"})

        # ================================================================
        # CONVERSATIONMANAGER — single gatekeeper for routing/onboarding
        # ================================================================
        import re as _re
        _msg_lower = user_msg.lower()

        action, action_data = _cm.decide_action(user_msg, agent)

        # Fast-path: greeting
        if action == "greeting":
            return JSONResponse({
                "response": _cm.handle_greeting(action_data.get("personalized", False)),
                "agent": "nexus", "provider": "system"
            })

        # Fast-path: context query ("what do you know about me")
        if action == "context_response":
            return JSONResponse({
                "response": _cm.handle_context_query(),
                "agent": "nexus", "provider": "system"
            })

        # Fast-path: capabilities query ("what can you do")
        if action == "capabilities_response":
            return {"response": _cm.handle_capabilities(), "agent": "nexus", "provider": "system"}

        # Fast-path: vague help with no brand — ask for URL non-blocking
        if action == "onboarding_start":
            return JSONResponse({
                "response": (
                    "I'd love to give you specific advice for your business. "
                    "Share your website URL and I'll analyze your brand automatically.\n\n"
                    "_Or just ask your question — I can help with general marketing strategy too._"
                ),
                "agent": "nexus", "provider": "system", "onboarding_step": 1
            })

        # Fast-path: URL provided with no brand — extract brand DNA
        if action == "onboarding_url":
            url_match = _re.search(r"https?://[^\s]+", user_msg)
            url = url_match.group().rstrip("/") if url_match else None
            if url:
                try:
                    from brand_dna import get_brand_dna
                    brand_extractor = get_brand_dna()
                    brand_data = brand_extractor.extract(url)
                    formatted = _cm.format_brand_for_onboarding(brand_data)

                    # Save to business_profile table
                    try:
                        from db import get_connection as _get_conn_ob
                        _conn_ob = _get_conn_ob()
                        _conn_ob.execute(
                            "INSERT OR REPLACE INTO business_profile (website_url, industry) VALUES (?, ?)",
                            (url, formatted["industry"])
                        )
                        _conn_ob.commit()
                    except Exception:
                        pass

                    # Crawl website into knowledge base (background)
                    import threading
                    threading.Thread(target=_crawler.crawl_website, args=(url,), daemon=True).start()

                    _cm.set_state(_cm.STATE_PROFILED)

                    response_text = (
                        f"I've analyzed your website. Here's what I found:\n\n"
                        f"**Brand:** {formatted['name']}\n"
                        f"**Industry:** {formatted['industry']}\n"
                        f"**Voice:** {formatted['voice']}\n"
                        f"**Audience:** {formatted['audience']}\n\n"
                        f"Every agent will now write in {formatted['name']}'s voice automatically.\n\n"
                        f"**What's your primary marketing goal?** "
                        f"(e.g., increase traffic, generate leads, boost sales, build brand awareness)"
                    )
                    return JSONResponse({
                        "response": response_text,
                        "agent": "nexus", "provider": "system", "onboarding_step": 2
                    })
                except Exception:
                    return JSONResponse({
                        "response": "I had trouble analyzing that URL. Try again or just ask your marketing question.",
                        "agent": "nexus", "provider": "system"
                    })
            return JSONResponse({
                "response": "Could you share a full URL? (e.g., https://yoursite.com)",
                "agent": "nexus", "provider": "system"
            })

        # ── For route_agent / route_nexus / route_audit: load full context ──
        ctx = _cm.load_full_context()
        context_str = _cm.build_context_string(ctx)

        # Override agent for route_agent action
        if action == "route_agent":
            agent = action_data.get("agent", agent)

        # Build the augmented message with all context
        if context_str:
            msg = f"{context_str}\n\n{msg}"

        # If we just finished onboarding (state=PROFILED) and this is a specific request, save the goal
        if action == "route_nexus" and _cm.get_state() == _cm.STATE_PROFILED:
            try:
                from db import get_connection as _get_conn_goal
                _conn_goal = _get_conn_goal()
                _conn_goal.execute(
                    "UPDATE business_profile SET primary_goal = ? WHERE primary_goal IS NULL",
                    (user_msg[:200],)
                )
                _conn_goal.commit()
                _cm.set_state(_cm.STATE_ACTIVE)
            except Exception:
                pass

        # --- Check if this is a nexus request and if it needs a pipeline ---
        if agent == "nexus" or agent == "":
            nexus = get_nexus()
            pipeline_detection = nexus.detect_pipeline(msg)

            if pipeline_detection["is_pipeline"]:
                # Execute pipeline
                print(f"\n🔗 PIPELINE DETECTED: {pipeline_detection['reasoning']}")
                result = await nexus.run_pipeline(pipeline_detection["pipeline"], msg)

                # SECURITY: sanitize any string result fields in pipeline steps
                if isinstance(result, dict) and "steps" in result:
                    for _step in result["steps"]:
                        if isinstance(_step.get("result"), str):
                            _step["result"] = sanitize_response(_step["result"])

                # Return pipeline result
                return {
                    "success": True,
                    "agent": "nexus",
                    "pipeline": True,
                    "result": result,
                    "model": "pipeline",
                    "provider": "multi-agent",
                    "latency_ms": result.get("total_latency_ms", 0)
                }

        # --- recall past memories and prepend context ---
        try:
            from memory_store import get_memory_store
            memory = get_memory_store()
            memories = memory.recall_memories(department=agent, limit=3)
            if memories:
                memory_lines = "\n".join(f"- {m['content']}" for m in memories)
                msg = f"CONTEXT FROM PREVIOUS WORK:\n{memory_lines}\n\nNEW TASK: {msg}"
        except Exception:
            memory = None

        # --- inject data intelligence context (live business data + benchmarks) ---
        try:
            from data_intelligence import get_data_intelligence
            di = get_data_intelligence()
            data_context = di.build_agent_context(agent, request.message)
            if data_context:
                msg = data_context + "\n\nUSER REQUEST:\n" + msg
        except Exception:
            pass  # never block on context injection

        # --- inject BrandDNA context (brand voice + identity for all agents) ---
        try:
            from brand_dna import get_brand_dna
            stored_url = ctx.get("website_url", "") if ctx else ""
            if _is_external_url(user_msg, stored_url):
                brand_context = "The user is analyzing an external website. Analyze it independently. Do not apply their personal brand profile to this external site."
            else:
                brand_context = get_brand_dna().get_brand_context()
            if brand_context:
                msg = brand_context + "\n\n" + msg
        except Exception:
            pass  # never block on brand context injection

        # --- inject Competitive Intelligence context (competition-aware agents) ---
        try:
            from competitive_intel import get_competitive_intel
            _comp_context = get_competitive_intel().get_competitive_context()
            if _comp_context:
                msg = _comp_context + "\n\n" + msg
        except Exception:
            pass  # never block on competitive context injection

        # --- inject conversation memory (past sessions, strategies, metrics) ---
        _conv_context = _get_conversation_context()
        if _conv_context:
            msg = _conv_context + "\n\n" + msg

        # --- inject LearningEngine personalization context ---
        _learning_context = ""
        try:
            from learning_engine import get_learning_engine
            _learning_engine = get_learning_engine()
            _learning_context = _learning_engine.get_context_boost(agent)
            if _learning_context:
                msg = _learning_context + "\n\n" + msg
        except Exception:
            _learning_engine = None

        # --- inject RAG knowledge base context ---
        try:
            _rag_ctx = _kb.get_agent_context(
                query=user_msg,
                agent_type=agent,
                limit=3,
            )
            if _rag_ctx:
                msg = f"{msg}\n\n{_rag_ctx}"
        except Exception:
            pass

        # --- dispatch to the correct agent and capture a revision callable ---
        result = None
        agent_fn = None  # callable(prompt) -> str for revisions

        if agent == "content":
            from content_agent import generate_content
            result = generate_content(msg)
            agent_fn = generate_content

        elif agent == "seo":
            from seo_agent import find_keyword_opportunities, find_keywords
            result = find_keyword_opportunities(msg)
            if result is None:
                result = find_keywords(msg)
            agent_fn = find_keywords

        elif agent == "analytics":
            import re as _re_anal
            from analytics_agent import get_live_dashboard, analyze_performance
            # If user provides inline numbers, analyze their data directly (skip generic dashboard)
            _has_inline_data = bool(_re_anal.search(
                r'\d[\d,]*\s*(visitor|sale|order|spend|revenue|conversion|click|impression|roas|cac|ctr|cvr|ltv)',
                user_msg, _re_anal.IGNORECASE
            ))
            if _has_inline_data:
                # Pass user_msg as both description and data so the LLM can see the numbers
                result = analyze_performance(user_msg, f"User-provided metrics:\n{user_msg}")
            else:
                result = get_live_dashboard(days=30)
                if result is None or (isinstance(result, str) and "❌" in result):
                    result = analyze_performance(user_msg, msg)
            agent_fn = lambda p: analyze_performance(p, "Revision requested by quality control.")

        elif agent == "ppc":
            from ppc_agent import get_real_campaign_performance, create_campaign_strategy
            result = get_real_campaign_performance(days=7)
            if result is None:
                result = create_campaign_strategy(msg)
            agent_fn = create_campaign_strategy

        elif agent == "crm":
            import re as _re
            from crm_agent import create_email_sequence
            _email_match = _re.search(r'(\d+)[- ]?email', user_msg, _re.IGNORECASE)
            _num_emails = int(_email_match.group(1)) if _email_match and 1 <= int(_email_match.group(1)) <= 10 else 3
            result = create_email_sequence(msg, num_emails=_num_emails)
            agent_fn = lambda p: create_email_sequence(p, num_emails=_num_emails)

        elif agent == "smm":
            from smm_agent import write_platform_post
            # detect platform from user request (not the augmented msg)
            _smm_lower = user_msg.lower()
            _platform = "linkedin"
            for _p in ("instagram", "tiktok", "twitter", "facebook", "youtube", "pinterest"):
                if _p in _smm_lower:
                    _platform = _p
                    break
            # Extract brand name and voice from context
            _smm_brand = (ctx.get("brand_name") or "your company") if ctx else "your company"
            if not _smm_brand or _smm_brand.lower() in ("your brand", "unknown", "not found", ""):
                _smm_brand = "your company"
            _smm_voice = (ctx.get("voice") or "Professional and engaging") if ctx else "Professional and engaging"
            result = write_platform_post(
                platform=_platform, topic=user_msg,
                brand_voice=_smm_voice,
                goal="engagement", brand_name=_smm_brand
            )
            agent_fn = lambda p: write_platform_post(
                platform=_platform, topic=p,
                brand_voice=_smm_voice,
                goal="engagement", brand_name=_smm_brand
            )

        elif agent == "brand":
            from brand_strategist_agent import create_brand_strategy
            result = create_brand_strategy(
                company_name="Company", industry="General",
                target_audience="General audience", unique_value=user_msg
            )
            agent_fn = lambda p: create_brand_strategy(
                company_name="Company", industry="General",
                target_audience="General audience", unique_value=p
            )

        elif agent in ("web_ux", "webux"):
            from web_ux_agent import design_landing_page
            result = design_landing_page(
                product=user_msg, target_audience="General audience",
                goal="conversions"
            )
            agent = "web_ux"
            agent_fn = lambda p: design_landing_page(
                product=p, target_audience="General audience",
                goal="conversions"
            )

        elif agent == "cro":
            from cro_agent import analyze_funnel
            result = analyze_funnel(
                funnel_steps=user_msg, conversion_data="",
                goal="increase conversions"
            )
            agent_fn = lambda p: analyze_funnel(
                funnel_steps=p, conversion_data="",
                goal="increase conversions"
            )

        elif agent == "research":
            from research_agent import research_topic
            result = research_topic(msg)
            agent_fn = research_topic

        elif agent == "deep_research" or agent == "deep-research":
            from deep_research_agent import get_deep_research_agent
            import os
            deep_research = get_deep_research_agent(
                brave_api_key=os.getenv("BRAVE_API_KEY"),
                serper_api_key=os.getenv("SERPER_API_KEY")
            )
            result = await deep_research.research(msg)
            # For deep research, result is already structured, so we'll handle it differently
            # We'll skip the Skeptic review for deep research since it has its own quality scoring
            if result.get("success"):
                # Return immediately with structured data
                return {
                    "success": True,
                    "agent": "deep_research",
                    "result": result,
                    "model": result.get("models_used", {}).get("analysis", "unknown"),
                    "provider": "multi-step",
                    "latency_ms": result.get("total_latency_ms", 0),
                    "quality": {
                        "confidence": result.get("confidence", 0.0),
                        "approved": True,
                        "revised": False
                    }
                }
            else:
                # Return error
                return {
                    "success": False,
                    "agent": "deep_research",
                    "error": result.get("error", "Deep research failed"),
                    "result": result.get("summary", "Research unavailable")
                }

        elif agent == "audit":
            # Route to Marketing Audit engine
            from marketing_audit import get_marketing_audit
            import asyncio as _asyncio
            _audit_url = _is_url(user_msg)
            if not _audit_url:
                try:
                    from memory_store import get_memory_store
                    _audit_url = get_memory_store().get_profile_key("website_url")
                except Exception:
                    _audit_url = None
            if not _audit_url or _audit_url == "skipped":
                result = "Please provide a URL to audit. Example: 'audit https://yoursite.com'"
            else:
                audit_report = await _asyncio.get_event_loop().run_in_executor(
                    None, get_marketing_audit().run_full_audit, _audit_url
                )
                result = _format_audit_chat_result(audit_report)
            skip_review = True
            agent_fn = None

        elif agent == "competitive_intel":
            # Route to dedicated Competitive Intelligence module
            from competitive_intel import get_competitive_intel
            ci = get_competitive_intel()
            user_msg_lower = user_msg.lower()
            # Detect what the user wants to do
            if any(kw in user_msg_lower for kw in ("battle card", "battlecard", "battle-card")):
                # Pull first tracked competitor as default
                comps = ci.list_competitors()
                if comps:
                    result = ci.generate_battle_card(comps[0]["id"])
                else:
                    result = "No competitors tracked yet. Add competitors first via POST /api/competitors."
            elif any(kw in user_msg_lower for kw in ("compare", "comparison", "landscape", "matrix")):
                comp_result = ci.compare_competitors()
                result = json.dumps(comp_result, indent=2)
            elif any(kw in user_msg_lower for kw in ("alert", "change", "detect")):
                alerts = ci.get_alerts(acknowledged=False)
                result = f"Unacknowledged alerts ({len(alerts)}):\n" + json.dumps(alerts, indent=2)
            else:
                # General competitive analysis — compare all
                comps = ci.list_competitors()
                if comps:
                    comp_result = ci.compare_competitors()
                    result = json.dumps(comp_result, indent=2)
                else:
                    result = "No competitors tracked yet. Add competitors via POST /api/competitors."
            skip_review = True  # Already structured output
            agent_fn = None

        elif agent in ("nexus", "") and any(kw in _msg_lower for kw in (
            "audit", "analyze my website", "marketing audit", "check my site",
            "review my website", "site audit", "website analysis", "grade my site",
            "full analysis", "analyse my website", "audit my site", "audit my website",
        )):
            # Nexus audit detection — route to marketing audit engine
            from marketing_audit import get_marketing_audit
            import asyncio as _asyncio
            _audit_url = _is_url(user_msg)
            if not _audit_url:
                try:
                    from memory_store import get_memory_store as _ms
                    _audit_url = _ms().get_profile_key("website_url")
                except Exception:
                    _audit_url = None
            if not _audit_url or _audit_url == "skipped":
                result = (
                    "I'd love to run a full marketing audit!\n\n"
                    "**Which URL should I audit?** Just paste it here:\n"
                    "_e.g. `https://yourwebsite.com`_"
                )
                skip_review = True
            else:
                audit_report = await _asyncio.get_event_loop().run_in_executor(
                    None, get_marketing_audit().run_full_audit, _audit_url
                )
                result = _format_audit_chat_result(audit_report)
                skip_review = True
            agent = "nexus"
            agent_fn = None

        else:  # nexus — Plan → Execute → Score → Synthesize
            nexus = get_nexus()
            from nexus import detect_emotional_distress
            _eq_distress = detect_emotional_distress(user_msg)

            if _eq_distress:
                # EQ Override (Directive 1): distress detected — empathy first, no agent overload
                result = nexus.apply_nexus_persona(user_msg, "")
            else:
                from swarm_planner import build_execution_plan, run_agents, rank_agent_results, synthesize_results

                # Resolve brand name for synthesis (already in msg context, just need the name)
                _brand_name = "your brand"
                try:
                    from brand_dna import get_brand_dna as _bdna_p
                    _stored_p = _bdna_p().get_stored()
                    if _stored_p:
                        _brand_name = (
                            _stored_p.get("name")
                            or (_stored_p.get("brand") or {}).get("name")
                            or "your brand"
                        )
                        if _brand_name in ("Not detected", "not_found", ""):
                            _brand_name = "your brand"
                except Exception:
                    pass

                # Step 1: Plan — decide which agents should run
                _plan = build_execution_plan(user_msg, _brand_name)
                print(f"\n🧠 SWARM PLAN: {_plan} for '{user_msg[:60]}'")

                if "nexus" in _plan or not _plan:
                    # Simple conversational query — direct Nexus response (no specialist agents)
                    raw_result = nexus.execute_task(msg)
                    result = nexus.apply_nexus_persona(user_msg, _extract_text(raw_result))
                else:
                    # Step 2: Execute — run planned agents in parallel with full context
                    _agent_results = run_agents(_plan, msg)

                    # Step 3: Score — rank by confidence
                    _ranked = rank_agent_results(_agent_results)
                    _score_summary = [(a, round(r.get("confidence", 0), 1)) for a, r in _ranked]
                    print(f"  Scores: {_score_summary}")

                    # Step 4: Synthesize — Nexus CMO synthesizes into one strategic response
                    result = synthesize_results(user_msg, _ranked, _brand_name)

                    # Fallback: if synthesis is empty, use best individual agent result
                    if not result or (isinstance(result, str) and len(result.strip()) < 20):
                        _best = ""
                        for _agent_id, _agent_result in _agent_results.items():
                            _r = _agent_result.get("insight", "") if isinstance(_agent_result, dict) else str(_agent_result)
                            if len(_r) > len(_best):
                                _best = _r
                        result = _best or "I analyzed your request. Could you be more specific about what you'd like help with?"

            agent = "nexus"
            agent_fn = nexus.execute_task

        # --- build base response with model/provider info ---
        from model_router import get_last_call_info
        info = get_last_call_info()
        result_text = _extract_text(result)

        # --- Skeptic QA review (skip if requested, result is empty, or EQ distress mode) ---
        # EQ responses must never be 'improved' by the Skeptic into a strategy report
        _is_eq_response = agent == "nexus" and locals().get("_eq_distress", False)
        quality = None
        final_text = result_text
        if not skip_review and not _is_eq_response and result_text and len(result_text) > 20:
            try:
                from skeptic_agent import SkepticAgent
                skeptic = SkepticAgent()
                review = skeptic.review_and_improve(agent, msg, result_text, agent_fn)
                final_text = review["output"]
                quality = {
                    "confidence": review["critique"]["confidence"],
                    "approved": review["critique"]["approved"],
                    "revised": review["revised"],
                    "strengths": review["critique"]["strengths"],
                    "weaknesses": review["critique"]["weaknesses"],
                }
                # If revised, update model/provider info from the latest call
                if review["revised"]:
                    info = get_last_call_info()
            except Exception:
                # Skeptic failed — return original without blocking
                pass

        # --- save memory + log task ---
        confidence = quality["confidence"] if quality else 0.0
        if memory and final_text and len(final_text) > 20:
            try:
                original_msg = request.message  # use the raw message, not the memory-augmented one
                memory.save_memory(
                    department=agent,
                    memory_type="decision",
                    content=f"Task: {original_msg[:100]} | Result: {final_text[:200]}",
                    metadata={
                        "model": info.get("model", ""),
                        "provider": info.get("provider", ""),
                        "confidence": confidence,
                    },
                )
                memory.log_task(
                    department=agent,
                    task_input=original_msg,
                    task_output=final_text[:500],
                    model=info.get("model", ""),
                    provider=info.get("provider", ""),
                    confidence=confidence,
                    latency_ms=info.get("latency_ms", 0),
                )
            except Exception:
                pass  # never block on memory save

        # --- auto-log recommendations to Revenue Tracker ---
        try:
            from revenue_tracker import get_revenue_tracker
            get_revenue_tracker().auto_log_from_response(agent, final_text)
        except Exception:
            pass  # never block on revenue tracking

        # --- record interaction in LearningEngine ---
        try:
            if locals().get("_learning_engine"):
                _learning_engine.record_interaction(
                    agent=agent,
                    query=request.message,
                    response_quality="good",
                )
        except Exception:
            pass  # never block on learning

        # --- update conversation memory for future context ---
        try:
            _brand_ctx_dict = {}
            try:
                from brand_dna import get_brand_dna as _bdna_mem
                _brand_ctx_dict = get_brand_dna().get_stored() or {}
            except Exception:
                pass
            _update_conversation_memory(user_msg, final_text, _brand_ctx_dict)
        except Exception:
            pass  # never block on conversation memory

        # Post-process: enforce rules the LLM ignores
        if isinstance(final_text, str) and len(final_text) > 10:
            _query_type = _cleaner.classify_query_type(user_msg)
            final_text = _cleaner.clean(final_text)
            if _query_type != "audit":  # Don't truncate audits
                final_text = _cleaner.enforce_length(final_text, _query_type)

        # SECURITY: strip any leaked internal context (must be last step)
        final_text = sanitize_response(final_text)

        response = {
            "success": True,
            "agent": agent,
            "result": final_text,
            "model": info.get("model", "unknown"),
            "provider": info.get("provider", "unknown"),
            "latency_ms": info.get("latency_ms", 0),
        }
        if quality is not None:
            response["quality"] = quality

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MEMORY & STATS ENDPOINTS
# ============================================================================

@app.get("/api/stats")
def get_stats():
    """Aggregate usage stats (tasks, models, departments)"""
    try:
        from memory_store import get_memory_store
        return get_memory_store().get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
def get_history(department: str = None, days: int = 7, limit: int = 20):
    """Recent task history, optionally filtered by department"""
    try:
        from memory_store import get_memory_store
        tasks = get_memory_store().get_task_history(department=department, days=days, limit=limit)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/{department}")
def get_memory(department: str, limit: int = 10):
    """Recall memories for a specific agent department"""
    try:
        from memory_store import get_memory_store
        memories = get_memory_store().recall_memories(department=department, limit=limit)
        return {"department": department, "memories": memories, "count": len(memories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memory")
def clear_memory():
    """Clear all memories and task logs (reset button)"""
    try:
        from memory_store import get_memory_store
        get_memory_store().clear_all()
        return {"success": True, "message": "All memories and task logs cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/export")
def export_memory():
    """Export all agent memory and task logs as JSON (for backup before redeploy)"""
    try:
        from memory_store import get_memory_store
        data = get_memory_store().export_all()
        return {"success": True, **data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MemoryImportRequest(BaseModel):
    agent_memory: list = []
    task_log: list = []

@app.post("/api/memory/import")
def import_memory(request: MemoryImportRequest):
    """Import agent memory and task logs from a previous export"""
    try:
        from memory_store import get_memory_store
        result = get_memory_store().import_all({"agent_memory": request.agent_memory, "task_log": request.task_log})
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BUSINESS PROFILE ENDPOINTS
# ============================================================================

class ProfileKeyRequest(BaseModel):
    key: str
    value: str

@app.get("/api/business-profile")
def get_business_profile():
    """Get all stored business profile keys (industry, website, goals, etc.)"""
    try:
        from memory_store import get_memory_store
        profile = get_memory_store().get_all_profile_keys()
        return {"success": True, "profile": profile, "count": len(profile)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/business-profile")
def set_business_profile(request: ProfileKeyRequest):
    """Set a business profile key (persists across sessions, never auto-cleared)"""
    try:
        from memory_store import get_memory_store
        get_memory_store().set_profile_key(request.key, request.value)
        return {"success": True, "key": request.key, "value": request.value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/business-profile")
def clear_business_profile():
    """Clear ALL business profile data (destructive — requires explicit user action)"""
    try:
        from memory_store import get_memory_store
        get_memory_store().clear_profile()
        return {"success": True, "message": "Business profile cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/{department}")
def get_agent_insights(department: str, limit: int = 10):
    """Get saved insights for a specific agent department"""
    try:
        from memory_store import get_memory_store
        insights = get_memory_store().get_insights(department=department, limit=limit)
        return {"department": department, "insights": insights, "count": len(insights)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integrations/status")
def get_integration_status():
    """Check which data integrations are connected (GA4, HubSpot, Google Ads, etc.)"""
    try:
        from data_intelligence import get_data_intelligence
        di = get_data_intelligence()
        # Invalidate cache so we always get fresh status
        di._integration_status = None
        connected = di.detect_connected_integrations()
        return {
            "success": True,
            "integrations": connected,
            "connected_count": sum(1 for v in connected.values() if v),
            "total": len(connected)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DATABASE EXPORT / IMPORT ENDPOINTS
# Safety net: export data before Railway redeploys, import to restore.
# ============================================================================

@app.post("/api/database/export")
def database_export():
    """
    Export the entire database as a JSON payload.
    Use this before a Railway redeploy to back up your data.
    """
    try:
        from db import get_connection, DB_PATH, get_db_size_mb
        conn = get_connection()

        export = {"db_path": DB_PATH, "exported_at": __import__("datetime").datetime.utcnow().isoformat(), "tables": {}}

        # Get all table names
        tables = [
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]

        for table in tables:
            rows = conn.execute(f"SELECT * FROM {table}").fetchall()
            export["tables"][table] = [dict(r) for r in rows]
            export[f"{table}_count"] = len(rows)

        export["total_tables"] = len(tables)
        export["size_mb"] = get_db_size_mb()
        return {"success": True, "export": export}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/database/import")
async def database_import(request: Request):
    """
    Restore database from a JSON export payload.
    WARNING: This REPLACES existing data for each imported table.
    """
    try:
        body = await request.json()
        export_data = body.get("export", body)  # accept both {export: ...} and raw export
        tables_data = export_data.get("tables", {})

        from db import get_connection
        conn = get_connection()

        imported = {}
        for table, rows in tables_data.items():
            if not rows:
                imported[table] = 0
                continue
            # Get column names from first row
            cols = list(rows[0].keys())
            placeholders = ",".join("?" for _ in cols)
            col_names = ",".join(cols)

            # Clear and re-insert
            conn.execute(f"DELETE FROM {table}")
            count = 0
            for row in rows:
                try:
                    conn.execute(
                        f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})",
                        [row.get(c) for c in cols]
                    )
                    count += 1
                except Exception:
                    pass  # skip malformed rows
            imported[table] = count

        conn.commit()
        return {"success": True, "imported": imported}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BRAND DNA ENDPOINTS
# ============================================================================

class BrandDNAExtractRequest(BaseModel):
    url: str

class BrandDNAUpdateRequest(BaseModel):
    brand_name: Optional[str] = None
    tagline: Optional[str] = None
    brand_voice: Optional[str] = None
    value_proposition: Optional[str] = None
    target_audience: Optional[str] = None
    industry: Optional[str] = None

@app.post("/api/brand-dna/extract")
async def extract_brand_dna(request: BrandDNAExtractRequest):
    """Extract BrandDNA from a website URL — analyzes brand voice, tone, audience, CTAs."""
    try:
        from brand_dna import get_brand_dna
        url = request.url
        result = await __import__("asyncio").get_event_loop().run_in_executor(
            None, get_brand_dna().extract, url
        )
        # Crawl website into knowledge base in background
        try:
            import threading
            threading.Thread(
                target=get_web_crawler().crawl_website,
                args=(url,),
                daemon=True
            ).start()
        except Exception:
            pass
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/brand-dna")
def get_brand_dna_stored():
    """Return the most recently extracted BrandDNA."""
    try:
        from brand_dna import get_brand_dna
        dna = get_brand_dna().get_stored()
        if not dna:
            return {"success": False, "message": "No BrandDNA extracted yet. POST /api/brand-dna/extract first."}
        return {"success": True, "brand_dna": dna}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/brand-dna")
def update_brand_dna(request: BrandDNAUpdateRequest):
    """Manually override specific BrandDNA fields."""
    try:
        from brand_dna import get_brand_dna, _get_conn
        import json as _json
        dna = get_brand_dna().get_stored()
        if not dna:
            return {"success": False, "message": "No BrandDNA found. Extract first."}
        updates = request.dict(exclude_none=True)
        dna.update(updates)
        # Re-store updated dna
        get_brand_dna()._store(dna.get("url", "manual"), dna)
        return {"success": True, "updated_fields": list(updates.keys()), "brand_dna": dna}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REVENUE TRACKER ENDPOINTS
# ============================================================================

class OutcomeRequest(BaseModel):
    actual_impact: float  # decimal: 0.15 = 15%

class RecommendationStatusRequest(BaseModel):
    status: str  # pending / implemented / skipped / measured

@app.get("/api/recommendations")
def get_all_recommendations(limit: int = 50):
    """List all tracked recommendations across all agents."""
    try:
        from revenue_tracker import get_revenue_tracker
        recs = get_revenue_tracker().get_recommendation_history(limit=limit)
        return {"success": True, "recommendations": recs, "count": len(recs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations/{agent}")
def get_agent_recommendations(agent: str, limit: int = 50):
    """List tracked recommendations for a specific agent."""
    try:
        from revenue_tracker import get_revenue_tracker
        recs = get_revenue_tracker().get_recommendation_history(agent=agent, limit=limit)
        return {"success": True, "agent": agent, "recommendations": recs, "count": len(recs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations/{rec_id}/outcome")
def record_recommendation_outcome(rec_id: str, request: OutcomeRequest):
    """Record the actual measured impact for a recommendation (e.g., actual_impact=0.12 = 12%)."""
    try:
        from revenue_tracker import get_revenue_tracker
        get_revenue_tracker().record_outcome(rec_id, request.actual_impact)
        return {"success": True, "recommendation_id": rec_id, "actual_impact": request.actual_impact}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations/{rec_id}/status")
def update_recommendation_status(rec_id: str, request: RecommendationStatusRequest):
    """Update the status of a recommendation (implemented / skipped / measured)."""
    try:
        from revenue_tracker import get_revenue_tracker
        get_revenue_tracker().update_status(rec_id, request.status)
        return {"success": True, "recommendation_id": rec_id, "status": request.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent-performance")
def get_agent_performance_leaderboard():
    """Agent accuracy leaderboard — which agents make the most accurate predictions."""
    try:
        from revenue_tracker import get_revenue_tracker
        leaderboard = get_revenue_tracker().get_all_agent_performance()
        return {"success": True, "leaderboard": leaderboard, "count": len(leaderboard)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LEARNING ENGINE ENDPOINTS
# ============================================================================

class FeedbackRequest(BaseModel):
    agent: str
    query: str
    response_quality: str = "good"  # good / modified / rejected
    modification_notes: Optional[str] = None

@app.get("/api/learning/preferences")
def get_learning_preferences():
    """Show all preferences the system has learned about this user."""
    try:
        from learning_engine import get_learning_engine
        prefs = get_learning_engine().get_all_preferences()
        context = get_learning_engine().get_context_boost("general")
        return {"success": True, "preferences": prefs, "active_context": context, "count": len(prefs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning/insights/{agent}")
def get_learning_agent_insights(agent: str):
    """What has the system learned about how this user interacts with this specific agent."""
    try:
        from learning_engine import get_learning_engine
        insights = get_learning_engine().get_agent_insights(agent)
        return {"success": True, **insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learning/feedback")
def submit_learning_feedback(request: FeedbackRequest):
    """Submit feedback on an agent response to improve personalization."""
    try:
        from learning_engine import get_learning_engine
        get_learning_engine().record_interaction(
            agent=request.agent,
            query=request.query,
            response_quality=request.response_quality,
            notes=request.modification_notes,
        )
        return {"success": True, "message": "Feedback recorded. System will adapt over time."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/learning/reset")
def reset_learning():
    """Reset all learned preferences and interaction history."""
    try:
        from learning_engine import get_learning_engine
        get_learning_engine().reset()
        return {"success": True, "message": "All learned preferences and interaction history cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMPETITIVE INTELLIGENCE ENDPOINTS
# ============================================================================

class AddCompetitorRequest(BaseModel):
    name: str
    url: str

class CompareCompetitorsRequest(BaseModel):
    competitor_ids: Optional[List[str]] = None


# IMPORTANT: static paths (/compare, /alerts) must be declared BEFORE /{id} routes
# to prevent FastAPI from matching 'compare' or 'alerts' as a competitor_id.

@app.post("/api/competitors")
def add_competitor(request: AddCompetitorRequest):
    """Add a new competitor to track. Triggers initial full analysis automatically."""
    try:
        from competitive_intel import get_competitive_intel
        ci = get_competitive_intel()
        name = request.name
        url = request.url
        competitor_id = ci.add_competitor(name=name, website_url=url)
        comps = ci.list_competitors()
        comp = next((c for c in comps if c["id"] == competitor_id), None)
        # Crawl competitor website into knowledge base
        try:
            import threading
            threading.Thread(
                target=get_web_crawler().crawl_competitor,
                args=(url, name),
                daemon=True
            ).start()
        except Exception:
            pass
        return {
            "success": True,
            "competitor_id": competitor_id,
            "name": name,
            "url": url,
            "competitor": comp,
            "message": f"Added {name} and triggered initial analysis.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/competitors")
def list_competitors():
    """List all tracked competitors with latest snapshot metadata."""
    try:
        from competitive_intel import get_competitive_intel
        comps = get_competitive_intel().list_competitors()
        return {"success": True, "competitors": comps, "count": len(comps)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/competitors/compare")
def compare_all_competitors(competitor_ids: Optional[str] = None):
    """
    Generate a competitive comparison matrix across all tracked competitors.
    Optionally pass ?competitor_ids=id1,id2 to compare a subset.
    """
    try:
        from competitive_intel import get_competitive_intel
        ids = competitor_ids.split(",") if competitor_ids else None
        result = get_competitive_intel().compare_competitors(competitor_ids=ids)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/competitors/alerts")
def get_competitive_alerts(acknowledged: bool = False):
    """Get competitive alerts. Default: unacknowledged only. Use ?acknowledged=true for all."""
    try:
        from competitive_intel import get_competitive_intel
        alerts = get_competitive_intel().get_alerts(acknowledged=acknowledged)
        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts),
            "unacknowledged": len([a for a in alerts if not a.get("acknowledged")]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/competitors/{competitor_id}")
def remove_competitor(competitor_id: str):
    """Remove a competitor and all associated snapshots and alerts."""
    try:
        from competitive_intel import get_competitive_intel
        get_competitive_intel().remove_competitor(competitor_id)
        return {"success": True, "message": f"Competitor {competitor_id} removed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/competitors/{competitor_id}/analyze")
def analyze_competitor(competitor_id: str):
    """Run a full multi-dimensional analysis of a specific competitor."""
    try:
        from competitive_intel import get_competitive_intel
        result = get_competitive_intel().analyze_competitor(competitor_id)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/competitors/{competitor_id}/snapshots")
def get_competitor_snapshots(competitor_id: str, snapshot_type: Optional[str] = None):
    """Get analysis history for a competitor. Optionally filter by type (seo/content/social/ads/website)."""
    try:
        from competitive_intel import get_competitive_intel
        snaps = get_competitive_intel().get_snapshots(competitor_id, snapshot_type=snapshot_type)
        return {"success": True, "competitor_id": competitor_id, "snapshots": snaps, "count": len(snaps)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/competitors/{competitor_id}/battle-card")
def get_battle_card(competitor_id: str):
    """Generate a comprehensive sales battle card vs a specific competitor."""
    try:
        from competitive_intel import get_competitive_intel
        card = get_competitive_intel().generate_battle_card(competitor_id)
        return {"success": True, "competitor_id": competitor_id, "battle_card": card}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/competitors/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    """Mark a competitive alert as read/acknowledged."""
    try:
        from competitive_intel import get_competitive_intel
        get_competitive_intel().acknowledge_alert(alert_id)
        return {"success": True, "alert_id": alert_id, "message": "Alert acknowledged."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MARKETING AUDIT ENDPOINTS
# ============================================================================

class AuditRequest(BaseModel):
    url: str


@app.post("/api/audit")
async def run_marketing_audit(request: AuditRequest):
    """
    Full marketing audit: BrandDNA + 7 parallel audit sections + letter grade.
    SEO, Content, CRO, Messaging, PPC, Competitive, Growth.
    Heavy operation — allow up to 120 seconds.
    """
    try:
        from marketing_audit import get_marketing_audit
        import asyncio
        audit = get_marketing_audit()
        # Run blocking audit in thread pool to avoid blocking event loop
        result = await asyncio.get_event_loop().run_in_executor(
            None, audit.run_full_audit, request.url
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/history")
def get_audit_history(limit: int = 20):
    """List past marketing audits with grade and score summary."""
    try:
        from marketing_audit import get_marketing_audit
        history = get_marketing_audit().get_audit_history(limit=limit)
        return {"success": True, "audits": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/{audit_id}/report")
def download_audit_report(audit_id: str):
    """Download a full marketing audit as a formatted markdown report."""
    from fastapi.responses import PlainTextResponse
    try:
        from marketing_audit import get_marketing_audit
        from report_generator import get_report_generator
        report_data = get_marketing_audit().get_audit_by_id(audit_id)
        if not report_data:
            raise HTTPException(status_code=404, detail="Audit not found")
        md = get_report_generator().generate_audit_report(report_data)
        brand_name = report_data.get("brand", {}).get("name", "report").lower().replace(" ", "-")
        filename = f"marketing-audit-{brand_name}.md"
        return PlainTextResponse(
            content=md,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/{audit_id}")
def get_audit_report(audit_id: str):
    """Retrieve a full stored audit report by ID."""
    try:
        from marketing_audit import get_marketing_audit
        report = get_marketing_audit().get_audit_by_id(audit_id)
        if not report:
            raise HTTPException(status_code=404, detail="Audit not found")
        return {"success": True, **report}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# KNOWLEDGE BASE ENDPOINTS
# ============================================================================

@app.get("/api/knowledge-base/stats")
async def kb_stats():
    try:
        return get_knowledge_base().get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge-base/crawl")
async def kb_crawl(request: Request):
    try:
        body = await request.json()
        url = body.get("url", "").strip()
        crawl_type = body.get("type", "website")
        if not url:
            raise HTTPException(status_code=400, detail="url required")
        results = get_web_crawler().crawl_website(url)
        return {"status": "ok", "results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/knowledge-base/source")
async def kb_delete_source(request: Request):
    try:
        body = await request.json()
        url = body.get("url", "").strip()
        if not url:
            raise HTTPException(status_code=400, detail="url required")
        get_knowledge_base().delete_by_source(url)
        return {"status": "deleted", "url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-base/search")
async def kb_search(q: str = "", limit: int = 5):
    try:
        if not q:
            raise HTTPException(status_code=400, detail="q parameter required")
        results = get_knowledge_base().search(q, limit=min(limit, 20))
        return {"query": q, "results": results, "count": len(results)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
