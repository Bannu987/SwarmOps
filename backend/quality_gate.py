"""
Quality Gate — generator + critic loop for agent responses.
Validates LLM outputs before they reach the user.
Max 1 retry to avoid latency blowup.
"""
import re
import logging
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Quality criteria — each returns (passed: bool, reason: str)
# -----------------------------------------------------------------------

def _check_length(text: str, min_words: int = 30) -> tuple[bool, str]:
    word_count = len(text.split())
    if word_count < min_words:
        return False, f"Too short ({word_count} words, minimum {min_words})"
    return True, ""


def _check_no_placeholders(text: str) -> tuple[bool, str]:
    """Reject responses with obvious template placeholders."""
    placeholder_patterns = [
        r'\[YOUR\s+\w+\]', r'\{YOUR\s+\w+\}', r'<YOUR\s+\w+>',
        r'\[COMPANY NAME\]', r'\[BRAND NAME\]', r'\[INSERT\s+\w+\]',
        r'\[ADD\s+\w+\]', r'\[PLACEHOLDER\]', r'Lorem ipsum',
        r'your_company_name', r'example\.com',
    ]
    for pattern in placeholder_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Contains template placeholder: {pattern}"
    return True, ""


def _check_no_hallucinated_urls(text: str) -> tuple[bool, str]:
    """Flag responses that contain obviously fake/hallucinated URLs."""
    # Only flag if URL contains placeholder-style text
    fake_url_patterns = [
        r'https?://(?:yoursite|example|yourdomain|yourcompany|yourbrand)\.',
        r'https?://\[.*?\]',
    ]
    for pattern in fake_url_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Contains hallucinated URL"
    return True, ""


def _check_actionable(text: str) -> tuple[bool, str]:
    """Verify response has at least one actionable recommendation."""
    action_signals = [
        "recommend", "should", "focus on", "start with", "implement",
        "create", "build", "optimize", "use", "add", "remove", "test",
        "increase", "decrease", "target", "try", "consider",
        "step 1", "step 2", "first,", "next,", "finally,",
    ]
    text_lower = text.lower()
    for signal in action_signals:
        if signal in text_lower:
            return True, ""
    return False, "Response lacks actionable recommendations"


def _check_no_leaked_context(text: str) -> tuple[bool, str]:
    """Ensure internal system context didn't leak into response."""
    leaked_patterns = [
        r'SWARMOPS DATA CONTEXT', r'USER PREFERENCES:', r'BRAND CONTEXT FOR',
        r'SYSTEM PROMPT:', r'<system>', r'\[INTERNAL\]',
        r'Still needs improvement \(score:',
    ]
    for pattern in leaked_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Internal context leaked: {pattern}"
    return True, ""


# -----------------------------------------------------------------------
# QualityGate class
# -----------------------------------------------------------------------

class QualityGate:
    """Validate agent responses. Run generator → check → retry once if needed."""

    # Ordered list of checks (name, fn, is_blocking)
    CHECKS = [
        ("no_leaked_context", _check_no_leaked_context, True),
        ("no_placeholders", _check_no_placeholders, True),
        ("no_hallucinated_urls", _check_no_hallucinated_urls, True),
        ("length", _check_length, False),
        ("actionable", _check_actionable, False),
    ]

    def check(self, text: str, min_words: int = 30) -> Dict:
        """
        Run all quality checks on a response.

        Returns:
            {
                "passed": bool,
                "blocking_failures": [str],
                "warnings": [str],
                "score": float  # 0.0 - 1.0
            }
        """
        blocking_failures = []
        warnings = []
        total_checks = len(self.CHECKS)
        passed_checks = 0

        for name, fn, is_blocking in self.CHECKS:
            try:
                if name == "length":
                    ok, reason = fn(text, min_words)
                else:
                    ok, reason = fn(text)

                if ok:
                    passed_checks += 1
                elif is_blocking:
                    blocking_failures.append(reason)
                else:
                    warnings.append(reason)
            except Exception as e:
                logger.warning(f"QualityGate check '{name}' error: {e}")

        score = passed_checks / total_checks
        return {
            "passed": len(blocking_failures) == 0,
            "blocking_failures": blocking_failures,
            "warnings": warnings,
            "score": round(score, 2),
        }

    def gate_with_retry(
        self,
        generator_fn: Callable[[], str],
        agent_id: str = "unknown",
        min_words: int = 30,
        retry_instruction: Optional[str] = None,
    ) -> Dict:
        """
        Run generator, check quality, retry once if blocking failures found.

        Args:
            generator_fn: callable that returns a response string (called 1-2 times)
            agent_id: for logging
            min_words: minimum word count to pass length check
            retry_instruction: extra instruction to append on retry (optional)

        Returns:
            {
                "response": str,
                "quality": dict (from check()),
                "attempts": int,
                "passed": bool,
            }
        """
        # Attempt 1
        try:
            response = generator_fn()
        except Exception as e:
            logger.error(f"QualityGate generator failed ({agent_id}): {e}")
            return {
                "response": "",
                "quality": {"passed": False, "blocking_failures": [str(e)], "warnings": [], "score": 0.0},
                "attempts": 1,
                "passed": False,
            }

        quality = self.check(response, min_words)

        if quality["passed"]:
            return {
                "response": response,
                "quality": quality,
                "attempts": 1,
                "passed": True,
            }

        # Attempt 2 — retry
        logger.info(
            f"QualityGate: {agent_id} failed on attempt 1. "
            f"Failures: {quality['blocking_failures']}. Retrying..."
        )

        try:
            response2 = generator_fn()
        except Exception as e:
            logger.error(f"QualityGate retry failed ({agent_id}): {e}")
            # Return attempt 1 result even if it failed quality checks
            return {
                "response": response,
                "quality": quality,
                "attempts": 2,
                "passed": False,
            }

        quality2 = self.check(response2, min_words)

        # Pick the better response (by score)
        if quality2["score"] >= quality["score"]:
            final_response = response2
            final_quality = quality2
        else:
            final_response = response
            final_quality = quality

        return {
            "response": final_response,
            "quality": final_quality,
            "attempts": 2,
            "passed": final_quality["passed"],
        }


# Module-level singleton
_gate = None

def get_quality_gate() -> QualityGate:
    global _gate
    if _gate is None:
        _gate = QualityGate()
    return _gate
