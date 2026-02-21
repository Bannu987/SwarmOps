"""
Rate Limiter - SwarmOps
In-memory rate limiter to prevent hitting provider API limits
"""

import time
from typing import Dict, List
from threading import Lock


class RateLimiter:
    """In-memory rate limiter. Tracks calls per provider per minute."""

    LIMITS = {
        "groq": 28,        # 30/min actual, leave 2 buffer
        "openrouter": 18,  # 20/min actual, leave 2 buffer
        "nvidia": 8,       # conservative, free tier
        "google": 14,      # 15/min actual (Gemini)
        "gemini": 14,      # alias for google
        "deepseek": 28,    # if using direct API
        "serper": 1,       # 2500/month = ~1.4/min sustained, be careful
        "brave": 1         # similar caution for search
    }

    def __init__(self):
        self.calls: Dict[str, List[float]] = {}  # {"groq": [(timestamp1), (timestamp2), ...]}
        self.lock = Lock()  # Thread-safe operations

    def can_call(self, provider: str) -> bool:
        """
        Check if we can make a call to the provider without exceeding rate limit.

        Args:
            provider: Provider name (e.g., "groq", "openrouter")

        Returns:
            True if under limit, False if rate-limited
        """
        with self.lock:
            provider = provider.lower()

            # Get limit for this provider
            limit = self.LIMITS.get(provider, 10)  # Default to 10/min if unknown

            # Initialize call history if needed
            if provider not in self.calls:
                self.calls[provider] = []

            # Remove calls older than 60 seconds
            current_time = time.time()
            self.calls[provider] = [
                ts for ts in self.calls[provider]
                if current_time - ts < 60
            ]

            # Check if under limit
            return len(self.calls[provider]) < limit

    def record_call(self, provider: str):
        """
        Record a successful API call.

        Args:
            provider: Provider name
        """
        with self.lock:
            provider = provider.lower()

            if provider not in self.calls:
                self.calls[provider] = []

            self.calls[provider].append(time.time())

    def get_status(self) -> dict:
        """
        Get current rate limit status for all providers.

        Returns:
            {"groq": {"used": 5, "limit": 28, "available": True, "wait_time": 0}, ...}
        """
        with self.lock:
            current_time = time.time()
            status = {}

            for provider, limit in self.LIMITS.items():
                # Clean old calls
                if provider in self.calls:
                    self.calls[provider] = [
                        ts for ts in self.calls[provider]
                        if current_time - ts < 60
                    ]
                    used = len(self.calls[provider])
                else:
                    used = 0

                # Calculate wait time if rate-limited
                wait = self.wait_time(provider) if used >= limit else 0

                status[provider] = {
                    "used": used,
                    "limit": limit,
                    "available": used < limit,
                    "wait_time_seconds": round(wait, 2)
                }

            return status

    def wait_time(self, provider: str) -> float:
        """
        Calculate how long to wait until a slot opens up.

        Args:
            provider: Provider name

        Returns:
            Seconds to wait (0 if not rate-limited)
        """
        with self.lock:
            provider = provider.lower()
            limit = self.LIMITS.get(provider, 10)

            if provider not in self.calls:
                return 0.0

            current_time = time.time()

            # Clean old calls
            self.calls[provider] = [
                ts for ts in self.calls[provider]
                if current_time - ts < 60
            ]

            # If not rate-limited, no wait
            if len(self.calls[provider]) < limit:
                return 0.0

            # Find oldest call that's still within the 60-second window
            oldest_call = min(self.calls[provider])

            # Time until oldest call expires (exits the 60-second window)
            wait = 60 - (current_time - oldest_call)

            return max(0.0, wait)

    def reset(self):
        """Reset all rate limit tracking. Useful for testing."""
        with self.lock:
            self.calls.clear()


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance (singleton)."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING RATE LIMITER")
    print("=" * 60)

    rl = RateLimiter()

    # Test 1: Check status
    print("\n--- Initial Status ---")
    status = rl.get_status()
    for provider, info in status.items():
        print(f"{provider}: {info['used']}/{info['limit']} (available: {info['available']})")

    # Test 2: Simulate calls
    print("\n--- Simulating 30 Groq calls ---")
    for i in range(30):
        if rl.can_call("groq"):
            rl.record_call("groq")
            print(f"  Call {i+1}: OK")
        else:
            wait = rl.wait_time("groq")
            print(f"  Call {i+1}: RATE LIMITED (wait {wait:.1f}s)")
            break

    # Test 3: Check status after calls
    print("\n--- Status After Calls ---")
    status = rl.get_status()
    for provider in ["groq", "openrouter", "nvidia", "gemini"]:
        info = status[provider]
        print(f"{provider}: {info['used']}/{info['limit']} (available: {info['available']}, wait: {info['wait_time_seconds']}s)")

    print("\n" + "=" * 60)
