"""Unit tests for the TTL cache."""

import time

import pytest

from thetvdb_mcp_server.cache import TtlCache


@pytest.fixture
def cache():
    """Fresh cache instance for each test."""
    return TtlCache(ttl=1)


def test_cache_set_get(cache) -> None:
    """Basic set and get."""
    cache.set("key", {"data": "value"})
    result = cache.get("key")
    assert result == {"data": "value"}


def test_cache_get_missing(cache) -> None:
    """Get a key that doesn't exist."""
    result = cache.get("missing")
    assert result is None


def test_cache_expiry(cache) -> None:
    """Entries expire after TTL."""
    cache.set("key", "value")
    # Wait for expiry
    time.sleep(1.1)
    result = cache.get("key")
    assert result is None


def test_cache_clear(cache) -> None:
    """Clear all entries."""
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None
    assert cache.size() == 0


def test_cache_size(cache) -> None:
    """Cache size tracking."""
    assert cache.size() == 0
    cache.set("key1", "value1")
    assert cache.size() == 1
    cache.set("key2", "value2")
    assert cache.size() == 2


async def test_cache_start_stop() -> None:
    """Cache can be started and stopped."""
    c = TtlCache(ttl=1, cleanup_interval=1)
    await c.start()
    await c.start()  # idempotent
    await c.stop()
    await c.stop()  # idempotent
