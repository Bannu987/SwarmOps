"""
OpenRouter unified model gateway.
Single API for 200+ models. Free tier for background agents.
"""
import os
import time
import logging
import httpx
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model assignments
NEXUS_MODEL = "anthropic/claude-sonnet-4-20250514"

FREE_MODELS = {
    "primary":   "google/gemma-3-27b-it:free",
    "large":     "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
    "fast":      "google/gemma-3-12b-it:free",
    "reasoning": "deepseek/deepseek-r1:free",
    "fallback":  "meta-llama/llama-4-maverick:free",
}

AGENT_MODEL = {
    "nexus":     NEXUS_MODEL,
    "seo":       FREE_MODELS["primary"],
    "content":   FREE_MODELS["primary"],
    "analytics": FREE_MODELS["fast"],
    "cro":       FREE_MODELS["primary"],
    "aeo":       FREE_MODELS["primary"],
}

FALLBACK_CHAIN = [
    FREE_MODELS["primary"],
    FREE_MODELS["fast"],
    FREE_MODELS["fallback"],
]


class ModelRouter:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self._last_request = 0

    def call(
        self,
        prompt: str,
        agent_id: str = "nexus",
        system: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        """Call a model via OpenRouter."""
        if not self.api_key:
            return "[OpenRouter API key not configured]"

        model = AGENT_MODEL.get(agent_id, FREE_MODELS["primary"])

        # Simple rate limit (18 RPM buffer from 20 RPM limit)
        elapsed = time.time() - self._last_request
        if elapsed < 3.5:
            time.sleep(3.5 - elapsed)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add fallbacks for free models (not Nexus)
        if agent_id != "nexus":
            payload["models"] = [model] + FALLBACK_CHAIN
            payload["route"] = "fallback"

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://swarmops.ai",
            "X-Title": "SwarmOps",
        }

        for attempt in range(3):
            try:
                response = httpx.post(
                    OPENROUTER_URL,
                    json=payload,
                    headers=headers,
                    timeout=90.0,
                )
                self._last_request = time.time()

                if response.status_code == 429:
                    wait = int(response.headers.get("retry-after", 5))
                    logger.warning(f"Rate limited. Wait {wait}s")
                    time.sleep(wait)
                    continue

                if response.status_code != 200:
                    logger.error(f"OpenRouter {response.status_code}: {response.text[:200]}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    return f"[Model error {response.status_code}]"

                data = response.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if text:
                    usage = data.get("usage", {})
                    logger.info(f"[{agent_id}] {model.split('/')[-1]} | tokens={usage.get('total_tokens', 0)}")
                    return text

                if attempt < 2:
                    time.sleep(1)
                    continue
                return "[No response]"

            except httpx.TimeoutException:
                logger.warning(f"Timeout attempt {attempt+1}")
                if attempt < 2:
                    continue
                return "[Request timed out]"
            except Exception as e:
                logger.error(f"Model call failed: {e}")
                if attempt < 2:
                    continue
                return f"[Error: {str(e)[:80]}]"

        return "[All retries failed]"


# Singleton
_router = ModelRouter()


def call_model(prompt: str, agent_id: str = "nexus", **kwargs) -> str:
    return _router.call(prompt, agent_id, **kwargs)
