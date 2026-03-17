import re


class ResponseCleaner:
    """Post-process LLM responses to enforce rules the model ignores."""

    BANNED_HEADERS = [
        r'^#+\s*(Targeted|Strategic|Comprehensive|Complete|Full|Overall)\s+\w+\s*(Strategy|Plan|Analysis|Approach|Initiative|Campaign)',
        r'^#+\s*(Top Priority Actions|Priority Actions|Key Actions)',
        r'^#+\s*(Expected Impact|Estimated Impact|Projected Impact)',
        r'^#+\s*(Critical Issues|Key Issues|Main Issues)',
        r'^#+\s*(Heuristic Evaluation|Assessment Matrix)',
        r'^#+\s*(What We Found|What This Means|Your Next Move)',
        r'^#+\s*(Action Architecture|Strategic Roadmap|Implementation)',
        r'^#+\s*(Traffic Boost|Lead Generation|Conversion)\s+(Strategy|Acceleration|Initiative|Plan)',
    ]

    THERAPY_PATTERNS = [
        r"I can sense the weight of[^.]*\.",
        r"I can sense your[^.]*\.",
        r"It'?s completely normal to feel[^.]*\.",
        r"many (?:founders|entrepreneurs|business owners) have been in your shoes[^.]*\.",
        r"I want you to know that I'?m here to[^.]*\.",
        r"I'?m here to offer a supportive ear[^.]*\.",
        r"Taking a step back to reassess[^.]*\.",
    ]

    WE_OUR_PATTERNS = [
        (r'\bour\s+(website|business|brand|company|product|service|audience|strategy|campaign|team|goal)', r'your \1'),
        (r'\bwe\s+(need|should|can|must|will|have|are|recommend)', r'you \1'),
        (r'\bour\s+(SEO|PPC|CRM|content|social|email|marketing)', r'your \1'),
        (r'At SwarmOps,\s*we', 'For your business, you'),
    ]

    def clean(self, response_text, brand_name=None):
        if not response_text:
            return response_text

        text = response_text

        # 1. Remove therapy-speak
        for pattern in self.THERAPY_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # 2. Remove banned headers
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            skip = False
            for pattern in self.BANNED_HEADERS:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    skip = True
                    break
            if not skip:
                cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)

        # 3. Fix we/our -> you/your
        for pattern, replacement in self.WE_OUR_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # 4. Remove "Expected Impact:" blocks with fake percentages
        text = re.sub(
            r'(?:Expected|Estimated|Projected)\s+Impact:.*?(?=\n\n|\n[A-Z#]|\Z)',
            '', text, flags=re.IGNORECASE | re.DOTALL
        )

        # 5. Clean extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        if text and text[0] in ['\n', ' ', ',']:
            text = text.lstrip('\n ,')

        return text

    def enforce_length(self, text, query_type="normal"):
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

    def classify_query_type(self, message):
        msg = message.lower()
        if msg in ['hi', 'hello', 'hey', 'hii', 'sup', 'yo']:
            return "short"
        if any(w in msg for w in ['what is', 'what are', 'explain', 'define']):
            return "short"
        if any(w in msg for w in ['detailed', 'comprehensive', 'full plan',
                                   '3 month', 'three month', 'deep analysis',
                                   'complete strategy', 'budget plan', 'organic and paid',
                                   'organic vs paid']):
            return "detailed"
        if any(w in msg for w in ['audit', 'grade my', 'analyze my site']):
            return "audit"
        return "normal"


_cleaner_instance = None


def get_response_cleaner():
    global _cleaner_instance
    if _cleaner_instance is None:
        _cleaner_instance = ResponseCleaner()
    return _cleaner_instance
