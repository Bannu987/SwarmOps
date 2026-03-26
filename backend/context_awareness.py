"""
Context Awareness Layer — SwarmOps.
Stateless: reads from DB/env at call time. Safe for multi-worker Railway.

Fixes:
- Audit without URL → asks for URL instead of hallucinating scores
- Meta-questions ("how did you do that") → honest data inventory response
- All agent calls → DATA AWARENESS header injected (what's available/missing + honesty rules)
"""
import re
import os
import logging

logger = logging.getLogger(__name__)

# ── Message Classification ─────────────────────────────────────────────────

_META_PATTERNS = [
    r"how did you",
    r"how do you( do| work| know)",
    r"where did you get",
    r"where did (those|that) (numbers?|score|data|metrics?) come from",
    r"without.*\b(url|website|data|my site)\b",
    r"how.*\b(without|no)\b.*(url|data|website)",
    r"what data (do you|did you)",
    r"how (are|were) (those|that|the) (numbers?|scores?)",
    r"how (is|was) that possible",
    r"how (did|do) you (know|generate|create|come up with)",
    r"why did you say",
]


def classify_message_type(message: str) -> str:
    """
    Returns one of: meta_question, requires_url_for_audit, general_question.
    Only checks patterns relevant to the context awareness layer.
    ConversationManager handles greetings/capabilities/onboarding.
    """
    msg = message.lower().strip()
    for pattern in _META_PATTERNS:
        if re.search(pattern, msg):
            return "meta_question"
    # Audit patterns without a URL already in the message
    if re.search(r'\baudit\b|analyze my site|review my website|grade my site', msg):
        if not re.search(r'https?://', msg):
            return "requires_url_for_audit"
    return "general_question"


# ── Data Inventory ─────────────────────────────────────────────────────────

def build_data_inventory() -> dict:
    """
    Read what data SwarmOps actually has. Stateless — reads DB + env each call.
    Returns: {available, missing, has_website, has_brand, has_analytics, has_search}
    """
    available = []
    missing = []
    has_brand = False
    has_website = False
    has_analytics = False
    has_search = False

    # Brand DNA
    try:
        from brand_dna import get_brand_dna
        dna = get_brand_dna().get_stored()
        if dna and dna.get("brand_name") and dna["brand_name"] not in ("not_found", ""):
            available.append(
                f"Brand profile: {dna['brand_name']} ({dna.get('industry', 'unknown industry')})"
            )
            _url = dna.get("url") or dna.get("website_url")
            if _url:
                available.append(f"Website content: {_url} (crawled)")
                has_website = True
            has_brand = True
        else:
            missing.append("Brand profile (share your website URL to extract)")
    except Exception:
        missing.append("Brand profile")

    # Stored website URL (may exist outside brand DNA)
    if not has_website:
        try:
            from memory_store import get_memory_store
            stored_url = get_memory_store().get_profile_key("website_url")
            if stored_url:
                available.append(f"Website URL on file: {stored_url}")
                has_website = True
        except Exception:
            pass

    # Analytics integrations — check env vars
    if os.environ.get("GA4_PROPERTY_ID"):
        available.append("Google Analytics 4 (live traffic + conversion data)")
        has_analytics = True
    else:
        missing.append("Google Analytics 4 (no live traffic data — use /tools to connect)")

    if os.environ.get("GSC_SITE_URL"):
        available.append("Google Search Console (live keyword rankings)")
        has_search = True
    else:
        missing.append("Google Search Console (no real keyword rankings)")

    if os.environ.get("HUBSPOT_API_KEY"):
        available.append("HubSpot CRM (live contact/lead data)")
    else:
        missing.append("HubSpot CRM (no live lead data)")

    if os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"):
        available.append("Google Ads (live campaign performance)")
    else:
        missing.append("Google Ads (no live ad data)")

    return {
        "available": available,
        "missing": missing,
        "has_website": has_website,
        "has_brand": has_brand,
        "has_analytics": has_analytics,
        "has_search": has_search,
    }


# ── Agent Context Header ────────────────────────────────────────────────────

def build_agent_context_header() -> str:
    """
    Returns a header prepended to EVERY agent prompt.
    Tells agents exactly what data they have and don't have.
    """
    try:
        inv = build_data_inventory()
    except Exception:
        return ""  # never block agent calls

    lines = ["=== DATA AWARENESS (READ THIS FIRST) ==="]

    if inv["available"]:
        lines.append("DATA YOU HAVE:")
        for item in inv["available"]:
            lines.append(f"  \u2713 {item}")

    if inv["missing"]:
        lines.append("DATA YOU DO NOT HAVE:")
        for item in inv["missing"]:
            lines.append(f"  \u2717 {item}")

    lines += [
        "",
        "HONESTY RULES (ABSOLUTE \u2014 never break):",
        "1. NEVER fabricate specific metrics (traffic, conversion rates, revenue figures).",
        "   Without GA4/GSC: say 'Based on industry benchmarks...' or 'I estimate...'",
        "2. NEVER invent a site score without having analyzed a specific URL.",
        "   Without a URL: say 'I\u2019d need your website URL to give specific scores.'",
        "3. When you have data, be specific. When you don\u2019t, be honest about it.",
        "4. If asked how you arrived at a number, explain your reasoning honestly.",
        "=== END DATA AWARENESS ===",
        "",
    ]
    return "\n".join(lines)


# ── Meta-Question Response ──────────────────────────────────────────────────

def get_meta_response(message: str):
    """
    Generate an honest response to 'how did you do that' / 'where did that come from'.
    Returns str or None. None means let it fall through to normal handling.
    """
    msg = message.lower()
    try:
        inv = build_data_inventory()
    except Exception:
        return None

    available_str = (
        "\n".join(f"- {x}" for x in inv["available"])
        if inv["available"] else "- No specific data yet"
    )
    missing_str = (
        "\n".join(f"- {x}" for x in inv["missing"][:4])
        if inv["missing"] else "- Nothing"
    )

    # "Without URL/website/data" questions
    if re.search(r'without.*\b(url|website|data|my site)\b', msg):
        return (
            f"You're right to question that. Here's exactly what I had:\n\n"
            f"**Data I had:**\n{available_str}\n\n"
            f"**Data I was missing:**\n{missing_str}\n\n"
            f"Without your website URL or connected analytics, I provided general recommendations "
            f"based on industry best practices and marketing frameworks \u2014 not your specific site data.\n\n"
            f"For a real analysis with actual scores, share your URL or type `/tools` to connect Google Analytics."
        )

    # "Where did those numbers/scores come from"
    if re.search(r'where did.*(numbers?|scores?|data|metrics?)|how.*(numbers?|scores?) come from', msg):
        if inv["has_analytics"]:
            return "Those numbers came from your connected Google Analytics 4 data."
        return (
            f"Those were estimates based on industry benchmarks \u2014 not your real data. "
            f"I don't have live analytics connected yet.\n\n"
            f"**What I actually have:**\n{available_str}\n\n"
            f"Connect Google Analytics with `/tools` to get real numbers."
        )

    # Generic "how did you do/know/generate that"
    if re.search(r'how did you (do|know|generate|create|come up with)|how (is|was) that possible', msg):
        return (
            f"Here's what I used for that analysis:\n\n"
            f"**Available data:**\n{available_str}\n\n"
            f"**Missing data:**\n{missing_str}\n\n"
            f"When I don't have specific data, I apply marketing frameworks and industry benchmarks. "
            f"Would you like me to walk through the reasoning, or share your URL for a data-backed analysis?"
        )

    # "What data do you have"
    if re.search(r'what data (do you|did you)', msg):
        return (
            f"Here's exactly what data I have access to:\n\n"
            f"**Available:**\n{available_str}\n\n"
            f"**Not connected yet:**\n{missing_str}\n\n"
            f"Type `/tools` to connect additional data sources."
        )

    return None  # Let it fall through to normal handling


# ── Audit URL Guard ─────────────────────────────────────────────────────────

def get_audit_url_redirect() -> str:
    """Message to return when audit is requested without a URL."""
    return (
        "I'd need your website URL to run a proper marketing audit with real scores.\n\n"
        "Try:\n"
        "`run a marketing audit on https://yoursite.com`\n\n"
        "Or if you'd like general marketing recommendations without a site audit, just ask!"
    )
