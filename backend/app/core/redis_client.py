"""
Shared Redis connection pool + JSON cache helpers with graceful fallback.

What it does:
- Lazily opens one pooled Redis connection (get_redis) and caches the result.
- cache_get / cache_set / cache_delete / cache_delete_pattern wrap key access with a
  "vectorhire:" prefix and silently no-op if Redis is unreachable or REDIS_URL="".
- make_hash builds short stable cache-key components from arbitrary strings.

Upstream (who imports this): app.llm.gateway, app.llm.chains,
app.llm.providers.openrouter_provider, app.resume.parser, app.resume.extractor,
app.ingestion.* (pipeline, embedder, normalizer, adapters), app.graph.nodes.*,
app.rag.* (retrievers, embeddings, vectordb, cleanup), app.api.routes (search, debug,
ingestion, analysis), app.db.job_repository, app.db.init_db.
Downstream (what this imports): redis-py, json, hashlib, app.core.settings, app.core.logging.
"""
from __future__ import annotations

# json: serialise/deserialise cached values (dict → bytes → dict)
import json
# hashlib: SHA-256 in make_hash() to derive short cache-key suffixes
import hashlib
# Any/Optional: cache_get returns Any|None — values are arbitrary JSON-encodable objects
from typing import Any, Optional

# redis_lib: only used for .from_url() factory; renamed to avoid shadowing the Redis type
import redis as redis_lib
# Redis: type annotation for the module-level `_redis` singleton
from redis import Redis
# RedisError: swallowed in every cache op so caching failures never break the request path
from redis.exceptions import RedisError

# get_settings: needs settings.redis_url to know if Redis is enabled + where to connect
from app.core.settings import get_settings
# get_logger: emit warnings on connect failure + debug logs on per-op errors
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis: Redis | None = None
_redis_available: bool = True   # False after first connection failure


def get_redis() -> Redis | None:
    """
    Return the shared Redis connection pool instance.
    Returns None if Redis is disabled or unreachable.
    """
    global _redis, _redis_available

    if not _redis_available:
        return None

    settings = get_settings()
    if not settings.redis_url:
        return None  # Redis explicitly disabled

    if _redis is None:
        try:
            _redis = redis_lib.from_url(
                settings.redis_url,
                decode_responses=False,   # we handle encoding ourselves
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=False,
            )
            _redis.ping()
            logger.info(f"Redis connected: {settings.redis_url}")
        except Exception as e:
            logger.warning(f"Redis unavailable — caching disabled: {e}")
            _redis = None
            _redis_available = False

    return _redis


def cache_get(key: str) -> Any | None:
    """
    Retrieve a cached value. Returns None on cache miss or Redis down.
    Deserialises from JSON automatically.
    """
    client = get_redis()
    if client is None:
        return None
    try:
        raw = client.get(f"vectorhire:{key}")
        if raw is None:
            return None
        return json.loads(raw)
    except (RedisError, json.JSONDecodeError) as e:
        logger.debug(f"Cache get error ({key}): {e}")
        return None


def cache_set(key: str, value: Any, ttl: int) -> bool:
    """
    Store a value in cache with a TTL in seconds.
    Returns True if stored, False if Redis is down or value couldn't be serialised.
    """
    client = get_redis()
    if client is None:
        return False
    try:
        serialised = json.dumps(value, default=str)
        client.setex(f"vectorhire:{key}", ttl, serialised)
        return True
    except (RedisError, TypeError) as e:
        logger.debug(f"Cache set error ({key}): {e}")
        return False


def cache_delete(key: str) -> None:
    """Delete a specific cache key."""
    client = get_redis()
    if client is None:
        return
    try:
        client.delete(f"vectorhire:{key}")
    except RedisError:
        pass


def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern (e.g. 'search:*'). Returns count deleted."""
    client = get_redis()
    if client is None:
        return 0
    try:
        keys = client.keys(f"vectorhire:{pattern}")
        if keys:
            return client.delete(*keys)
        return 0
    except RedisError:
        return 0


def make_hash(data: str) -> str:
    """Create a short, consistent hash string for use as a cache key component."""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def ping() -> bool:
    """Health check — True if Redis is reachable."""
    client = get_redis()
    if client is None:
        return False
    try:
        return client.ping()
    except RedisError:
        return False
