"""TVDB API client wrapper using the official tvdb_v4_official package."""

import logging

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

    def _translate_and_strip(self, record: dict) -> dict:
        """Apply result_language translation and strip overviews/translations fields.

        If result_language is set, replaces `name` with the translation from the
        `translations` map (if available) and `overview` with the translation from
        the `overviews` map (if available). Then removes both maps from the record.

        Handles two TVDB response formats:
        1. Search results: flat maps {"eng": "Name", "deu": "Name"}
        2. Extended endpoints: nested nameTranslations/overviewTranslations arrays

        Args:
            record: A TVDB API response record.

        Returns:
            The modified record with translations applied and maps stripped.
        """
        if self._result_language is None:
            return record

        translations = record.get("translations")
        overviews = record.get("overviews")
        name_translations = record.get("nameTranslations")
        overview_translations = record.get("overviewTranslations")

        _logger.debug(
            "_translate_and_strip called with result_language=%r, "
            "has_translations=%s, has_overviews=%s, has_nameTranslations=%s, "
            "has_overviewTranslations=%s",
            self._result_language,
            translations is not None,
            overviews is not None,
            name_translations is not None,
            overview_translations is not None,
        )

        # Determine format
        if isinstance(translations, dict) and "nameTranslations" in translations:
            # Extended endpoint format (nested)
            name_found = False
            for t in translations["nameTranslations"]:
                if t.get("language") == self._result_language:
                    record["name"] = t["name"]
                    name_found = True
                    break
            _logger.debug(
                "Extended format (nested): name translation %s found for %s",
                "successfully" if name_found else "not",
                self._result_language,
            )

            overview_found = False
            overview_list = translations.get("overviewTranslations")
            if overview_list is not None:
                for o in overview_list:
                    if o.get("language") == self._result_language:
                        record["overview"] = o["overview"]
                        overview_found = True
                        break
            _logger.debug(
                "Extended format (nested): overview translation %s found for %s",
                "successfully" if overview_found else "not",
                self._result_language,
            )

            record.pop("translations", None)
            # Also strip top-level language code arrays if present
            if name_translations is not None:
                record.pop("nameTranslations", None)
            if overview_translations is not None:
                record.pop("overviewTranslations", None)

        elif name_translations is not None or overview_translations is not None:
            # Extended endpoint format (top-level arrays of language codes)
            # These are just lists of available languages, not actual translation data.
            # Strip them out.
            if name_translations is not None:
                _logger.debug(
                    "Extended format (top-level arrays): stripping nameTranslations (%d languages available)",
                    len(name_translations) if isinstance(name_translations, list) else 0,
                )
            if overview_translations is not None:
                _logger.debug(
                    "Extended format (top-level arrays): stripping overviewTranslations (%d languages available)",
                    len(overview_translations) if isinstance(overview_translations, list) else 0,
                )
            record.pop("nameTranslations", None)
            record.pop("overviewTranslations", None)

        else:
            # Search results format (flat maps)
            if isinstance(translations, dict) and self._result_language in translations:
                record["name"] = translations[self._result_language]
                _logger.debug(
                    "Search format: name translation found for %s",
                    self._result_language,
                )
            else:
                _logger.debug(
                    "Search format: no name translation for %s (available: %s)",
                    self._result_language,
                    list(translations.keys()) if isinstance(translations, dict) else None,
                )

            if isinstance(overviews, dict) and self._result_language in overviews:
                record["overview"] = overviews[self._result_language]
                _logger.debug(
                    "Search format: overview translation found for %s",
                    self._result_language,
                )
            else:
                _logger.debug(
                    "Search format: no overview translation for %s",
                    self._result_language,
                )

            record.pop("translations", None)
            record.pop("overviews", None)

        # Filter aliases to result_language (at top level)
        # Search results have aliases as list of strings; extended results have list of dicts
        aliases = record.get("aliases")
        if isinstance(aliases, list) and aliases:
            if isinstance(aliases[0], dict):
                # Extended format: list of {language, name} dicts
                filtered = [a for a in aliases if a.get("language") == self._result_language]
                record["aliases"] = filtered
            # else: search format (list of strings) - keep as-is

        # Filter trailers to result_language
        trailers = record.get("trailers")
        if isinstance(trailers, list) and trailers:
            filtered = [t for t in trailers if t.get("language") == self._result_language]
            record["trailers"] = filtered

        # Strip nameTranslations/overviewTranslations from nested structures
        # Companies (can be a list or object with list values)
        companies = record.get("companies")
        if isinstance(companies, list):
            # Series extended format: list of company objects
            for company in companies:
                if isinstance(company, dict):
                    company.pop("nameTranslations", None)
                    company.pop("overviewTranslations", None)
                    # Filter company aliases (extended format: list of dicts)
                    company_aliases = company.get("aliases")
                    if isinstance(company_aliases, list) and company_aliases:
                        if isinstance(company_aliases[0], dict):
                            company["aliases"] = [
                                a for a in company_aliases if a.get("language") == self._result_language
                            ]
        elif isinstance(companies, dict):
            # Movie extended format: object with list values
            for company_list in companies.values():
                if isinstance(company_list, list):
                    for company in company_list:
                        if isinstance(company, dict):
                            company.pop("nameTranslations", None)
                            company.pop("overviewTranslations", None)
                            # Filter company aliases
                            company_aliases = company.get("aliases")
                            if isinstance(company_aliases, list) and company_aliases:
                                if isinstance(company_aliases[0], dict):
                                    company["aliases"] = [
                                        a for a in company_aliases if a.get("language") == self._result_language
                                    ]

        # Networks (originalNetwork, latestNetwork)
        for field in ["originalNetwork", "latestNetwork"]:
            network = record.get(field)
            if isinstance(network, dict):
                network.pop("nameTranslations", None)
                network.pop("overviewTranslations", None)
                # Filter network aliases (extended format: list of dicts)
                network_aliases = network.get("aliases")
                if isinstance(network_aliases, list) and network_aliases:
                    if isinstance(network_aliases[0], dict):
                        network["aliases"] = [a for a in network_aliases if a.get("language") == self._result_language]

        # Lists
        lists = record.get("lists")
        if isinstance(lists, list):
            for item in lists:
                if isinstance(item, dict):
                    item.pop("nameTranslations", None)
                    item.pop("overviewTranslations", None)
                    # Filter list aliases (extended format: list of dicts)
                    list_aliases = item.get("aliases")
                    if isinstance(list_aliases, list) and list_aliases:
                        if isinstance(list_aliases[0], dict):
                            item["aliases"] = [a for a in list_aliases if a.get("language") == self._result_language]

        # Characters (in movie/series extended)
        characters = record.get("characters")
        if isinstance(characters, list):
            for character in characters:
                if isinstance(character, dict):
                    character.pop("nameTranslations", None)
                    character.pop("overviewTranslations", None)
                    # Filter character aliases
                    char_aliases = character.get("aliases")
                    if isinstance(char_aliases, list) and char_aliases:
                        if isinstance(char_aliases[0], dict):
                            character["aliases"] = [
                                a for a in char_aliases if a.get("language") == self._result_language
                            ]

        # Seasons (nested in get_series_extended)
        seasons = record.get("seasons")
        if isinstance(seasons, list):
            for season in seasons:
                if isinstance(season, dict):
                    season.pop("nameTranslations", None)
                    season.pop("overviewTranslations", None)
                    # Handle companies nested in seasons
                    season_companies = season.get("companies")
                    if isinstance(season_companies, dict):
                        for company_type in season_companies.values():
                            if isinstance(company_type, list):
                                for company in company_type:
                                    if isinstance(company, dict):
                                        company.pop("nameTranslations", None)
                                        company.pop("overviewTranslations", None)
                                        # Filter company aliases
                                        comp_aliases = company.get("aliases")
                                        if isinstance(comp_aliases, list) and comp_aliases:
                                            if isinstance(comp_aliases[0], dict):
                                                company["aliases"] = [
                                                    a
                                                    for a in comp_aliases
                                                    if a.get("language") == self._result_language
                                                ]

        return record

    def _clean_extended_response(
        self,
        record: dict,
        include_lists: str = "all",
        include_tags: bool = True,
        include_content_ratings: bool = True,
        include_remote_ids: bool = True,
        include_seasons: str = "all",
        include_companies: bool = True,
        include_awards: bool = True,
        include_characters: bool = True,
        include_biographies: bool = True,
    ) -> dict:
        """Handle include_* parameters for extended TVDB response records.

        Assumes _translate_and_strip has already been called.

        Args:
            record: A TVDB API response record (already translated/stripped).
            include_lists: "none", "all", or "official" (default: "all")
            include_tags: Whether to include tags array (default: True)
            include_content_ratings: Whether to include contentRatings array (default: True)
            include_remote_ids: Whether to include remoteIds array (default: True)
            include_seasons: "none", "all", or a season type string (default: "all")
            include_companies: Whether to include companies array/map (default: True)
            include_awards: Whether to include awards array (default: True)
            include_characters: Whether to include characters array (default: True)
            include_biographies: Whether to include biographies array (default: True)

        Returns:
            The record with include_* parameters applied.
        """
        # Handle include_lists parameter
        if include_lists == "none":
            record.pop("lists", None)
        elif include_lists == "official":
            lists = record.get("lists")
            if isinstance(lists, list):
                official_lists = [item for item in lists if item.get("isOfficial")]
                record["lists"] = official_lists

        # Handle include_tags parameter
        if not include_tags:
            record.pop("tags", None)

        # Handle include_content_ratings parameter
        if not include_content_ratings:
            record.pop("contentRatings", None)

        # Handle include_remote_ids parameter
        if not include_remote_ids:
            record.pop("remoteIds", None)

        # Handle include_seasons parameter
        if include_seasons == "none":
            record.pop("seasons", None)
        elif include_seasons != "all":
            # Filter to specific season type
            seasons = record.get("seasons")
            if isinstance(seasons, list):
                filtered_seasons = [
                    s
                    for s in seasons
                    if isinstance(s, dict) and s.get("type", {}).get("name", "").lower() == include_seasons.lower()
                ]
                record["seasons"] = filtered_seasons

        # Handle include_companies parameter
        if not include_companies:
            record.pop("companies", None)

        # Handle include_awards parameter
        if not include_awards:
            record.pop("awards", None)

        # Handle include_characters parameter
        if not include_characters:
            record.pop("characters", None)

        # Handle include_biographies parameter
        if not include_biographies:
            record.pop("biographies", None)

        return record

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

        if not short:
            if not include_characters:
                result.pop("characters", None)
            if not include_artworks:
                result.pop("artworks", None)
            if not include_trailers:
                result.pop("trailers", None)

        return self._clean_extended_response(
            result,
            include_lists=include_lists,
            include_tags=include_tags,
            include_content_ratings=include_content_ratings,
            include_remote_ids=include_remote_ids,
            include_companies=include_companies,
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

        if not short:
            if not include_characters:
                result.pop("characters", None)
            if not include_artworks:
                result.pop("artworks", None)

        return self._clean_extended_response(
            result,
            include_lists=include_lists,
            include_tags=include_tags,
            include_content_ratings=include_content_ratings,
            include_remote_ids=include_remote_ids,
            include_seasons=include_seasons,
            include_companies=include_companies,
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

        if self._result_language is not None:
            series = result.get("series")
            if isinstance(series, dict):
                self._translate_and_strip(series)
            episodes = result.get("episodes")
            if isinstance(episodes, list):
                for ep in episodes:
                    if isinstance(ep, dict):
                        self._translate_and_strip(ep)
        return result

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

    async def get_season_extended(self, season_id: int) -> dict:
        """Fetch a season extended record by ID."""
        async with self._rate_limiter:
            result = self._tvdb.get_season_extended(season_id)
        return self._translate_and_strip(result)

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
        async with self._rate_limiter:
            result = self._tvdb.get_artwork_extended(artwork_id)
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
    ) -> dict:
        """Fetch an episode extended record by ID."""
        meta = "translations" if self._result_language is not None else None
        async with self._rate_limiter:
            result = self._tvdb.get_episode_extended(episode_id, meta=meta)
        result = self._translate_and_strip(result)
        return self._clean_extended_response(
            result,
            include_awards=include_awards,
            include_characters=include_characters,
            include_companies=include_companies,
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
    ) -> dict:
        """Fetch a person extended record by ID."""
        meta = "translations" if self._result_language is not None else None
        async with self._rate_limiter:
            result = self._tvdb.get_person_extended(person_id, meta=meta)
        result = self._translate_and_strip(result)
        return self._clean_extended_response(
            result,
            include_awards=include_awards,
            include_characters=include_characters,
            include_biographies=include_biographies,
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

        if self._result_language is not None:
            for record in results:
                if isinstance(record, dict):
                    self._translate_and_strip(record)
        return results
