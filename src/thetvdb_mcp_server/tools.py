"""MCP tool implementations for thetvdb-mcp-server."""

from typing import Any

from thetvdb_mcp_server.config import AppConfig
from thetvdb_mcp_server.rate_limiter import tvdb_rate_limiter
from thetvdb_mcp_server.tvdb_client import TvdbClient

_client: TvdbClient | None = None


def init_tools(config: AppConfig) -> None:
    """Initialise the shared TVDB client from application configuration.

    Must be called once at startup before any TVDB tool is invoked.

    Args:
        config: Loaded application configuration.
    """
    global _client
    _client = TvdbClient(
        api_key=config.tvdb.api_key,
        pin=config.tvdb.pin,
        rate_limiter=tvdb_rate_limiter,
        primary_language=config.tvdb.primary_language,
    )


# ======================================================================
# Private core implementations for dual-variant tools
# ======================================================================


async def _search_impl(
    query: str,
    type_: str | None,
    year: int | None,
    offset: int,
    limit: int,
    primary_language: str | None,
) -> list[dict[str, Any]]:
    """Core search implementation shared by both language variants."""
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.search(
        query=query,
        type_=type_,
        year=year,
        offset=offset,
        limit=limit,
        primary_language=primary_language,
    )


async def _get_series_episodes_impl(
    series_id: int,
    season_type: str,
    page: int,
    lang: str | None,
) -> dict[str, Any]:
    """Core implementation for fetching series episodes shared by both language variants."""
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_series_episodes(
        series_id=series_id,
        season_type=season_type,
        page=page,
        lang=lang,
    )


# ======================================================================
# tvdb_search — two variants depending on primary_language config
# ======================================================================


async def tvdb_search_with_lang(
    query: str,
    type: str | None = None,
    year: int | None = None,
    offset: int = 0,
    limit: int = 10,
    primary_language: str | None = None,
) -> list[dict[str, Any]]:
    """Search TVDB for series, movies, people, episodes, and more.

    Searches for series, movies, people, episodes, etc. by title, alias,
    and translation. Returns up to `limit` results (default 10).

    Args:
        query: Search text to match against titles, aliases, and translations.
        type: Filter by entity type. One of: series, movie, person, episode,
            artwork, award, awardCategory, company, country, genre, language,
            sourceType, peopleType, season, seasonType, tag, user. Omit to
            search all types.
        year: Restrict results to items first aired or released in this year.
        offset: Number of results to skip (pagination).
        limit: Maximum number of results to return. Defaults to 10.
        primary_language: 3-character ISO 639-2 language code (e.g. "eng").

    Returns:
        List of unfiltered search result objects.
    """
    return await _search_impl(
        query=query,
        type_=type,
        year=year,
        offset=offset,
        limit=limit,
        primary_language=primary_language,
    )


async def tvdb_search_without_lang(
    query: str,
    type: str | None = None,
    year: int | None = None,
    offset: int = 0,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search TVDB for series, movies, people, episodes, and more.

    Searches for series, movies, people, episodes, etc. by title, alias,
    and translation. Uses the server's configured primary language.
    Returns up to `limit` results (default 10).

    Args:
        query: Search text to match against titles, aliases, and translations.
        type: Filter by entity type. One of: series, movie, person, episode,
            artwork, award, awardCategory, company, country, genre, language,
            sourceType, peopleType, season, seasonType, tag, user. Omit to
            search all types.
        year: Restrict results to items first aired or released in this year.
        offset: Number of results to skip (pagination).
        limit: Maximum number of results to return. Defaults to 10.

    Returns:
        List of unfiltered search result objects.
    """
    return await _search_impl(
        query=query,
        type_=type,
        year=year,
        offset=offset,
        limit=limit,
        primary_language=None,
    )


# ======================================================================
# tvdb_get_series_episodes — two variants depending on primary_language config
# ======================================================================


async def tvdb_get_series_episodes_with_lang(
    series_id: int,
    season_type: str,
    page: int = 0,
    lang: str | None = None,
) -> dict[str, Any]:
    """Fetch all episodes for a series by season ordering type.

    Valid season_type values: default, aired, dvd, digital, streaming,
    absolute, alternate, regional.

    Args:
        series_id: Numeric TVDB series ID.
        season_type: Season ordering. Valid values: default, aired, dvd,
            digital, streaming, absolute, alternate, regional.
        page: Page number for pagination.
        lang: 3-character ISO 639-2 language code (e.g. "eng").

    Returns:
        Unfiltered episodes response containing `series` and `episodes` keys.
    """
    return await _get_series_episodes_impl(
        series_id=series_id,
        season_type=season_type,
        page=page,
        lang=lang,
    )


async def tvdb_get_series_episodes_without_lang(
    series_id: int,
    season_type: str,
    page: int = 0,
) -> dict[str, Any]:
    """Fetch all episodes for a series by season ordering type.

    Uses the server's configured primary language. Valid season_type
    values: default, aired, dvd, digital, streaming, absolute, alternate,
    regional.

    Args:
        series_id: Numeric TVDB series ID.
        season_type: Season ordering. Valid values: default, aired, dvd,
            digital, streaming, absolute, alternate, regional.
        page: Page number for pagination.

    Returns:
        Unfiltered episodes response containing `series` and `episodes` keys.
    """
    return await _get_series_episodes_impl(
        series_id=series_id,
        season_type=season_type,
        page=page,
        lang=None,
    )


# ======================================================================
# Series tools
# ======================================================================


async def tvdb_get_series(series_id: int) -> dict[str, Any]:
    """Fetch a series base record by its numeric TVDB ID.

    Args:
        series_id: Numeric TVDB series ID.

    Returns:
        Unfiltered series base record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_series(series_id)


async def tvdb_get_series_extended(
    series_id: int,
    include_characters: bool = False,
    include_artworks: bool = False,
) -> dict[str, Any]:
    """Fetch a series extended record with optional characters and artworks.

    The `characters` and `artworks` arrays are only included when the
    respective `include_*` parameter is True.

    Args:
        series_id: Numeric TVDB series ID.
        include_characters: When True, includes the `characters` array.
        include_artworks: When True, includes the `artworks` array.

    Returns:
        Series extended record with requested arrays.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_series_extended(
        series_id,
        include_characters=include_characters,
        include_artworks=include_artworks,
    )


async def tvdb_get_series_by_slug(slug: str) -> dict[str, Any]:
    """Fetch a series record by its slug.

    Args:
        slug: Series slug, e.g. "doctor-who".

    Returns:
        Unfiltered series record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_series_by_slug(slug)


# ======================================================================
# Season tools
# ======================================================================


async def tvdb_get_season(season_id: int) -> dict[str, Any]:
    """Fetch a season base record by its numeric TVDB ID.

    Args:
        season_id: Numeric TVDB season ID.

    Returns:
        Unfiltered season base record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_season(season_id)


async def tvdb_get_season_extended(season_id: int) -> dict[str, Any]:
    """Fetch a season extended record by its numeric TVDB ID.

    Args:
        season_id: Numeric TVDB season ID.

    Returns:
        Unfiltered season extended record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_season_extended(season_id)


# ======================================================================
# Artwork tools
# ======================================================================


async def tvdb_get_artwork(artwork_id: int) -> dict[str, Any]:
    """Fetch an artwork base record by its numeric TVDB ID.

    Args:
        artwork_id: Numeric TVDB artwork ID.

    Returns:
        Unfiltered artwork base record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_artwork(artwork_id)


async def tvdb_get_artwork_extended(artwork_id: int) -> dict[str, Any]:
    """Fetch an artwork extended record by its numeric TVDB ID.

    Args:
        artwork_id: Numeric TVDB artwork ID.

    Returns:
        Unfiltered artwork extended record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_artwork_extended(artwork_id)


# ======================================================================
# Episode tools
# ======================================================================


async def tvdb_get_episode(episode_id: int) -> dict[str, Any]:
    """Fetch an episode base record by its numeric TVDB ID.

    Args:
        episode_id: Numeric TVDB episode ID.

    Returns:
        Unfiltered episode base record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_episode(episode_id)


async def tvdb_get_episode_extended(episode_id: int) -> dict[str, Any]:
    """Fetch an episode extended record by its numeric TVDB ID.

    Args:
        episode_id: Numeric TVDB episode ID.

    Returns:
        Unfiltered episode extended record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_episode_extended(episode_id)


# ======================================================================
# Person tools
# ======================================================================


async def tvdb_get_person(person_id: int) -> dict[str, Any]:
    """Fetch a person base record by their numeric TVDB ID.

    Args:
        person_id: Numeric TVDB person ID.

    Returns:
        Unfiltered person base record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_person(person_id)


async def tvdb_get_person_extended(person_id: int) -> dict[str, Any]:
    """Fetch a person extended record by their numeric TVDB ID.

    Args:
        person_id: Numeric TVDB person ID.

    Returns:
        Unfiltered person extended record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_person_extended(person_id)
