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


async def tvdb_get_movie(movie_id: int) -> dict[str, Any]:
    """Fetch a movie base record by its numeric TVDB ID.

    Args:
        movie_id: Numeric TVDB movie ID.

    Returns:
        Unfiltered movie base record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_movie(movie_id)


async def tvdb_get_movie_extended(
    movie_id: int,
    include_characters: bool = False,
    include_artworks: bool = False,
    include_trailers: bool = False,
) -> dict[str, Any]:
    """Fetch a movie extended record with optional characters, artworks, and trailers.

    The `characters`, `artworks`, and `trailers` arrays are only included
    when the respective `include_*` parameter is True.

    TIP: Leave include_* parameters as False unless you specifically need
    that data. Including them significantly increases the response size.
    If you only need basic movie info, use tvdb_get_movie instead.

    Args:
        movie_id: Numeric TVDB movie ID.
        include_characters: When True, includes the `characters` array.
            Leave False unless you specifically need character information.
        include_artworks: When True, includes the `artworks` array.
            Leave False unless you specifically need artwork information.
        include_trailers: When True, includes the `trailers` array.
            Leave False unless you specifically need trailer information.

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

    TIP: Use the `type` parameter to narrow results. For a specific show,
    set type="series". For a person, set type="person". The `remote_id`
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
            contain a 3 character country code (e.g. "USA"). Currently only
            used for series and movies. Note: may return empty results.
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

    TIP: Leave include_characters and include_artworks as False unless you
    specifically need that data. Including them significantly increases the
    response size. If you only need basic series info, use tvdb_get_series
    instead of this extended version.

    Args:
        series_id: Numeric TVDB series ID.
        include_characters: When True, includes the `characters` array.
            Leave False unless you specifically need character information.
        include_artworks: When True, includes the `artworks` array.
            Leave False unless you specifically need artwork information.

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

    TIP: Only use this extended version if you need additional season
    details. For basic info, use tvdb_get_season instead.

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

    TIP: Only use this extended version if you need additional artwork
    details. For basic info, use tvdb_get_artwork instead.

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

    TIP: Only use this extended version if you need additional episode
    details. For basic info, use tvdb_get_episode instead.

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

    NOTE: The person_id must be a pure numeric ID (e.g. 327579), not the
    formatted ID returned by search results (e.g. "person-327579"). If you
    get a person ID from tvdb_search, strip the "person-" prefix first.

    Args:
        person_id: Numeric TVDB person ID (e.g. 327579, not "person-327579").

    Returns:
        Unfiltered person base record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_person(person_id)


async def tvdb_get_person_extended(person_id: int) -> dict[str, Any]:
    """Fetch a person extended record by their numeric TVDB ID.

    NOTE: The person_id must be a pure numeric ID (e.g. 327579), not the
    formatted ID returned by search results (e.g. "person-327579"). If you
    get a person ID from tvdb_search, strip the "person-" prefix first.

    TIP: Only use this extended version if you need additional person
    details. For basic info, use tvdb_get_person instead.

    Args:
        person_id: Numeric TVDB person ID (e.g. 327579, not "person-327579").

    Returns:
        Unfiltered person extended record.
    """
    if _client is None:
        raise RuntimeError("init_tools() must be called before using TVDB tools")
    return await _client.get_person_extended(person_id)
