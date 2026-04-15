"""
SwarmOps Model Router v2 — OpenRouter Unified Gateway
=====================================================
One API key replaces 5 separate integrations.

Tier mapping (backward-compatible with old call_model_sync callers):
  tier 1 → fast free model   (sub-agents, quick tasks)
  tier 2 → primary free model (main agent work)
  tier 3 → premium free model (complex reasoning)
  tier 4 → tier 3 + web search augmentation

Architecture:
  Background agents  → free models ($0.00)
  Nexus / synthesis  → frontier paid model (high quality)
"""
import os
import time
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY  = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ─────────────────────────────────────────────────────────────
# MODEL CATALOGUE
# ─────────────────────────────────────────────────────────────

# Frontier model for user-facing Nexus responses
PAID_MODEL = "anthropic/claude-sonnet-4-5"

# Best free models on OpenRouter (as of mid-2026)
_FREE = {
    "fast":         "google/gemma-3-12b-it:free",
    "primary":      "google/gemma-3-27b-it:free",
    "large":        "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
    "reasoning":    "deepseek/deepseek-r1:free",
    "fallback":     "meta-llama/llama-4-maverick:free",
}

# tier → ordered list of models to try
TIER_MODELS = {
    1: [_FREE["fast"],     _FREE["primary"],   _FREE["fallback"]],
    2: [_FREE["primary"],  _FREE["fast"],      _FREE["fallback"]],
    3: [_FREE["large"],    _FREE["reasoning"], _FREE["primary"], _FREE["fallback"]],
    4: [_FREE["large"],    _FREE["reasoning"], _FREE["primary"], _FREE["fallback"]],  # + web search
}

# Per-agent model (used when callers pass agent_id kwarg)
AGENT_TIER = {
    "nexus":        3,   # uses PAID_MODEL via special path below
    "seo":          2,
    "content":      2,
    "ppc":          2,
    "analytics":    1,
    "crm":          1,
    "smm":          1,
    "brand":        1,
    "web_ux":       1,
    "cro":          2,
    "research":     3,
    "deep_research":3,
    "aeo":          2,
}

# ─────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────
_last_call: dict = {}
_request_count = 0
_rate_limit_until = 0.0


# ─────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────

def _headers() -> dict:
    return {
        "Authorization":  f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":   "application/json",
        "HTTP-Referer":   "https://swarmops.ai",
        "X-Title":        "SwarmOps",
    }


def _wait_rate_limit():
    global _rate_limit_until
    now = time.time()
    if now < _rate_limit_until:
        time.sleep(_rate_limit_until - now)


def _post(payload: dict, timeout: float = 120.0) -> dict | None:
    """
    POST to OpenRouter and return the JSON response, or None on failure.
    Handles 429 rate limits with a single retry.
    """
    global _rate_limit_until, _request_count
    _wait_rate_limit()
    try:
        resp = httpx.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            json=payload,
            headers=_headers(),
            timeout=timeout,
        )
        _request_count += 1

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("retry-after", "10"))
            logger.warning(f"[model_router] 429 – waiting {retry_after}s")
            _rate_limit_until = time.time() + retry_after
            time.sleep(retry_after)
            # one retry
            resp = httpx.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                json=payload, headers=_headers(), timeout=timeout,
            )
            _request_count += 1

        if resp.status_code != 200:
            logger.error(f"[model_router] HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        return resp.json()

    except httpx.TimeoutException:
        logger.warning("[model_router] Request timed out")
        return None
    except Exception as e:
        logger.error(f"[model_router] Request failed: {e}")
        return None


def _extract_text(data: dict) -> str:
    """Pull the content string from an OpenRouter response dict."""
    choices = data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "") or ""
    return ""


def _build_payload(model: str, messages: list, max_tokens: int, temperature: float,
                   json_mode: bool, fallback_models: list | None = None) -> dict:
    payload: dict = {
        "model":       model,
        "messages":    messages,
        "max_tokens":  max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if fallback_models:
        payload["models"] = [model] + fallback_models
        payload["route"]  = "fallback"
    return payload


# ─────────────────────────────────────────────────────────────
# PUBLIC API  (same signatures as old model_router.py)
# ─────────────────────────────────────────────────────────────

def get_last_call_info() -> dict:
    """Return metadata about the last model call."""
    return _last_call.copy()


def call_model_sync(
    prompt: str,
    system_prompt: str = "",
    tier: int = 2,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    json_mode: bool = False,
    # Optional: callers that know about agent_id can pass it
    agent_id: str = "",
) -> dict:
    """
    Synchronous model call via OpenRouter.

    Returns:
        {"content": str, "model": str, "provider": "openrouter", "latency_ms": int}

    Backward-compatible with the old model_router return format.
    """
    global _last_call

    if not OPENROUTER_API_KEY:
        logger.error("[model_router] OPENROUTER_API_KEY not set")
        return {"content": "[OpenRouter API key not configured]", "model": "none",
                "provider": "openrouter", "latency_ms": 0}

    # Resolve tier from agent_id if provided
    if agent_id and agent_id in AGENT_TIER:
        tier = AGENT_TIER[agent_id]

    # Tier 4: augment with web search first
    actual_prompt = prompt
    if tier == 4:
        try:
            results = search_brave(prompt, max_results=5) or search_serper(prompt, max_results=5)
            if results:
                search_text = "\n".join(
                    f"{r.get('rank', i+1)}. {r.get('title','')}\n   {r.get('description','')}\n   {r.get('url','')}"
                    for i, r in enumerate(results)
                )
                actual_prompt = (
                    f"Web Search Results:\n{search_text}\n\n"
                    f"Based on these search results, {prompt}"
                )
        except Exception:
            pass  # web search failure is non-fatal

    # Build messages
    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": actual_prompt})

    # Determine model list for this tier
    model_list = TIER_MODELS.get(min(tier, 4), TIER_MODELS[2])
    primary    = model_list[0]
    fallbacks  = model_list[1:]

    t0 = time.time()

    # Try each model in the chain
    for i, model in enumerate(model_list):
        is_last = i == len(model_list) - 1
        payload  = _build_payload(
            model       = model,
            messages    = messages,
            max_tokens  = max_tokens,
            temperature = temperature,
            json_mode   = json_mode,
            # Only set fallbacks on the first attempt (OpenRouter handles them)
            fallback_models = fallbacks if i == 0 else None,
        )

        data = _post(payload)
        if data:
            text = _extract_text(data)
            if text:
                latency_ms    = int((time.time() - t0) * 1000)
                model_used    = data.get("model", model)
                usage         = data.get("usage", {})
                logger.info(
                    f"[model_router] tier={tier} → {model_used} | "
                    f"tokens={usage.get('total_tokens', 0)} | {latency_ms}ms"
                )
                result = {
                    "content":    text,
                    "model":      model_used,
                    "provider":   "openrouter",
                    "latency_ms": latency_ms,
                }
                _last_call = result.copy()
                return result

        if not is_last:
            logger.warning(f"[model_router] {model} failed, trying next in chain")
            time.sleep(1)

    latency_ms = int((time.time() - t0) * 1000)
    result = {"content": "[All model attempts failed — please try again]",
              "model": "none", "provider": "openrouter", "latency_ms": latency_ms}
    _last_call = result.copy()
    return result


def test_all_providers() -> dict:
    """Quick connectivity test for OpenRouter."""
    if not OPENROUTER_API_KEY:
        return {"openrouter": {"status": "no_key", "error": "OPENROUTER_API_KEY not set"}}

    t0   = time.time()
    data = _post({
        "model":      _FREE["fast"],
        "messages":   [{"role": "user", "content": "Reply with: OK"}],
        "max_tokens": 10,
    })
    latency = int((time.time() - t0) * 1000)

    if data and _extract_text(data):
        return {"openrouter": {"status": "ok", "latency_ms": latency,
                               "model": _FREE["fast"]}}
    return {"openrouter": {"status": "error", "latency_ms": latency}}


# ─────────────────────────────────────────────────────────────
# WEB SEARCH — delegate to old router (unchanged)
# ─────────────────────────────────────────────────────────────

def search_brave(query: str, max_results: int = 5) -> list[dict]:
    """Brave web search — delegated to model_router_old."""
    try:
        from model_router_old import search_brave as _sb
        return _sb(query, max_results)
    except Exception:
        return []


def search_serper(query: str, max_results: int = 5) -> list[dict]:
    """Serper.dev web search — delegated to model_router_old."""
    try:
        from model_router_old import search_serper as _ss
        return _ss(query, max_results)
    except Exception:
        return []


def web_search_multi(query: str, max_results: int = 5) -> list[dict]:
    """Try Brave first, then Serper."""
    results = search_brave(query, max_results)
    if results:
        return results
    return search_serper(query, max_results)


# ─────────────────────────────────────────────────────────────
# USAGE STATS
# ─────────────────────────────────────────────────────────────

def get_usage_stats() -> dict:
    return {"total_requests": _request_count, "api": "openrouter"}
