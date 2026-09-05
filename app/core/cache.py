"""
app/core/cache.py
-----------------
Zero-dependency in-memory TTL cache.
No Redis, no cachetools - just a thread-safe dict + timestamps.

Usage
-----
    from app.core.cache import cache_get, cache_set, cache_delete, cache_delete_prefix

    # Manual style:
    val = cache_get("my_key")
    if val is None:
        val = expensive_query()
        cache_set("my_key", val, ttl=5)
"""

import time
import threading
from typing import Any, Optional

_store: dict = {}   # key -> (value, expires_at)
_lock = threading.Lock()


def cache_get(key: str) -> Optional[Any]:
    """Return cached value or None if missing / expired."""
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            _store.pop(key, None)
            return None
        return value


def cache_set(key: str, value: Any, ttl: float = 10.0) -> None:
    """Store value under key for ttl seconds."""
    with _lock:
        _store[key] = (value, time.monotonic() + ttl)


def cache_delete(key: str) -> None:
    """Explicitly invalidate a cache key."""
    with _lock:
        _store.pop(key, None)


def cache_delete_prefix(prefix: str) -> None:
    """Invalidate all keys that start with prefix."""
    with _lock:
        keys = [k for k in list(_store.keys()) if k.startswith(prefix)]
        for k in keys:
            _store.pop(k, None)
