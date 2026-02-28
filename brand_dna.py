"""
BrandDNA Auto-Extraction — SwarmOps
Extracts brand identity from a website URL and injects it into all agent prompts.
Like Google Pomelli, but built for all 11 SwarmOps agents.
"""

import os
import re
import json
import requests
from datetime import datetime, timezone
from typing import Optional
from db import get_connection as _get_conn, DB_PATH


def _init_tables():
    """Create brand_dna table if it doesn't exist."""
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
# HTML Parsing — no BeautifulSoup (not in requirements), pure regex
# ---------------------------------------------------------------------------

def _fetch_page(url: str, timeout: int = 10) -> str:
    """
    Fetch homepage HTML. Returns empty string on failure.
    Uses a realistic User-Agent to avoid bot blocks.
    """
    try:
        if not url.startswith("http"):
            url = "https://" + url
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[brand_dna] Fetch error for {url}: {e}")
        return ""


def _extract_page_signals(html: str, url: str) -> dict:
    """
    Extract brand signals from raw HTML using regex.
    Returns a dict of extracted text signals for LLM analysis.
    """
    signals = {}

    # Title tag
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    signals["title"] = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else ""

    # Meta description
    meta_desc = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    ) or re.search(
        r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']description["\']',
        html, re.IGNORECASE
    )
    signals["meta_description"] = meta_desc.group(1).strip() if meta_desc else ""

    # OG title and description (often cleaner brand messaging)
    og_title = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    signals["og_title"] = og_title.group(1).strip() if og_title else ""

    og_desc = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    signals["og_description"] = og_desc.group(1).strip() if og_desc else ""

    # H1 tags (hero headline — key brand signal)
    h1_matches = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    h1_texts = [re.sub(r"<[^>]+>", "", h).strip() for h in h1_matches if h.strip()]
    signals["h1_tags"] = h1_texts[:3]

    # H2 tags (subheadings — value props)
    h2_matches = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.IGNORECASE | re.DOTALL)
    h2_texts = [re.sub(r"<[^>]+>", "", h).strip() for h in h2_matches if h.strip()]
    signals["h2_tags"] = h2_texts[:5]

    # CTA buttons and links (action language)
    button_matches = re.findall(r"<(?:button|a)[^>]*>(.*?)</(?:button|a)>", html, re.IGNORECASE | re.DOTALL)
    cta_texts = []
    for btn in button_matches:
        text = re.sub(r"<[^>]+>", "", btn).strip()
        if 2 < len(text) < 50 and any(
            word in text.lower() for word in
            ["get", "start", "try", "sign", "book", "demo", "join", "free", "buy",
             "learn", "explore", "request", "contact", "watch", "download"]
        ):
            cta_texts.append(text)
    signals["cta_patterns"] = list(dict.fromkeys(cta_texts))[:10]  # dedupe, cap at 10

    # Color palette — hex codes from inline styles and CSS
    hex_colors = re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", html)
    # Filter out near-white / near-black, dedupe
    meaningful_colors = []
    seen = set()
    for c in hex_colors:
        full = c if len(c) == 6 else c[0]*2 + c[1]*2 + c[2]*2
        val = int(full, 16)
        if val not in (0x000000, 0xFFFFFF, 0xffffff, 0x000) and full not in seen:
            seen.add(full)
            meaningful_colors.append("#" + full.upper())
        if len(meaningful_colors) >= 8:
            break
    signals["color_palette"] = meaningful_colors

    # Domain name as fallback brand name
    domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    signals["domain"] = domain_match.group(1).split(".")[0].capitalize() if domain_match else ""

    # Body text sample for voice analysis (first 2000 chars of visible text)
    body_text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    body_text = re.sub(r"<style[^>]*>.*?</style>", "", body_text, flags=re.DOTALL | re.IGNORECASE)
    body_text = re.sub(r"<[^>]+>", " ", body_text)
    body_text = re.sub(r"\s+", " ", body_text).strip()
    signals["body_sample"] = body_text[:2000]

    return signals


# ---------------------------------------------------------------------------
# LLM Analysis
# ---------------------------------------------------------------------------

_EXTRACTION_SYSTEM_PROMPT = """You are a brand intelligence analyst.
You analyze website content and extract structured brand DNA.
Return ONLY valid JSON — no markdown, no explanation, just the JSON object."""

_EXTRACTION_PROMPT_TEMPLATE = """Analyze this website content and extract the brand DNA.

Website URL: {url}
Page Title: {title}
Meta Description: {meta_description}
OG Title: {og_title}
OG Description: {og_description}
H1 Headlines: {h1_tags}
H2 Subheadings: {h2_tags}
CTA Buttons Found: {cta_patterns}
Body Text Sample: {body_sample}

Return ONLY this exact JSON structure (no markdown, no explanation):
{{
  "brand_name": "string — company name",
  "tagline": "string — main hero tagline or value statement",
  "brand_voice": "string — one of: formal / casual / technical / friendly / professional / bold / authoritative",
  "tone_keywords": ["adj1", "adj2", "adj3", "adj4", "adj5"],
  "value_proposition": "string — the main benefit or promise in 1-2 sentences",
  "target_audience": "string — who this brand serves",
  "industry": "string — one of: ecommerce / saas / b2b / b2c / healthcare / fintech / edtech / agency / media / other",
  "competitors": ["competitor1", "competitor2"],
  "content_style": {{
    "avg_sentence_length": "short / medium / long",
    "reading_level": "simple / intermediate / advanced",
    "uses_emoji": true or false,
    "uses_jargon": true or false
  }},
  "cta_patterns": ["cta1", "cta2", "cta3"]
}}"""


def _analyze_with_llm(signals: dict, url: str) -> Optional[dict]:
    """
    Send extracted signals to the LLM and get structured JSON back.
    Returns parsed dict or None on failure.
    """
    try:
        from model_router import call_model_sync
        prompt = _EXTRACTION_PROMPT_TEMPLATE.format(
            url=url,
            title=signals.get("title", ""),
            meta_description=signals.get("meta_description", ""),
            og_title=signals.get("og_title", ""),
            og_description=signals.get("og_description", ""),
            h1_tags=", ".join(signals.get("h1_tags", [])),
            h2_tags=", ".join(signals.get("h2_tags", [])),
            cta_patterns=", ".join(signals.get("cta_patterns", [])),
            body_sample=signals.get("body_sample", "")[:1500],
        )
        result = call_model_sync(
            prompt=prompt,
            system_prompt=_EXTRACTION_SYSTEM_PROMPT,
            tier=2,
            max_tokens=1024,
            temperature=0.3,  # Low temp for consistent structured output
        )
        raw = result.get("content", "")

        # Strip markdown fences if model wraps in ```json
        clean = raw.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```[a-z]*\n?", "", clean)
            clean = re.sub(r"\n?```$", "", clean)

        return json.loads(clean.strip())
    except Exception as e:
        print(f"[brand_dna] LLM analysis failed: {e}")
        return None


# ---------------------------------------------------------------------------
# BrandDNA Class
# ---------------------------------------------------------------------------

class BrandDNA:
    """
    Extracts, stores, and serves brand identity from a website URL.
    Thread-safe singleton pattern — use get_brand_dna() factory.
    """

    def extract(self, url: str) -> dict:
        """
        Full pipeline: fetch → parse → LLM analyze → store → return.
        Never raises — returns error dict on failure.
        """
        try:
            print(f"[brand_dna] Extracting BrandDNA from: {url}")

            # 1. Fetch the homepage
            html = _fetch_page(url)
            if not html:
                # Fallback: try Brave search for brand info
                html = self._fallback_search(url)

            # 2. Extract signals from HTML
            signals = _extract_page_signals(html, url)

            # 3. LLM analysis
            dna = _analyze_with_llm(signals, url)
            if not dna:
                # Minimal fallback from signals
                dna = {
                    "brand_name": signals.get("domain", "Unknown Brand"),
                    "tagline": signals.get("og_title") or signals.get("title", ""),
                    "brand_voice": "professional",
                    "tone_keywords": ["professional", "clear", "direct", "reliable", "modern"],
                    "value_proposition": signals.get("meta_description", ""),
                    "target_audience": "General audience",
                    "industry": "other",
                    "competitors": [],
                    "content_style": {
                        "avg_sentence_length": "medium",
                        "reading_level": "intermediate",
                        "uses_emoji": False,
                        "uses_jargon": False,
                    },
                    "cta_patterns": signals.get("cta_patterns", []),
                }

            # 4. Merge in color palette from HTML (LLM doesn't extract these)
            dna["color_palette"] = signals.get("color_palette", [])
            dna["url"] = url

            # 5. Store in DB
            self._store(url, dna)

            print(f"[brand_dna] Extracted: {dna.get('brand_name')} | {dna.get('industry')} | {dna.get('brand_voice')}")
            return {"success": True, "brand_dna": dna}

        except Exception as e:
            print(f"[brand_dna] Extraction error: {e}")
            return {"success": False, "error": str(e)}

    def _fallback_search(self, url: str) -> str:
        """Use Brave/Serper to get brand info if direct fetch fails."""
        try:
            from model_router import search_brave, search_serper
            domain = re.search(r"https?://(?:www\.)?([^/]+)", url)
            brand_domain = domain.group(1) if domain else url
            results = search_brave(f"site:{brand_domain} brand about", max_results=3)
            if not results:
                results = search_serper(f"{brand_domain} company about", max_results=3)
            if results:
                combined = " ".join(r.get("description", "") for r in results)
                return f"<title>{brand_domain}</title><meta name='description' content='{combined}'>"
        except Exception:
            pass
        return ""

    def _store(self, url: str, dna: dict):
        """Upsert BrandDNA into the database (one row — always overwrite latest)."""
        try:
            conn = _get_conn()
            # Delete old entry for this domain, keep only latest
            conn.execute("DELETE FROM brand_dna WHERE url = ?", (url,))
            conn.execute(
                """INSERT INTO brand_dna
                   (url, brand_name, tagline, brand_voice, tone_keywords,
                    value_proposition, target_audience, industry, competitors,
                    content_style, color_palette, cta_patterns, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    url,
                    dna.get("brand_name", ""),
                    dna.get("tagline", ""),
                    dna.get("brand_voice", ""),
                    json.dumps(dna.get("tone_keywords", [])),
                    dna.get("value_proposition", ""),
                    dna.get("target_audience", ""),
                    dna.get("industry", ""),
                    json.dumps(dna.get("competitors", [])),
                    json.dumps(dna.get("content_style", {})),
                    json.dumps(dna.get("color_palette", [])),
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
            return dna
        except Exception as e:
            print(f"[brand_dna] get_stored error: {e}")
            return None

    def get_brand_context(self) -> str:
        """
        Returns a formatted brand context string for injection into agent prompts.
        Returns empty string if no BrandDNA has been extracted yet.
        """
        try:
            dna = self.get_stored()
            if not dna:
                return ""

            brand_name = dna.get("brand_name", "")
            industry = dna.get("industry", "")
            brand_voice = dna.get("brand_voice", "")
            target_audience = dna.get("target_audience", "")
            value_proposition = dna.get("value_proposition", "")
            tone_keywords = dna.get("tone_keywords", [])
            tone_str = ", ".join(tone_keywords) if isinstance(tone_keywords, list) else tone_keywords

            if not brand_name:
                return ""

            return (
                f"BRAND CONTEXT: {brand_name} is a {industry} company. "
                f"Voice: {brand_voice}. "
                f"Target audience: {target_audience}. "
                f"Value proposition: {value_proposition}. "
                f"Tone: {tone_str}. "
                f"Write all content matching this brand identity."
            )
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
