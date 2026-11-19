"""Simple thread-safe in-memory cache with TTL and hit/miss tracking."""

import time
from threading import Lock
from typing import Any, Optional


class QueryCache:
    """Thread-safe TTL in-memory cache."""

    def __init__(self, default_ttl: int = 300, max_size: int = 500):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = Lock()
        self.hits = 0
        self.misses = 0

    def _make_key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{str(key).strip().casefold()}"

    def get(self, namespace: str, key: str) -> Optional[Any]:
        cache_key = self._make_key(namespace, key)
        now = time.time()
        with self._lock:
            if cache_key in self._store:
                value, expires_at = self._store[cache_key]
                if now < expires_at:
                    self.hits += 1
                    return value
                del self._store[cache_key]
            self.misses += 1
            return None

    def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        cache_key = self._make_key(namespace, key)
        expires_at = time.time() + (ttl or self.default_ttl)
        with self._lock:
            if len(self._store) >= self.max_size:
                now = time.time()
                self._store = {k: v for k, v in self._store.items() if v[1] > now}
            self._store[cache_key] = (value, expires_at)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total) if total > 0 else 0.0
            return {
                "hits": self.hits,
                "misses": self.misses,
                "total_lookups": total,
                "size": len(self._store),
                "hit_rate": round(hit_rate, 4),
            }

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self.hits = 0
            self.misses = 0


CACHE = QueryCache(default_ttl=300)
