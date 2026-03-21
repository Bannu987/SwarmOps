"""
AEO Formatter — Answer Engine Optimization.
Formats responses to maximize visibility in AI-generated search answers,
Google featured snippets, and voice search results.
"""
import json
import re
from typing import List, Dict, Optional


class AEOFormatter:
    """Format marketing content for maximum answer engine visibility."""

    # Citable statistics to inject when no real data is available
    _CITABLE_STATS = {
        "email": [
            "Email marketing returns $36 for every $1 spent (Litmus, 2023)",
            "Average email open rate across industries: 21.5% (Mailchimp)",
            "Welcome emails generate 4× higher open rates than standard campaigns",
        ],
        "seo": [
            "75% of users never scroll past the first page of search results (HubSpot)",
            "Long-tail keywords account for 70% of all search traffic (Moz)",
            "Pages with video are 53× more likely to rank on page 1 (Forrester)",
        ],
        "content": [
            "Companies that blog get 55% more website visitors (HubSpot)",
            "Long-form content (2,000+ words) earns 3× more backlinks than short articles",
            "Interactive content generates 2× more conversions than passive content",
        ],
        "social": [
            "Social media posts with images get 150% more engagement (Buffer)",
            "LinkedIn generates 80% of B2B leads from social media (LinkedIn)",
            "Video posts on social get 48% more views than static images",
        ],
        "ppc": [
            "Google Ads average conversion rate: 3.75% for search (WordStream)",
            "PPC visitors are 50% more likely to make a purchase than organic visitors",
            "Remarketing ads can increase conversion rates by up to 150%",
        ],
        "conversion": [
            "Average website conversion rate across industries: 2.35% (WordStream)",
            "A/B testing landing pages can increase conversions by 300%",
            "Reducing form fields from 11 to 4 increases conversions by 120% (HubSpot)",
        ],
        "general": [
            "Businesses with documented marketing strategies are 313% more likely to succeed",
            "Companies using data-driven marketing are 6× more likely to be profitable year-over-year",
            "Integrated marketing campaigns drive 3× higher effectiveness than single-channel",
        ],
    }

    def format_inverted_pyramid(self, content: str, topic: str = "") -> str:
        """
        Restructure content using inverted pyramid:
        1. Direct answer (most important) first
        2. Supporting context
        3. Details and elaboration last

        This matches how AI answer engines extract information.
        """
        if not content or len(content.strip()) < 50:
            return content

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            return content

        # Heuristic: find the paragraph most likely to be a direct answer
        # (shorter, contains action verbs or key conclusions)
        answer_signals = ["recommend", "should", "best", "key", "most important",
                          "start with", "focus on", "the answer", "in short", "bottom line"]

        best_idx = 0
        best_score = -1
        for i, para in enumerate(paragraphs):
            score = 0
            para_lower = para.lower()
            # Short paragraphs are more likely to be summary statements
            if len(para.split()) < 60:
                score += 2
            for signal in answer_signals:
                if signal in para_lower:
                    score += 1
            # First paragraph often already is the answer
            if i == 0:
                score += 1
            if score > best_score:
                best_score = score
                best_idx = i

        # Move best paragraph to front
        reordered = [paragraphs[best_idx]]
        reordered += [p for i, p in enumerate(paragraphs) if i != best_idx]

        return "\n\n".join(reordered)

    def generate_faq_schema(self, questions_and_answers: List[Dict]) -> str:
        """
        Generate FAQ JSON-LD schema markup for search engines.

        Args:
            questions_and_answers: [{"question": "...", "answer": "..."}]

        Returns:
            JSON-LD string ready to embed in HTML <script> tag.
        """
        faq_items = []
        for qa in questions_and_answers:
            faq_items.append({
                "@type": "Question",
                "name": qa.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa.get("answer", "")
                }
            })

        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_items
        }
        return json.dumps(schema, indent=2)

    def generate_article_schema(self, title: str, description: str,
                                author: str = "SwarmOps AI",
                                brand_name: str = "") -> str:
        """Generate Article JSON-LD schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "author": {
                "@type": "Person",
                "name": author
            },
            "publisher": {
                "@type": "Organization",
                "name": brand_name or "SwarmOps"
            }
        }
        return json.dumps(schema, indent=2)

    def generate_howto_schema(self, title: str, steps: List[str]) -> str:
        """Generate HowTo JSON-LD schema for step-by-step content."""
        how_to_steps = []
        for i, step in enumerate(steps, 1):
            how_to_steps.append({
                "@type": "HowToStep",
                "position": i,
                "text": step
            })

        schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": title,
            "step": how_to_steps
        }
        return json.dumps(schema, indent=2)

    def inject_citable_stats(self, content: str, topic_hint: str = "") -> str:
        """
        Inject 1-2 citable statistics into content where relevant.
        Only injects if content doesn't already have citations.
        """
        # Don't inject if content already has citations
        if re.search(r'\(\w+,?\s*\d{4}\)', content):
            return content

        # Detect topic from hint and content
        combined = (topic_hint + " " + content).lower()
        stats_to_inject = []

        for category, stats in self._CITABLE_STATS.items():
            if category in combined or any(kw in combined for kw in [category]):
                stats_to_inject.extend(stats[:1])  # Take 1 from each matching category

        if not stats_to_inject:
            stats_to_inject = self._CITABLE_STATS["general"][:1]

        # Find a good insertion point — after a recommendation sentence
        stat_block = "\n\n**Benchmark data:** " + " ".join(stats_to_inject[:2])
        return content + stat_block

    def create_entity_map(self, content: str) -> Dict:
        """
        Extract key entities from content for knowledge graph alignment.
        Identifies: brands, channels, metrics, tactics, timeframes.
        """
        content_lower = content.lower()

        channels = []
        channel_patterns = ["google ads", "facebook ads", "meta ads", "linkedin ads",
                            "instagram", "tiktok", "youtube", "email", "seo", "ppc",
                            "organic search", "paid search", "social media"]
        for ch in channel_patterns:
            if ch in content_lower:
                channels.append(ch.title())

        metrics = []
        metric_patterns = {
            "CTR": r'\bctr\b', "CVR": r'\bcvr\b|\bconversion rate\b',
            "ROAS": r'\broas\b', "CPC": r'\bcpc\b', "CAC": r'\bcac\b',
            "LTV": r'\bltv\b|\bclv\b', "MQL": r'\bmql\b', "SQL": r'\bsql\b',
        }
        for metric, pattern in metric_patterns.items():
            if re.search(pattern, content_lower):
                metrics.append(metric)

        tactics = []
        tactic_patterns = ["a/b test", "retargeting", "remarketing", "lead magnet",
                          "landing page", "email sequence", "content calendar",
                          "keyword research", "backlink", "cta", "upsell", "cross-sell"]
        for tac in tactic_patterns:
            if tac in content_lower:
                tactics.append(tac.replace("/", "or").title())

        timeframes = []
        tf_patterns = r'\b(\d+\s*(?:day|week|month|quarter|year)s?)\b'
        found_tfs = re.findall(tf_patterns, content_lower)
        timeframes = list(set(found_tfs))[:5]

        return {
            "channels": list(set(channels)),
            "metrics": list(set(metrics)),
            "tactics": list(set(tactics)),
            "timeframes": timeframes,
        }

    def format_for_snippet(self, content: str, max_chars: int = 300) -> str:
        """
        Extract or create a featured snippet-optimized paragraph.
        Google prefers 40–60 word direct answers.
        """
        # Look for the most answer-like paragraph
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        paragraphs = [p for p in paragraphs if not p.startswith("#") and not p.startswith("-")]

        for para in paragraphs:
            word_count = len(para.split())
            if 25 <= word_count <= 80 and not para.startswith("*"):
                return para[:max_chars]

        # Fallback: take first 300 chars
        return content[:max_chars].rstrip()


# Module-level singleton
_formatter = None

def get_aeo_formatter() -> AEOFormatter:
    global _formatter
    if _formatter is None:
        _formatter = AEOFormatter()
    return _formatter
