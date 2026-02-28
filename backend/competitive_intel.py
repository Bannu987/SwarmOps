"""
Competitive Intelligence Agent — SwarmOps
Auto-analyze competitor websites, SEO, content, social, ads, and pricing.
Track multiple competitors with historical snapshots and severity-based alerts.
Injects competitive awareness into every agent response.
"""

import os
import json
import uuid
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional
from db import get_connection as _get_conn


# ---------------------------------------------------------------------------
# DB Init
# ---------------------------------------------------------------------------

def _init_tables():
    """Create competitors, competitor_snapshots, and competitive_alerts tables."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS competitors (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            website_url     TEXT NOT NULL,
            industry        TEXT,
            added_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_analyzed   TIMESTAMP,
            analysis_count  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS competitor_snapshots (
            id              TEXT PRIMARY KEY,
            competitor_id   TEXT NOT NULL,
            snapshot_type   TEXT NOT NULL,
            data            TEXT NOT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS competitive_alerts (
            id              TEXT PRIMARY KEY,
            competitor_id   TEXT NOT NULL,
            alert_type      TEXT NOT NULL,
            severity        TEXT NOT NULL,
            title           TEXT NOT NULL,
            description     TEXT,
            data            TEXT,
            acknowledged    INTEGER DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_snapshots_competitor ON competitor_snapshots(competitor_id);
        CREATE INDEX IF NOT EXISTS idx_snapshots_type ON competitor_snapshots(snapshot_type);
        CREATE INDEX IF NOT EXISTS idx_alerts_competitor ON competitive_alerts(competitor_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_ack ON competitive_alerts(acknowledged);
    """)
    conn.commit()


_init_tables()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _domain_from_url(url: str) -> str:
    """Extract bare domain (e.g. 'paypal.com') from a URL."""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return match.group(1) if match else url


def _search(query: str, max_results: int = 5) -> list:
    """Search using Brave first, fall back to Serper. Never crashes."""
    try:
        from model_router import search_brave
        results = search_brave(query, max_results=max_results)
        if results:
            return results
    except Exception:
        pass
    try:
        from model_router import search_serper
        results = search_serper(query, max_results=max_results)
        if results:
            return results
    except Exception:
        pass
    return []


def _llm(prompt: str, system: str = "", tier: int = 2, max_tokens: int = 512) -> str:
    """Call LLM via model_router. Returns content string or '' on failure."""
    try:
        from model_router import call_model_sync
        result = call_model_sync(
            prompt=prompt,
            system_prompt=system,
            tier=tier,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return result.get("content", "").strip()
    except Exception as e:
        print(f"[competitive_intel] LLM error: {e}")
        return ""


def _results_to_text(results: list, max_chars: int = 1500) -> str:
    """Format search results into a compact text block for LLM context."""
    lines = []
    for r in results:
        title = r.get("title", "")
        url = r.get("url", "")
        desc = r.get("description", "")
        lines.append(f"- {title} ({url}): {desc}")
    return "\n".join(lines)[:max_chars]


def _severity_for(alert_type: str, data: dict) -> str:
    """Determine alert severity from type and data."""
    if alert_type == "ad_detected":
        return "critical"
    if alert_type in ("ranking_change", "website_change"):
        return "high"
    if alert_type in ("new_content", "social_spike"):
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# CompetitiveIntel Class
# ---------------------------------------------------------------------------

class CompetitiveIntel:
    """
    Tracks, analyzes, and monitors competitors.
    All methods are safe — they log errors silently and never crash the API.
    """

    # -----------------------------------------------------------------------
    # Competitor Management
    # -----------------------------------------------------------------------

    def add_competitor(self, name: str, website_url: str) -> str:
        """
        Add a new competitor to track.
        Detects industry, stores in DB, triggers initial full analysis.
        Returns competitor_id.
        """
        competitor_id = str(uuid.uuid4())
        try:
            # Normalize URL
            if not website_url.startswith("http"):
                website_url = "https://" + website_url

            domain = _domain_from_url(website_url)

            # Detect industry with a fast LLM call
            industry = self._detect_industry(name, domain)

            conn = _get_conn()
            conn.execute(
                """INSERT INTO competitors (id, name, website_url, industry)
                   VALUES (?, ?, ?, ?)""",
                (competitor_id, name.strip(), website_url.strip(), industry),
            )
            conn.commit()
            print(f"[competitive_intel] Added competitor: {name} ({domain}) → {industry}")

            # Initial analysis
            self.analyze_competitor(competitor_id)

        except Exception as e:
            print(f"[competitive_intel] add_competitor error: {e}")

        return competitor_id

    def remove_competitor(self, competitor_id: str):
        """Remove a competitor and all associated data from all tables."""
        try:
            conn = _get_conn()
            conn.execute("DELETE FROM competitive_alerts WHERE competitor_id = ?", (competitor_id,))
            conn.execute("DELETE FROM competitor_snapshots WHERE competitor_id = ?", (competitor_id,))
            conn.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
            conn.commit()
            print(f"[competitive_intel] Removed competitor {competitor_id}")
        except Exception as e:
            print(f"[competitive_intel] remove_competitor error: {e}")

    def list_competitors(self) -> list:
        """Return all tracked competitors with their latest snapshot metadata."""
        try:
            conn = _get_conn()
            rows = conn.execute(
                "SELECT * FROM competitors ORDER BY added_at DESC"
            ).fetchall()
            competitors = []
            for row in rows:
                c = dict(row)
                # Attach snapshot types available
                snap_rows = conn.execute(
                    """SELECT DISTINCT snapshot_type, MAX(created_at) as latest
                       FROM competitor_snapshots WHERE competitor_id = ?
                       GROUP BY snapshot_type""",
                    (row["id"],),
                ).fetchall()
                c["snapshots_available"] = {s["snapshot_type"]: s["latest"] for s in snap_rows}
                competitors.append(c)
            return competitors
        except Exception as e:
            print(f"[competitive_intel] list_competitors error: {e}")
            return []

    # -----------------------------------------------------------------------
    # Analysis Pipeline
    # -----------------------------------------------------------------------

    def analyze_competitor(self, competitor_id: str) -> dict:
        """
        Run a comprehensive multi-dimensional analysis of a competitor.
        Executes 5 sub-analyses in parallel using ThreadPoolExecutor.
        Stores each result as a snapshot. Returns full analysis dict.
        """
        try:
            conn = _get_conn()
            row = conn.execute(
                "SELECT * FROM competitors WHERE id = ?", (competitor_id,)
            ).fetchone()
            if not row:
                return {"error": f"Competitor {competitor_id} not found"}

            competitor = dict(row)
            domain = _domain_from_url(competitor["website_url"])
            name = competitor["name"]
            print(f"[competitive_intel] Analyzing: {name} ({domain})")

            # Run all 5 sub-analyses in parallel
            analysis = {}
            tasks = {
                "website": lambda: self._analyze_website(name, domain, competitor),
                "seo": lambda: self._analyze_seo(name, domain),
                "content": lambda: self._analyze_content(name, domain),
                "social": lambda: self._analyze_social(name, domain),
                "ads": lambda: self._analyze_ads(name, domain),
            }

            with ThreadPoolExecutor(max_workers=5) as executor:
                future_map = {executor.submit(fn): key for key, fn in tasks.items()}
                for future in as_completed(future_map):
                    key = future_map[future]
                    try:
                        result = future.result(timeout=25)
                        analysis[key] = result
                        self._save_snapshot(competitor_id, key, result)
                    except Exception as e:
                        print(f"[competitive_intel] {key} analysis error: {e}")
                        analysis[key] = {"error": str(e)}

            # Detect changes vs previous snapshot and create alerts
            try:
                self.detect_changes(competitor_id)
            except Exception:
                pass

            # Update last_analyzed and increment analysis_count
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                """UPDATE competitors SET last_analyzed = ?, analysis_count = analysis_count + 1
                   WHERE id = ?""",
                (now, competitor_id),
            )
            conn.commit()

            analysis["competitor_id"] = competitor_id
            analysis["competitor_name"] = name
            analysis["analyzed_at"] = now
            print(f"[competitive_intel] Analysis complete for {name}")
            return analysis

        except Exception as e:
            print(f"[competitive_intel] analyze_competitor error: {e}")
            return {"error": str(e)}

    def _detect_industry(self, name: str, domain: str) -> str:
        """Fast LLM call to detect competitor's industry from name + domain."""
        prompt = (
            f"What industry is '{name}' ({domain}) in? "
            f"Reply with ONE word only from this list: "
            f"ecommerce, saas, b2b, b2c, healthcare, fintech, edtech, agency, media, other"
        )
        result = _llm(prompt, tier=1, max_tokens=10)
        # Extract just the word
        word = result.strip().lower().split()[0] if result.strip() else "other"
        valid = {"ecommerce","saas","b2b","b2c","healthcare","fintech","edtech","agency","media","other"}
        return word if word in valid else "other"

    def _analyze_website(self, name: str, domain: str, competitor: dict) -> dict:
        """
        Analyze the competitor's homepage: value proposition, CTA, pricing model.
        Compares against user's BrandDNA where available.
        """
        results = _search(f"{name} {domain}", max_results=5)
        if not results:
            results = _search(f'"{name}" homepage features pricing', max_results=5)

        context = _results_to_text(results)

        # Try to get brand context for comparison
        brand_name = ""
        try:
            from brand_dna import get_brand_dna
            dna = get_brand_dna().get_stored()
            if dna:
                brand_name = dna.get("brand_name", "")
        except Exception:
            pass

        comparison_note = f"\nOur brand is {brand_name}. Note any competitive positioning." if brand_name else ""

        prompt = f"""Analyze {name}'s website based on these search results:

{context}{comparison_note}

Return ONLY this JSON (no markdown):
{{
  "headline": "their main hero headline or value statement",
  "value_proposition": "their core value proposition in 1-2 sentences",
  "cta": "their primary call-to-action text",
  "pricing_model": "freemium|subscription|one_time|custom|unknown",
  "key_features": ["feature1", "feature2", "feature3"],
  "target_market": "who they target",
  "website_score": 0
}}

Set website_score 0-100 based on clarity, sophistication, and conversion focus."""

        raw = _llm(prompt, tier=2, max_tokens=400)
        try:
            # Strip markdown fences if present
            clean = re.sub(r"^```[a-z]*\n?", "", raw.strip())
            clean = re.sub(r"\n?```$", "", clean)
            data = json.loads(clean)
        except Exception:
            data = {
                "headline": name,
                "value_proposition": context[:200] if context else "",
                "cta": "Get Started",
                "pricing_model": "unknown",
                "key_features": [],
                "target_market": competitor.get("industry", "unknown"),
                "website_score": 50,
            }

        data["search_results_count"] = len(results)
        return data

    def _analyze_seo(self, name: str, domain: str) -> dict:
        """
        Estimate competitor's SEO presence: domain authority, top keywords, content topics.
        """
        # Two searches: brand presence + top pages
        results_brand = _search(f"{name} site:{domain}", max_results=5)
        results_top = _search(f"site:{domain} best top guide how", max_results=5)
        all_results = results_brand + results_top

        context = _results_to_text(all_results, max_chars=1800)

        prompt = f"""Analyze {name}'s SEO presence based on these search results:

{context}

Return ONLY this JSON (no markdown):
{{
  "seo_score": 0,
  "domain_authority_estimate": 0,
  "top_keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
  "top_pages": ["page type 1", "page type 2", "page type 3"],
  "content_topics": ["topic1", "topic2", "topic3"],
  "search_presence": "strong|moderate|weak",
  "ranking_assessment": "brief 1-sentence assessment"
}}

seo_score: 0-100. domain_authority_estimate: 0-100 based on brand recognition and result quality."""

        raw = _llm(prompt, tier=2, max_tokens=400)
        try:
            clean = re.sub(r"^```[a-z]*\n?", "", raw.strip())
            clean = re.sub(r"\n?```$", "", clean)
            data = json.loads(clean)
        except Exception:
            data = {
                "seo_score": 50,
                "domain_authority_estimate": 50,
                "top_keywords": [],
                "top_pages": [],
                "content_topics": [],
                "search_presence": "moderate",
                "ranking_assessment": "Analysis unavailable",
            }

        data["results_analyzed"] = len(all_results)
        return data

    def _analyze_content(self, name: str, domain: str) -> dict:
        """
        Analyze content strategy: frequency, formats, topics, themes.
        """
        results = _search(f"{name} blog guide tutorial article", max_results=6)
        if not results:
            results = _search(f"site:{domain} blog content", max_results=6)

        context = _results_to_text(results, max_chars=1500)

        prompt = f"""Analyze {name}'s content marketing strategy from these results:

{context}

Return ONLY this JSON (no markdown):
{{
  "content_score": 0,
  "content_frequency": "daily|weekly|bi-weekly|monthly|unknown",
  "formats": ["blog", "video", "podcast", "infographic", "case_study", "webinar"],
  "top_topics": ["topic1", "topic2", "topic3", "topic4"],
  "content_themes": ["theme1", "theme2", "theme3"],
  "content_depth": "shallow|intermediate|deep",
  "audience_education_level": "beginner|intermediate|advanced",
  "content_assessment": "1-sentence assessment"
}}

content_score: 0-100 based on volume, quality signals, and topic breadth. formats: only include detected ones."""

        raw = _llm(prompt, tier=2, max_tokens=400)
        try:
            clean = re.sub(r"^```[a-z]*\n?", "", raw.strip())
            clean = re.sub(r"\n?```$", "", clean)
            data = json.loads(clean)
        except Exception:
            data = {
                "content_score": 40,
                "content_frequency": "unknown",
                "formats": [],
                "top_topics": [],
                "content_themes": [],
                "content_depth": "intermediate",
                "audience_education_level": "intermediate",
                "content_assessment": "Analysis unavailable",
            }

        data["results_analyzed"] = len(results)
        return data

    def _analyze_social(self, name: str, domain: str) -> dict:
        """
        Analyze social media presence across major platforms.
        Estimates follower levels and engagement.
        """
        results = _search(f"{name} twitter linkedin instagram youtube social media", max_results=6)
        context = _results_to_text(results, max_chars=1500)

        prompt = f"""Analyze {name}'s social media presence from these search results:

{context}

Return ONLY this JSON (no markdown):
{{
  "social_score": 0,
  "active_platforms": ["twitter", "linkedin", "instagram", "youtube", "tiktok", "facebook"],
  "engagement_level": "low|medium|high",
  "estimated_following": "small (<10k)|medium (10k-100k)|large (100k-1M)|massive (1M+)|unknown",
  "content_style": "educational|promotional|entertainment|thought_leadership|mixed",
  "trending_topics": ["topic1", "topic2"],
  "social_assessment": "1-sentence assessment"
}}

social_score: 0-100. active_platforms: only include platforms where you have evidence of presence."""

        raw = _llm(prompt, tier=2, max_tokens=400)
        try:
            clean = re.sub(r"^```[a-z]*\n?", "", raw.strip())
            clean = re.sub(r"\n?```$", "", clean)
            data = json.loads(clean)
        except Exception:
            data = {
                "social_score": 40,
                "active_platforms": [],
                "engagement_level": "medium",
                "estimated_following": "unknown",
                "content_style": "mixed",
                "trending_topics": [],
                "social_assessment": "Analysis unavailable",
            }

        data["results_analyzed"] = len(results)
        return data

    def _analyze_ads(self, name: str, domain: str) -> dict:
        """
        Detect paid advertising activity: Google Ads, ad themes, aggressiveness.
        """
        # Search for sponsored results + ad-specific queries
        results_ads = _search(f"{name} sponsored ad buy", max_results=5)
        results_brand = _search(f"{name}", max_results=5)  # May show sponsored results
        all_results = results_ads + results_brand

        context = _results_to_text(all_results, max_chars=1500)

        prompt = f"""Analyze {name}'s paid advertising strategy from these search results:

{context}

Return ONLY this JSON (no markdown):
{{
  "ad_aggressiveness": 0,
  "is_running_ads": false,
  "ad_platforms": ["google", "facebook", "linkedin", "display"],
  "ad_themes": ["theme1", "theme2"],
  "estimated_keywords": ["kw1", "kw2", "kw3"],
  "ad_copy_style": "direct_response|brand_awareness|retargeting|mixed|none_detected",
  "budget_estimate": "low (<$10k/mo)|medium ($10k-100k/mo)|high (>$100k/mo)|unknown",
  "ads_assessment": "1-sentence assessment"
}}

ad_aggressiveness: 0-100 (100 = very aggressive paid strategy). is_running_ads: true if evidence found.
ad_platforms: only include platforms with evidence. Flag sponsored search results as evidence of Google Ads."""

        raw = _llm(prompt, tier=2, max_tokens=400)
        try:
            clean = re.sub(r"^```[a-z]*\n?", "", raw.strip())
            clean = re.sub(r"\n?```$", "", clean)
            data = json.loads(clean)
        except Exception:
            data = {
                "ad_aggressiveness": 30,
                "is_running_ads": False,
                "ad_platforms": [],
                "ad_themes": [],
                "estimated_keywords": [],
                "ad_copy_style": "none_detected",
                "budget_estimate": "unknown",
                "ads_assessment": "Analysis unavailable",
            }

        data["results_analyzed"] = len(all_results)
        return data

    def _save_snapshot(self, competitor_id: str, snapshot_type: str, data: dict):
        """Store an analysis snapshot in the database."""
        try:
            conn = _get_conn()
            conn.execute(
                """INSERT INTO competitor_snapshots (id, competitor_id, snapshot_type, data)
                   VALUES (?, ?, ?, ?)""",
                (str(uuid.uuid4()), competitor_id, snapshot_type, json.dumps(data)),
            )
            conn.commit()
        except Exception as e:
            print(f"[competitive_intel] _save_snapshot error: {e}")

    def get_snapshots(self, competitor_id: str, snapshot_type: str = None) -> list:
        """Return snapshot history for a competitor, optionally filtered by type."""
        try:
            conn = _get_conn()
            if snapshot_type:
                rows = conn.execute(
                    """SELECT * FROM competitor_snapshots
                       WHERE competitor_id = ? AND snapshot_type = ?
                       ORDER BY created_at DESC LIMIT 20""",
                    (competitor_id, snapshot_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM competitor_snapshots
                       WHERE competitor_id = ?
                       ORDER BY created_at DESC LIMIT 50""",
                    (competitor_id,),
                ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["data"] = json.loads(item["data"])
                except Exception:
                    pass
                result.append(item)
            return result
        except Exception as e:
            print(f"[competitive_intel] get_snapshots error: {e}")
            return []

    # -----------------------------------------------------------------------
    # Change Detection & Alerts
    # -----------------------------------------------------------------------

    def detect_changes(self, competitor_id: str) -> list:
        """
        Compare the two most recent snapshots for each type.
        Creates alerts in competitive_alerts for significant changes.
        Returns list of new alert dicts.
        """
        new_alerts = []
        try:
            conn = _get_conn()
            competitor_row = conn.execute(
                "SELECT name FROM competitors WHERE id = ?", (competitor_id,)
            ).fetchone()
            comp_name = competitor_row["name"] if competitor_row else competitor_id

            snapshot_types = ["website", "seo", "content", "social", "ads"]
            for stype in snapshot_types:
                rows = conn.execute(
                    """SELECT data, created_at FROM competitor_snapshots
                       WHERE competitor_id = ? AND snapshot_type = ?
                       ORDER BY created_at DESC LIMIT 2""",
                    (competitor_id, stype),
                ).fetchall()

                if len(rows) < 2:
                    continue  # Need at least 2 snapshots to detect changes

                try:
                    latest = json.loads(rows[0]["data"])
                    previous = json.loads(rows[1]["data"])
                except Exception:
                    continue

                alert_data = self._compare_snapshots(stype, latest, previous, comp_name)
                if alert_data:
                    alert_id = str(uuid.uuid4())
                    conn.execute(
                        """INSERT INTO competitive_alerts
                           (id, competitor_id, alert_type, severity, title, description, data)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            alert_id,
                            competitor_id,
                            alert_data["alert_type"],
                            alert_data["severity"],
                            alert_data["title"],
                            alert_data["description"],
                            json.dumps(alert_data.get("data", {})),
                        ),
                    )
                    new_alerts.append(alert_data)

            conn.commit()
        except Exception as e:
            print(f"[competitive_intel] detect_changes error: {e}")

        return new_alerts

    def _compare_snapshots(self, stype: str, latest: dict, previous: dict, comp_name: str) -> Optional[dict]:
        """
        Compare two snapshots of the same type.
        Returns an alert dict if a significant change is detected, else None.
        """
        if stype == "website":
            old_vp = previous.get("value_proposition", "")
            new_vp = latest.get("value_proposition", "")
            old_pricing = previous.get("pricing_model", "")
            new_pricing = latest.get("pricing_model", "")

            if new_pricing != old_pricing and old_pricing not in ("unknown", ""):
                return {
                    "alert_type": "website_change",
                    "severity": "critical",
                    "title": f"{comp_name} changed pricing model: {old_pricing} → {new_pricing}",
                    "description": f"Pricing strategy shift detected. New model: {new_pricing}",
                    "data": {"old_pricing": old_pricing, "new_pricing": new_pricing},
                }
            # Value prop changed significantly (rough heuristic: > 30% different words)
            if old_vp and new_vp and _text_change_pct(old_vp, new_vp) > 0.3:
                return {
                    "alert_type": "website_change",
                    "severity": "high",
                    "title": f"{comp_name} updated their value proposition",
                    "description": f"Messaging shift: '{new_vp[:100]}'",
                    "data": {"old": old_vp[:200], "new": new_vp[:200]},
                }

        elif stype == "seo":
            old_score = previous.get("seo_score", 0)
            new_score = latest.get("seo_score", 0)
            if abs(new_score - old_score) >= 10:
                direction = "gained" if new_score > old_score else "lost"
                return {
                    "alert_type": "ranking_change",
                    "severity": "high",
                    "title": f"{comp_name} {direction} significant SEO ground ({old_score} → {new_score})",
                    "description": f"SEO score change of {new_score - old_score:+d} points detected.",
                    "data": {"old_score": old_score, "new_score": new_score},
                }

        elif stype == "content":
            old_topics = set(previous.get("top_topics", []))
            new_topics = set(latest.get("top_topics", []))
            new_entries = new_topics - old_topics
            if len(new_entries) >= 2:
                return {
                    "alert_type": "new_content",
                    "severity": "medium",
                    "title": f"{comp_name} is covering new content topics",
                    "description": f"New topics detected: {', '.join(list(new_entries)[:3])}",
                    "data": {"new_topics": list(new_entries)},
                }

        elif stype == "social":
            old_level = previous.get("engagement_level", "")
            new_level = latest.get("engagement_level", "")
            if new_level == "high" and old_level in ("low", "medium"):
                return {
                    "alert_type": "social_spike",
                    "severity": "medium",
                    "title": f"{comp_name} social engagement spiked to HIGH",
                    "description": "Unusual social media activity detected. May indicate a campaign or viral moment.",
                    "data": {"old_level": old_level, "new_level": new_level},
                }

        elif stype == "ads":
            old_running = previous.get("is_running_ads", False)
            new_running = latest.get("is_running_ads", False)
            if new_running and not old_running:
                return {
                    "alert_type": "ad_detected",
                    "severity": "critical",
                    "title": f"{comp_name} started running paid ads",
                    "description": f"Ad themes: {', '.join(latest.get('ad_themes', [])[:3])}. Budget est: {latest.get('budget_estimate', 'unknown')}",
                    "data": latest,
                }
            # Ad aggressiveness jumped
            old_agg = previous.get("ad_aggressiveness", 0)
            new_agg = latest.get("ad_aggressiveness", 0)
            if new_agg - old_agg >= 20:
                return {
                    "alert_type": "ad_detected",
                    "severity": "high",
                    "title": f"{comp_name} significantly increased ad spend ({old_agg} → {new_agg})",
                    "description": f"Estimated keywords: {', '.join(latest.get('estimated_keywords', [])[:3])}",
                    "data": {"old_aggressiveness": old_agg, "new_aggressiveness": new_agg},
                }

        return None

    # -----------------------------------------------------------------------
    # Alerts
    # -----------------------------------------------------------------------

    def get_alerts(self, acknowledged: bool = False) -> list:
        """
        Return competitive alerts sorted by severity.
        acknowledged=False (default) returns only unread alerts.
        """
        try:
            conn = _get_conn()
            ack_val = 1 if acknowledged else 0
            rows = conn.execute(
                """SELECT a.*, c.name as competitor_name
                   FROM competitive_alerts a
                   LEFT JOIN competitors c ON a.competitor_id = c.id
                   WHERE a.acknowledged = ?
                   ORDER BY
                     CASE a.severity
                       WHEN 'critical' THEN 1
                       WHEN 'high' THEN 2
                       WHEN 'medium' THEN 3
                       WHEN 'low' THEN 4
                       ELSE 5
                     END,
                     a.created_at DESC""",
                (ack_val,),
            ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["data"] = json.loads(item["data"]) if item.get("data") else {}
                except Exception:
                    pass
                result.append(item)
            return result
        except Exception as e:
            print(f"[competitive_intel] get_alerts error: {e}")
            return []

    def acknowledge_alert(self, alert_id: str):
        """Mark a competitive alert as read/acknowledged."""
        try:
            conn = _get_conn()
            conn.execute(
                "UPDATE competitive_alerts SET acknowledged = 1 WHERE id = ?", (alert_id,)
            )
            conn.commit()
        except Exception as e:
            print(f"[competitive_intel] acknowledge_alert error: {e}")

    # -----------------------------------------------------------------------
    # Comparison Matrix
    # -----------------------------------------------------------------------

    def compare_competitors(self, competitor_ids: list = None) -> dict:
        """
        Generate a competitive comparison matrix across all tracked competitors.
        Uses LLM to synthesize findings into a structured market position report.
        """
        try:
            conn = _get_conn()

            # Get competitors to compare
            if competitor_ids:
                placeholders = ",".join("?" * len(competitor_ids))
                competitors = [
                    dict(r) for r in conn.execute(
                        f"SELECT * FROM competitors WHERE id IN ({placeholders})", competitor_ids
                    ).fetchall()
                ]
            else:
                competitors = [dict(r) for r in conn.execute(
                    "SELECT * FROM competitors ORDER BY added_at"
                ).fetchall()]

            if not competitors:
                return {
                    "success": False,
                    "error": "No competitors tracked yet. Add competitors first.",
                    "comparison_matrix": {},
                }

            # Build profiles from latest snapshots
            profiles = []
            for comp in competitors:
                profile = {"name": comp["name"], "url": comp["website_url"]}
                for stype in ["website", "seo", "content", "social", "ads"]:
                    snap = conn.execute(
                        """SELECT data FROM competitor_snapshots
                           WHERE competitor_id = ? AND snapshot_type = ?
                           ORDER BY created_at DESC LIMIT 1""",
                        (comp["id"], stype),
                    ).fetchone()
                    if snap:
                        try:
                            profile[stype] = json.loads(snap["data"])
                        except Exception:
                            profile[stype] = {}
                profiles.append(profile)

            # Get our brand context
            brand_info = ""
            try:
                from brand_dna import get_brand_dna
                dna = get_brand_dna().get_stored()
                if dna:
                    brand_info = (
                        f"Our brand: {dna.get('brand_name','us')} | "
                        f"Industry: {dna.get('industry','')} | "
                        f"Voice: {dna.get('brand_voice','')} | "
                        f"Value prop: {dna.get('value_proposition','')} | "
                        f"Audience: {dna.get('target_audience','')}"
                    )
            except Exception:
                pass

            # Build profiles summary for LLM
            profiles_text = ""
            for p in profiles:
                seo_score = p.get("seo", {}).get("seo_score", "?")
                content_score = p.get("content", {}).get("content_score", "?")
                social_score = p.get("social", {}).get("social_score", "?")
                ad_agg = p.get("ads", {}).get("ad_aggressiveness", "?")
                vp = p.get("website", {}).get("value_proposition", "")[:150]
                topics = p.get("content", {}).get("top_topics", [])[:3]
                platforms = p.get("social", {}).get("active_platforms", [])[:3]
                is_ads = p.get("ads", {}).get("is_running_ads", False)
                profiles_text += (
                    f"\n## {p['name']} ({p['url']})\n"
                    f"Value prop: {vp}\n"
                    f"SEO score: {seo_score}/100 | Content score: {content_score}/100 | "
                    f"Social score: {social_score}/100 | Ad aggressiveness: {ad_agg}/100\n"
                    f"Running ads: {is_ads}\n"
                    f"Content topics: {', '.join(topics)}\n"
                    f"Social platforms: {', '.join(platforms)}\n"
                )

            prompt = f"""You are a strategic marketing analyst. Compare these competitors against our brand.

{f"OUR BRAND: {brand_info}" if brand_info else ""}

COMPETITOR PROFILES:
{profiles_text}

Return ONLY this exact JSON (no markdown, fill ALL fields with real analysis):
{{
  "comparison_matrix": {{
    "<competitor_name>": {{
      "strengths": ["strength1", "strength2", "strength3"],
      "weaknesses": ["weakness1", "weakness2"],
      "seo_score": 0,
      "content_score": 0,
      "social_score": 0,
      "ad_aggressiveness": 0,
      "threat_level": "low|medium|high"
    }}
  }},
  "our_advantages": ["advantage1", "advantage2", "advantage3"],
  "our_vulnerabilities": ["vulnerability1", "vulnerability2"],
  "recommended_actions": ["action1", "action2", "action3"],
  "market_position": "leader|challenger|follower|nicher"
}}

Repeat the comparison_matrix block for each competitor listed above. Be specific and actionable."""

            raw = _llm(prompt, tier=3, max_tokens=1200)
            try:
                clean = re.sub(r"^```[a-z]*\n?", "", raw.strip())
                clean = re.sub(r"\n?```$", "", clean)
                data = json.loads(clean)
            except Exception:
                # Fallback minimal structure
                data = {
                    "comparison_matrix": {
                        comp["name"]: {
                            "strengths": ["Established brand"],
                            "weaknesses": ["Unknown"],
                            "seo_score": 50,
                            "content_score": 50,
                            "social_score": 50,
                            "ad_aggressiveness": 30,
                            "threat_level": "medium",
                        }
                        for comp in competitors
                    },
                    "our_advantages": ["Agile and data-driven"],
                    "our_vulnerabilities": ["Brand awareness vs established players"],
                    "recommended_actions": ["Differentiate on speed and intelligence"],
                    "market_position": "challenger",
                }

            # Save as a special "comparison" snapshot (attached to first competitor for indexing)
            if competitors:
                self._save_snapshot(competitors[0]["id"], "comparison", data)

            data["competitors_compared"] = [c["name"] for c in competitors]
            data["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            return data

        except Exception as e:
            print(f"[competitive_intel] compare_competitors error: {e}")
            return {"error": str(e), "comparison_matrix": {}}

    # -----------------------------------------------------------------------
    # Battle Card
    # -----------------------------------------------------------------------

    def generate_battle_card(self, competitor_id: str) -> str:
        """
        Generate a comprehensive sales battle card vs a specific competitor.
        Uses brand DNA for our brand info and latest snapshots for competitor data.
        """
        try:
            conn = _get_conn()
            comp_row = conn.execute(
                "SELECT * FROM competitors WHERE id = ?", (competitor_id,)
            ).fetchone()
            if not comp_row:
                return f"Competitor not found: {competitor_id}"

            comp = dict(comp_row)
            comp_name = comp["name"]

            # Gather all latest snapshots
            snap_data = {}
            for stype in ["website", "seo", "content", "social", "ads"]:
                row = conn.execute(
                    """SELECT data FROM competitor_snapshots
                       WHERE competitor_id = ? AND snapshot_type = ?
                       ORDER BY created_at DESC LIMIT 1""",
                    (competitor_id, stype),
                ).fetchone()
                if row:
                    try:
                        snap_data[stype] = json.loads(row["data"])
                    except Exception:
                        snap_data[stype] = {}

            # Get our brand info
            our_brand = "Our Brand"
            brand_vp = ""
            brand_features = ""
            try:
                from brand_dna import get_brand_dna
                dna = get_brand_dna().get_stored()
                if dna:
                    our_brand = dna.get("brand_name", "Our Brand")
                    brand_vp = dna.get("value_proposition", "")
                    brand_features = ", ".join(dna.get("tone_keywords", []))
            except Exception:
                pass

            # Summarize competitor data for LLM
            comp_summary = (
                f"Competitor: {comp_name}\n"
                f"Website: {comp.get('website_url', '')}\n"
                f"Industry: {comp.get('industry', '')}\n"
                f"Value prop: {snap_data.get('website', {}).get('value_proposition', 'Unknown')}\n"
                f"CTA: {snap_data.get('website', {}).get('cta', 'Unknown')}\n"
                f"Pricing model: {snap_data.get('website', {}).get('pricing_model', 'Unknown')}\n"
                f"Key features: {', '.join(snap_data.get('website', {}).get('key_features', []))}\n"
                f"Target market: {snap_data.get('website', {}).get('target_market', 'Unknown')}\n"
                f"SEO score: {snap_data.get('seo', {}).get('seo_score', '?')}/100\n"
                f"SEO keywords: {', '.join(snap_data.get('seo', {}).get('top_keywords', [])[:5])}\n"
                f"Content topics: {', '.join(snap_data.get('content', {}).get('top_topics', [])[:4])}\n"
                f"Content frequency: {snap_data.get('content', {}).get('content_frequency', 'unknown')}\n"
                f"Social platforms: {', '.join(snap_data.get('social', {}).get('active_platforms', []))}\n"
                f"Social engagement: {snap_data.get('social', {}).get('engagement_level', 'unknown')}\n"
                f"Running ads: {snap_data.get('ads', {}).get('is_running_ads', False)}\n"
                f"Ad aggressiveness: {snap_data.get('ads', {}).get('ad_aggressiveness', 0)}/100\n"
            )

            our_summary = (
                f"Our brand: {our_brand}\n"
                f"Our value prop: {brand_vp}\n"
                f"Our strengths: {brand_features}\n"
            )

            prompt = f"""You are a strategic sales enablement expert. Create a competitive battle card.

{our_summary}
{comp_summary}

Write the battle card in this exact markdown format:

## {comp_name} vs {our_brand} — Battle Card

### Why Customers Choose {our_brand}
- [specific advantage with supporting data point]
- [specific advantage with supporting data point]
- [specific advantage with supporting data point]

### Why Customers Choose {comp_name}
- [their real strength]
- [their real strength]

### Objection Handling
- If prospect says "I'm already using {comp_name}": [specific response]
- If prospect says "{comp_name} has feature X": [specific response]
- If prospect says "{comp_name} is cheaper": [specific response]

### Head-to-Head Comparison
| Dimension | {our_brand} | {comp_name} |
|-----------|-------------|-------------|
| SEO Presence | [our level] | [their level] |
| Content Strategy | [our approach] | [their approach] |
| Ad Spend | [our approach] | [their approach] |
| Target Market | [our audience] | [their audience] |
| Pricing | [our model] | {snap_data.get('website', {}).get('pricing_model', 'unknown')} |

### Recommended Positioning Against {comp_name}
[2-3 sentences of specific messaging to use when competing with {comp_name}]

### Win Signals (when we beat them)
- [scenario where we win]
- [scenario where we win]

### Loss Signals (when they beat us)
- [scenario where we lose]
"""

            card = _llm(prompt, tier=3, max_tokens=1500)
            if not card:
                card = f"## {comp_name} vs {our_brand} — Battle Card\n\nAnalysis data collected. Run a competitor analysis first to populate full battle card data."

            # Save as snapshot
            self._save_snapshot(competitor_id, "battle_card", {"content": card, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")})

            return card

        except Exception as e:
            print(f"[competitive_intel] generate_battle_card error: {e}")
            return f"Battle card generation failed: {e}"

    # -----------------------------------------------------------------------
    # Context Injection (for all agents)
    # -----------------------------------------------------------------------

    def get_competitive_context(self) -> str:
        """
        Returns a competitive context string for injection into all agent system prompts.
        Returns '' if no competitors tracked yet.
        """
        try:
            competitors = self.list_competitors()
            if not competitors:
                return ""

            comp_names = [c["name"] for c in competitors]

            # Get brand name for context
            our_brand = ""
            try:
                from brand_dna import get_brand_dna
                dna = get_brand_dna().get_stored()
                if dna:
                    our_brand = dna.get("brand_name", "")
            except Exception:
                pass

            # Get latest comparison if available
            advantages = []
            vulnerabilities = []
            conn = _get_conn()
            # Look for most recent comparison snapshot
            comp_snap = conn.execute(
                """SELECT data FROM competitor_snapshots WHERE snapshot_type = 'comparison'
                   ORDER BY created_at DESC LIMIT 1"""
            ).fetchone()
            if comp_snap:
                try:
                    comp_data = json.loads(comp_snap["data"])
                    advantages = comp_data.get("our_advantages", [])[:3]
                    vulnerabilities = comp_data.get("our_vulnerabilities", [])[:2]
                except Exception:
                    pass

            n = len(comp_names)
            names_str = ", ".join(comp_names[:3])
            if len(comp_names) > 3:
                names_str += f" and {len(comp_names) - 3} more"

            brand_ref = f" for {our_brand}" if our_brand else ""
            ctx = f"COMPETITIVE CONTEXT: Tracking {n} competitor{'s' if n != 1 else ''}{brand_ref}: {names_str}."

            if advantages:
                ctx += f" Key competitive advantages: {'; '.join(advantages)}."
            if vulnerabilities:
                ctx += f" Areas where competitors lead: {'; '.join(vulnerabilities)}."

            ctx += " Factor competitor positioning into all recommendations."
            return ctx

        except Exception as e:
            print(f"[competitive_intel] get_competitive_context error: {e}")
            return ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _text_change_pct(text_a: str, text_b: str) -> float:
    """Rough measure of how different two texts are (0.0 = same, 1.0 = completely different)."""
    if not text_a or not text_b:
        return 1.0
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 1.0
    overlap = len(words_a & words_b)
    union = len(words_a | words_b)
    return 1.0 - (overlap / union)


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_instance: Optional[CompetitiveIntel] = None


def get_competitive_intel() -> CompetitiveIntel:
    global _instance
    if _instance is None:
        _instance = CompetitiveIntel()
    return _instance
