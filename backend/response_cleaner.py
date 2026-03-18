import re


class ResponseCleaner:
    """Post-process LLM responses to enforce rules the model ignores.

    All patterns are intentionally broad to catch markdown variations,
    asterisk wrapping, and colon suffixes the LLM adds.
    """

    # Catches ## **Strategic Plan**: and # Top Priority Actions etc.
    BANNED_HEADERS = [
        r'^#+\s*\**\s*(Targeted|Strategic|Comprehensive|Complete|Full|Overall)[\w\s]+(Strategy|Plan|Analysis|Approach|Initiative|Campaign)\**\s*:?',
        r'^#+\s*\**\s*(Top Priority Actions|Priority Actions|Key Actions|Action Items)\**\s*:?',
        r'^#+\s*\**\s*(Expected Impact|Estimated Impact|Projected Impact|Potential Impact)\**\s*:?',
        r'^#+\s*\**\s*(Critical Issues|Key Issues|Main Issues|Core Issues)\**\s*:?',
        r'^#+\s*\**\s*(Heuristic Evaluation|Assessment Matrix|Audit Framework)\**\s*:?',
        r'^#+\s*\**\s*(What We Found|What This Means|Your Next Move)\**\s*:?',
        r'^#+\s*\**\s*(Action Architecture|Strategic Roadmap|Implementation Framework|Implementation Plan)\**\s*:?',
        r'^#+\s*\**\s*(Traffic Boost|Lead Generation|Conversion|Growth Acceleration)\s+(Strategy|Plan|Initiative|Approach|Acceleration)\**\s*:?',
        r'^\*\*\s*(Targeted|Strategic|Comprehensive|Top Priority Actions|Expected Impact|Critical Issues|Traffic Boost|Lead Generation|Conversion|Growth)[\w\s]*\*\*\s*:?',
    ]

    # Therapy-speak and empathy fillers
    THERAPY_PATTERNS = [
        r"I can sense the weight of[^.!?]*[.!?]",
        r"I can sense your[^.!?]*[.!?]",
        r"It'?s completely normal to feel[^.!?]*[.!?]",
        r"many (?:founders|entrepreneurs|business owners) have been in your shoes[^.!?]*[.!?]",
        r"I want you to know that I'?m here to[^.!?]*[.!?]",
        r"I'?m here to offer a supportive ear[^.!?]*[.!?]",
        r"Taking a step back to reassess[^.!?]*[.!?]",
        r"I understand how frustrating[^.!?]*[.!?]",
        r"I understand that[^.!?]*[.!?]",
        r"I hear you[^.!?]*[.!?]",
        r"Let'?s work through this together[^.!?]*[.!?]",
        r"That'?s a great question[.!?]?",
        r"Great question[.!?]?",
        r"Absolutely[,!]\s*",
        r"Of course[,!]\s*(?=I|we|let|here)",
    ]

    # we/our/us presumptive pronouns — replace with you/your
    WE_OUR_PATTERNS = [
        (r'\bour\s+(website|business|brand|company|product|service|audience|strategy|campaign|team|goal|content|marketing|SEO|PPC|CRM|social|email|clients|customers|users|platform)', r'your \1'),
        (r'\bwe\s+(need|should|can|must|will|have|are|recommend|want|believe|think)', r'you \1'),
        (r'\bour\s+(SEO|PPC|CRM|content|social|email|marketing|analytics|funnel)', r'your \1'),
        (r'At SwarmOps,?\s*we', 'For your business, you'),
        (r'\bdifferentiate ourselves\b', 'differentiate your brand'),
        (r"\bour website'?s?\b", "your website's"),
        (r"\bwe'?ve\b", "you've"),
        (r"\bwe'?re\b", "you're"),
        (r'\bus\b(?=\s+(?:to|from|with|in|on|at|by|for))', 'you'),
    ]

    def clean(self, response_text: str, brand_name: str = None) -> str:
        if not response_text:
            return response_text

        text = response_text

        # 1. Remove therapy-speak / empathy fillers
        for pattern in self.THERAPY_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # 2. Remove banned section headers (line by line)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            skip = False
            stripped = line.strip()
            for pattern in self.BANNED_HEADERS:
                if re.match(pattern, stripped, re.IGNORECASE):
                    skip = True
                    break
            if not skip:
                cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)

        # 3. Fix we/our → you/your
        for pattern, replacement in self.WE_OUR_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # 4. Remove "Expected Impact:" / "Estimated Impact:" blocks
        text = re.sub(
            r'\*?\*?(?:Expected|Estimated|Projected|Potential)\s+Impact\*?\*?:.*?(?=\n\n|\n[A-Z#\*]|\Z)',
            '', text, flags=re.IGNORECASE | re.DOTALL
        )

        # 5. Remove empty bullet points left behind after excisions
        text = re.sub(r'^\s*[-*•]\s*$', '', text, flags=re.MULTILINE)

        # 6. Remove dangling colons at end of line (left by header removal)
        text = re.sub(r'^\s*:\s*$', '', text, flags=re.MULTILINE)

        # 7. Collapse multiple blank lines to max 2
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 8. Strip leading junk chars
        text = text.lstrip('\n ,;:')
        text = text.strip()

        return text

    def enforce_length(self, text: str, query_type: str = "normal") -> str:
        words = text.split()
        limits = {
            "short": 100,
            "normal": 250,
            "detailed": 500,
            "audit": 2000,
        }
        max_words = limits.get(query_type, 250)
        if len(words) > max_words:
            truncated = ' '.join(words[:max_words])
            last_period = truncated.rfind('.')
            if last_period > len(truncated) * 0.5:
                truncated = truncated[:last_period + 1]
            return truncated
        return text

    def classify_query_type(self, message: str) -> str:
        msg = message.lower().strip()
        if msg in ['hi', 'hello', 'hey', 'hii', 'sup', 'yo', 'hiya']:
            return "short"
        if any(msg.startswith(w) for w in ['what is ', 'what are ', 'explain ', 'define ']):
            return "short"
        if any(w in msg for w in [
            'detailed', 'comprehensive', 'full plan', '3 month', 'three month',
            'deep analysis', 'complete strategy', 'budget plan',
            'organic and paid', 'organic vs paid', 'step by step', 'step-by-step',
        ]):
            return "detailed"
        if any(w in msg for w in ['audit', 'grade my', 'analyze my site', 'website analysis']):
            return "audit"
        return "normal"


_cleaner_instance = None


def get_response_cleaner() -> ResponseCleaner:
    global _cleaner_instance
    if _cleaner_instance is None:
        _cleaner_instance = ResponseCleaner()
    return _cleaner_instance
