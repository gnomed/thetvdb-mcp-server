"""Unit tests for TvdbClient wrapper."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thetvdb_mcp_server.rate_limiter import AsyncRateLimiter
from thetvdb_mcp_server.tvdb_client import TvdbClient


def make_mock_tvdb():
    """Return a mock TVDB instance with mocked methods.

    The official tvdb_v4_official client uses synchronous HTTP calls via urllib.
    """
    mock_tvdb = MagicMock()
    mock_tvdb.get_series = MagicMock(return_value={"id": 1, "name": "Test Series"})
    mock_tvdb.get_series_episodes = MagicMock(
        return_value={
            "series": {"id": 1, "name": "Test Series"},
            "episodes": [{"id": 100, "number": 1, "seasonNumber": 1}],
        }
    )
    mock_tvdb.search = MagicMock(return_value=[{"tvdb_id": "1", "name": "Test"}])
    return mock_tvdb


@pytest.mark.asyncio
async def test_get_series_calls_tvdb_get_series() -> None:
    """get_series forwards the call to the TVDB client."""
    mock_tvdb = make_mock_tvdb()
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        client = TvdbClient("key", None, AsyncRateLimiter())
        result = await client.get_series(78804)

    mock_tvdb.get_series.assert_called_once_with(78804)
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_get_series_episodes_without_lang() -> None:
    """get_series_episodes without lang does not pass lang to TVDB."""
    mock_tvdb = make_mock_tvdb()
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        client = TvdbClient("key", None, AsyncRateLimiter())
        await client.get_series_episodes(78804, season_type="official")

    _, kwargs = mock_tvdb.get_series_episodes.call_args
    assert kwargs["lang"] is None


@pytest.mark.asyncio
async def test_get_series_episodes_with_explicit_lang() -> None:
    """get_series_episodes with explicit lang passes it to TVDB."""
    mock_tvdb = make_mock_tvdb()
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        client = TvdbClient("key", None, AsyncRateLimiter())
        await client.get_series_episodes(78804, season_type="official", lang="deu")

    _, kwargs = mock_tvdb.get_series_episodes.call_args
    assert kwargs["lang"] == "deu"


@pytest.mark.asyncio
async def test_get_series_episodes_with_primary_language() -> None:
    """get_series_episodes uses primary_language when lang is not provided."""
    mock_tvdb = make_mock_tvdb()
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        client = TvdbClient("key", None, AsyncRateLimiter(), primary_language="eng")
        await client.get_series_episodes(78804, season_type="official")

    _, kwargs = mock_tvdb.get_series_episodes.call_args
    assert kwargs["lang"] == "eng"


@pytest.mark.asyncio
async def test_get_series_episodes_explicit_lang_overrides_primary() -> None:
    """Explicit lang overrides primary_language."""
    mock_tvdb = make_mock_tvdb()
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        client = TvdbClient("key", None, AsyncRateLimiter(), primary_language="eng")
        await client.get_series_episodes(78804, season_type="official", lang="deu")

    _, kwargs = mock_tvdb.get_series_episodes.call_args
    assert kwargs["lang"] == "deu"


@pytest.mark.asyncio
async def test_search_without_primary_language() -> None:
    """search without primary_language does not include it in params."""
    mock_tvdb = make_mock_tvdb()
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        client = TvdbClient("key", None, AsyncRateLimiter())
        await client.search("doctor who", type_="series")

    _, kwargs = mock_tvdb.search.call_args
    assert "primaryLanguage" not in kwargs


@pytest.mark.asyncio
async def test_search_with_primary_language() -> None:
    """search with primary_language includes it in params."""
    mock_tvdb = make_mock_tvdb()
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        client = TvdbClient("key", None, AsyncRateLimiter(), primary_language="eng")
        await client.search("doctor who", type_="series")

    _, kwargs = mock_tvdb.search.call_args
    assert kwargs["primaryLanguage"] == "eng"


@pytest.mark.asyncio
async def test_search_passes_all_params() -> None:
    """search passes all provided params to TVDB."""
    mock_tvdb = make_mock_tvdb()
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        client = TvdbClient("key", None, AsyncRateLimiter())
        await client.search("doctor who", type_="series", year=2005, offset=10, limit=5)

    _, kwargs = mock_tvdb.search.call_args
    assert kwargs["type"] == "series"
    assert kwargs["year"] == 2005
    assert kwargs["offset"] == 10
    assert kwargs["limit"] == 5
