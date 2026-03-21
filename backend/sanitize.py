"""
Response sanitizer — SECURITY REQUIREMENT.
Strips leaked internal context from ALL responses before returning to user.
Runs as the absolute last step in every response path.
"""
import re

# Internal markers that must never reach the user
INTERNAL_MARKERS = [
    "=== SWARMOPS DATA CONTEXT ===",
    "=== END CONTEXT ===",
    "USER PREFERENCES:",
    "BRAND CONTEXT FOR",
    "CONVERSATION HISTORY:",
    "Previously discussed:",
    "CONNECTED INTEGRATIONS:",
    "DATA GAPS (ask user",
    "INSTRUCTION: Write all content",
    "Still needs improvement (score:",
    "RETRIEVED KNOWLEDGE (from crawled",
    "AGENT_CONVERSATIONAL_RULES",
    "RULES (override everything)",
    "RULES (these override",
    "Answer the user's question immediately",
    "=== YOUR 5-STEP THINKING",
    "USER REQUEST:",
    "Website (already provided):",
    "Website URL unknown",
    "No website analytics",
    "No ad performance data",
    "No live SEO data",
    "BUSINESS PROFILE: Not yet configured",
    "BRAND CONTEXT:",
    "Recent history:",
    "RETRIEVED KNOWLEDGE",
]

# Scoring/revision feedback patterns
SCORING_PATTERNS = [
    r"Still needs improvement \(score:\s*\d+%\)[^\n]*",
    r"Score:\s*\d+/\d+[^\n]*",
    r"Be much more specific[^\n]*",
    r"Original task:[^\n]*",
]


def sanitize_response(text: str) -> str:
    """Remove any leaked internal context from LLM responses.

    Must run as the LAST step before returning any response to the user.
    """
    if not text or not isinstance(text, str):
        return text or ""

    original_length = len(text)

    # 1. Check for internal markers — truncate at first occurrence
    for marker in INTERNAL_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            before = text[:idx].rstrip()
            if len(before) < 20:
                # Marker near start with no meaningful content — entire response is leaked context
                text = ""
                break
            else:
                # Keep everything before the marker
                text = before

    # 2. Remove scoring/revision feedback lines
    for pattern in SCORING_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # 3. Remove raw JSON routing payloads
    text = re.sub(
        r'\{["\'](?:topic|agent|message|query)["\']:\s*["\'].*?\}',
        "",
        text,
    )

    # 4. Clean up artifacts
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    # 5. If >80% was stripped, the whole thing was internal context
    if not text or (original_length > 100 and len(text) < original_length * 0.2):
        return (
            "I need a bit more context to help with that. "
            "Could you rephrase your question or be more specific?"
        )

    return text
