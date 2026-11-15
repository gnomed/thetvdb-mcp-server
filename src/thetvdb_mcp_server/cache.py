"""Simple in-memory TTL cache for TVDB API responses.

Designed for a low-traffic single-user service. Entries expire after a fixed
TTL (default 12 hours). A background task periodically sweeps expired entries
so they don't linger indefinitely after their TTL passes.
"""

import asyncio
import logging
import time
from typing import Any

_logger = logging.getLogger(__name__)


class TtlCache:
    """In-memory cache with TTL and periodic cleanup.

    Not thread-safe (designed for single-user asyncio usage). Entries expire
    after the configured TTL. A background task periodically sweeps expired
    entries.

    Args:
        ttl: Time-to-live in seconds. Defaults to 43200 (12 hours).
        cleanup_interval: How often to sweep expired entries, in seconds.
            Defaults to 3600 (1 hour).
    """

    def __init__(self, ttl: int = 43200, cleanup_interval: int = 3600) -> None:
        self._ttl = ttl
        self._cleanup_interval = cleanup_interval
        self._entries: dict[str, tuple[float, Any]] = {}
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the background cleanup task."""
        if self._running:
            return
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        _logger.info("Cache cleanup task started (interval=%ds, ttl=%ds)", self._cleanup_interval, self._ttl)

    async def stop(self) -> None:
        """Stop the background cleanup task."""
        if not self._running:
            return
        self._running = False
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        _logger.info("Cache cleanup task stopped")

    def get(self, key: str) -> Any | None:
        """Retrieve a cached value, or None if missing or expired."""
        entry = self._entries.get(key)
        if entry is None:
            return None
        timestamp, value = entry
        if time.time() - timestamp > self._ttl:
            # Expired — remove and report miss
            del self._entries[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
        self._entries[key] = (time.time(), value)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._entries.clear()
        _logger.info("Cache cleared")

    def size(self) -> int:
        """Return the number of entries in the cache."""
        return len(self._entries)

    async def _cleanup_loop(self) -> None:
        """Periodically sweep expired entries."""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                self._sweep()
            except asyncio.CancelledError:
                break
            except Exception:
                _logger.exception("Error during cache cleanup sweep")

    def _sweep(self) -> None:
        """Remove all expired entries."""
        now = time.time()
        expired_keys = [key for key, (timestamp, _value) in self._entries.items() if now - timestamp > self._ttl]
        for key in expired_keys:
            del self._entries[key]
        if expired_keys:
            _logger.info("Cache sweep: removed %d expired entries", len(expired_keys))


# Module-level singleton
tvdb_cache = TtlCache()
