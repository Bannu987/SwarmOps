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
    "primary":   "google/gemma-4-31b-it:free",
    "large":     "openai/gpt-oss-120b:free",
    "fast":      "openai/gpt-oss-120b:free",
    "reasoning": "google/gemma-4-31b-it:free",
    "fallback":  "nvidia/nemotron-3-super-120b-a12b:free",
}



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
        user_message: str = "",       # used for tier classification
        is_synthesis: bool = False,   # synthesis is always Tier 3
    ) -> str:
        """Call a model via OpenRouter with tier-based routing."""
        from .tier_router import classify_task, select_model, fallback_chain

        masked_key = "MISSING"
        if self.api_key:
            if len(self.api_key) <= 10:
                masked_key = "****"
            else:
                masked_key = f"{self.api_key[:6]}...{self.api_key[-4:]}"

        # Classify the task and pick the model
        tier = classify_task(user_message or prompt, agent_id, is_synthesis)
        model = select_model(tier)
        fallbacks = fallback_chain(tier)

        logger.info(
            f"[MODEL ROUTER DIAGNOSTICS] Provider: openrouter | Agent: {agent_id} | Tier: {tier} | "
            f"Selected Model: {model} | API Key status: Present ({masked_key})"
        )

        if not self.api_key:
            logger.error("[MODEL ROUTER DIAGNOSTICS] OpenRouter API key is missing or not configured!")
            return "[OpenRouter API key not configured]"

        # Rate limit buffer
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
            "models": fallbacks,
            "route": "fallback",
        }

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
                logger.info(f"[MODEL ROUTER DIAGNOSTICS] Sending request to OpenRouter (Attempt {attempt+1}/3)...")
                response = httpx.post(
                    OPENROUTER_URL,
                    json=payload,
                    headers=headers,
                    timeout=90.0,
                )
                self._last_request = time.time()

                status = response.status_code
                logger.info(f"[MODEL ROUTER DIAGNOSTICS] OpenRouter HTTP status code: {status}")

                if status == 429:
                    wait = int(response.headers.get("retry-after", 5))
                    logger.warning(f"[MODEL ROUTER DIAGNOSTICS] Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                if status != 200:
                    err_preview = response.text[:200].replace("\n", " ")
                    logger.error(f"[MODEL ROUTER DIAGNOSTICS] OpenRouter error body: {err_preview}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    return f"[Model error {status}]"

                data = response.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if text:
                    usage = data.get("usage", {})
                    actual_model = data.get("model", model).split("/")[-1]
                    raw_preview = text[:150].replace("\n", " ") + "..." if len(text) > 150 else text
                    logger.info(
                        f"[MODEL ROUTER DIAGNOSTICS] Successful response from model={actual_model} | "
                        f"Tokens: {usage.get('total_tokens', 0)} | Response Preview: {raw_preview}"
                    )
                    return text

                if attempt < 2:
                    logger.warning("[MODEL ROUTER DIAGNOSTICS] Response content was empty. Retrying...")
                    time.sleep(1)
                    continue
                return "[No response]"

            except httpx.TimeoutException:
                logger.warning(f"[MODEL ROUTER DIAGNOSTICS] Timeout occurred on attempt {attempt+1}")
                if attempt < 2:
                    continue
                return "[Request timed out]"
            except Exception as e:
                logger.error(f"[MODEL ROUTER DIAGNOSTICS] Connection failed on attempt {attempt+1} with error: {e}")
                if attempt < 2:
                    continue
                return f"[Error: {str(e)[:80]}]"

        return "[All retries failed]"



# Singleton
_router = ModelRouter()


def call_model(prompt: str, agent_id: str = "nexus", **kwargs) -> str:
    return _router.call(prompt, agent_id=agent_id, **kwargs)
