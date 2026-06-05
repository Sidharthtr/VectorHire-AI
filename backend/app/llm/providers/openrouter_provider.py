from __future__ import annotations

# Patch Python SSL to use native OS certificate store (macOS Keychain, etc.)
# Makes SSL behave like curl — no cert issues on pyenv/Mac
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from openai import OpenAI, RateLimitError, APIStatusError
import httpx
from app.core.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: OpenAI | None = None

# Circuit breaker — after all models fail, skip LLM calls for this many seconds.
# Prevents the next LLM call (e.g. generate_suggestions right after extract_skills failed)
# from burning another 90s cycling through exhausted models again.
_CIRCUIT_OPEN_SECONDS = 60
_last_all_failed_at: float = 0.0


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        # verify=False: Zscaler proxy intercepts TLS — add Zscaler CA cert for production
        # timeout=15s per request: free-tier models take up to 56s to return 429.
        # With a 15s cap, we skip to the next model faster.
        # 6 models × 15s max = 90s worst-case vs 180s without timeout.
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            http_client=httpx.Client(verify=False, timeout=httpx.Timeout(15.0)),
        )
        logger.info(f"OpenRouter client ready — primary: {settings.llm_model} | fallback: {settings.llm_fallback_model}")
    return _client


_FALLBACK_CHAIN = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "qwen/qwen3-coder:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
]


def generate(prompt: str, temperature: float | None = None, max_tokens: int | None = None) -> str:
    import time as _time
    global _last_all_failed_at

    # Redis LLM cache — same prompt → same result, no API call needed.
    # Only cache deterministic prompts (temperature=0.1 structured calls).
    # Skip cache for high-temperature creative calls (explanations vary intentionally).
    _temp_for_cache = temperature if temperature is not None else get_settings().llm_temperature
    _use_cache = _temp_for_cache <= 0.15
    if _use_cache:
        from app.core.redis_client import cache_get, cache_set, make_hash
        _cache_key = f"llm:{make_hash(prompt)}"
        _cached = cache_get(_cache_key)
        if _cached and isinstance(_cached, str):
            logger.debug("LLM cache hit")
            return _cached

    # Circuit breaker: if all models failed recently, don't waste time trying again
    seconds_since_failure = _time.time() - _last_all_failed_at
    if _last_all_failed_at > 0 and seconds_since_failure < _CIRCUIT_OPEN_SECONDS:
        remaining = int(_CIRCUIT_OPEN_SECONDS - seconds_since_failure)
        raise RuntimeError(f"Circuit breaker open — all models rate-limited, retry in ~{remaining}s")

    client = _get_client()
    settings = get_settings()
    temp = temperature if temperature is not None else settings.llm_temperature
    tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens

    models = [settings.llm_model, settings.llm_fallback_model] + _FALLBACK_CHAIN
    last_error = None

    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=tokens,
            )
            if model != settings.llm_model:
                logger.info(f"Used fallback model: {model}")
            result = response.choices[0].message.content
            # Store in Redis cache for deterministic prompts
            if _use_cache:
                from app.core.redis_client import cache_set, make_hash
                cache_set(f"llm:{make_hash(prompt)}", result, ttl=get_settings().redis_ttl_llm)
            return result
        except RateLimitError:
            # 429 — skip instantly, try next model
            logger.warning(f"Model {model} rate-limited, skipping instantly")
            last_error = Exception(f"{model} rate-limited")
        except APIStatusError as e:
            # 503 / 404 / other provider errors — skip instantly
            logger.warning(f"Model {model} provider error ({e.status_code}), skipping")
            last_error = e
        except httpx.TimeoutException:
            # Model took >15s to respond (free tier queuing) — skip, don't wait
            logger.warning(f"Model {model} timed out after 15s, skipping")
            last_error = Exception(f"{model} timeout")
        except Exception as e:
            logger.warning(f"Model {model} failed: {e}")
            last_error = e

    _last_all_failed_at = _time.time()  # trip the circuit breaker
    raise RuntimeError(f"All LLM models failed. Last error: {last_error}")


def generate_structured(prompt: str, temperature: float = 0.1) -> str:
    """Lower temperature for structured JSON output."""
    return generate(prompt, temperature=temperature)
