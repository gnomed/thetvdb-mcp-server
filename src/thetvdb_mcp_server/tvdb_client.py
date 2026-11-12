"""TVDB API client wrapper using the official tvdb_v4_official package."""

import tvdb_v4_official

from thetvdb_mcp_server.rate_limiter import AsyncRateLimiter


class TvdbClient:
    """Wrapper around the official TVDB v4 Python client.

    Handles rate limiting and provides a simplified interface for the
    operations this MCP server needs.

    Args:
        api_key: TVDB API key obtained from the TVDB developer portal.
        pin: Optional subscriber PIN for extended access. Pass ``None``
            if not applicable.
        rate_limiter: Shared rate limiter instance used to throttle all
            outbound calls.
        primary_language: Optional 3-character ISO 639-2 language code
            (e.g. "eng") applied to search and episode queries. Pass ``None``
            to disable language filtering.
    """

    def __init__(
        self,
        api_key: str,
        pin: str | None,
        rate_limiter: AsyncRateLimiter,
        primary_language: str | None = None,
    ) -> None:
        self._tvdb = tvdb_v4_official.TVDB(api_key, pin or "")
        self._rate_limiter = rate_limiter
        self._primary_language = primary_language

    async def get_series(self, series_id: int) -> dict:
        """Fetch a series base record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_series(series_id)

    async def get_series_episodes(
        self,
        series_id: int,
        season_type: str = "default",
        lang: str | None = None,
        page: int = 0,
    ) -> dict:
        """Fetch episodes for a series by season type with optional language.

        If ``lang`` is not provided, the configured ``primary_language`` is used.
        If neither is set, episodes are returned in their default language.
        """
        effective_lang = lang or self._primary_language
        async with self._rate_limiter:
            return self._tvdb.get_series_episodes(
                series_id,
                season_type=season_type,
                page=page,
                lang=effective_lang,
            )

    async def search(
        self,
        query: str,
        type_: str | None = None,
        year: int | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list:
        """Search TVDB with optional language filtering.

        Applies the configured ``primary_language`` to restrict results to
        series and movies in that language.
        """
        params: dict[str, object] = {
            "type": type_,
            "year": year,
            "offset": offset,
            "limit": limit,
        }
        if self._primary_language is not None:
            params["primaryLanguage"] = self._primary_language
        async with self._rate_limiter:
            return self._tvdb.search(query, **params)
