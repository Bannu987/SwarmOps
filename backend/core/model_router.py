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
    "primary":   "google/gemma-2-9b-it",
    "large":     "meta-llama/llama-3-8b-instruct",
    "fast":      "meta-llama/llama-3-8b-instruct",
    "reasoning": "google/gemma-2-9b-it",
    "fallback":  "qwen/qwen-2-7b-instruct",
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
        selected_model = select_model(tier)
        fallbacks = fallback_chain(tier)

        # Build sequence of models to attempt defensively if 404 occurs
        models_to_try = [selected_model]
        for f in fallbacks:
            if f not in models_to_try:
                models_to_try.append(f)

        logger.info(
            f"[MODEL ROUTER DIAGNOSTICS] Provider: openrouter | Agent: {agent_id} | Tier: {tier} | "
            f"Selected Model: {selected_model} | Fallback Chain: {models_to_try} | API Key status: Present ({masked_key})"
        )

        if not self.api_key:
            logger.error("[MODEL ROUTER DIAGNOSTICS] OpenRouter API key is missing or not configured!")
            return "[OpenRouter API key not configured]"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://swarmops.ai",
            "X-Title": "SwarmOps",
        }

        current_model_index = 0
        attempt = 0
        max_attempts = 4  # Allow up to 4 total attempts to try different models in the chain

        while attempt < max_attempts and current_model_index < len(models_to_try):
            active_model = models_to_try[current_model_index]
            remaining_fallbacks = models_to_try[current_model_index + 1:]

            # Rate limit buffer (3.5s spacing between OpenRouter calls)
            elapsed = time.time() - self._last_request
            if elapsed < 3.5:
                time.sleep(3.5 - elapsed)

            payload = {
                "model": active_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if remaining_fallbacks:
                payload["models"] = remaining_fallbacks
                payload["route"] = "fallback"

            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            try:
                logger.info(
                    f"[MODEL ROUTER DIAGNOSTICS] Sending request to OpenRouter (Attempt {attempt+1}/{max_attempts}) | "
                    f"Active Model: {active_model} | Fallback Models Offered: {remaining_fallbacks}"
                )
                response = httpx.post(
                    OPENROUTER_URL,
                    json=payload,
                    headers=headers,
                    timeout=90.0,
                )
                self._last_request = time.time()

                status = response.status_code
                logger.info(f"[MODEL ROUTER DIAGNOSTICS] OpenRouter HTTP status code: {status} for model: {active_model}")

                if status == 429:
                    wait = int(response.headers.get("retry-after", 5))
                    logger.warning(f"[MODEL ROUTER DIAGNOSTICS] Rate limited. Waiting {wait}s before retrying same model...")
                    time.sleep(wait)
                    attempt += 1
                    continue

                if status != 200:
                    err_preview = response.text[:200].replace("\n", " ")
                    logger.error(
                        f"[MODEL ROUTER DIAGNOSTICS] OpenRouter returned error {status} for model: {active_model} | "
                        f"Error preview: {err_preview}"
                    )

                    # Check for 404 model not found or unavailable messages
                    is_unavailable = (
                        status == 404 or 
                        "not found" in response.text.lower() or 
                        "unavailable" in response.text.lower() or
                        "slug" in response.text.lower()
                    )
                    
                    if is_unavailable:
                        current_model_index += 1
                        if current_model_index < len(models_to_try):
                            next_model = models_to_try[current_model_index]
                            logger.warning(
                                f"[MODEL ROUTER DIAGNOSTICS] Model '{active_model}' is unavailable/404. "
                                f"Bypassing retries and falling back directly to: '{next_model}'"
                            )
                            attempt += 1
                            continue
                        else:
                            logger.error("[MODEL ROUTER DIAGNOSTICS] Model unavailable and no further fallbacks exist.")
                            return f"[Model unavailable {status}]"

                    # For other errors (e.g. 500, 502), do standard exponential backoff retry
                    if attempt < max_attempts - 1:
                        sleep_time = 2 ** attempt
                        logger.info(f"[MODEL ROUTER DIAGNOSTICS] Temporary server error. Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                        attempt += 1
                        continue
                    return f"[Model error {status}]"

                data = response.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if text:
                    usage = data.get("usage", {})
                    actual_model = data.get("model", active_model).split("/")[-1]
                    raw_preview = text[:150].replace("\n", " ") + "..." if len(text) > 150 else text
                    logger.info(
                        f"[MODEL ROUTER DIAGNOSTICS] Successful response! Final Model: {actual_model} "
                        f"(Started as: {selected_model}) | Tokens: {usage.get('total_tokens', 0)} | "
                        f"Response Preview: {raw_preview}"
                    )
                    return text

                if attempt < max_attempts - 1:
                    logger.warning("[MODEL ROUTER DIAGNOSTICS] Response content was empty. Retrying...")
                    time.sleep(1)
                    attempt += 1
                    continue
                return "[No response]"

            except httpx.TimeoutException:
                logger.warning(f"[MODEL ROUTER DIAGNOSTICS] Timeout occurred on active model {active_model} (Attempt {attempt+1})")
                if attempt < max_attempts - 1:
                    attempt += 1
                    continue
                return "[Request timed out]"
            except Exception as e:
                logger.error(
                    f"[MODEL ROUTER DIAGNOSTICS] Connection failed on active model {active_model} "
                    f"(Attempt {attempt+1}) with error: {e}"
                )
                if attempt < max_attempts - 1:
                    attempt += 1
                    continue
                return f"[Error: {str(e)[:80]}]"

        return "[All retries and model fallbacks failed]"



# Singleton
_router = ModelRouter()


def call_model(prompt: str, agent_id: str = "nexus", **kwargs) -> str:
    return _router.call(prompt, agent_id=agent_id, **kwargs)
