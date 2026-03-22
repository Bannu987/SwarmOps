"""
Execution Engine for SwarmOps.
Handles publishing content, deploying campaigns, and managing approvals.
Works in preview/demo mode without API keys.
Connects to real APIs (WordPress, Google Ads, HubSpot) when credentials are set.

ARCHITECTURE:
  Agent generates recommendation → Execution engine creates deployable artifact
  → Human reviews (approval queue) → Engine deploys to platform

SAFETY: Nothing goes live without explicit human approval.
"""
import os
import json
import logging
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Unified execution layer for SwarmOps marketing actions."""

    def __init__(self):
        self.approval_queue = []  # In-memory queue (SQLite in production)
        self.execution_log = []
        self._check_credentials()

    def _check_credentials(self):
        """Check which execution platforms are available."""
        self.platforms = {
            "wordpress": {
                "available": bool(os.environ.get("WORDPRESS_URL") and os.environ.get("WORDPRESS_TOKEN")),
                "url": os.environ.get("WORDPRESS_URL", ""),
                "name": "WordPress",
            },
            "google_ads": {
                "available": bool(os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")),
                "name": "Google Ads",
            },
            "hubspot_email": {
                "available": bool(os.environ.get("HUBSPOT_API_KEY")),
                "name": "HubSpot Email",
            },
            "linkedin": {
                "available": bool(os.environ.get("LINKEDIN_ACCESS_TOKEN")),
                "name": "LinkedIn",
            },
            "twitter": {
                "available": bool(os.environ.get("TWITTER_BEARER_TOKEN")),
                "name": "Twitter/X",
            },
        }

    def get_platform_status(self):
        """Return status of all execution platforms."""
        return {
            name: {
                "name": info["name"],
                "connected": info["available"],
                "status": "Connected" if info["available"] else "Preview mode",
            }
            for name, info in self.platforms.items()
        }

    # ============================================================
    # CONTENT PUBLISHING
    # ============================================================

    def prepare_blog_post(self, title, content, target_keyword="",
                           meta_description="", tags=None,
                           schema_markup=None, brand_context=""):
        """Prepare a blog post for publishing. Returns a deployable artifact."""
        artifact = {
            "id": self._generate_id("post"),
            "type": "blog_post",
            "platform": "wordpress",
            "status": "pending_approval",
            "created_at": datetime.now().isoformat(),
            "content": {
                "title": title,
                "body": content,
                "meta_description": meta_description or content[:155],
                "target_keyword": target_keyword,
                "tags": tags or [],
                "schema_markup": schema_markup,
                "word_count": len(content.split()),
                "reading_time_min": max(1, len(content.split()) // 200),
            },
            "seo_checklist": {
                "has_target_keyword_in_title": target_keyword.lower() in title.lower() if target_keyword else False,
                "has_meta_description": bool(meta_description),
                "has_schema_markup": bool(schema_markup),
                "word_count_adequate": len(content.split()) >= 300,
                "has_internal_links": "[link]" in content.lower() or "](/)" in content,
            },
            "deploy_config": {
                "wordpress_url": self.platforms["wordpress"].get("url", ""),
                "publish_status": "draft",
                "categories": [],
                "featured_image": None,
            },
        }
        self.approval_queue.append(artifact)
        return artifact

    def deploy_blog_post(self, artifact_id):
        """Deploy an approved blog post to WordPress."""
        artifact = self._find_artifact(artifact_id)
        if not artifact:
            return {"success": False, "error": "Artifact not found"}
        if artifact["status"] != "approved":
            return {"success": False, "error": "Artifact not approved yet"}

        if not self.platforms["wordpress"]["available"]:
            return {
                "success": True,
                "preview_mode": True,
                "message": f"Blog post '{artifact['content']['title']}' would be published as draft to WordPress.",
                "details": {
                    "title": artifact["content"]["title"],
                    "word_count": artifact["content"]["word_count"],
                    "url": f"{self.platforms['wordpress'].get('url', 'https://yourblog.com')}/draft/{artifact['id']}",
                },
                "note": "Connect WordPress API to publish for real. Set WORDPRESS_URL and WORDPRESS_TOKEN environment variables.",
            }

        try:
            import requests
            wp_url = self.platforms["wordpress"]["url"]
            wp_token = os.environ.get("WORDPRESS_TOKEN")
            response = requests.post(
                f"{wp_url}/wp-json/wp/v2/posts",
                headers={"Authorization": f"Bearer {wp_token}", "Content-Type": "application/json"},
                json={
                    "title": artifact["content"]["title"],
                    "content": artifact["content"]["body"],
                    "status": "draft",
                    "meta": {"description": artifact["content"]["meta_description"]},
                },
                timeout=30,
            )
            if response.status_code in [200, 201]:
                result = response.json()
                artifact["status"] = "deployed"
                artifact["deployed_at"] = datetime.now().isoformat()
                artifact["deployed_url"] = result.get("link", "")
                self.execution_log.append({
                    "action": "blog_post_published",
                    "artifact_id": artifact_id,
                    "url": result.get("link"),
                    "timestamp": datetime.now().isoformat(),
                })
                return {"success": True, "preview_mode": False, "url": result.get("link"),
                        "wp_post_id": result.get("id"), "status": "draft"}
            return {"success": False, "error": f"WordPress API error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================
    # GOOGLE ADS CAMPAIGN GENERATION
    # ============================================================

    def prepare_ad_campaign(self, campaign_name, campaign_type="search",
                             keywords=None, ad_copy=None, budget_daily=0,
                             target_audience="", landing_page="",
                             brand_context=""):
        """Prepare a Google Ads campaign artifact."""
        artifact = {
            "id": self._generate_id("ads"),
            "type": "google_ads_campaign",
            "platform": "google_ads",
            "status": "pending_approval",
            "created_at": datetime.now().isoformat(),
            "campaign": {
                "name": campaign_name,
                "type": campaign_type,
                "budget_daily_usd": budget_daily,
                "budget_monthly_usd": budget_daily * 30,
                "bidding_strategy": "maximize_conversions" if budget_daily >= 20 else "maximize_clicks",
                "start_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "target_audience": target_audience,
                "landing_page": landing_page,
            },
            "ad_groups": self._generate_ad_groups(keywords or [], ad_copy or []),
            "keywords": {
                "total": len(keywords or []),
                "match_types": ["broad", "phrase"],
                "negative_keywords": [],
            },
            "ads": {
                "responsive_search_ads": (ad_copy or [])[:3],
                "headlines_count": sum(len(ad.get("headlines", [])) for ad in (ad_copy or [])),
                "descriptions_count": sum(len(ad.get("descriptions", [])) for ad in (ad_copy or [])),
            },
            "estimated_performance": {
                "estimated_daily_clicks": max(10, budget_daily * 2),
                "estimated_cpc": round(budget_daily / max(10, budget_daily * 2), 2),
                "estimated_monthly_conversions": max(3, int(budget_daily * 30 * 0.03)),
                "estimated_cpa": round(budget_daily * 30 / max(3, int(budget_daily * 30 * 0.03)), 2),
            },
        }
        self.approval_queue.append(artifact)
        return artifact

    def _generate_ad_groups(self, keywords, ad_copy):
        if not keywords:
            return []
        groups = []
        chunk_size = max(1, len(keywords) // 3)
        for i in range(0, len(keywords), chunk_size):
            chunk = keywords[i:i + chunk_size]
            group_name = chunk[0] if chunk else f"Ad Group {i // chunk_size + 1}"
            groups.append({
                "name": f"AG: {group_name[:30]}",
                "keywords": chunk,
                "match_type": "broad",
                "ads": ad_copy[:2] if ad_copy else [],
            })
        return groups[:3]

    def deploy_ad_campaign(self, artifact_id):
        """Deploy an approved Google Ads campaign."""
        artifact = self._find_artifact(artifact_id)
        if not artifact:
            return {"success": False, "error": "Artifact not found"}

        if not self.platforms["google_ads"]["available"]:
            return {
                "success": True,
                "preview_mode": True,
                "message": f"Campaign '{artifact['campaign']['name']}' ready for deployment.",
                "details": {
                    "campaign": artifact["campaign"]["name"],
                    "budget": f"${artifact['campaign']['budget_daily_usd']}/day",
                    "ad_groups": len(artifact["ad_groups"]),
                    "keywords": artifact["keywords"]["total"],
                    "estimated_monthly_conversions": artifact["estimated_performance"]["estimated_monthly_conversions"],
                },
                "note": "Connect Google Ads API to deploy. Set GOOGLE_ADS_DEVELOPER_TOKEN environment variable.",
                "export_ready": True,
                "export_format": "Google Ads Editor CSV",
            }
        return {"success": False, "error": "Google Ads API integration coming in next release"}

    # ============================================================
    # EMAIL SEQUENCE
    # ============================================================

    def prepare_email_sequence(self, sequence_name, emails=None,
                                target_segment="", brand_context=""):
        """Prepare an email nurture sequence."""
        artifact = {
            "id": self._generate_id("email"),
            "type": "email_sequence",
            "platform": "hubspot_email",
            "status": "pending_approval",
            "created_at": datetime.now().isoformat(),
            "sequence": {
                "name": sequence_name,
                "target_segment": target_segment,
                "total_emails": len(emails or []),
                "duration_days": len(emails or []) * 3,
            },
            "emails": emails or [],
            "metrics_to_track": ["open_rate", "click_through_rate", "reply_rate",
                                  "conversion_rate", "revenue_per_email"],
            "ab_test_plan": {
                "test_element": "subject_line",
                "variant_a": (emails[0]["subject"] if emails else ""),
                "variant_b": "",
                "split": "50/50",
                "minimum_sample": 100,
                "significance_level": 0.95,
            },
        }
        self.approval_queue.append(artifact)
        return artifact

    # ============================================================
    # SOCIAL MEDIA
    # ============================================================

    def prepare_social_post(self, platform, content, hashtags=None,
                             media_description="", schedule_time=None,
                             brand_context=""):
        """Prepare a social media post for publishing."""
        limits = self._get_platform_limits(platform)
        artifact = {
            "id": self._generate_id("social"),
            "type": "social_post",
            "platform": platform.lower(),
            "status": "pending_approval",
            "created_at": datetime.now().isoformat(),
            "post": {
                "platform": platform,
                "content": content,
                "hashtags": hashtags or [],
                "media_description": media_description,
                "schedule_time": schedule_time or (datetime.now() + timedelta(hours=24)).isoformat(),
                "char_count": len(content),
            },
            "platform_limits": limits,
            "compliance_check": {
                "within_char_limit": len(content) <= limits.get("max_chars", 5000),
                "has_hashtags": bool(hashtags),
                "has_cta": any(cta in content.lower() for cta in
                               ["learn more", "click", "visit", "sign up", "check out", "link in"]),
            },
        }
        self.approval_queue.append(artifact)
        return artifact

    def _get_platform_limits(self, platform):
        limits = {
            "linkedin": {"max_chars": 3000, "max_hashtags": 5, "image_ratio": "1.91:1"},
            "twitter": {"max_chars": 280, "max_hashtags": 3, "image_ratio": "16:9"},
            "instagram": {"max_chars": 2200, "max_hashtags": 30, "image_ratio": "1:1"},
            "facebook": {"max_chars": 63206, "max_hashtags": 10, "image_ratio": "1.91:1"},
            "tiktok": {"max_chars": 2200, "max_hashtags": 5, "video_required": True},
        }
        return limits.get(platform.lower(), {"max_chars": 5000, "max_hashtags": 10})

    # ============================================================
    # APPROVAL WORKFLOW
    # ============================================================

    def get_pending_approvals(self):
        return [a for a in self.approval_queue if a["status"] == "pending_approval"]

    def approve_artifact(self, artifact_id):
        artifact = self._find_artifact(artifact_id)
        if artifact:
            artifact["status"] = "approved"
            artifact["approved_at"] = datetime.now().isoformat()
            return {"success": True, "artifact_id": artifact_id, "status": "approved"}
        return {"success": False, "error": "Artifact not found"}

    def reject_artifact(self, artifact_id, reason=""):
        artifact = self._find_artifact(artifact_id)
        if artifact:
            artifact["status"] = "rejected"
            artifact["rejected_at"] = datetime.now().isoformat()
            artifact["rejection_reason"] = reason
            return {"success": True, "artifact_id": artifact_id, "status": "rejected"}
        return {"success": False, "error": "Artifact not found"}

    def get_execution_log(self):
        return self.execution_log

    # ============================================================
    # UTILITY
    # ============================================================

    def _generate_id(self, prefix):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_part = hashlib.md5(f"{prefix}{timestamp}".encode()).hexdigest()[:6]
        return f"{prefix}_{timestamp}_{hash_part}"

    def _find_artifact(self, artifact_id):
        for artifact in self.approval_queue:
            if artifact["id"] == artifact_id:
                return artifact
        return None

    def format_artifact_preview(self, artifact):
        """Format an artifact as readable preview text."""
        a_type = artifact.get("type", "unknown")

        if a_type == "blog_post":
            content = artifact.get("content", {})
            checklist = artifact.get("seo_checklist", {})
            checks = sum(1 for v in checklist.values() if v)
            total = len(checklist)
            body_preview = content.get("body", "")[:400]
            if len(content.get("body", "")) > 400:
                body_preview += "..."
            return (
                f"**Blog Post Preview**\n"
                f"**Title:** {content.get('title', '')}\n"
                f"**Target Keyword:** {content.get('target_keyword', 'Not set')}\n"
                f"**Word Count:** {content.get('word_count', 0)} ({content.get('reading_time_min', 0)} min read)\n"
                f"**SEO Checklist:** {checks}/{total} passed\n"
                f"**Status:** {artifact.get('status', 'unknown')}\n\n"
                f"{body_preview}"
            )

        elif a_type == "google_ads_campaign":
            campaign = artifact.get("campaign", {})
            perf = artifact.get("estimated_performance", {})
            return (
                f"**Google Ads Campaign Preview**\n"
                f"**Campaign:** {campaign.get('name', '')}\n"
                f"**Type:** {campaign.get('type', 'search')}\n"
                f"**Budget:** ${campaign.get('budget_daily_usd', 0)}/day (${campaign.get('budget_monthly_usd', 0)}/month)\n"
                f"**Bidding:** {campaign.get('bidding_strategy', '')}\n"
                f"**Ad Groups:** {len(artifact.get('ad_groups', []))}\n"
                f"**Keywords:** {artifact.get('keywords', {}).get('total', 0)}\n\n"
                f"**Estimated Performance:**\n"
                f"- Daily clicks: ~{perf.get('estimated_daily_clicks', 0)}\n"
                f"- Avg CPC: ${perf.get('estimated_cpc', 0)}\n"
                f"- Monthly conversions: ~{perf.get('estimated_monthly_conversions', 0)}\n"
                f"- Est. CPA: ${perf.get('estimated_cpa', 0)}"
            )

        elif a_type == "email_sequence":
            seq = artifact.get("sequence", {})
            emails = artifact.get("emails", [])
            email_preview = ""
            for i, email in enumerate(emails[:3], 1):
                email_preview += f"\n  Email {i}: \"{email.get('subject', '')}\" — {email.get('purpose', '')} (Day {email.get('day', i * 3)})"
            return (
                f"**Email Sequence Preview**\n"
                f"**Name:** {seq.get('name', '')}\n"
                f"**Segment:** {seq.get('target_segment', 'All leads')}\n"
                f"**Emails:** {seq.get('total_emails', 0)} over {seq.get('duration_days', 0)} days"
                f"{email_preview}"
            )

        elif a_type == "social_post":
            post = artifact.get("post", {})
            compliance = artifact.get("compliance_check", {})
            hashtags = " ".join("#" + h for h in post.get("hashtags", []))
            return (
                f"**Social Post Preview ({post.get('platform', '')})**\n"
                f"**Scheduled:** {post.get('schedule_time', '')[:16]}\n"
                f"**Characters:** {post.get('char_count', 0)}/{artifact.get('platform_limits', {}).get('max_chars', '?')}\n"
                f"**Has CTA:** {'Yes' if compliance.get('has_cta') else 'Missing — add one'}\n\n"
                f"{post.get('content', '')}\n\n"
                f"{hashtags}"
            )

        return f"**{a_type}** — {artifact.get('status', 'unknown')}"


# Singleton
_engine = None


def get_execution_engine() -> ExecutionEngine:
    global _engine
    if _engine is None:
        _engine = ExecutionEngine()
    return _engine
