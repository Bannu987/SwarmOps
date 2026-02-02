"""
MarketingOS 2.0 - FastAPI Backend
Full Nexus orchestrator + 10 agents + real integrations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize FastAPI first (before heavy imports)
app = FastAPI(
    title="MarketingOS 2.0 API",
    description="AI-Powered Marketing with 10 Agents + Real Integrations",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy loading for heavy modules
_nexus = None
def get_nexus():
    global _nexus
    if _nexus is None:
        from nexus import Nexus
        _nexus = Nexus()
    return _nexus

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

class EmailRequest(BaseModel):
    contact_id: str
    email_template_id: str
    template_variables: Optional[Dict] = None

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
        "message": "MarketingOS 2.0 API",
        "version": "2.0.0",
        "agents": 10,
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "agents": 10}

@app.get("/api/integrations/status")
def integration_status():
    """Check which integrations are connected"""
    status = {}

    try:
        from integrations.wordpress import WordPress
        status['wordpress'] = WordPress().available
    except:
        status['wordpress'] = False

    try:
        from integrations.hubspot import HubSpot
        status['hubspot'] = HubSpot().available
    except:
        status['hubspot'] = False

    try:
        from integrations.dataforseo import DataForSEO
        status['dataforseo'] = DataForSEO().available
    except:
        status['dataforseo'] = False

    try:
        from integrations.google_analytics import GoogleAnalytics
        status['ga4'] = GoogleAnalytics().available
    except:
        status['ga4'] = False

    try:
        from integrations.google_search_console import GoogleSearchConsole
        status['search_console'] = GoogleSearchConsole().available
    except:
        status['search_console'] = False

    try:
        from integrations.google_ads import GoogleAds
        status['google_ads'] = GoogleAds().available
    except:
        status['google_ads'] = False

    return {"integrations": status, "connected": sum(status.values()), "total": len(status)}

# ============================================================================
# NEXUS ENDPOINTS (Smart Routing)
# ============================================================================

@app.post("/api/task")
def execute_task(request: TaskRequest):
    """Execute any task via Nexus smart routing"""
    try:
        nexus = get_nexus()
        result = nexus.execute_task(request.goal)
        return {"success": True, "goal": request.goal, "result": result}
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
        return {"success": True, "debate": result}
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
        return {"success": True, "result": result, "trigger": request.trigger if request else "manual"}
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
        return {"success": True, "agent": "content", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANALYTICS AGENT
# ============================================================================

@app.get("/api/analytics/dashboard")
def analytics_dashboard(days: int = 30):
    try:
        from analytics_agent import get_live_dashboard
        result = get_live_dashboard(days=days)
        return {"success": True, "agent": "analytics", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/anomalies")
def detect_anomalies(days: int = 7):
    try:
        from analytics_agent import detect_live_anomalies
        result = detect_live_anomalies(days=days)
        return {"success": True, "agent": "analytics", "anomalies": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SEO AGENT
# ============================================================================

@app.get("/api/seo/rankings")
def get_rankings(days: int = 28):
    try:
        from seo_agent import get_real_rankings
        result = get_real_rankings(days=days)
        return {"success": True, "agent": "seo", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seo/keywords/{keyword}")
def get_keyword_data(keyword: str, location_code: int = 2840):
    try:
        from seo_agent import get_real_keyword_data
        result = get_real_keyword_data(keyword, location_code=location_code)
        return {"success": True, "agent": "seo", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seo/opportunities")
def keyword_opportunities(topic: str = "marketing"):
    try:
        from seo_agent import find_keyword_opportunities
        result = find_keyword_opportunities(topic)
        return {"success": True, "agent": "seo", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PPC AGENT
# ============================================================================

@app.get("/api/ppc/campaigns")
def get_campaigns(days: int = 7):
    try:
        from ppc_agent import get_real_campaign_performance
        result = get_real_campaign_performance(days=days)
        return {"success": True, "agent": "ppc", "campaigns": result}
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
        return {"success": True, "agent": "ppc", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ppc/optimize")
def optimize_campaigns(days: int = 7):
    try:
        from ppc_agent import auto_optimize_campaigns
        result = auto_optimize_campaigns(days=days)
        return {"success": True, "agent": "ppc", "recommendations": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CRM AGENT
# ============================================================================

@app.get("/api/crm/contacts")
def get_contacts(limit: int = 100):
    try:
        from crm_agent import get_real_contacts
        result = get_real_contacts(limit=limit)
        return {"success": True, "agent": "crm", "contacts": result}
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
        return {"success": True, "agent": "crm", "contact": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crm/email-performance")
def email_performance():
    try:
        from crm_agent import get_real_email_performance
        result = get_real_email_performance()
        return {"success": True, "agent": "crm", "stats": result}
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
        return {"success": True, "agent": "smm", "trends": result}
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
        return {"success": True, "agent": "smm", "post": result}
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
        return {"success": True, "agent": "smm", "calendar": result}
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
        return {"success": True, "agent": "research", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/research/topic")
def research_topic_get(topic: str):
    try:
        from research_agent import research_topic
        result = research_topic(topic)
        return {"success": True, "agent": "research", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
