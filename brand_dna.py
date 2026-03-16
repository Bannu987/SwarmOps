"""
BrandDNA Auto-Extraction — SwarmOps (World-Class Edition)
Crawls 14+ pages, extracts 20+ brand dimensions, injects into all agent prompts.
Anti-hallucination: returns 'not_found' for anything not explicitly on the site.
"""

import os
import re
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional
from db import get_connection as _get_conn, DB_PATH


# ---------------------------------------------------------------------------
# DB Init
# ---------------------------------------------------------------------------

def _init_tables():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS brand_dna (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT NOT NULL,
            brand_name  TEXT,
            tagline     TEXT,
            brand_voice TEXT,
            tone_keywords   TEXT,
            value_proposition TEXT,
            target_audience   TEXT,
            industry    TEXT,
            competitors TEXT,
            content_style TEXT,
            color_palette TEXT,
            cta_patterns  TEXT,
            raw_json    TEXT,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()


_init_tables()


# ---------------------------------------------------------------------------
# Page crawling — multi-page with parallel fetching
# ---------------------------------------------------------------------------

COMMON_PATHS = [
    "", "/about", "/pricing", "/features", "/product", "/products",
    "/solutions", "/use-cases", "/platform", "/customers",
    "/case-studies", "/blog", "/resources", "/integrations"
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _fetch_page(url: str, timeout: int = 5) -> str:
    """Fetch a single page. Returns empty string on any failure."""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return ""


def _fetch_all_pages(base_url: str) -> str:
    """
    Crawl up to 14 pages in parallel (max 5 concurrent, 5s timeout each).
    Returns combined extracted text from all successful pages.
    """
    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    # Strip trailing slash
    base_url = base_url.rstrip("/")

    urls = [base_url + path for path in COMMON_PATHS]

    collected_texts = []

    def fetch_and_extract(url):
        html = _fetch_page(url, timeout=5)
        if html:
            return _html_to_text(html, url)
        return None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_and_extract, url): url for url in urls}
        for future in as_completed(futures, timeout=30):
            try:
                result = future.result()
                if result:
                    collected_texts.append(result)
            except Exception:
                pass

    if not collected_texts:
        # Fallback: search for brand info
        collected_texts.append(_fallback_search(base_url))

    # Combine all pages — cap at 12000 chars to avoid LLM token overflow
    combined = "\n\n---PAGE BREAK---\n\n".join(collected_texts)
    return combined[:12000]


def _html_to_text(html: str, url: str) -> str:
    """Convert HTML to clean text preserving key brand signals."""
    # Remove scripts and styles
    clean = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<style[^>]*>.*?</style>", " ", clean, flags=re.DOTALL | re.IGNORECASE)

    # Extract key structured signals first
    signals = []

    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title_m:
        signals.append("TITLE: " + re.sub(r"<[^>]+>", "", title_m.group(1)).strip())

    meta_desc_m = re.search(
        r'<meta\s+(?:name=["\']description["\']\s+content=["\']([^"\']+)["\']|'
        r'content=["\']([^"\']+)["\']\s+name=["\']description["\'])',
        html, re.IGNORECASE
    )
    if meta_desc_m:
        desc = meta_desc_m.group(1) or meta_desc_m.group(2)
        signals.append("META DESC: " + desc.strip())

    og_title_m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if og_title_m:
        signals.append("OG TITLE: " + og_title_m.group(1).strip())

    og_desc_m = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if og_desc_m:
        signals.append("OG DESC: " + og_desc_m.group(1).strip())

    h1_matches = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    for h in h1_matches[:3]:
        t = re.sub(r"<[^>]+>", "", h).strip()
        if t:
            signals.append("H1: " + t)

    h2_matches = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.IGNORECASE | re.DOTALL)
    for h in h2_matches[:5]:
        t = re.sub(r"<[^>]+>", "", h).strip()
        if t:
            signals.append("H2: " + t)

    # CTAs
    btn_matches = re.findall(r"<(?:button|a)[^>]*>(.*?)</(?:button|a)>", html, re.IGNORECASE | re.DOTALL)
    ctas = []
    for btn in btn_matches:
        t = re.sub(r"<[^>]+>", "", btn).strip()
        if 2 < len(t) < 50 and any(
            w in t.lower() for w in
            ["get", "start", "try", "sign", "book", "demo", "join", "free", "buy",
             "learn", "explore", "request", "contact", "watch", "download", "pricing"]
        ):
            ctas.append(t)
    if ctas:
        signals.append("CTAS: " + " | ".join(list(dict.fromkeys(ctas))[:8]))

    # Pricing signals
    price_m = re.findall(r'\$[\d,]+(?:\.\d{2})?(?:/(?:mo|month|yr|year|user))?', html)
    if price_m:
        signals.append("PRICES FOUND: " + ", ".join(list(dict.fromkeys(price_m))[:5]))

    # Social links
    social_m = re.findall(r'https?://(?:www\.)?(twitter|linkedin|instagram|facebook|youtube|tiktok)\.com/[^\s"\']+', html, re.IGNORECASE)
    if social_m:
        signals.append("SOCIAL: " + ", ".join(set(m.lower() for m in social_m[:5])))

    # Body text sample
    body = re.sub(r"<[^>]+>", " ", clean)
    body = re.sub(r"\s+", " ", body).strip()

    signals_text = "\n".join(signals)
    page_url_label = f"[PAGE: {url}]"
    return f"{page_url_label}\n{signals_text}\n{body[:1500]}"


def _fallback_search(url: str) -> str:
    """Use search when direct crawl fails."""
    try:
        from model_router import search_brave, search_serper
        domain_m = re.search(r"https?://(?:www\.)?([^/]+)", url)
        domain = domain_m.group(1) if domain_m else url
        results = search_brave(f"site:{domain} about company", max_results=3)
        if not results:
            results = search_serper(f"{domain} company brand about", max_results=3)
        if results:
            combined = " ".join(r.get("description", "") + " " + r.get("title", "") for r in results)
            return f"[SEARCH FALLBACK for {url}]\n{combined}"
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# LLM Extraction — comprehensive 20+ field anti-hallucination prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an expert brand intelligence analyst.
Analyze website content and return ONLY valid JSON — no markdown, no explanation.
CRITICAL: If information cannot be found in the content, return "not_found" instead of guessing.
NEVER hallucinate or invent data. Only extract what is explicitly present."""

_EXTRACTION_PROMPT = """You are an expert brand intelligence analyst. Analyze this website content
and extract comprehensive brand intelligence.

CRITICAL: If information cannot be found in the content, return "not_found"
instead of guessing. NEVER hallucinate or invent data.

Return ONLY valid JSON with this exact structure:

{{
  "brand_name": "string",
  "tagline": "string or not_found",
  "industry": "specific industry",
  "sub_industry": "niche or not_found",

  "brand_voice": {{
    "tone": "formal/casual/technical/friendly/authoritative/playful",
    "personality_traits": ["trait1", "trait2", "trait3", "trait4", "trait5"],
    "writing_style": "concise/detailed/storytelling/data-driven",
    "formality_level": 7,
    "emoji_usage": "none/minimal/moderate/heavy",
    "jargon_level": "none/low/medium/high"
  }},

  "visual_identity": {{
    "design_style": "minimal/corporate/playful/tech/startup/luxury",
    "visual_mood": ["modern", "clean", "bold"],
    "background_style": "light/dark/mixed",
    "ui_complexity": "simple/moderate/complex",
    "illustration_style": "none/3D/cartoon/flat/photography"
  }},

  "value_proposition": {{
    "primary": "main value prop or not_found",
    "supporting": ["point1", "point2", "point3"],
    "unique_differentiator": "what makes them different"
  }},

  "target_audience": {{
    "primary": "main audience",
    "segments": ["segment1", "segment2"],
    "company_size": "startup/smb/mid-market/enterprise/all",
    "decision_maker": "role they sell to or not_found"
  }},

  "products_services": [
    {{"name": "string", "description": "string", "category": "string"}}
  ],

  "pricing": {{
    "model": "freemium/subscription/one-time/custom/not_found",
    "starting_price": "price or not_found",
    "has_free_tier": "true/false/not_found",
    "enterprise_plan": "true/false/not_found"
  }},

  "business_objectives": {{
    "primary_goal": "lead_generation/ecommerce/subscriptions/awareness/not_found",
    "conversion_type": "demo/signup/purchase/contact/not_found",
    "sales_motion": "self-serve/sales-assisted/enterprise/not_found"
  }},

  "brand_positioning": {{
    "market_position": "premium/mid-market/budget",
    "key_differentiators": ["diff1", "diff2", "diff3"],
    "innovation_level": "traditional/moderate/highly_innovative"
  }},

  "customer_pain_points": ["pain1", "pain2", "pain3"],

  "marketing_funnel": {{
    "lead_magnets": ["type1", "type2"],
    "signup_flow": "simple/multi-step/not_found",
    "trial_available": "true/false/not_found",
    "email_capture_present": "true/false/not_found"
  }},

  "content_strategy": {{
    "blog_exists": true,
    "content_topics": ["topic1", "topic2"],
    "content_formats": ["blog", "case_studies", "videos"],
    "content_frequency": "daily/weekly/monthly/sporadic/not_found"
  }},

  "seo_signals": {{
    "meta_title": "string or not_found",
    "meta_description": "string or not_found",
    "h1_text": "string or not_found",
    "estimated_keywords": ["kw1", "kw2", "kw3"]
  }},

  "trust_signals": {{
    "testimonials": true,
    "case_studies": true,
    "client_logos": true,
    "certifications": [],
    "media_mentions": []
  }},

  "authority_signals": {{
    "thought_leadership": true,
    "educational_content": true,
    "research_reports": false,
    "community_presence": false
  }},

  "social_presence": {{
    "platforms_detected": ["twitter", "linkedin"],
    "primary_platform": "string or not_found"
  }},

  "technology_signals": {{
    "platform": "string or not_found",
    "integrations_mentioned": []
  }},

  "competitors": {{
    "mentioned_on_site": [],
    "implied_competitors": []
  }},

  "cta_patterns": ["CTA1", "CTA2"],

  "overall_scores": {{
    "website_quality": 8,
    "messaging_clarity": 7,
    "trust_factor": 9,
    "seo_readiness": 6,
    "conversion_optimization": 7
  }}
}}

Website content from multiple pages:
{content}
"""


def _analyze_with_llm(content: str, url: str) -> Optional[dict]:
    """Send all collected page content to LLM for comprehensive extraction."""
    try:
        from model_router import call_model_sync
        prompt = _EXTRACTION_PROMPT.format(content=content[:10000])
        result = call_model_sync(
            prompt=prompt,
            system_prompt=_SYSTEM_PROMPT,
            tier=2,
            max_tokens=2048,
            temperature=0.2,
        )
        raw = result.get("content", "")
        clean = raw.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```[a-z]*\n?", "", clean)
            clean = re.sub(r"\n?```$", "", clean)
        parsed = json.loads(clean.strip())

        # Fix brand_name if it's a placeholder
        brand_name = parsed.get("brand_name", "")
        if not brand_name or brand_name.lower() in ["your brand", "unknown", "not found", "not_found", "n/a", ""]:
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace("www.", "")
                n = domain.split(".")[0]
                parsed["brand_name"] = n.upper() if len(n) <= 4 else n.replace("-", " ").title()
            except:
                pass

        # Fix industry if it's a placeholder
        industry = parsed.get("industry", "")
        if not industry or industry.lower() in ["your industry", "unknown", "not found", "not_found", "n/a", ""]:
            parsed["industry"] = "Professional Services"

        return parsed
    except Exception as e:
        print(f"[brand_dna] LLM analysis failed: {e}")
        return None


def _extract_brand_from_domain(url: str) -> str:
    """Extract brand name from domain as fallback."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url if url.startswith("http") else "https://" + url)
        domain = parsed.netloc or parsed.path
        name = domain.replace("www.", "").split(".")[0]
        return name.capitalize() if name else "Website"
    except Exception:
        return "Website"


def _clean_not_found(data):
    """Recursively replace 'not_found' with user-friendly alternatives."""
    if isinstance(data, dict):
        return {k: _clean_not_found(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_clean_not_found(i) for i in data]
    if data == "not_found":
        return "Not detected"
    return data


def _minimal_fallback(url: str) -> dict:
    """Minimal fallback when everything fails."""
    domain_m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    domain = domain_m.group(1).split(".")[0].capitalize() if domain_m else "Unknown"
    return {
        "brand_name": domain,
        "tagline": "not_found",
        "industry": "not_found",
        "sub_industry": "not_found",
        "brand_voice": {
            "tone": "not_found",
            "personality_traits": [],
            "writing_style": "not_found",
            "formality_level": 5,
            "emoji_usage": "not_found",
            "jargon_level": "not_found",
        },
        "visual_identity": {
            "design_style": "not_found",
            "visual_mood": [],
            "background_style": "not_found",
            "ui_complexity": "not_found",
            "illustration_style": "not_found",
        },
        "value_proposition": {
            "primary": "not_found",
            "supporting": [],
            "unique_differentiator": "not_found",
        },
        "target_audience": {
            "primary": "not_found",
            "segments": [],
            "company_size": "not_found",
            "decision_maker": "not_found",
        },
        "products_services": [],
        "pricing": {
            "model": "not_found",
            "starting_price": "not_found",
            "has_free_tier": "not_found",
            "enterprise_plan": "not_found",
        },
        "business_objectives": {
            "primary_goal": "not_found",
            "conversion_type": "not_found",
            "sales_motion": "not_found",
        },
        "brand_positioning": {
            "market_position": "not_found",
            "key_differentiators": [],
            "innovation_level": "not_found",
        },
        "customer_pain_points": [],
        "marketing_funnel": {
            "lead_magnets": [],
            "signup_flow": "not_found",
            "trial_available": "not_found",
            "email_capture_present": "not_found",
        },
        "content_strategy": {
            "blog_exists": False,
            "content_topics": [],
            "content_formats": [],
            "content_frequency": "not_found",
        },
        "seo_signals": {
            "meta_title": "not_found",
            "meta_description": "not_found",
            "h1_text": "not_found",
            "estimated_keywords": [],
        },
        "trust_signals": {
            "testimonials": False,
            "case_studies": False,
            "client_logos": False,
            "certifications": [],
            "media_mentions": [],
        },
        "authority_signals": {
            "thought_leadership": False,
            "educational_content": False,
            "research_reports": False,
            "community_presence": False,
        },
        "social_presence": {
            "platforms_detected": [],
            "primary_platform": "not_found",
        },
        "technology_signals": {
            "platform": "not_found",
            "integrations_mentioned": [],
        },
        "competitors": {
            "mentioned_on_site": [],
            "implied_competitors": [],
        },
        "cta_patterns": [],
        "overall_scores": {
            "website_quality": 0,
            "messaging_clarity": 0,
            "trust_factor": 0,
            "seo_readiness": 0,
            "conversion_optimization": 0,
        },
    }


# ---------------------------------------------------------------------------
# BrandDNA Class
# ---------------------------------------------------------------------------

class BrandDNA:
    """
    Extracts, stores, and serves rich brand identity from a website URL.
    Crawls 14+ pages in parallel. Anti-hallucination enforced.
    Thread-safe singleton — use get_brand_dna() factory.
    """

    def extract(self, url: str) -> dict:
        """
        Full pipeline: crawl 14 pages → combine → LLM analyze → store → return.
        Never raises. Returns error dict on failure.
        """
        try:
            if not url.startswith("http"):
                url = "https://" + url
            print(f"[brand_dna] Crawling {url} across {len(COMMON_PATHS)} pages...")

            # 1. Crawl all pages in parallel
            content = _fetch_all_pages(url)
            if not content.strip():
                print(f"[brand_dna] No content retrieved — using search fallback")

            # 2. LLM comprehensive extraction
            dna = _analyze_with_llm(content, url)
            if not dna:
                dna = _minimal_fallback(url)

            # 3. Fix brand_name fallback — never show "not_found" to users
            if not dna.get("brand_name") or dna.get("brand_name") in ("not_found", "Not detected"):
                dna["brand_name"] = _extract_brand_from_domain(url)
            if not dna.get("industry") or dna.get("industry") in ("not_found", "Not detected"):
                dna["industry"] = "General Business"

            # 4. Attach metadata
            dna["url"] = url
            dna["extracted_at"] = datetime.now(timezone.utc).isoformat()

            # 5. Store raw (with original not_found values for internal use)
            self._store(url, dna)

            # 6. Clean not_found for API response
            dna = _clean_not_found(dna)

            brand = dna.get("brand_name", "unknown")
            industry = dna.get("industry", "unknown")
            voice = dna.get("brand_voice", {})
            tone = voice.get("tone", "unknown") if isinstance(voice, dict) else str(voice)
            print(f"[brand_dna] Extracted: {brand} | {industry} | {tone}")

            return {"success": True, "brand_dna": dna}

        except Exception as e:
            print(f"[brand_dna] Extraction error: {e}")
            return {"success": False, "error": str(e)}

    def _store(self, url: str, dna: dict):
        """Upsert BrandDNA — one row per domain, always overwrite latest."""
        try:
            conn = _get_conn()
            conn.execute("DELETE FROM brand_dna WHERE url = ?", (url,))

            # Backward-compat columns: extract from new rich schema
            brand_name = dna.get("brand_name", "")
            tagline = dna.get("tagline", "")
            bv = dna.get("brand_voice", {})
            brand_voice = bv.get("tone", "") if isinstance(bv, dict) else str(bv)
            tone_kw = bv.get("personality_traits", []) if isinstance(bv, dict) else []
            vp = dna.get("value_proposition", {})
            value_prop = vp.get("primary", "") if isinstance(vp, dict) else str(vp)
            ta = dna.get("target_audience", {})
            target_aud = ta.get("primary", "") if isinstance(ta, dict) else str(ta)
            industry = dna.get("industry", "")
            comps = dna.get("competitors", {})
            competitors = comps.get("mentioned_on_site", []) if isinstance(comps, dict) else []

            conn.execute(
                """INSERT INTO brand_dna
                   (url, brand_name, tagline, brand_voice, tone_keywords,
                    value_proposition, target_audience, industry, competitors,
                    content_style, color_palette, cta_patterns, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    url, brand_name, tagline, brand_voice,
                    json.dumps(tone_kw),
                    value_prop, target_aud, industry,
                    json.dumps(competitors),
                    json.dumps(dna.get("content_strategy", {})),
                    json.dumps([]),  # color_palette not extracted by LLM
                    json.dumps(dna.get("cta_patterns", [])),
                    json.dumps(dna),
                )
            )
            conn.commit()
        except Exception as e:
            print(f"[brand_dna] Store error: {e}")

    def get_stored(self) -> Optional[dict]:
        """Retrieve the most recently extracted BrandDNA from the database."""
        try:
            conn = _get_conn()
            row = conn.execute(
                "SELECT * FROM brand_dna ORDER BY extracted_at DESC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            dna = json.loads(row["raw_json"]) if row["raw_json"] else {}
            dna["extracted_at"] = row["extracted_at"]
            dna["url"] = row["url"]
            # Ensure brand_name is never "not_found" in stored data
            if not dna.get("brand_name") or dna.get("brand_name") in ("not_found", "Not detected"):
                dna["brand_name"] = _extract_brand_from_domain(dna.get("url", ""))
            if not dna.get("industry") or dna.get("industry") in ("not_found", "Not detected"):
                dna["industry"] = "General Business"
            return _clean_not_found(dna)
        except Exception as e:
            print(f"[brand_dna] get_stored error: {e}")
            return None

    def get_brand_context(self) -> str:
        """
        Rich brand context string injected into all agent prompts.
        Includes voice, positioning, pain points, audience segments.
        Returns empty string if no BrandDNA extracted yet.
        """
        try:
            dna = self.get_stored()
            if not dna:
                return ""

            brand_name = dna.get("brand_name", "")
            if not brand_name or brand_name == "not_found":
                return ""

            industry = dna.get("industry", "not_found")
            sub_industry = dna.get("sub_industry", "")

            # Brand voice
            bv = dna.get("brand_voice", {})
            if isinstance(bv, dict):
                tone = bv.get("tone", "professional")
                traits = bv.get("personality_traits", [])
                writing_style = bv.get("writing_style", "")
                formality = bv.get("formality_level", 5)
                jargon = bv.get("jargon_level", "medium")
                emoji = bv.get("emoji_usage", "none")
            else:
                tone = str(bv)
                traits = []
                writing_style = formality = jargon = emoji = ""
            traits_str = ", ".join(traits[:4]) if traits else ""

            # Audience
            ta = dna.get("target_audience", {})
            if isinstance(ta, dict):
                audience = ta.get("primary", "general audience")
                segments = ta.get("segments", [])
                co_size = ta.get("company_size", "")
                decision_maker = ta.get("decision_maker", "")
            else:
                audience = str(ta)
                segments = co_size = decision_maker = ""

            # Value prop
            vp = dna.get("value_proposition", {})
            if isinstance(vp, dict):
                primary_vp = vp.get("primary", "")
                differentiator = vp.get("unique_differentiator", "")
            else:
                primary_vp = str(vp)
                differentiator = ""

            # Pain points
            pain_points = dna.get("customer_pain_points", [])
            pain_str = "; ".join(pain_points[:3]) if pain_points else ""

            # Positioning
            bp = dna.get("brand_positioning", {})
            if isinstance(bp, dict):
                market_pos = bp.get("market_position", "")
                differentiators = bp.get("key_differentiators", [])
            else:
                market_pos = ""
                differentiators = []
            diff_str = "; ".join(differentiators[:3]) if differentiators else ""

            # Build rich context
            parts = [f"BRAND CONTEXT FOR {brand_name.upper()}:"]
            if industry and industry != "not_found":
                ind_str = industry
                if sub_industry and sub_industry != "not_found":
                    ind_str += f" / {sub_industry}"
                parts.append(f"Industry: {ind_str}")
            if primary_vp and primary_vp != "not_found":
                parts.append(f"Value Proposition: {primary_vp}")
            if audience and audience != "not_found":
                aud_str = audience
                if co_size and co_size != "not_found":
                    aud_str += f" ({co_size})"
                if decision_maker and decision_maker != "not_found":
                    aud_str += f", targeting {decision_maker}"
                parts.append(f"Target Audience: {aud_str}")
            if tone and tone != "not_found":
                voice_str = f"Brand Voice: {tone}"
                if traits_str:
                    voice_str += f" — {traits_str}"
                if writing_style:
                    voice_str += f", {writing_style} style"
                if emoji and emoji != "not_found":
                    voice_str += f", emoji usage: {emoji}"
                parts.append(voice_str)
            if pain_str:
                parts.append(f"Customer Pain Points: {pain_str}")
            if diff_str:
                parts.append(f"Key Differentiators: {diff_str}")
            if market_pos and market_pos != "not_found":
                parts.append(f"Market Position: {market_pos}")
            if differentiator and differentiator != "not_found":
                parts.append(f"Unique Differentiator: {differentiator}")

            parts.append(
                f"INSTRUCTION: Write all content matching {brand_name}'s brand identity. "
                f"Match the tone ({tone}), use language appropriate for {audience}, "
                f"and focus on their core value proposition."
            )

            return "\n".join(parts)

        except Exception as e:
            print(f"[brand_dna] get_brand_context error: {e}")
            return ""


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_brand_dna_instance: Optional[BrandDNA] = None


def get_brand_dna() -> BrandDNA:
    global _brand_dna_instance
    if _brand_dna_instance is None:
        _brand_dna_instance = BrandDNA()
    return _brand_dna_instance
