"""Tests for in-memory query cache."""

import time

from app.cache import QueryCache


def test_cache_set_and_get_hit():
    cache = QueryCache(default_ttl=10)
    cache.set("rag", "pm-kisan deadline?", {"answer": "I don't know."})

    hit = cache.get("rag", "pm-kisan deadline?")
    assert hit is not None
    assert hit["answer"] == "I don't know."

    # Case insensitive and stripped
    hit2 = cache.get("rag", "  PM-KISAN DEADLINE?  ")
    assert hit2 is not None

    stats = cache.stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 0
    assert stats["hit_rate"] == 1.0


def test_cache_miss_and_expiration():
    cache = QueryCache(default_ttl=1)  # 1 second TTL
    val = cache.get("rag", "unseen query")
    assert val is None
    assert cache.stats()["misses"] == 1

    cache.set("rag", "short-lived", "temp-val", ttl=1)
    time.sleep(1.05)
    expired = cache.get("rag", "short-lived")
    assert expired is None
    assert cache.stats()["misses"] == 2


def test_cache_different_namespaces():
    cache = QueryCache(default_ttl=10)
    cache.set("search", "kisan", ["res1"])
    cache.set("rag", "kisan", {"answer": "ans1"})

    assert cache.get("search", "kisan") == ["res1"]
    assert cache.get("rag", "kisan") == {"answer": "ans1"}
