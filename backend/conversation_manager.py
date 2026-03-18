import json
import re
from db import get_connection


class ConversationManager:
    """
    Central brain that manages conversation state, context loading,
    and routing decisions. Replaces scattered if/else logic in main.py.

    Principles:
    1. NEVER block a user question with setup
    2. Answer first, ask for context after
    3. Load ALL stored context before every response
    4. Setup runs ONCE, progressively, non-blocking
    """

    STATE_NEW = "new"
    STATE_PROFILED = "profiled"
    STATE_ACTIVE = "active"

    # Intent scoring weights — each intent has keyword signals with weights
    _INTENT_SIGNALS = {
        "seo": {
            "keywords": ["seo", "keyword", "rank", "ranking", "search engine", "organic traffic",
                         "backlink", "meta tag", "serp", "google search", "search visibility"],
            "weight": 1.0,
        },
        "content": {
            "keywords": ["blog", "article", "content", "copy", "write", "writing", "post ideas",
                         "content strategy", "content calendar", "headline", "copywriting"],
            "weight": 1.0,
        },
        "ppc": {
            "keywords": ["ads", "ppc", "google ads", "facebook ads", "paid", "campaign",
                         "ad copy", "cpc", "roas", "budget", "ad spend", "retargeting"],
            "weight": 1.0,
        },
        "analytics": {
            "keywords": ["analytics", "metrics", "data", "roi", "conversion rate", "bounce rate",
                         "traffic stats", "performance", "kpi", "dashboard", "report"],
            "weight": 1.0,
        },
        "cro": {
            "keywords": ["conversion", "cro", "funnel", "checkout", "cart", "a/b test",
                         "landing page", "cta", "button", "form", "checkout flow"],
            "weight": 1.0,
        },
        "leads": {
            "keywords": ["leads", "lead generation", "lead gen", "pipeline", "prospects",
                         "sign up", "sign-up", "more customers", "get clients"],
            "weight": 1.0,
        },
        "social": {
            "keywords": ["social media", "instagram", "linkedin", "twitter", "tiktok",
                         "facebook", "post", "engagement", "viral", "followers"],
            "weight": 1.0,
        },
        "email": {
            "keywords": ["email", "newsletter", "sequence", "drip", "nurture",
                         "open rate", "click rate", "unsubscribe", "crm", "retention"],
            "weight": 1.0,
        },
        "brand": {
            "keywords": ["brand", "branding", "positioning", "identity", "voice", "tone",
                         "messaging", "differentiation", "value proposition"],
            "weight": 1.0,
        },
        "research": {
            "keywords": ["competitor", "competition", "market research", "industry",
                         "trends", "analysis", "benchmark", "compare"],
            "weight": 1.0,
        },
        "traffic": {
            "keywords": ["traffic", "visitors", "website traffic", "more traffic",
                         "increase traffic", "grow traffic", "site traffic",
                         "grow my business", "grow my website", "grow my brand"],
            "weight": 1.0,
        },
        "sales": {
            "keywords": ["sales", "revenue", "sell", "selling", "increase sales",
                         "more sales", "close deals", "customers"],
            "weight": 1.0,
        },
        "general_marketing": {
            "keywords": ["marketing", "marketing strategy", "marketing strategies",
                         "marketing plan", "marketing ideas", "digital marketing",
                         "online marketing", "help me grow", "grow my", "business growth"],
            "weight": 1.0,
        },
    }

    def __init__(self):
        self._ensure_tables()

    def _ensure_tables(self):
        conn = get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def get_state(self):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT value FROM conversation_state WHERE key='state'"
            ).fetchone()
            return row[0] if row else self.STATE_NEW
        except Exception:
            return self.STATE_NEW

    def set_state(self, state):
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO conversation_state (key, value, updated_at) VALUES ('state', ?, CURRENT_TIMESTAMP)",
            (state,),
        )
        conn.commit()

    def has_brand(self):
        try:
            conn = get_connection()
            count = conn.execute("SELECT COUNT(*) FROM brand_dna").fetchone()[0]
            return count > 0
        except Exception:
            return False

    def has_profile(self):
        try:
            from memory_store import get_memory_store as _get_ms_hp
            url = _get_ms_hp().get_profile_key("website_url")
            return bool(url and url != "skipped")
        except Exception:
            return False

    def load_full_context(self):
        """Load ALL stored context into one dict. Called before every response."""
        context = {
            "brand_name": None,
            "industry": None,
            "voice": None,
            "audience": None,
            "value_prop": None,
            "website_url": None,
            "goal": None,
            "competitors": [],
            "conversation_history": [],
            "kb_stats": None,
        }

        conn = get_connection()

        # Brand DNA
        try:
            row = conn.execute(
                "SELECT raw_json, url FROM brand_dna ORDER BY extracted_at DESC LIMIT 1"
            ).fetchone()
            if row:
                brand = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
                context["brand_name"] = brand.get("brand_name")
                context["industry"] = brand.get("industry")
                context["website_url"] = brand.get("website_url") or brand.get("url") or row[1]

                voice = brand.get("brand_voice", {})
                if isinstance(voice, dict):
                    tone = voice.get("tone", "professional")
                    traits = voice.get("personality_traits", [])
                    context["voice"] = (
                        f"{tone} — {', '.join(traits[:3])}" if traits else tone
                    )
                else:
                    context["voice"] = str(voice) if voice else None

                audience = brand.get("target_audience", {})
                if isinstance(audience, dict):
                    primary = audience.get("primary", "businesses")
                    segments = audience.get("segments", [])
                    context["audience"] = primary + (
                        f" ({', '.join(segments[:3])})" if segments else ""
                    )
                else:
                    context["audience"] = str(audience) if audience else None

                vp = brand.get("value_proposition", {})
                if isinstance(vp, dict):
                    context["value_prop"] = vp.get("primary", "")
                else:
                    context["value_prop"] = str(vp) if vp else ""
        except Exception:
            pass

        # Load website_url — check business_profile key/value store FIRST (most reliable)
        try:
            from memory_store import get_memory_store as _get_ms
            _ms = _get_ms()
            _stored_url = _ms.get_profile_key("website_url")
            if _stored_url and _stored_url != "skipped":
                context["website_url"] = _stored_url
        except Exception:
            pass

        # Fallback to brand_dna table if not in business_profile
        if not context.get("website_url"):
            try:
                row = conn.execute(
                    "SELECT data FROM brand_dna ORDER BY created_at DESC LIMIT 1"
                ).fetchone()
                if row:
                    import json as _json
                    d = _json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    if isinstance(d, dict):
                        context["website_url"] = d.get("website_url") or d.get("url", "")
            except Exception:
                pass

        # Business profile goal (from key/value store)
        try:
            from memory_store import get_memory_store as _get_ms2
            _ms2 = _get_ms2()
            _goal = _ms2.get_profile_key("primary_goal")
            if _goal:
                context["goal"] = _goal
        except Exception:
            pass

        # Competitors
        try:
            rows = conn.execute("SELECT name FROM competitors LIMIT 5").fetchall()
            context["competitors"] = [r[0] for r in rows]
        except Exception:
            pass

        # Conversation memory (last 3 entries)
        try:
            rows = conn.execute(
                "SELECT strategies_discussed, metrics_mentioned "
                "FROM conversation_memory ORDER BY created_at DESC LIMIT 3"
            ).fetchall()
            for row in rows:
                if row[0]:
                    context["conversation_history"].append(
                        f"Previously discussed: {row[0]}"
                    )
                if row[1]:
                    context["conversation_history"].append(
                        f"Known metrics: {row[1]}"
                    )
        except Exception:
            pass

        # KB stats
        try:
            from knowledge_base import get_knowledge_base
            context["kb_stats"] = get_knowledge_base().get_stats()
        except Exception:
            pass

        return context

    def build_context_string(self, context):
        """Convert context dict to a prompt-injection string."""
        parts = []
        # URL first — so Nexus never asks for it again
        if context.get("website_url"):
            parts.append(f"Website (already provided): {context['website_url']}")
        if context.get("brand_name"):
            parts.append(f"Brand: {context['brand_name']}")
        if context.get("industry"):
            parts.append(f"Industry: {context['industry']}")
        if context.get("voice"):
            parts.append(f"Voice: {context['voice']}")
        if context.get("audience"):
            parts.append(f"Audience: {context['audience']}")
        if context.get("value_prop"):
            parts.append(f"Value Proposition: {context['value_prop']}")
        if context.get("goal"):
            parts.append(f"Goal: {context['goal']}")
        if context.get("competitors"):
            parts.append(f"Competitors: {', '.join(context['competitors'])}")
        if context.get("conversation_history"):
            parts.append(
                "Recent history: " + "; ".join(context["conversation_history"][:3])
            )

        if parts:
            return "BRAND CONTEXT:\n" + "\n".join(parts)
        return ""

    def _score_intent(self, msg: str) -> str:
        """Score message against intent signals. Returns best-matching intent or 'general'."""
        msg_lower = msg.lower()
        scores = {}
        for intent, cfg in self._INTENT_SIGNALS.items():
            score = sum(1 for kw in cfg["keywords"] if kw in msg_lower)
            if score > 0:
                scores[intent] = score * cfg["weight"]
        if not scores:
            return "general"
        return max(scores, key=scores.get)

    def classify_intent(self, message: str) -> str:
        """Classify user intent using deterministic bypasses + scoring-based routing."""
        msg = message.lower().strip()

        # ── DETERMINISTIC BYPASSES (checked first, no scoring needed) ──

        # Capability queries — hardcoded response, never touch LLM
        capability_patterns = [
            "how can you help", "what can you do", "what do you do",
            "your capabilities", "what are your features",
            "show me what you can do", "what can swarmops do",
            "what features", "what do you offer",
        ]
        if any(p in msg for p in capability_patterns):
            return "capabilities"

        # URL provided
        if re.search(r'https?://|www\.|\.\w{2,3}/', msg):
            return "url_provided"

        # Context/memory queries — ONLY exact recall phrases
        context_patterns = [
            "what do you know about me", "what do you know about my",
            "what have you learned", "what do you remember",
            "my profile", "my brand data", "show my data",
            "what do you know",
        ]
        if any(p in msg for p in context_patterns):
            return "context_query"

        # Audit request
        audit_patterns = ["audit", "analyze my site", "review my website",
                          "grade my site", "website analysis", "grade my website"]
        if any(w in msg for w in audit_patterns):
            return "audit"

        # Greetings
        if msg in ["hello", "hi", "hey", "hii", "sup", "yo", "hiya", "howdy"]:
            return "greeting"

        # Vague help — exact phrases that indicate no specific intent
        # These always return vague_help regardless of keyword scoring
        vague_patterns = ["help me with marketing", "help me with my marketing",
                          "i need marketing help", "get started", "set up my profile"]
        if any(p in msg for p in vague_patterns):
            return "vague_help"

        # ── SCORING-BASED ROUTING ──
        scored_intent = self._score_intent(msg)
        if scored_intent != "general":
            return "specific_request"

        # Fallback: general questions → nexus
        return "general_question"

    def decide_action(self, message, agent):
        """
        Main decision function — called for every chat message.
        Returns (action, data).

        Actions:
          onboarding_start   — vague help, no brand -> ask for URL (non-blocking)
          onboarding_url     — URL provided, no brand -> extract brand DNA
          context_response   — 'what do you know about me'
          greeting           — short greeting
          route_agent        — specific agent explicitly selected
          route_nexus        — route to Nexus with full context
          route_audit        — trigger marketing audit
        """
        intent = self.classify_intent(message)
        has_brand = self.has_brand()

        # Specific agent selected -> always route directly (never block)
        if agent and agent not in ("nexus", ""):
            return ("route_agent", {"agent": agent})

        if intent == "greeting":
            return ("greeting", {"personalized": has_brand})

        if intent == "context_query":
            return ("context_response", {})

        if intent == "capabilities":
            return ("capabilities_response", {})

        if intent == "audit":
            url_match = re.search(r"https?://[^\s]+", message)
            return ("route_audit", {"url": url_match.group() if url_match else None})

        if intent == "url_provided" and not has_brand:
            return ("onboarding_url", {})

        if intent == "vague_help" and not has_brand:
            return ("onboarding_start", {})

        # Everything else -> Nexus with full context
        return ("route_nexus", {})

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    def handle_greeting(self, personalized=False):
        if personalized:
            context = self.load_full_context()
            name = context.get("brand_name") or "there"
            goal = context.get("goal") or "growth"
            return (
                f"Welcome back! Ready to work on {goal} for {name}? "
                "What would you like to focus on today?"
            )
        return (
            "Hello! I'm SwarmOps — your AI marketing team. "
            "What marketing challenge can I help you with today?"
        )

    def handle_context_query(self):
        context = self.load_full_context()
        parts = ["Here's everything I know about your business:\n"]

        if context.get("brand_name"):
            parts.append(f"**Brand:** {context['brand_name']}")
            parts.append(f"**Industry:** {context.get('industry') or 'Not detected'}")
            if context.get("voice"):
                parts.append(f"**Voice:** {context['voice']}")
            if context.get("audience"):
                parts.append(f"**Audience:** {context['audience']}")
            if context.get("value_prop"):
                parts.append(f"**Value Proposition:** {context['value_prop']}")
            if context.get("website_url"):
                parts.append(f"**Website:** {context['website_url']}")
        else:
            parts.append(
                "I don't have your brand profile yet. "
                "Share your website URL and I'll analyze it automatically."
            )

        if context.get("goal"):
            parts.append(f"\n**Goal:** {context['goal']}")
        if context.get("competitors"):
            parts.append(f"**Competitors tracked:** {', '.join(context['competitors'])}")

        kb = context.get("kb_stats")
        if kb and kb.get("total_documents", 0) > 0:
            parts.append(
                f"\n**Knowledge Base:** {kb['total_documents']} pages crawled, "
                f"{kb['total_chunks']} data chunks stored"
            )

        if context.get("conversation_history"):
            parts.append(
                "\n**What we've discussed:** "
                + "; ".join(context["conversation_history"][:3])
            )

        parts += [
            "\nWhat would you like to do next?",
            "1. Update any of this information",
            "2. Run a full marketing audit",
            "3. Start working on a specific goal",
        ]
        return "\n".join(parts)

    def handle_capabilities(self):
        return """I'm SwarmOps — your AI marketing team with 11 specialized agents:

• **SEO** — Keyword research, ranking strategy, technical SEO
• **Content** — Blog posts, articles, copy in your brand voice
• **PPC** — Google Ads campaigns, budget optimization
• **Analytics** — Performance analysis, ROI computation
• **CRM** — Email sequences, lead nurturing
• **Social Media** — Post strategy, platform optimization
• **Brand** — Positioning, messaging, differentiation
• **Web/UX** — Landing page optimization, conversion design
• **CRO** — Funnel analysis, A/B test recommendations
• **Research** — Market research, competitor analysis

I also offer:
• **Marketing Audit** — Grade any website A+ through F
• **Brand DNA** — Extract your brand identity from your URL
• **Competitive Intel** — Track and compare competitors

Share your website URL and I'll personalize everything to your business. Or just ask a question and I'll route it to the right specialist."""

    def format_brand_for_onboarding(self, brand_data):
        """Format brand data for onboarding display. NEVER show defaults."""
        import logging

        # Handle string (JSON)
        if isinstance(brand_data, str):
            try:
                brand_data = json.loads(brand_data)
            except Exception:
                pass

        # Handle nested wrappers
        if isinstance(brand_data, dict) and "data" in brand_data:
            brand_data = brand_data["data"]
        if isinstance(brand_data, dict) and "raw_json" in brand_data:
            try:
                brand_data = json.loads(brand_data["raw_json"])
            except Exception:
                pass

        # Handle brand_dna wrapper returned by BrandDNA.extract()
        if isinstance(brand_data, dict) and "brand_dna" in brand_data:
            brand_data = brand_data["brand_dna"]

        if not isinstance(brand_data, dict):
            brand_data = {}

        logging.info(f"format_brand_for_onboarding: brand_name={brand_data.get('brand_name', 'MISSING')}")

        name = brand_data.get("brand_name", "")
        industry = brand_data.get("industry", "")

        # Never show default placeholders
        if not name or name.lower() in ["your brand", "unknown", "not found", "not_found", "", "none", "n/a"]:
            url = brand_data.get("website_url", "") or brand_data.get("url", "")
            if url:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace("www.", "")
                n = domain.split(".")[0]
                name = n.upper() if len(n) <= 4 else n.replace("-", " ").title()
            else:
                name = "Your Business"

        if not industry or industry.lower() in ["your industry", "unknown", "not found", "not_found", "", "none", "n/a"]:
            industry = "Technology"

        # Format voice
        voice = brand_data.get("brand_voice", {})
        if isinstance(voice, dict):
            tone = voice.get("tone", "professional")
            traits = voice.get("personality_traits", [])
            voice_str = f"{tone} — {', '.join(traits[:3])}" if traits else tone
        elif isinstance(voice, str) and voice not in ["not_found", ""]:
            voice_str = voice
        else:
            voice_str = "professional"

        # Format audience
        audience = brand_data.get("target_audience", {})
        if isinstance(audience, dict):
            primary = audience.get("primary", "businesses")
            segments = audience.get("segments", [])
            audience_str = f"{primary}" + (f" ({', '.join(segments[:3])})" if segments else "")
        elif isinstance(audience, str) and audience not in ["not_found", ""]:
            audience_str = audience
        else:
            audience_str = "businesses"

        return {
            "name": name,
            "industry": industry,
            "voice": voice_str,
            "audience": audience_str
        }


_cm_instance = None


def get_conversation_manager():
    global _cm_instance
    if _cm_instance is None:
        _cm_instance = ConversationManager()
    return _cm_instance
