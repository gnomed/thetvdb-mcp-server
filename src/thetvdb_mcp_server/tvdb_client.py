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

    # ------------------------------------------------------------------
    # Series endpoints
    # ------------------------------------------------------------------

    async def get_series(self, series_id: int) -> dict:
        """Fetch a series base record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_series(series_id)

    async def get_series_extended(
        self,
        series_id: int,
        include_characters: bool = False,
        include_artworks: bool = False,
    ) -> dict:
        """Fetch a series extended record with optional arrays.

        The TVDB API only supports an all-or-nothing ``short`` parameter.
        To provide granular control, this method calls the API with
        ``short=True`` when both ``include_characters`` and ``include_artworks``
        are ``False``, and with ``short=False`` otherwise, stripping any
        unrequested arrays from the response.
        """
        short = not (include_characters or include_artworks)
        async with self._rate_limiter:
            result = self._tvdb.get_series_extended(series_id, short=short)

        if short:
            return result

        if not include_characters:
            result.pop("characters", None)
        if not include_artworks:
            result.pop("artworks", None)
        return result

    async def get_series_episodes(
        self,
        series_id: int,
        season_type: str = "default",
        page: int = 0,
        lang: str | None = None,
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

    async def get_series_by_slug(self, slug: str) -> dict:
        """Fetch a series record by its slug."""
        async with self._rate_limiter:
            return self._tvdb.get_series_by_slug(slug)

    # ------------------------------------------------------------------
    # Season endpoints
    # ------------------------------------------------------------------

    async def get_season(self, season_id: int) -> dict:
        """Fetch a season base record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_season(season_id)

    async def get_season_extended(self, season_id: int) -> dict:
        """Fetch a season extended record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_season_extended(season_id)

    # ------------------------------------------------------------------
    # Artwork endpoints
    # ------------------------------------------------------------------

    async def get_artwork(self, artwork_id: int) -> dict:
        """Fetch an artwork base record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_artwork(artwork_id)

    async def get_artwork_extended(self, artwork_id: int) -> dict:
        """Fetch an artwork extended record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_artwork_extended(artwork_id)

    # ------------------------------------------------------------------
    # Episode endpoints
    # ------------------------------------------------------------------

    async def get_episode(self, episode_id: int) -> dict:
        """Fetch an episode base record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_episode(episode_id)

    async def get_episode_extended(self, episode_id: int) -> dict:
        """Fetch an episode extended record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_episode_extended(episode_id)

    # ------------------------------------------------------------------
    # People endpoints
    # ------------------------------------------------------------------

    async def get_person(self, person_id: int) -> dict:
        """Fetch a person base record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_person(person_id)

    async def get_person_extended(self, person_id: int) -> dict:
        """Fetch a person extended record by ID."""
        async with self._rate_limiter:
            return self._tvdb.get_person_extended(person_id)

    # ------------------------------------------------------------------
    # Search endpoint
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        type_: str | None = None,
        year: int | None = None,
        offset: int = 0,
        limit: int = 10,
        primary_language: str | None = None,
    ) -> list:
        """Search TVDB with optional language filtering.

        If ``primary_language`` is not provided, the configured
        ``primary_language`` is used. If neither is set, no language
        filter is applied.
        """
        effective_language = primary_language or self._primary_language
        params: dict[str, object] = {
            "type": type_,
            "year": year,
            "offset": offset,
            "limit": limit,
        }
        if effective_language is not None:
            params["primaryLanguage"] = effective_language
        async with self._rate_limiter:
            return self._tvdb.search(query, **params)
