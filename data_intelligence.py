"""
Data Intelligence Layer - SwarmOps
The brain that makes every agent actually intelligent.
Collects, processes, and provides real business data context to all agents.
"""

import os
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()


class DataIntelligence:
    """
    Central data layer: checks connected integrations, fetches real data,
    computes metrics, and builds rich context strings for agents.

    If real APIs are connected → uses real data.
    If not → tells agents what specific data to ask the user for.
    """

    def __init__(self):
        self._integration_status: Optional[Dict[str, bool]] = None

    # ------------------------------------------------------------------
    # Integration Detection
    # ------------------------------------------------------------------

    def detect_connected_integrations(self) -> Dict[str, bool]:
        """Check which integrations are actually connected and working."""
        if self._integration_status is not None:
            return self._integration_status

        status = {
            "ga4": False,
            "hubspot": False,
            "google_ads": False,
            "dataforseo": False,
            "search_console": False,
            "wordpress": False,
        }

        try:
            from integrations.google_analytics import GoogleAnalytics
            status["ga4"] = GoogleAnalytics().available
        except Exception:
            pass

        try:
            from integrations.hubspot import HubSpot
            status["hubspot"] = HubSpot().available
        except Exception:
            pass

        try:
            from integrations.google_ads import GoogleAds
            status["google_ads"] = GoogleAds().available
        except Exception:
            pass

        try:
            from integrations.dataforseo import DataForSEO
            status["dataforseo"] = DataForSEO().available
        except Exception:
            pass

        try:
            from integrations.google_search_console import GoogleSearchConsole
            status["search_console"] = GoogleSearchConsole().available
        except Exception:
            pass

        try:
            from integrations.wordpress import WordPress
            status["wordpress"] = WordPress().available
        except Exception:
            pass

        self._integration_status = status
        return status

    # ------------------------------------------------------------------
    # Real Data Fetching (returns None if integration not connected)
    # ------------------------------------------------------------------

    def get_analytics_data(self, timeframe: str = "30d") -> Optional[Dict]:
        """
        Fetch real traffic data from GA4.
        Returns structured dict or None if GA4 not connected.
        """
        integrations = self.detect_connected_integrations()
        if not integrations.get("ga4"):
            return None

        try:
            from integrations.google_analytics import GoogleAnalytics
            days = int(timeframe.replace("d", "")) if timeframe.endswith("d") else 30
            ga = GoogleAnalytics()
            traffic = ga.get_traffic_summary(days=days)
            sources = ga.get_traffic_sources(days=days)
            pages = ga.get_page_performance(days=days)

            if not traffic:
                return None

            return {
                "sessions": traffic.get("sessions", 0),
                "users": traffic.get("users", 0),
                "pageviews": traffic.get("pageviews", 0),
                "bounce_rate": traffic.get("bounce_rate", 0),
                "avg_session_duration": traffic.get("avg_session_duration", 0),
                "conversion_rate": traffic.get("conversion_rate", 0),
                "conversions": traffic.get("conversions", 0),
                "new_users": traffic.get("new_users", 0),
                "top_sources": [
                    f"{s['source']}/{s['medium']}: {s['sessions']:,} sessions, {s['conversion_rate']}% CVR"
                    for s in (sources or [])[:5]
                ],
                "top_pages": [
                    f"{p['page_path']}: {p['sessions']:,} sessions, {p['bounce_rate']}% bounce"
                    for p in (pages or [])[:5]
                ],
                "timeframe": f"Last {days} days",
            }
        except Exception as e:
            print(f"[DataIntelligence] GA4 fetch error: {e}")
            return None

    def get_crm_data(self) -> Optional[Dict]:
        """
        Fetch contact and email stats from HubSpot.
        Returns structured dict or None if not connected.
        """
        integrations = self.detect_connected_integrations()
        if not integrations.get("hubspot"):
            return None

        try:
            from integrations.hubspot import HubSpot
            hs = HubSpot()
            contacts = hs.get_contacts(limit=1)  # Just for count
            stats = hs.get_email_stats()

            data = {
                "contacts_available": contacts is not None,
                "email_stats": stats,
            }
            return data if (contacts is not None or stats) else None
        except Exception as e:
            print(f"[DataIntelligence] HubSpot fetch error: {e}")
            return None

    def get_ads_data(self, days: int = 30) -> Optional[Dict]:
        """
        Fetch campaign performance from Google Ads.
        Returns structured dict or None if not connected.
        """
        integrations = self.detect_connected_integrations()
        if not integrations.get("google_ads"):
            return None

        try:
            from integrations.google_ads import GoogleAds
            ads = GoogleAds()
            campaigns = ads.get_campaign_performance(days=days)

            if not campaigns:
                return None

            total_spend = sum(c.get("cost_usd", 0) for c in campaigns)
            total_clicks = sum(c.get("clicks", 0) for c in campaigns)
            total_conversions = sum(c.get("conversions", 0) for c in campaigns)
            avg_cpa = total_spend / total_conversions if total_conversions > 0 else 0

            return {
                "total_campaigns": len(campaigns),
                "total_spend_usd": round(total_spend, 2),
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "avg_cpa_usd": round(avg_cpa, 2),
                "campaigns_summary": [
                    f"{c['name']}: ${c['cost_usd']} spent, {c['conversions']} conv, ${c.get('cpa_usd', 0)} CPA"
                    for c in campaigns[:5]
                ],
            }
        except Exception as e:
            print(f"[DataIntelligence] Google Ads fetch error: {e}")
            return None

    def get_seo_data(self, days: int = 28) -> Optional[Dict]:
        """
        Fetch rankings and keyword data from Search Console + DataForSEO.
        Returns structured dict or None if not connected.
        """
        integrations = self.detect_connected_integrations()
        has_gsc = integrations.get("search_console", False)
        has_dfs = integrations.get("dataforseo", False)

        if not has_gsc and not has_dfs:
            return None

        result = {}

        try:
            if has_gsc:
                from integrations.google_search_console import GoogleSearchConsole
                gsc = GoogleSearchConsole()
                queries = gsc.get_top_queries(days=days, limit=10)
                opportunities = gsc.get_keyword_opportunities(days=days)
                if queries:
                    result["top_queries"] = [
                        f"'{q['query']}': pos {q['position']}, {q['clicks']} clicks, {q['ctr']}% CTR"
                        for q in queries[:5]
                    ]
                if opportunities:
                    result["opportunities"] = [
                        f"'{o['query']}': {o['impressions']} impressions, pos {o['position']}"
                        for o in opportunities[:5]
                    ]
        except Exception as e:
            print(f"[DataIntelligence] GSC fetch error: {e}")

        return result if result else None

    # ------------------------------------------------------------------
    # Computed Metrics (Real Formulas — Never Hallucinated)
    # ------------------------------------------------------------------

    def compute_cac(self, total_spend: float, new_customers: int) -> Dict:
        """Customer Acquisition Cost = Total Marketing Spend / New Customers"""
        if not new_customers or new_customers == 0:
            return {"value": None, "note": "Need customer count to calculate CAC"}
        return {
            "value": round(total_spend / new_customers, 2),
            "formula": f"${total_spend} / {new_customers} customers",
            "confidence": "high",
        }

    def compute_ltv(self, avg_revenue_per_customer: float, avg_lifespan_months: float,
                    gross_margin: float = 1.0) -> Dict:
        """LTV = Avg Revenue Per Customer × Avg Lifespan × Gross Margin"""
        if avg_revenue_per_customer <= 0 or avg_lifespan_months <= 0:
            return {"value": None, "note": "Need revenue and lifespan data to calculate LTV"}
        value = avg_revenue_per_customer * avg_lifespan_months * gross_margin
        return {
            "value": round(value, 2),
            "formula": f"${avg_revenue_per_customer} × {avg_lifespan_months} months × {gross_margin} margin",
            "confidence": "high",
        }

    def compute_roas(self, revenue: float, ad_spend: float) -> Dict:
        """Return on Ad Spend = Revenue / Ad Spend"""
        if not ad_spend or ad_spend == 0:
            return {"value": None, "note": "Need ad spend data to calculate ROAS"}
        return {
            "value": round(revenue / ad_spend, 2),
            "formula": f"${revenue} revenue / ${ad_spend} spend",
            "confidence": "high",
        }

    def compute_conversion_rate(self, conversions: int, total_visitors: int) -> Dict:
        """Conversion Rate = Conversions / Total Visitors × 100"""
        if not total_visitors or total_visitors == 0:
            return {"value": None, "note": "Need visitor data to calculate conversion rate"}
        return {
            "value": round((conversions / total_visitors) * 100, 2),
            "formula": f"{conversions} conversions / {total_visitors:,} visitors",
            "confidence": "high",
        }

    def compute_churn_rate(self, lost_customers: int, start_customers: int) -> Dict:
        """Churn Rate = Lost Customers / Start-Period Customers × 100"""
        if not start_customers or start_customers == 0:
            return {"value": None, "note": "Need customer count data to calculate churn"}
        return {
            "value": round((lost_customers / start_customers) * 100, 2),
            "formula": f"{lost_customers} lost / {start_customers} starting customers",
            "confidence": "high",
        }

    def compute_funnel_metrics(self, stages: Dict[str, int]) -> Dict:
        """
        Compute drop-off rates between funnel stages.
        stages: ordered dict like {"visitors": 10000, "leads": 500, "customers": 50}
        """
        if not stages or len(stages) < 2:
            return {"error": "Need at least 2 funnel stages"}

        stage_names = list(stages.keys())
        stage_values = list(stages.values())
        funnel = []

        for i, (name, value) in enumerate(zip(stage_names, stage_values)):
            if i == 0:
                funnel.append({
                    "stage": name,
                    "count": value,
                    "conversion_from_prev": None,
                    "drop_off_pct": None,
                })
            else:
                prev = stage_values[i - 1]
                conv = (value / prev * 100) if prev > 0 else 0
                drop = 100 - conv
                funnel.append({
                    "stage": name,
                    "count": value,
                    "conversion_from_prev": round(conv, 1),
                    "drop_off_pct": round(drop, 1),
                })

        # Find biggest drop
        drops = [(s["stage"], s["drop_off_pct"]) for s in funnel[1:]]
        biggest_drop = max(drops, key=lambda x: x[1]) if drops else None

        return {
            "stages": funnel,
            "biggest_drop_stage": biggest_drop[0] if biggest_drop else None,
            "biggest_drop_pct": biggest_drop[1] if biggest_drop else None,
            "overall_conversion": round(
                (stage_values[-1] / stage_values[0] * 100) if stage_values[0] > 0 else 0, 2
            ),
        }

    # ------------------------------------------------------------------
    # Business Profile Helpers
    # ------------------------------------------------------------------

    def get_business_profile(self) -> Dict[str, str]:
        """Retrieve stored business profile from memory."""
        try:
            from memory_store import get_memory_store
            store = get_memory_store()
            return store.get_all_profile_keys()
        except Exception:
            return {}

    def set_profile_key(self, key: str, value: str):
        """Store a business profile key."""
        try:
            from memory_store import get_memory_store
            store = get_memory_store()
            store.set_profile_key(key, value)
        except Exception:
            pass

    def get_past_insights(self, department: str, limit: int = 5) -> List[str]:
        """Get relevant past insights for a department."""
        try:
            from memory_store import get_memory_store
            store = get_memory_store()
            insights = store.get_insights(department=department, limit=limit)
            return [i["content"] for i in insights]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Context Builder — The KEY Function
    # ------------------------------------------------------------------

    def build_agent_context(self, department: str, user_message: str) -> str:
        """
        Build a rich data context string to inject into any agent's prompt.
        Called BEFORE every agent generates a response.

        Returns a formatted string ready to prepend to the user message.
        """
        integrations = self.detect_connected_integrations()
        connected = [k for k, v in integrations.items() if v]
        missing = [k for k, v in integrations.items() if not v]

        profile = self.get_business_profile()
        past_insights = self.get_past_insights(department, limit=3)

        lines = ["=== SWARMOPS DATA CONTEXT ==="]

        # Business profile
        if profile:
            lines.append("\nBUSINESS PROFILE (stored from previous sessions):")
            for key, val in profile.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {val}")
        else:
            lines.append("\nBUSINESS PROFILE: Not yet configured (ask user for details if needed)")

        # Connected integrations
        if connected:
            lines.append(f"\nCONNECTED INTEGRATIONS: {', '.join(connected).upper()}")
        else:
            lines.append("\nCONNECTED INTEGRATIONS: None (all recommendations will be based on provided data or general best practices)")

        # Live data for relevant departments
        analytics_data = None
        if department in ("analytics", "cro", "ppc", "nexus") or "analytics" in user_message.lower():
            analytics_data = self.get_analytics_data()
            if analytics_data:
                lines.append(f"\nLIVE GA4 DATA ({analytics_data['timeframe']}):")
                lines.append(f"  Sessions: {analytics_data['sessions']:,} | Users: {analytics_data['users']:,}")
                lines.append(f"  Bounce Rate: {analytics_data['bounce_rate']}% | Session Duration: {analytics_data['avg_session_duration']}s")
                lines.append(f"  Conversion Rate: {analytics_data['conversion_rate']}% | Conversions: {analytics_data['conversions']:,}")
                if analytics_data.get("top_sources"):
                    lines.append("  Top Sources: " + " | ".join(analytics_data["top_sources"][:3]))

        ads_data = None
        if department in ("ppc", "analytics") or "ad" in user_message.lower() or "ppc" in user_message.lower():
            ads_data = self.get_ads_data()
            if ads_data:
                lines.append(f"\nLIVE GOOGLE ADS DATA:")
                lines.append(f"  Campaigns: {ads_data['total_campaigns']} | Total Spend: ${ads_data['total_spend_usd']}")
                lines.append(f"  Clicks: {ads_data['total_clicks']:,} | Conversions: {ads_data['total_conversions']} | Avg CPA: ${ads_data['avg_cpa_usd']}")

        seo_data = None
        if department in ("seo", "content"):
            seo_data = self.get_seo_data()
            if seo_data and seo_data.get("top_queries"):
                lines.append(f"\nLIVE SEARCH CONSOLE DATA:")
                for q in seo_data["top_queries"][:3]:
                    lines.append(f"  {q}")

        crm_data = None
        if department in ("crm", "analytics"):
            crm_data = self.get_crm_data()
            if crm_data and crm_data.get("email_stats"):
                lines.append(f"\nLIVE HUBSPOT DATA:")
                stats = crm_data["email_stats"]
                if isinstance(stats, dict):
                    for k, v in list(stats.items())[:4]:
                        lines.append(f"  {k}: {v}")

        # Industry benchmarks (if industry known)
        industry = profile.get("industry", "general")
        if industry != "general":
            try:
                from benchmarks import get_all_benchmarks_summary
                lines.append(f"\n{get_all_benchmarks_summary(industry)}")
            except Exception:
                pass

        # Past insights
        if past_insights:
            lines.append(f"\nPAST INSIGHTS ({department.upper()} AGENT):")
            for insight in past_insights:
                lines.append(f"  - {insight}")

        # Data gaps
        data_gaps = []
        if not analytics_data and "ga4" not in connected:
            data_gaps.append("No website analytics (GA4 not connected)")
        if not ads_data and "google_ads" not in connected:
            data_gaps.append("No ad performance data (Google Ads not connected)")
        if not crm_data and "hubspot" not in connected:
            data_gaps.append("No CRM data (HubSpot not connected)")
        if not seo_data and "dataforseo" not in connected and "search_console" not in connected:
            data_gaps.append("No live SEO data (Search Console/DataForSEO not connected)")

        # Only show profile gaps if no profile
        if not profile.get("website_url"):
            data_gaps.append("Website URL unknown")
        if not profile.get("industry"):
            data_gaps.append("Industry unknown")
        if not profile.get("monthly_budget"):
            data_gaps.append("Marketing budget unknown")

        if data_gaps:
            lines.append(f"\nDATA GAPS (ask user if critical for this request):")
            for gap in data_gaps[:4]:
                lines.append(f"  - {gap}")

        lines.append("=== END CONTEXT ===\n")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Missing Data Questions Generator
    # ------------------------------------------------------------------

    def get_required_data_questions(self, department: str, user_message: str) -> List[str]:
        """
        Return specific questions to ask the user if real data isn't available.
        NOT generic — specific to the department and request.
        """
        profile = self.get_business_profile()
        questions = []

        # Universal — check profile first
        if not profile.get("website_url"):
            questions.append("What is your website URL?")
        if not profile.get("industry"):
            questions.append("What industry are you in? (e.g., SaaS, ecommerce, local business, B2B)")

        department_questions = {
            "seo": [
                "What are your top 5 target keywords?",
                "What is your current monthly organic traffic (approximate)?",
                "Who are your top 3 competitors?",
                "What is your domain age/authority (if known)?",
            ],
            "analytics": [
                "What is your monthly website traffic (sessions)?",
                "What is your current conversion rate?",
                "What is your monthly marketing spend?",
                "How many new customers did you acquire last month?",
                "What are your primary conversion goals (purchases, leads, signups)?",
            ],
            "ppc": [
                "What is your current monthly ad spend?",
                "Which platforms are you advertising on (Google, Facebook, LinkedIn)?",
                "What is your target cost per acquisition (CPA)?",
                "What is your average sale value or customer LTV?",
            ],
            "crm": [
                "What is your email list size?",
                "What is your current average open rate?",
                "What is your average click-through rate?",
                "What lifecycle stages do your contacts go through?",
            ],
            "content": [
                "Who is your target audience (demographics, pain points)?",
                "What is your brand voice (professional, casual, authoritative)?",
                "What is the primary goal of this content (SEO, awareness, conversions)?",
                "What content do you currently publish?",
            ],
            "smm": [
                "Which social platforms are you on?",
                "What are your follower counts on each platform?",
                "How often do you currently post?",
                "What is your primary social media goal (brand awareness, leads, engagement)?",
            ],
            "cro": [
                "What is your current overall conversion rate?",
                "Which pages have the most traffic?",
                "Where do users drop off in your funnel?",
                "What is your current checkout/signup completion rate?",
            ],
            "brand": [
                "What are your core brand values (3-5 words)?",
                "Who is your ideal customer (be specific)?",
                "What makes you different from competitors?",
                "What is your brand personality (premium, playful, expert, etc.)?",
            ],
        }

        dept_qs = department_questions.get(department, [])

        # Only ask what we don't already know
        for q in dept_qs[:3]:
            questions.append(q)

        return questions[:5]  # Max 5 questions


# Singleton
_di = None

def get_data_intelligence() -> DataIntelligence:
    global _di
    if _di is None:
        _di = DataIntelligence()
    return _di
