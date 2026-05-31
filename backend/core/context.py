"""
Context awareness: data inventory + honesty rules + meta-question detection.
"""
import re
import os
from typing import Dict, Optional


class ContextAwareness:
    """Track what data the system has, prevent fabrication."""

    def __init__(self):
        self.brand_data: Dict = {}
        self.website_url: str = ""
        self.uploaded_files = []
        self.project_id: Optional[str] = None

    def update_brand(self, brand: Dict, url: str = ""):
        if isinstance(brand, dict):
            self.brand_data = brand
        if url:
            self.website_url = url

    def add_upload(self, file_info: Dict):
        self.uploaded_files.append(file_info)

    def classify_message(self, msg: str) -> str:
        """Classify intent: meta_question, requires_url, action_request, greeting, general."""
        low = msg.lower().strip()

        # Meta-questions
        meta_patterns = [
            r"how did you", r"how do you", r"what data do you",
            r"without.*url", r"without.*data", r"where.*get.*numbers",
        ]
        for p in meta_patterns:
            if re.search(p, low):
                return "meta_question"

        # URL-required tasks
        url_patterns = [r"audit", r"analyze.*site", r"crawl", r"check.*website"]
        for p in url_patterns:
            if re.search(p, low) and not self.website_url:
                return "requires_url"

        if low in ["hi", "hello", "hey", "help", "help me"]:
            return "greeting"

        if any(w in low for w in ["create", "write", "build", "generate", "make", "draft"]):
            return "action_request"

        return "general"

    def data_inventory(self) -> Dict:
        """What data do we have / not have?"""
        has = []
        missing = []

        if self.brand_data.get("brand_name"):
            has.append(f"Brand: {self.brand_data['brand_name']}")
            if self.brand_data.get("industry"):
                has.append(f"Industry: {self.brand_data['industry']}")
        else:
            missing.append("Brand profile (no URL shared yet)")

        if self.website_url:
            has.append(f"Website crawled: {self.website_url}")
        else:
            missing.append("Website URL (no site analysis possible)")

        if self.uploaded_files:
            has.append(f"Uploaded files: {len(self.uploaded_files)}")

        # Integrations
        if os.environ.get("GA4_PROPERTY_ID"):
            has.append("Google Analytics 4 (live data)")
        else:
            missing.append("Google Analytics 4 (no traffic data)")

        if os.environ.get("HUBSPOT_API_KEY"):
            has.append("HubSpot CRM")
        else:
            missing.append("HubSpot CRM (no lead data)")

        return {
            "available": has,
            "missing": missing,
            "has_url": bool(self.website_url),
            "has_brand": bool(self.brand_data.get("brand_name")),
        }

    def context_header(self) -> str:
        """Build context header for agent prompts."""
        inv = self.data_inventory()

        lines = ["=== DATA AWARENESS (READ FIRST) ==="]

        if inv["available"]:
            lines.append("DATA YOU HAVE:")
            for item in inv["available"]:
                lines.append(f"  + {item}")

        if inv["missing"]:
            lines.append("DATA YOU DO NOT HAVE:")
            for item in inv["missing"]:
                lines.append(f"  - {item}")

        # Inject persistent project memories to prevent redundant / generic advice
        if self.project_id:
            try:
                from .memory import retrieve_relevant_memories
                memories = retrieve_relevant_memories(self.project_id, limit=6)
                if memories:
                    lines.append("\n=== PERSISTENT BRAND & CAMPAIGN HISTORY (DO NOT CONTRADICT) ===")
                    grouped = {}
                    for m in memories:
                        t = m.get("memory_type", "insight").replace("_", " ").upper()
                        if t not in grouped:
                            grouped[t] = []
                        grouped[t].append(f"  * {m.get('title')}: {m.get('summary')}")
                    
                    for t, items in grouped.items():
                        lines.append(f" [{t}]:")
                        lines.extend(items)
            except Exception as e:
                pass

        lines.append("")
        lines.append("HONESTY RULES (ABSOLUTE):")
        lines.append("1. NEVER fabricate specific metrics without data sources")
        lines.append("2. NEVER invent scores for sites you haven't analyzed")
        lines.append("3. Qualify recommendations: 'Based on benchmarks...' if no data")
        lines.append("4. If asked how you knew something, explain honestly")

        # Uploaded files
        if self.uploaded_files:
            lines.append("\n=== UPLOADED DOCUMENTS ===")
            for f in self.uploaded_files[-3:]:
                lines.append(f"--- {f.get('filename')} ---")
                lines.append(f.get('content', '')[:1500])

        return "\n".join(lines)

    def meta_response(self, msg: str) -> Optional[str]:
        """Generate honest response to meta-questions."""
        inv = self.data_inventory()
        low = msg.lower()

        if "without" in low and ("url" in low or "data" in low):
            avail = ", ".join(inv["available"]) if inv["available"] else "no specific data"
            missing = ", ".join(inv["missing"][:3])
            return f"""You're right to ask. Here's exactly what I had:

**Data I had:** {avail}

**Data I was missing:** {missing}

Without your website URL or analytics, I provided recommendations based on industry benchmarks. For a real, data-driven analysis I'd need:

1. **Your website URL** — for actual content, SEO, UX analysis
2. **Google Analytics** — for real traffic and conversion data
3. **Search Console** — for keyword rankings

Share your URL and I'll run a real analysis."""

        if "how did you" in low or "how do you" in low:
            return f"""Here's how that analysis worked:

1. I checked what data was available (brand profile, website, integrations)
2. I routed your request to the relevant specialist agents
3. Each agent applied their domain expertise to the available data
4. I synthesized findings into one response

**Currently available:** {', '.join(inv['available']) if inv['available'] else 'No specific data yet'}

Want to add more data sources? Type `/tools` or share your website URL."""

        return None


_contexts: Dict[str, ContextAwareness] = {}


def get_context(conversation_id: str = "default") -> ContextAwareness:
    if conversation_id not in _contexts:
        _contexts[conversation_id] = ContextAwareness()
    return _contexts[conversation_id]
