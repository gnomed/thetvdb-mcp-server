"""TVDB API client wrapper using the official tvdb_v4_official package."""

import logging
from typing import Any

import tvdb_v4_official

from thetvdb_mcp_server.rate_limiter import AsyncRateLimiter

_logger = logging.getLogger(__name__)


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
    """

    def __init__(
        self,
        api_key: str,
        pin: str | None,
        rate_limiter: AsyncRateLimiter,
        result_language: str | None = None,
    ) -> None:
        self._tvdb = tvdb_v4_official.TVDB(api_key, pin or "")
        self._rate_limiter = rate_limiter
        self._result_language = result_language

    def _translate_and_strip(self, data: Any) -> Any:
        """Recursively walk the JSON tree, translating/normalizing every record.

        If result_language is not set, only normalizes field names.
        """
        if isinstance(data, dict):
            self._normalize_and_translate_record(data)
            for key in data:
                data[key] = self._translate_and_strip(data[key])
            return data
        if isinstance(data, list):
            return [self._translate_and_strip(item) for item in data]
        return data

    def _normalize_and_translate_record(self, record: dict) -> None:
        """Normalize field names and apply translation to a single record dict."""
        # --- Normalization (always applied) ---

        # tagOptions -> tags (same concept/structure, different key per endpoint)
        if "tagOptions" in record and "tags" not in record:
            record["tags"] = record.pop("tagOptions")

        # artwork -> artworks (season uses singular, others use plural)
        if "artwork" in record and "artworks" not in record:
            record["artworks"] = record.pop("artwork")

        # --- Translation (only if result_language is set) ---
        if self._result_language is None:
            return

        lang = self._result_language

        # translations: nested {nameTranslations:[...], overviewTranslations:[...]}
        #               OR flat {eng:"Name", deu:"Name"}
        translations = record.get("translations")
        if isinstance(translations, dict):
            if "nameTranslations" in translations:
                self._pick_translation(record, "name", translations.get("nameTranslations") or [], "name")
                self._pick_translation(record, "overview", translations.get("overviewTranslations") or [], "overview")
            elif lang in translations:
                record["name"] = translations[lang]
            record.pop("translations", None)

        # overviews: flat {eng:"Overview", deu:"Overview"}
        overviews = record.get("overviews")
        if isinstance(overviews, dict):
            if lang in overviews:
                record["overview"] = overviews[lang]
            record.pop("overviews", None)

        # Strip language-code-only arrays (lists of available languages, no data)
        record.pop("nameTranslations", None)
        record.pop("overviewTranslations", None)

        # Filter language-specific list fields to result_language
        for field in ("aliases", "trailers"):
            items = record.get(field)
            if isinstance(items, list) and items and isinstance(items[0], dict):
                record[field] = [i for i in items if i.get("language") == lang]

    def _pick_translation(self, record: dict, field: str, translations: list, value_key: str) -> None:
        """Set record[field] from the first translation matching result_language."""
        for t in translations:
            if isinstance(t, dict) and t.get("language") == self._result_language:
                record[field] = t[value_key]
                return

    def _apply_include_filters(self, data: Any, **filters) -> Any:
        """Recursively apply include_* filters to nested TVDB response data.

        Works on any JSON structure (dicts, lists, primitives). Boolean filters
        pop the field when False; string filters handle "none"/"all"/"official"
        or season type strings. Filters that don't apply to a given level are
        no-ops (pop with default None).

        Assumes _translate_and_strip has already been called.
        """
        include_tags = filters.get("include_tags", True)
        include_content_ratings = filters.get("include_content_ratings", True)
        include_remote_ids = filters.get("include_remote_ids", True)
        include_companies = filters.get("include_companies", True)
        include_awards = filters.get("include_awards", True)
        include_characters = filters.get("include_characters", True)
        include_biographies = filters.get("include_biographies", True)
        include_artworks = filters.get("include_artworks", True)
        include_trailers = filters.get("include_trailers", True)
        include_episodes = filters.get("include_episodes", True)
        include_releases = filters.get("include_releases", True)
        include_lists = filters.get("include_lists", "all")
        include_seasons = filters.get("include_seasons", "all")

        if isinstance(data, dict):
            # Boolean filters
            for field, include in [
                ("tags", include_tags),
                ("contentRatings", include_content_ratings),
                ("remoteIds", include_remote_ids),
                ("companies", include_companies),
                ("awards", include_awards),
                ("characters", include_characters),
                ("biographies", include_biographies),
                ("artworks", include_artworks),
                ("trailers", include_trailers),
                ("episodes", include_episodes),
                ("releases", include_releases),
            ]:
                if not include:
                    data.pop(field, None)

            # Lists: "none", "all", or "official"
            if include_lists == "none":
                data.pop("lists", None)
            elif include_lists == "official":
                lists = data.get("lists")
                if isinstance(lists, list):
                    data["lists"] = [item for item in lists if item.get("isOfficial")]

            # Seasons: "none", "all", or season type string
            if include_seasons == "none":
                data.pop("seasons", None)
            elif include_seasons != "all":
                seasons = data.get("seasons")
                if isinstance(seasons, list):
                    data["seasons"] = [
                        s
                        for s in seasons
                        if isinstance(s, dict) and s.get("type", {}).get("name", "").lower() == include_seasons.lower()
                    ]

            # Recurse into remaining fields
            for key in data:
                data[key] = self._apply_include_filters(data[key], **filters)

        elif isinstance(data, list):
            return [self._apply_include_filters(item, **filters) for item in data]

        return data

    # ------------------------------------------------------------------
    # Movie endpoints
    # ------------------------------------------------------------------

    async def get_movie(self, movie_id: int) -> dict:
        """Fetch a movie base record by ID."""
        async with self._rate_limiter:
            result = self._tvdb.get_movie(movie_id)
        return self._translate_and_strip(result)

    async def get_movie_extended(
        self,
        movie_id: int,
        include_characters: bool = False,
        include_artworks: bool = False,
        include_trailers: bool = False,
        include_lists: str = "none",
        include_tags: bool = False,
        include_content_ratings: bool = False,
        include_remote_ids: bool = True,
        include_companies: bool = True,
        include_awards: bool = True,
        include_releases: bool = True,
    ) -> dict:
        """Fetch a movie extended record with optional arrays.

        The TVDB API only supports an all-or-nothing ``short`` parameter.
        To provide granular control, this method calls the API with
        ``short=True`` when all ``include_*`` parameters are ``False``,
        and with ``short=False`` otherwise, stripping any unrequested
        arrays from the response.
        """
        short = not (include_characters or include_artworks or include_trailers)
        meta = "translations" if self._result_language is not None else None
        async with self._rate_limiter:
            result = self._tvdb.get_movie_extended(movie_id, short=short, meta=meta)

        result = self._translate_and_strip(result)

        return self._apply_include_filters(
            result,
            include_tags=include_tags,
            include_content_ratings=include_content_ratings,
            include_remote_ids=include_remote_ids,
            include_companies=include_companies,
            include_awards=include_awards,
            include_characters=include_characters,
            include_biographies=False,
            include_artworks=include_artworks,
            include_trailers=include_trailers,
            include_episodes=False,
            include_lists=include_lists,
            include_seasons="none",
            include_releases=include_releases,
        )

    async def get_movie_by_slug(self, slug: str) -> dict:
        """Fetch a movie record by its slug."""
        async with self._rate_limiter:
            result = self._tvdb.get_movie_by_slug(slug)
        return self._translate_and_strip(result)

    # ------------------------------------------------------------------
    # Series endpoints
    # ------------------------------------------------------------------

    async def get_series(self, series_id: int) -> dict:
        """Fetch a series base record by ID."""
        async with self._rate_limiter:
            result = self._tvdb.get_series(series_id)
        return self._translate_and_strip(result)

    async def get_series_extended(
        self,
        series_id: int,
        include_characters: bool = False,
        include_artworks: bool = False,
        include_lists: str = "none",
        include_tags: bool = False,
        include_content_ratings: bool = False,
        include_remote_ids: bool = True,
        include_seasons: str = "all",
        include_companies: bool = True,
        include_trailers: bool = False,
    ) -> dict:
        """Fetch a series extended record with optional arrays.

        The TVDB API only supports an all-or-nothing ``short`` parameter.
        To provide granular control, this method calls the API with
        ``short=True`` when both ``include_characters`` and ``include_artworks``
        are ``False``, and with ``short=False`` otherwise, stripping any
        unrequested arrays from the response.
        """
        short = not (include_characters or include_artworks)
        meta = "translations" if self._result_language is not None else None
        async with self._rate_limiter:
            result = self._tvdb.get_series_extended(series_id, short=short, meta=meta)

        result = self._translate_and_strip(result)

        return self._apply_include_filters(
            result,
            include_tags=include_tags,
            include_content_ratings=include_content_ratings,
            include_remote_ids=include_remote_ids,
            include_companies=include_companies,
            include_awards=False,
            include_characters=include_characters,
            include_biographies=False,
            include_artworks=include_artworks,
            include_trailers=include_trailers,
            include_episodes=False,
            include_lists=include_lists,
            include_seasons=include_seasons,
        )

    async def get_series_episodes(
        self,
        series_id: int,
        season_type: str | None = None,
        page: int = 0,
        lang: str | None = None,
    ) -> dict:
        """Fetch episodes for a series by season type.

        If season_type is not specified, the TVDB library uses "default".
        Note: The TVDB Python library does not support filtering by season
        or episode number. To get a specific season's episodes, filter the
        results client-side.
        """
        params: dict[str, object] = {
            "page": page,
            "lang": lang,
        }
        if season_type is not None:
            params["season_type"] = season_type
        async with self._rate_limiter:
            result = self._tvdb.get_series_episodes(series_id, **params)

        return self._translate_and_strip(result)

    async def get_series_by_slug(self, slug: str) -> dict:
        """Fetch a series record by its slug."""
        async with self._rate_limiter:
            result = self._tvdb.get_series_by_slug(slug)
        return self._translate_and_strip(result)

    # ------------------------------------------------------------------
    # Season endpoints
    # ------------------------------------------------------------------

    async def get_season(self, season_id: int) -> dict:
        """Fetch a season base record by ID."""
        async with self._rate_limiter:
            result = self._tvdb.get_season(season_id)
        return self._translate_and_strip(result)

    async def get_season_extended(
        self,
        season_id: int,
        include_artworks: bool = False,
        include_companies: bool = True,
        include_episodes: bool = True,
        include_trailers: bool = False,
        include_tags: bool = True,
    ) -> dict:
        """Fetch a season extended record by ID."""
        meta = "translations" if self._result_language is not None else None
        async with self._rate_limiter:
            result = self._tvdb.get_season_extended(season_id, meta=meta)

        result = self._translate_and_strip(result)

        return self._apply_include_filters(
            result,
            include_tags=include_tags,
            include_content_ratings=False,
            include_remote_ids=False,
            include_companies=include_companies,
            include_awards=False,
            include_characters=False,
            include_biographies=False,
            include_artworks=include_artworks,
            include_trailers=include_trailers,
            include_episodes=include_episodes,
            include_lists="none",
            include_seasons="none",
        )

    # ------------------------------------------------------------------
    # Artwork endpoints
    # ------------------------------------------------------------------

    async def get_artwork(self, artwork_id: int) -> dict:
        """Fetch an artwork base record by ID."""
        async with self._rate_limiter:
            result = self._tvdb.get_artwork(artwork_id)
        return self._translate_and_strip(result)

    async def get_artwork_extended(self, artwork_id: int) -> dict:
        """Fetch an artwork extended record by ID."""
        meta = "translations" if self._result_language is not None else None
        async with self._rate_limiter:
            result = self._tvdb.get_artwork_extended(artwork_id, meta=meta)
        return self._translate_and_strip(result)

    # ------------------------------------------------------------------
    # Episode endpoints
    # ------------------------------------------------------------------

    async def get_episode(self, episode_id: int) -> dict:
        """Fetch an episode base record by ID."""
        async with self._rate_limiter:
            result = self._tvdb.get_episode(episode_id)
        return self._translate_and_strip(result)

    async def get_episode_extended(
        self,
        episode_id: int,
        include_awards: bool = True,
        include_characters: bool = True,
        include_companies: bool = True,
        include_seasons: bool = True,
        include_content_ratings: bool = False,
        include_remote_ids: bool = True,
        include_tags: bool = True,
        include_trailers: bool = False,
    ) -> dict:
        """Fetch an episode extended record by ID."""
        meta = "translations" if self._result_language is not None else None
        async with self._rate_limiter:
            result = self._tvdb.get_episode_extended(episode_id, meta=meta)

        result = self._translate_and_strip(result)

        return self._apply_include_filters(
            result,
            include_tags=include_tags,
            include_content_ratings=include_content_ratings,
            include_remote_ids=include_remote_ids,
            include_companies=include_companies,
            include_awards=include_awards,
            include_characters=include_characters,
            include_biographies=False,
            include_artworks=False,
            include_trailers=include_trailers,
            include_episodes=False,
            include_lists="none",
            include_seasons="all" if include_seasons else "none",
        )

    # ------------------------------------------------------------------
    # People endpoints
    # ------------------------------------------------------------------

    async def get_person(self, person_id: int) -> dict:
        """Fetch a person base record by ID."""
        async with self._rate_limiter:
            result = self._tvdb.get_person(person_id)
        return self._translate_and_strip(result)

    async def get_person_extended(
        self,
        person_id: int,
        include_awards: bool = True,
        include_characters: bool = True,
        include_biographies: bool = True,
        include_remote_ids: bool = True,
        include_tags: bool = True,
    ) -> dict:
        """Fetch a person extended record by ID."""
        meta = "translations" if self._result_language is not None else None
        async with self._rate_limiter:
            result = self._tvdb.get_person_extended(person_id, meta=meta)

        result = self._translate_and_strip(result)

        return self._apply_include_filters(
            result,
            include_tags=include_tags,
            include_content_ratings=False,
            include_remote_ids=include_remote_ids,
            include_companies=False,
            include_awards=include_awards,
            include_characters=include_characters,
            include_biographies=include_biographies,
            include_artworks=False,
            include_trailers=False,
            include_episodes=False,
            include_lists="none",
            include_seasons="none",
        )

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
        country: str | None = None,
        director: str | None = None,
        remote_id: str | None = None,
    ) -> list:
        """Search TVDB with optional filtering parameters."""
        params: dict[str, object] = {
            "type": type_,
            "year": year,
            "offset": offset,
            "limit": limit,
        }
        if primary_language is not None:
            params["primaryLanguage"] = primary_language
        if country is not None:
            params["country"] = country
        if director is not None:
            params["director"] = director
        if remote_id is not None:
            params["remote_id"] = remote_id
        async with self._rate_limiter:
            results = self._tvdb.search(query, **params)

        return self._translate_and_strip(results)
