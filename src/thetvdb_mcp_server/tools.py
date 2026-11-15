"""MCP tool implementations for thetvdb-mcp-server."""

import logging
from typing import Any

from thetvdb_mcp_server.config import AppConfig
from thetvdb_mcp_server.rate_limiter import tvdb_rate_limiter
from thetvdb_mcp_server.tvdb_client import TvdbClient

_logger = logging.getLogger(__name__)

_client: TvdbClient | None = None


def init_tools(config: AppConfig) -> None:
    """Initialise the shared TVDB client from application configuration.

    Must be called once at startup before any TVDB tool is invoked.

    Args:
        config: Loaded application configuration.
    """
    global _client
    _logger.debug(
        "Initializing TvdbClient with result_language=%r",
        config.tvdb.result_language,
    )
    _client = TvdbClient(
        api_key=config.tvdb.api_key,
        pin=config.tvdb.pin,
        rate_limiter=tvdb_rate_limiter,
        result_language=config.tvdb.result_language,
    )


# ======================================================================
# Movie tools
# ======================================================================


async def tvdb_get_movie(
    movie_id: int,
    include_characters: bool = False,
    include_artworks: bool = False,
    include_trailers: bool = False,
    include_lists: str = "none",
    include_tags: bool = False,
    include_content_ratings: bool = False,
    include_remote_ids: bool = False,
    include_companies: bool = False,
    include_awards: bool = False,
    include_releases: bool = False,
) -> dict[str, Any]:
    """Fetch a movie extended record with optional characters, artworks, and trailers.

    The `characters`, `artworks`, `trailers`, `lists`, `tags`, `contentRatings`,
    `remoteIds`, `companies`, `awards`, and `releases` arrays are only included
    when the respective `include_*` parameter is True (or set to a non-"none" value).

    TIP: The include_* options default to false and should be omitted to keep
    responses small. Only set them to true if you need the additional data.

    Args:
        movie_id: Numeric TVDB movie ID.
        include_characters: When True, includes the `characters` array.
        include_artworks: When True, includes the `artworks` array.
        include_trailers: When True, includes the `trailers` array.
        include_lists: Whether to include the `lists` array. One of:
            "none" (default), "all", or "official" (only official lists).
        include_tags: When True, includes the `tags` array.
        include_content_ratings: When True, includes the `contentRatings` array.
        include_remote_ids: When True, includes the `remoteIds` array.
        include_companies: When True, includes the `companies` map.
        include_awards: When True, includes the `awards` array.
        include_releases: When True, includes the `releases` array.

    Returns:
        Movie extended record with requested arrays.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_movie_extended(
        movie_id,
        include_characters=include_characters,
        include_artworks=include_artworks,
        include_trailers=include_trailers,
        include_lists=include_lists,
        include_tags=include_tags,
        include_content_ratings=include_content_ratings,
        include_remote_ids=include_remote_ids,
        include_companies=include_companies,
        include_awards=include_awards,
        include_releases=include_releases,
    )


async def tvdb_get_movie_by_slug(slug: str) -> dict[str, Any]:
    """Fetch a movie record by its slug.

    Args:
        slug: Movie slug, e.g. "the-lord-of-the-rings-the-fellowship-of-the-ring".

    Returns:
        Unfiltered movie record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_movie_by_slug(slug)


# ======================================================================
# Search and episodes tools
# ======================================================================


async def tvdb_search(
    query: str,
    type: str | None = None,
    year: int | None = None,
    offset: int = 0,
    limit: int = 10,
    primary_language: str | None = None,
    country: str | None = None,
    director: str | None = None,
    remote_id: str | None = None,
) -> list[dict[str, Any]]:
    """Search TVDB for series, movies, people, and more.

    Searches by title, alias, and translation. Returns up to `limit`
    results (default 10).

    NOTE: The TVDB search index includes series, movies, people, and
    companies. The `type` parameter only reliably filters these types.
    type="episode", type="season", and type="artwork" will return empty
    results.

    TIP: Use the `type` parameter to narrow results. The `remote_id`
    parameter (e.g. IMDB ID) is the most precise search method.

    Args:
        query: Search text to match against titles, aliases, and translations.
        type: Filter by entity type. One of: series, movie, person, company.
            Omit to search all types. Other values (episode, season, artwork,
            etc.) are accepted but return empty results.
        year: Restrict results to items first aired or released in this year.
            Note: may broaden results rather than filter.
        offset: Number of results to skip (pagination).
        limit: Maximum number of results to return. Defaults to 10.
        primary_language: 3-character ISO 639-2 language code (e.g. "eng").
            Note: may broaden results rather than filter.
        country: Restrict results to a specific country of origin. Should
            contain a 3 character country code (e.g. "USA"). Note: may return
            empty results.
        director: Restrict results to a specific director. Generally only
            used for movies. Should include the full name, e.g. "Steven Spielberg".
        remote_id: Search for a specific remote ID. Allows searching by
            IMDB ID, EIDR, or other remote identifiers.

    Returns:
        List of unfiltered search result objects.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.search(
        query=query,
        type_=type,
        year=year,
        offset=offset,
        limit=limit,
        primary_language=primary_language,
        country=country,
        director=director,
        remote_id=remote_id,
    )


async def tvdb_get_series_episodes(
    series_id: int,
    season_type: str | None = None,
    page: int = 0,
    lang: str | None = None,
) -> dict[str, Any]:
    """Fetch episodes for a series.

    Returns ALL episodes for the series. To get a specific season's
    episodes, filter the results client-side by seasonNumber.

    Args:
        series_id: Numeric TVDB series ID.
        season_type: Season ordering. Omit to use TVDB's default ordering.
            Valid values: default, aired, dvd, digital, streaming, absolute,
            alternate, regional. Only specify if you need a non-default
            ordering — "default" works reliably, but other values (aired,
            streaming, digital, alternate) may return empty results for
            some series.
        page: Page number for pagination (default 0).
        lang: 3-character ISO 639-2 language code (e.g. "eng").

    Returns:
        Episodes response containing `series` and `episodes` keys.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_series_episodes(
        series_id=series_id,
        season_type=season_type,
        page=page,
        lang=lang,
    )


# ======================================================================
# Series tools
# ======================================================================


async def tvdb_get_series(
    series_id: int,
    include_characters: bool = False,
    include_artworks: bool = False,
    include_lists: str = "none",
    include_tags: bool = False,
    include_content_ratings: bool = False,
    include_remote_ids: bool = False,
    include_seasons: str = "none",
    include_companies: bool = False,
    include_trailers: bool = False,
) -> dict[str, Any]:
    """Fetch a series extended record with optional arrays.

    The `characters`, `artworks`, `lists`, `tags`, `contentRatings`, `remoteIds`,
    `companies`, and `trailers` arrays are only included when the respective
    `include_*` parameter is True (or set to a non-"none" value).

    TIP: The include_* options default to false and should be omitted to keep
    responses small. Only set them to true if you need the additional data.

    Args:
        series_id: Numeric TVDB series ID.
        include_characters: When True, includes the `characters` array.
        include_artworks: When True, includes the `artworks` array.
        include_lists: Whether to include the `lists` array. One of:
            "none" (default), "all", or "official" (only official lists).
        include_tags: When True, includes the `tags` array.
        include_content_ratings: When True, includes the `contentRatings` array.
        include_remote_ids: When True, includes the `remoteIds` array.
        include_seasons: Whether to include the `seasons` array. One of:
            "none" (default), "all", or a season type string (e.g. "Aired Order").
        include_companies: When True, includes the `companies` array.
        include_trailers: When True, includes the `trailers` array.

    Returns:
        Series extended record with requested arrays.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_series_extended(
        series_id,
        include_characters=include_characters,
        include_artworks=include_artworks,
        include_lists=include_lists,
        include_tags=include_tags,
        include_content_ratings=include_content_ratings,
        include_remote_ids=include_remote_ids,
        include_seasons=include_seasons,
        include_companies=include_companies,
        include_trailers=include_trailers,
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


async def tvdb_get_season(
    season_id: int,
    include_artworks: bool = False,
    include_companies: bool = False,
    include_episodes: bool = False,
    include_trailers: bool = False,
    include_tags: bool = False,
) -> dict[str, Any]:
    """Fetch a season extended record by its numeric TVDB ID.

    The `artworks`, `companies`, `episodes`, `trailers`, and `tags` arrays are
    only included when the respective `include_*` parameter is True.

    TIP: The include_* options default to false and should be omitted to keep
    responses small. Only set them to true if you need the additional data.

    Args:
        season_id: Numeric TVDB season ID.
        include_artworks: When True, includes the `artworks` array.
        include_companies: When True, includes the `companies` array.
        include_episodes: When True, includes the `episodes` array.
        include_trailers: When True, includes the `trailers` array.
        include_tags: When True, includes the `tags` array.

    Returns:
        Season extended record with requested arrays.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_season_extended(
        season_id,
        include_artworks=include_artworks,
        include_companies=include_companies,
        include_episodes=include_episodes,
        include_trailers=include_trailers,
        include_tags=include_tags,
    )


# ======================================================================
# Artwork tools
# ======================================================================


async def tvdb_get_artwork(artwork_id: int) -> dict[str, Any]:
    """Fetch an artwork extended record by its numeric TVDB ID.

    Returns the artwork record with its associated arrays.

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


async def tvdb_get_episode(
    episode_id: int,
    include_awards: bool = False,
    include_characters: bool = False,
    include_companies: bool = False,
    include_seasons: bool = False,
    include_content_ratings: bool = False,
    include_remote_ids: bool = False,
    include_tags: bool = False,
    include_trailers: bool = False,
) -> dict[str, Any]:
    """Fetch an episode extended record by its numeric TVDB ID.

    The `awards`, `characters`, `companies`, `seasons`, `contentRatings`,
    `remoteIds`, `tags`, and `trailers` arrays are only included when the
    respective `include_*` parameter is True.

    TIP: The include_* options default to false and should be omitted to keep
    responses small. Only set them to true if you need the additional data.

    Args:
        episode_id: Numeric TVDB episode ID.
        include_awards: When True, includes the `awards` array.
        include_characters: When True, includes the `characters` array.
        include_companies: When True, includes the `companies` array.
        include_seasons: When True, includes the `seasons` array.
        include_content_ratings: When True, includes the `contentRatings` array.
        include_remote_ids: When True, includes the `remoteIds` array.
        include_tags: When True, includes the `tags` array.
        include_trailers: When True, includes the `trailers` array.

    Returns:
        Episode extended record with requested arrays.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_episode_extended(
        episode_id,
        include_awards=include_awards,
        include_characters=include_characters,
        include_companies=include_companies,
        include_seasons=include_seasons,
        include_content_ratings=include_content_ratings,
        include_remote_ids=include_remote_ids,
        include_tags=include_tags,
        include_trailers=include_trailers,
    )


# ======================================================================
# Person tools
# ======================================================================


async def tvdb_get_person(
    person_id: int,
    include_awards: bool = False,
    include_characters: bool = False,
    include_biographies: bool = False,
    include_remote_ids: bool = False,
    include_tags: bool = False,
) -> dict[str, Any]:
    """Fetch a person extended record by their numeric TVDB ID.

    NOTE: The person_id must be a pure numeric ID (e.g. 327579), not the
    formatted ID returned by search results (e.g. "person-327579"). If you
    get a person ID from tvdb_search, strip the "person-" prefix first.

    The `awards`, `characters`, `biographies`, `remoteIds`, and `tags` arrays
    are only included when the respective `include_*` parameter is True.

    TIP: The include_* options default to false and should be omitted to keep
    responses small. Only set them to true if you need the additional data.

    Args:
        person_id: Numeric TVDB person ID (e.g. 327579, not "person-327579").
        include_awards: When True, includes the `awards` array.
        include_characters: When True, includes the `characters` array.
        include_biographies: When True, includes the `biographies` array.
        include_remote_ids: When True, includes the `remoteIds` array.
        include_tags: When True, includes the `tags` array.

    Returns:
        Person extended record with requested arrays.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_person_extended(
        person_id,
        include_awards=include_awards,
        include_characters=include_characters,
        include_biographies=include_biographies,
        include_remote_ids=include_remote_ids,
        include_tags=include_tags,
    )
