"""Integration tests for caching behavior in TvdbClient."""

from unittest.mock import MagicMock, patch

import pytest

from thetvdb_mcp_server.cache import tvdb_cache
from thetvdb_mcp_server.rate_limiter import AsyncRateLimiter
from thetvdb_mcp_server.tvdb_client import TvdbClient


@pytest.fixture
def mock_tvdb():
    """Mock TVDB instance."""
    mock = MagicMock()
    mock.get_series_extended = MagicMock(
        return_value={
            "id": 1,
            "name": "Test Series",
            "characters": [{"id": 10, "name": "Character 1"}],
            "artworks": [{"id": 20, "name": "Poster 1"}],
        }
    )
    mock.get_movie_extended = MagicMock(
        return_value={
            "id": 1,
            "name": "Test Movie",
            "characters": [{"id": 10, "name": "Character 1"}],
            "artworks": [{"id": 20, "name": "Poster 1"}],
            "trailers": [{"id": 30, "name": "Trailer 1"}],
        }
    )
    return mock


@pytest.fixture
def client(mock_tvdb):
    """TvdbClient with mocked TVDB backend."""
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        return TvdbClient("test-key", None, AsyncRateLimiter())


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache between tests."""
    tvdb_cache.clear()
    yield
    tvdb_cache.clear()


@pytest.mark.asyncio
async def test_series_cached_across_different_include_params(client, mock_tvdb) -> None:
    """Different include_* params for the same series only hit the API once."""
    mock_tvdb.get_series_extended.reset_mock()

    # First call with characters only
    result1 = await client.get_series_extended(78804, include_characters=True, include_artworks=False)
    assert "characters" in result1
    assert "artworks" not in result1

    # Second call with artworks only — should hit cache, not API
    result2 = await client.get_series_extended(78804, include_characters=False, include_artworks=True)
    assert "characters" not in result2
    assert "artworks" in result2

    # API was only called once
    mock_tvdb.get_series_extended.assert_called_once()


@pytest.mark.asyncio
async def test_movie_cached_across_different_include_params(client, mock_tvdb) -> None:
    """Different include_* params for the same movie only hit the API once."""
    mock_tvdb.get_movie_extended.reset_mock()

    # First call with characters only
    result1 = await client.get_movie_extended(
        1000, include_characters=True, include_artworks=False, include_trailers=False
    )
    assert "characters" in result1
    assert "artworks" not in result1
    assert "trailers" not in result1

    # Second call with artworks only — should hit cache, not API
    result2 = await client.get_movie_extended(
        1000, include_characters=False, include_artworks=True, include_trailers=False
    )
    assert "characters" not in result2
    assert "artworks" in result2
    assert "trailers" not in result2

    # API was only called once
    mock_tvdb.get_movie_extended.assert_called_once()


@pytest.mark.asyncio
async def test_different_entities_not_cached_together(client, mock_tvdb) -> None:
    """Different series IDs are cached separately."""
    mock_tvdb.get_series_extended.reset_mock()

    await client.get_series_extended(78804)
    await client.get_series_extended(78805)

    # API was called twice (different IDs)
    assert mock_tvdb.get_series_extended.call_count == 2


@pytest.mark.asyncio
async def test_cache_isolation_between_calls(client, mock_tvdb) -> None:
    """Filtering one cached result doesn't affect the original."""
    mock_tvdb.get_series_extended.reset_mock()
    mock_tvdb.get_series_extended.return_value = {
        "id": 1,
        "name": "Test",
        "characters": [{"id": 10}],
        "artworks": [{"id": 20}],
    }

    # Call with characters only
    result1 = await client.get_series_extended(78804, include_characters=True, include_artworks=False)
    assert "characters" in result1
    assert "artworks" not in result1

    # Call with both — should still have artworks (from cache)
    result2 = await client.get_series_extended(78804, include_characters=True, include_artworks=True)
    assert "characters" in result2
    assert "artworks" in result2
