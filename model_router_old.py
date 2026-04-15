"""
Model Router - SwarmOps
Unified multi-provider AI model routing with tiered fallback.

Providers:
  - Groq          (existing)   — fast inference, llama-3.3-70b
  - Gemini        (existing)   — Google Gemini 2.0 Flash
  - OpenRouter    (new, free)  — 18+ free models via OpenAI-compatible API
  - NVIDIA NIMs   (new, free)  — Kimi K2.5 agentic model
  - DeepSeek      (new, cheap) — deepseek-chat / deepseek-reasoner
  - Serper.dev    (new, free)  — Google search results (2,500/month)
  - Brave Search  (existing)   — web search (2,000/month)

Usage:
    from model_router import call_model, web_search_multi
    result = await call_model("Write a tagline", tier=2)
    # result = {"content": "...", "model": "...", "provider": "...", "latency_ms": 42}
"""

import os
import time
import asyncio
import threading
import requests
from typing import Optional
from dotenv import load_dotenv
from rate_limiter import get_rate_limiter

load_dotenv()


def extract_json_safe(text: str, fallback: dict = None) -> dict:
    """
    Robustly extract JSON from LLM output.
    Handles: raw JSON, markdown fences (```json...```), inline objects.
    Never raises — returns fallback on failure.
    """
    import json, re
    if not text:
        return fallback or {}

    # 1. Try direct parse first (cleanest case)
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # 2. Strip markdown fences
    fence_match = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except Exception:
            pass

    # 3. Find first {...} or [...] block
    obj_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\})', text, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except Exception:
            pass

    # 4. Find any JSON array
    arr_match = re.search(r'(\[[^\[\]]*\])', text, re.DOTALL)
    if arr_match:
        try:
            return json.loads(arr_match.group(1))
        except Exception:
            pass

    return fallback or {}

# ---------------------------------------------------------------------------
# Call tracking — thread-local so concurrent requests don't collide
# ---------------------------------------------------------------------------

_last_call_info = threading.local()

# ---------------------------------------------------------------------------
# Provider failure cache — skip dead/rate-limited providers for 5 minutes
# ---------------------------------------------------------------------------

_failed_providers: dict = {}  # {provider_name: fail_timestamp}
_FAILURE_TTL = 300  # 5 minutes


def _is_provider_failed(provider: str) -> bool:
    """Return True if this provider failed within the last 5 minutes."""
    ts = _failed_providers.get(provider)
    if ts is None:
        return False
    if time.time() - ts > _FAILURE_TTL:
        _failed_providers.pop(provider, None)
        return False
    return True


def _mark_provider_failed(provider: str, reason: str = ""):
    """Cache a provider failure for 5 minutes."""
    _failed_providers[provider] = time.time()
    print(f"[model_router] ⛔ {provider} marked as failed for 5 min: {reason[:80]}")


def get_last_call_info() -> dict:
    """Get metadata from the most recent call_model_sync call in this thread."""
    return getattr(_last_call_info, 'info', {"model": "unknown", "provider": "unknown", "latency_ms": 0})


# ---------------------------------------------------------------------------
# Provider clients — initialised lazily (only when first used)
# ---------------------------------------------------------------------------

_groq_client = None
_openrouter_client = None
_nvidia_client = None
_deepseek_client = None
_gemini_llm = None


def _get_groq():
    global _groq_client
    if _groq_client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            return None
        from groq import Groq
        _groq_client = Groq(api_key=key)
    return _groq_client


def _get_openrouter():
    global _openrouter_client
    if _openrouter_client is None:
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            return None
        from openai import OpenAI
        _openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
            timeout=15.0,
            default_headers={
                "HTTP-Referer": "https://swarmops.app",
                "X-Title": "SwarmOps",
            },
        )
    return _openrouter_client


def _get_nvidia():
    global _nvidia_client
    if _nvidia_client is None:
        key = os.getenv("NVIDIA_API_KEY")
        if not key:
            return None
        from openai import OpenAI
        _nvidia_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=key,
            timeout=15.0,
        )
    return _nvidia_client


def _get_deepseek():
    global _deepseek_client
    if _deepseek_client is None:
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            return None
        from openai import OpenAI
        _deepseek_client = OpenAI(
            base_url="https://api.deepseek.com",
            api_key=key,
            timeout=15.0,
        )
    return _deepseek_client


def _get_gemini():
    global _gemini_llm
    if _gemini_llm is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            return None
        from langchain_google_genai import ChatGoogleGenerativeAI
        _gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=key,
            temperature=0.7,
        )
    return _gemini_llm


# ---------------------------------------------------------------------------
# Model catalogue
# ---------------------------------------------------------------------------

OPENROUTER_MODELS = {
    "deepseek-r1": "deepseek/deepseek-r1-0528:free",
    "llama-3.3-70b": "meta-llama/llama-3.3-70b-instruct:free",
    "mistral-small": "mistralai/mistral-small-3.1-24b-instruct:free",
    "hermes-405b": "nousresearch/hermes-3-llama-3.1-405b:free",
    "qwen3-coder": "qwen/qwen3-coder:free",
}

NVIDIA_MODELS = {
    "kimi-k2.5": "moonshotai/kimi-k2.5",
}

DEEPSEEK_MODELS = {
    "deepseek-chat": "deepseek-chat",
    "deepseek-reasoner": "deepseek-reasoner",
}

# ---------------------------------------------------------------------------
# Low-level provider call helpers (synchronous)
# ---------------------------------------------------------------------------


def _call_groq(prompt: str, system_prompt: str = "", model: str = "llama-3.3-70b-versatile",
               max_tokens: int = 4096, temperature: float = 0.7) -> Optional[str]:
    """Call Groq API. Returns content string or None on failure."""
    client = _get_groq()
    if client is None:
        return None
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=model, messages=messages,
        max_tokens=max_tokens, temperature=temperature,
    )
    return resp.choices[0].message.content


def _call_openai_compat(client, model: str, prompt: str, system_prompt: str = "",
                        max_tokens: int = 4096, temperature: float = 0.7) -> Optional[str]:
    """Call any OpenAI-compatible API (OpenRouter, NVIDIA, DeepSeek).
    Handles reasoning models that put output in reasoning_content.
    Uses threading timeout as a safety net since OpenAI client timeout
    may not work reliably on all Python versions."""
    if client is None:
        return None
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        client.chat.completions.create,
        model=model, messages=messages,
        max_tokens=max_tokens, temperature=temperature,
    )
    try:
        resp = future.result(timeout=20)  # Hard 20s timeout
    except (concurrent.futures.TimeoutError, TimeoutError):
        print(f"[model_router] {model} timed out after 20s")
        executor.shutdown(wait=False, cancel_futures=True)
        return None
    executor.shutdown(wait=False)

    msg = resp.choices[0].message
    content = msg.content
    # Reasoning models (Kimi K2.5, DeepSeek R1) may put output in reasoning_content
    if not content:
        content = getattr(msg, "reasoning_content", None)
    return content


def _call_openrouter(prompt: str, system_prompt: str = "",
                     model_key: str = "llama-3.3-70b",
                     max_tokens: int = 4096, temperature: float = 0.7) -> Optional[str]:
    client = _get_openrouter()
    model_id = OPENROUTER_MODELS.get(model_key, model_key)
    return _call_openai_compat(client, model_id, prompt, system_prompt, max_tokens, temperature)


def _call_nvidia(prompt: str, system_prompt: str = "",
                 model_key: str = "kimi-k2.5",
                 max_tokens: int = 4096, temperature: float = 0.7) -> Optional[str]:
    client = _get_nvidia()
    model_id = NVIDIA_MODELS.get(model_key, model_key)
    return _call_openai_compat(client, model_id, prompt, system_prompt, max_tokens, temperature)


def _call_deepseek(prompt: str, system_prompt: str = "",
                   model_key: str = "deepseek-chat",
                   max_tokens: int = 4096, temperature: float = 0.7) -> Optional[str]:
    client = _get_deepseek()
    model_id = DEEPSEEK_MODELS.get(model_key, model_key)
    return _call_openai_compat(client, model_id, prompt, system_prompt, max_tokens, temperature)


def _call_gemini(prompt: str, system_prompt: str = "",
                 max_tokens: int = 4096, temperature: float = 0.7) -> Optional[str]:
    """Call Gemini via LangChain. Returns content string or None."""
    llm = _get_gemini()
    if llm is None:
        return None
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    resp = llm.invoke(full_prompt)
    return resp.content if hasattr(resp, "content") else str(resp)


# ---------------------------------------------------------------------------
# Web search helpers
# ---------------------------------------------------------------------------


def search_brave(query: str, max_results: int = 5) -> list[dict]:
    """Search with Brave. Returns list of {rank, title, url, description}."""
    key = os.getenv("BRAVE_API_KEY")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": key},
            params={"q": query, "count": max_results},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        results = resp.json().get("web", {}).get("results", [])
        return [
            {"rank": i + 1, "title": r.get("title", ""), "url": r.get("url", ""),
             "description": r.get("description", "")}
            for i, r in enumerate(results[:max_results])
        ]
    except Exception:
        return []


def search_serper(query: str, max_results: int = 5) -> list[dict]:
    """Search with Serper.dev (Google results). Returns same format as Brave."""
    key = os.getenv("SERPER_API_KEY")
    if not key:
        return []
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": max_results},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        organic = data.get("organic", [])
        return [
            {"rank": i + 1, "title": r.get("title", ""), "url": r.get("link", ""),
             "description": r.get("snippet", "")}
            for i, r in enumerate(organic[:max_results])
        ]
    except Exception:
        return []


def web_search_multi(query: str, max_results: int = 5) -> list[dict]:
    """
    Search using BOTH Brave and Serper, de-duplicate by URL, return combined results.
    Respects rate limits for search APIs.
    """
    rate_limiter = get_rate_limiter()
    brave_results = []
    serper_results = []

    # Try Brave if not rate-limited
    if rate_limiter.can_call("brave"):
        brave_results = search_brave(query, max_results)
        if brave_results:
            rate_limiter.record_call("brave")

    # Try Serper if not rate-limited
    if rate_limiter.can_call("serper"):
        serper_results = search_serper(query, max_results)
        if serper_results:
            rate_limiter.record_call("serper")

    seen_urls = set()
    combined = []
    for r in brave_results + serper_results:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            combined.append(r)

    # Re-rank
    for i, r in enumerate(combined):
        r["rank"] = i + 1

    return combined[:max_results * 2]  # Return up to 2x results


# ---------------------------------------------------------------------------
# Tier routing definitions
# ---------------------------------------------------------------------------

# Each tier is a list of (provider_call_func, kwargs) tuples tried in order.
# The first one that succeeds wins.

def _build_tier_chain(tier: int):
    """Return a list of (callable, display_model, display_provider) tuples.
    Priority order: Groq (fastest) → Gemini (reliable) → OpenRouter → NVIDIA → DeepSeek
    """
    if tier == 1:  # Fast classification
        return [
            (lambda p, s, mt, t: _call_groq(p, s, "llama-3.3-70b-versatile", mt, t),
             "llama-3.3-70b-versatile", "groq"),
            (lambda p, s, mt, t: _call_gemini(p, s, mt, t),
             "gemini-2.0-flash", "gemini"),
            (lambda p, s, mt, t: _call_openrouter(p, s, "llama-3.3-70b", mt, t),
             "llama-3.3-70b-instruct:free", "openrouter"),
            (lambda p, s, mt, t: _call_openrouter(p, s, "mistral-small", mt, t),
             "mistral-small-3.1-24b:free", "openrouter"),
        ]
    elif tier == 2:  # Content generation
        return [
            (lambda p, s, mt, t: _call_groq(p, s, "llama-3.3-70b-versatile", mt, t),
             "llama-3.3-70b-versatile", "groq"),
            (lambda p, s, mt, t: _call_gemini(p, s, mt, t),
             "gemini-2.0-flash", "gemini"),
            (lambda p, s, mt, t: _call_openrouter(p, s, "llama-3.3-70b", mt, t),
             "llama-3.3-70b-instruct:free", "openrouter"),
            (lambda p, s, mt, t: _call_openrouter(p, s, "mistral-small", mt, t),
             "mistral-small-3.1-24b:free", "openrouter"),
        ]
    elif tier == 3:  # Strategic reasoning
        return [
            (lambda p, s, mt, t: _call_groq(p, s, "llama-3.3-70b-versatile", mt, t),
             "llama-3.3-70b-versatile", "groq"),
            (lambda p, s, mt, t: _call_gemini(p, s, mt, t),
             "gemini-2.0-flash", "gemini"),
            (lambda p, s, mt, t: _call_openrouter(p, s, "llama-3.3-70b", mt, t),
             "llama-3.3-70b-instruct:free", "openrouter"),
            (lambda p, s, mt, t: _call_openrouter(p, s, "mistral-small", mt, t),
             "mistral-small-3.1-24b:free", "openrouter"),
            (lambda p, s, mt, t: _call_nvidia(p, s, "kimi-k2.5", mt, t),
             "kimi-k2.5", "nvidia"),
        ]
    elif tier == 4:  # Deep research (search + model)
        return [
            (lambda p, s, mt, t: _call_gemini(p, s, mt, t),
             "gemini-2.0-flash", "gemini"),
            (lambda p, s, mt, t: _call_groq(p, s, "llama-3.3-70b-versatile", mt, t),
             "llama-3.3-70b-versatile", "groq"),
            (lambda p, s, mt, t: _call_nvidia(p, s, "kimi-k2.5", mt, t),
             "kimi-k2.5", "nvidia"),
            (lambda p, s, mt, t: _call_openrouter(p, s, "deepseek-r1", mt, t),
             "deepseek-r1-0528:free", "openrouter"),
        ]
    else:
        # Default to tier 2
        return _build_tier_chain(2)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def call_model(
    prompt: str,
    system_prompt: str = "",
    tier: int = 2,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> dict:
    """
    Unified model call with tiered fallback + rate limiting.

    Args:
        prompt:        The user/task prompt.
        system_prompt: Optional system message.
        tier:          1=fast, 2=content, 3=strategic, 4=deep research.
        max_tokens:    Max response tokens.
        temperature:   Sampling temperature.

    Returns:
        {"content": str, "model": str, "provider": str, "latency_ms": int}

    For tier 4 (deep research), web search results are automatically prepended
    to the prompt before sending to the model.
    """
    rate_limiter = get_rate_limiter()

    # Tier 4: prepend web search context
    actual_prompt = prompt
    search_results = []
    if tier == 4:
        # Rate-limit search APIs
        if rate_limiter.can_call("serper") or rate_limiter.can_call("brave"):
            search_results = web_search_multi(prompt, max_results=5)
            if search_results:
                search_text = "\n".join(
                    f"{r['rank']}. {r['title']}\n   {r['description']}\n   URL: {r['url']}"
                    for r in search_results
                )
                actual_prompt = (
                    f"Web Search Results:\n{search_text}\n\n"
                    f"Based on these search results, {prompt}"
                )

    chain = _build_tier_chain(tier)
    last_error = None
    rate_limited_providers = []

    for call_fn, model_name, provider_name in chain:
        # Skip providers cached as failed (rate-limited / 402 / no response)
        if _is_provider_failed(provider_name):
            print(f"[model_router] ⏭️  {provider_name} in failure cache, skipping")
            continue

        # Check rate limit before attempting call
        if not rate_limiter.can_call(provider_name):
            wait = rate_limiter.wait_time(provider_name)
            print(f"[model_router] {provider_name} rate-limited (wait {wait:.1f}s), skipping to next")
            rate_limited_providers.append((provider_name, wait))
            continue

        t0 = time.time()
        try:
            # Run synchronous call in thread pool to keep async-compatible
            content = await asyncio.get_event_loop().run_in_executor(
                None, call_fn, actual_prompt, system_prompt, max_tokens, temperature
            )
            if content:
                latency = int((time.time() - t0) * 1000)
                # Record successful call
                rate_limiter.record_call(provider_name)
                print(f"[model_router] ✅ Used {provider_name}/{model_name} ({latency}ms)")
                return {
                    "content": content,
                    "model": model_name,
                    "provider": provider_name,
                    "latency_ms": latency,
                }
            else:
                _mark_provider_failed(provider_name, "empty response")
        except Exception as e:
            last_error = e
            err_str = str(e)
            print(f"[model_router] {provider_name}/{model_name} failed: {err_str[:120]}")
            if "429" in err_str or "rate" in err_str.lower() or "402" in err_str or "balance" in err_str.lower():
                _mark_provider_failed(provider_name, err_str)
            continue

    # If ALL providers were rate-limited, wait for shortest time and retry once
    if rate_limited_providers and len(rate_limited_providers) == len(chain):
        shortest_wait = min(wait for _, wait in rate_limited_providers)
        print(f"[model_router] All providers rate-limited, waiting {shortest_wait:.1f}s and retrying...")
        await asyncio.sleep(shortest_wait + 0.5)  # Add small buffer

        # Retry with first provider that should now be available
        for call_fn, model_name, provider_name in chain:
            if rate_limiter.can_call(provider_name):
                t0 = time.time()
                try:
                    content = await asyncio.get_event_loop().run_in_executor(
                        None, call_fn, actual_prompt, system_prompt, max_tokens, temperature
                    )
                    if content:
                        latency = int((time.time() - t0) * 1000)
                        rate_limiter.record_call(provider_name)
                        return {
                            "content": content,
                            "model": model_name,
                            "provider": provider_name,
                            "latency_ms": latency,
                        }
                except Exception as e:
                    last_error = e
                    continue

    # All providers failed
    return {
        "content": f"All providers failed. Last error: {last_error}",
        "model": "none",
        "provider": "none",
        "latency_ms": 0,
    }


def call_model_sync(
    prompt: str,
    system_prompt: str = "",
    tier: int = 2,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    json_mode: bool = False,
) -> dict:
    """
    Synchronous version of call_model for use in non-async contexts + rate limiting.
    Same interface and return format.
    """
    rate_limiter = get_rate_limiter()

    # json_mode: append JSON instruction to system prompt if not already there
    if json_mode and system_prompt and "json" not in system_prompt.lower():
        system_prompt = system_prompt + "\n\nIMPORTANT: Respond with valid JSON only. No markdown, no explanation."
    elif json_mode and not system_prompt:
        system_prompt = "Respond with valid JSON only. No markdown, no explanation."

    actual_prompt = prompt
    if tier == 4:
        # Rate-limit search APIs
        if rate_limiter.can_call("serper") or rate_limiter.can_call("brave"):
            search_results = web_search_multi(prompt, max_results=5)
            if search_results:
                search_text = "\n".join(
                    f"{r['rank']}. {r['title']}\n   {r['description']}\n   URL: {r['url']}"
                    for r in search_results
                )
                actual_prompt = (
                    f"Web Search Results:\n{search_text}\n\n"
                    f"Based on these search results, {prompt}"
                )

    chain = _build_tier_chain(tier)
    last_error = None
    rate_limited_providers = []

    for call_fn, model_name, provider_name in chain:
        # Skip providers cached as failed (rate-limited / 402 / no response)
        if _is_provider_failed(provider_name):
            print(f"[model_router] ⏭️  {provider_name} in failure cache, skipping")
            continue

        # Check rate limit before attempting call
        if not rate_limiter.can_call(provider_name):
            wait = rate_limiter.wait_time(provider_name)
            print(f"[model_router] {provider_name} rate-limited (wait {wait:.1f}s), skipping to next")
            rate_limited_providers.append((provider_name, wait))
            continue

        t0 = time.time()
        try:
            content = call_fn(actual_prompt, system_prompt, max_tokens, temperature)
            if content:
                latency = int((time.time() - t0) * 1000)
                # Record successful call
                rate_limiter.record_call(provider_name)
                info = {
                    "content": content,
                    "model": model_name,
                    "provider": provider_name,
                    "latency_ms": latency,
                }
                _last_call_info.info = info
                print(f"[model_router] ✅ Used {provider_name}/{model_name} ({latency}ms)")
                return info
            else:
                _mark_provider_failed(provider_name, "empty response")
        except Exception as e:
            last_error = e
            err_str = str(e)
            print(f"[model_router] {provider_name}/{model_name} failed: {err_str[:120]}")
            # Cache providers that are rate-limited (429) or have insufficient balance (402)
            if "429" in err_str or "rate" in err_str.lower() or "402" in err_str or "balance" in err_str.lower():
                _mark_provider_failed(provider_name, err_str)
            continue

    # If ALL providers were rate-limited, wait for shortest time and retry once
    if rate_limited_providers and len(rate_limited_providers) == len(chain):
        shortest_wait = min(wait for _, wait in rate_limited_providers)
        print(f"[model_router] All providers rate-limited, waiting {shortest_wait:.1f}s and retrying...")
        time.sleep(shortest_wait + 0.5)  # Add small buffer

        # Retry with first provider that should now be available
        for call_fn, model_name, provider_name in chain:
            if rate_limiter.can_call(provider_name):
                t0 = time.time()
                try:
                    content = call_fn(actual_prompt, system_prompt, max_tokens, temperature)
                    if content:
                        latency = int((time.time() - t0) * 1000)
                        rate_limiter.record_call(provider_name)
                        info = {
                            "content": content,
                            "model": model_name,
                            "provider": provider_name,
                            "latency_ms": latency,
                        }
                        _last_call_info.info = info
                        return info
                except Exception as e:
                    last_error = e
                    continue

    return {
        "content": f"All providers failed. Last error: {last_error}",
        "model": "none",
        "provider": "none",
        "latency_ms": 0,
    }


# ---------------------------------------------------------------------------
# Drop-in wrapper: Groq-compatible interface
# ---------------------------------------------------------------------------

class _FakeChoice:
    def __init__(self, content):
        self.message = type("msg", (), {"content": content})()

class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class RouterGroqCompat:
    """
    Drop-in replacement for groq.Groq() client.
    Agents that currently do:
        client = Groq(api_key=...)
        resp = client.chat.completions.create(model=..., messages=[...], ...)
    Can switch to:
        from model_router import RouterGroqCompat
        client = RouterGroqCompat(tier=2)
        resp = client.chat.completions.create(model=..., messages=[...], ...)
    And get tiered multi-provider fallback automatically.
    """

    def __init__(self, tier: int = 2):
        self.tier = tier
        self.chat = self  # self.chat.completions.create(...)
        self.completions = self

    def create(self, model=None, messages=None, max_tokens=4096,
               temperature=0.7, **kwargs):
        system_prompt = ""
        prompt = ""
        for msg in (messages or []):
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                prompt = msg["content"]

        result = call_model_sync(
            prompt=prompt,
            system_prompt=system_prompt,
            tier=self.tier,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return _FakeResponse(result["content"])


# ---------------------------------------------------------------------------
# Drop-in wrapper: Gemini/LangChain-compatible interface
# ---------------------------------------------------------------------------


class RouterGeminiCompat:
    """
    Drop-in replacement for ChatGoogleGenerativeAI.
    Agents that currently do:
        llm = ChatGoogleGenerativeAI(model=..., google_api_key=...)
        resp = llm.invoke(prompt)
        text = resp.content
    Can switch to:
        from model_router import RouterGeminiCompat
        llm = RouterGeminiCompat(tier=3)
        resp = llm.invoke(prompt)
        text = resp.content
    """

    def __init__(self, tier: int = 3):
        self.tier = tier

    def invoke(self, prompt, **kwargs):
        if isinstance(prompt, dict):
            text = str(prompt)
        else:
            text = str(prompt)

        result = call_model_sync(
            prompt=text,
            tier=self.tier,
        )
        return type("resp", (), {"content": result["content"]})()


# ---------------------------------------------------------------------------
# Provider health test
# ---------------------------------------------------------------------------


def test_all_providers() -> dict:
    """
    Test each provider with a simple prompt.
    Returns: {"groq": "ok", "openrouter": "error: ...", ...}
    """
    test_prompt = "Say hello in exactly 10 words."
    results = {}

    # Groq
    try:
        r = _call_groq(test_prompt, max_tokens=50)
        results["groq"] = "ok" if r else "no response"
    except Exception as e:
        results["groq"] = f"error: {e}"

    # Gemini
    try:
        r = _call_gemini(test_prompt, max_tokens=50)
        results["gemini"] = "ok" if r else "no response"
    except Exception as e:
        results["gemini"] = f"error: {e}"

    # OpenRouter — try multiple free models in case one is rate-limited
    if os.getenv("OPENROUTER_API_KEY"):
        or_ok = False
        for or_model in ["llama-3.3-70b", "mistral-small", "qwen3-coder"]:
            try:
                r = _call_openrouter(test_prompt, model_key=or_model, max_tokens=50)
                if r:
                    results["openrouter"] = f"ok (via {or_model})"
                    or_ok = True
                    break
            except Exception:
                continue
        if not or_ok:
            results["openrouter"] = "all free models rate-limited, try again later"
    else:
        results["openrouter"] = "skipped - no key"

    # NVIDIA
    if os.getenv("NVIDIA_API_KEY"):
        try:
            r = _call_nvidia(test_prompt, model_key="kimi-k2.5", max_tokens=512)
            results["nvidia"] = "ok" if r else "no response"
        except Exception as e:
            results["nvidia"] = f"error: {e}"
    else:
        results["nvidia"] = "skipped - no key"

    # DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        try:
            r = _call_deepseek(test_prompt, model_key="deepseek-chat", max_tokens=50)
            results["deepseek"] = "ok" if r else "no response"
        except Exception as e:
            results["deepseek"] = f"error: {e}"
    else:
        results["deepseek"] = "skipped - no key"

    # Serper
    if os.getenv("SERPER_API_KEY"):
        try:
            r = search_serper("test query", max_results=1)
            results["serper"] = "ok" if r else "no results"
        except Exception as e:
            results["serper"] = f"error: {e}"
    else:
        results["serper"] = "skipped - no key"

    # Brave
    if os.getenv("BRAVE_API_KEY"):
        try:
            r = search_brave("test query", max_results=1)
            results["brave"] = "ok" if r else "no results"
        except Exception as e:
            results["brave"] = f"error: {e}"
    else:
        results["brave"] = "skipped - no key"

    return results


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING MODEL ROUTER")
    print("=" * 60)

    results = test_all_providers()
    for provider, status in results.items():
        icon = "✅" if status == "ok" else ("⏭️" if "skipped" in status else "❌")
        print(f"  {icon} {provider}: {status}")

    print("\n--- Testing tier 2 (content generation) ---")
    r = call_model_sync("Write a one-sentence tagline for an AI marketing tool.", tier=2, max_tokens=100)
    print(f"  Provider: {r['provider']}/{r['model']}")
    print(f"  Latency:  {r['latency_ms']}ms")
    print(f"  Content:  {r['content'][:200]}")
    print("=" * 60)
