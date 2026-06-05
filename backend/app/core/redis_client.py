"""
Redis client — shared connection pool with graceful fallback.

All caching in VectorHire AI goes through this module.
If Redis is not configured (REDIS_URL="") or unreachable, every cache
operation silently returns None / does nothing — the app continues working,
just without caching. This means Redis is always optional.

Usage:
    from app.core.redis_client import get_redis, cache_get, cache_set

    # Store a value
    cache_set("my_key", {"result": 42}, ttl=3600)

    # Read it back (returns None on miss or Redis down)
    value = cache_get("my_key")

Keys are automatically prefixed with "vectorhire:" to avoid collisions
if this Redis instance is shared with other apps.
"""
from __future__ import annotations

import json
import hashlib
from typing import Any, Optional

import redis as redis_lib
from redis import Redis
from redis.exceptions import RedisError

from app.core.settings import get_settings
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
