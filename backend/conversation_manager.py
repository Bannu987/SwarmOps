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
            conn = get_connection()
            row = conn.execute(
                "SELECT website_url, primary_goal FROM business_profile LIMIT 1"
            ).fetchone()
            return row is not None and row[0] is not None
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
                "SELECT data FROM brand_dna ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if row:
                brand = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                context["brand_name"] = brand.get("brand_name")
                context["industry"] = brand.get("industry")
                context["website_url"] = brand.get("website_url") or brand.get("url")

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

        # Business profile (goal + url override)
        try:
            row = conn.execute(
                "SELECT website_url, primary_goal FROM business_profile LIMIT 1"
            ).fetchone()
            if row:
                if not context["website_url"] and row[0]:
                    context["website_url"] = row[0]
                context["goal"] = row[1]
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
        if context.get("website_url"):
            parts.append(f"Website: {context['website_url']}")
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

    def classify_intent(self, message):
        """Classify user intent to drive routing."""
        msg = message.lower().strip()

        # URL provided
        if re.search(r"https?://|www\.", msg):
            return "url_provided"

        # Context query
        if any(
            p in msg
            for p in [
                "what do you know",
                "what have you learned",
                "my business",
                "my brand",
                "my profile",
                "what do you remember",
            ]
        ):
            return "context_query"

        # Audit
        if any(
            w in msg
            for w in [
                "audit",
                "analyze my site",
                "review my website",
                "grade my site",
                "website analysis",
            ]
        ):
            return "audit"

        # Greeting
        if msg in {"hello", "hi", "hey", "hii", "sup", "yo", "hiya", "howdy"}:
            return "greeting"

        # Vague help (with no specific question)
        if any(
            p in msg
            for p in [
                "help me with marketing",
                "help me with my marketing",
                "i need marketing help",
                "get started",
                "set up my profile",
                "help me get started",
            ]
        ):
            return "vague_help"

        return "specific_request"

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

    def format_brand_for_onboarding(self, brand_data):
        """Format brand extraction result into clean display strings."""
        name = brand_data.get("brand_name") or "Your Brand"
        industry = brand_data.get("industry") or "your industry"

        voice = brand_data.get("brand_voice", {})
        if isinstance(voice, dict):
            tone = voice.get("tone", "professional")
            traits = voice.get("personality_traits", [])
            voice_str = f"{tone} — {', '.join(traits[:3])}" if traits else tone
        else:
            voice_str = str(voice) if voice else "professional"

        audience = brand_data.get("target_audience", {})
        if isinstance(audience, dict):
            primary = audience.get("primary", "businesses")
            segments = audience.get("segments", [])
            audience_str = primary + (
                f" ({', '.join(segments[:3])})" if segments else ""
            )
        else:
            audience_str = str(audience) if audience else "general audience"

        return {
            "name": name,
            "industry": industry,
            "voice": voice_str,
            "audience": audience_str,
        }


_cm_instance = None


def get_conversation_manager():
    global _cm_instance
    if _cm_instance is None:
        _cm_instance = ConversationManager()
    return _cm_instance
