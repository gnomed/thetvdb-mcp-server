"""Unit tests for MCP tool implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thetvdb_mcp_server.config import AppConfig, LoggingConfig, ServerConfig, TvdbConfig
from thetvdb_mcp_server.tools import (
    init_tools,
    tvdb_get_artwork,
    tvdb_get_artwork_extended,
    tvdb_get_episode,
    tvdb_get_episode_extended,
    tvdb_get_person,
    tvdb_get_person_extended,
    tvdb_get_season,
    tvdb_get_season_extended,
    tvdb_get_series,
    tvdb_get_series_by_slug,
    tvdb_get_series_episodes,
    tvdb_get_series_extended,
    tvdb_search,
)


def make_mock_client():
    """Return a mock TvdbClient with all methods as AsyncMocks."""
    mock = MagicMock()
    mock.get_series = AsyncMock(return_value={"id": 1, "name": "Test Series"})
    mock.get_series_extended = AsyncMock(
        return_value={
            "id": 1,
            "name": "Test Series",
            "characters": [{"id": 10}],
            "artworks": [{"id": 20}],
        }
    )
    mock.get_series_episodes = AsyncMock(
        return_value={
            "series": {"id": 1, "name": "Test Series"},
            "episodes": [{"id": 100}],
        }
    )
    mock.get_series_by_slug = AsyncMock(return_value={"id": 1, "name": "Test Series"})
    mock.get_season = AsyncMock(return_value={"id": 1, "name": "Season 1"})
    mock.get_season_extended = AsyncMock(return_value={"id": 1, "name": "Season 1"})
    mock.get_artwork = AsyncMock(return_value={"id": 1, "name": "Artwork 1"})
    mock.get_artwork_extended = AsyncMock(return_value={"id": 1, "name": "Artwork 1"})
    mock.get_episode = AsyncMock(return_value={"id": 1, "name": "Episode 1"})
    mock.get_episode_extended = AsyncMock(return_value={"id": 1, "name": "Episode 1"})
    mock.get_person = AsyncMock(return_value={"id": 1, "name": "Person 1"})
    mock.get_person_extended = AsyncMock(return_value={"id": 1, "name": "Person 1"})
    mock.search = AsyncMock(return_value=[{"id": 1, "name": "Test"}])
    return mock


def make_config() -> AppConfig:
    """Create a test AppConfig."""
    return AppConfig(
        server=ServerConfig(host="localhost", port=8080),
        logging=LoggingConfig(level="info"),
        tvdb=TvdbConfig(api_key="test-key", pin=None),
    )


@pytest.fixture
def mock_client():
    """Mock TvdbClient fixture."""
    return make_mock_client()


@pytest.fixture
def patched_tools(mock_client):
    """Patch tools module to use mock client."""
    with patch("thetvdb_mcp_server.tools._client", mock_client):
        yield mock_client


# ======================================================================
# tvdb_search
# ======================================================================


@pytest.mark.asyncio
async def test_search_calls_client(patched_tools) -> None:
    """tvdb_search calls client.search with correct args."""
    result = await tvdb_search("doctor who")

    patched_tools.search.assert_called_once_with(
        query="doctor who",
        type_=None,
        year=None,
        offset=0,
        limit=10,
        primary_language=None,
        country=None,
        director=None,
        remote_id=None,
    )
    assert len(result) == 1


@pytest.mark.asyncio
async def test_search_all_params(patched_tools) -> None:
    """tvdb_search passes all parameters correctly."""
    await tvdb_search("doctor who", type="series", year=2005, offset=5, limit=3, primary_language="eng")

    patched_tools.search.assert_called_once_with(
        query="doctor who",
        type_="series",
        year=2005,
        offset=5,
        limit=3,
        primary_language="eng",
        country=None,
        director=None,
        remote_id=None,
    )


# ======================================================================
# tvdb_get_series_episodes
# ======================================================================


@pytest.mark.asyncio
async def test_episodes_calls_client(patched_tools) -> None:
    """tvdb_get_series_episodes calls client correctly."""
    result = await tvdb_get_series_episodes(78804, "default")

    patched_tools.get_series_episodes.assert_called_once_with(
        series_id=78804,
        season_type="default",
        page=0,
        lang=None,
        season=None,
        episode_number=None,
    )
    assert "episodes" in result


@pytest.mark.asyncio
async def test_episodes_all_params(patched_tools) -> None:
    """tvdb_get_series_episodes passes all parameters."""
    await tvdb_get_series_episodes(78804, "aired", page=2, lang="deu")

    patched_tools.get_series_episodes.assert_called_once_with(
        series_id=78804,
        season_type="aired",
        page=2,
        lang="deu",
        season=None,
        episode_number=None,
    )


# ======================================================================
# tvdb_get_series
# ======================================================================


@pytest.mark.asyncio
async def test_get_series(patched_tools) -> None:
    """tvdb_get_series calls client.get_series and returns result."""
    result = await tvdb_get_series(78804)

    patched_tools.get_series.assert_called_once_with(78804)
    assert result["id"] == 1


# ======================================================================
# tvdb_get_series_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_series_extended_defaults(patched_tools) -> None:
    """tvdb_get_series_extended uses default include_ params (both False)."""
    await tvdb_get_series_extended(78804)

    patched_tools.get_series_extended.assert_called_once_with(
        78804,
        include_characters=False,
        include_artworks=False,
    )


@pytest.mark.asyncio
async def test_get_series_extended_characters_only(patched_tools) -> None:
    """tvdb_get_series_extended passes include_characters=True."""
    await tvdb_get_series_extended(78804, include_characters=True)

    patched_tools.get_series_extended.assert_called_once_with(
        78804,
        include_characters=True,
        include_artworks=False,
    )


@pytest.mark.asyncio
async def test_get_series_extended_artworks_only(patched_tools) -> None:
    """tvdb_get_series_extended passes include_artworks=True."""
    await tvdb_get_series_extended(78804, include_artworks=True)

    patched_tools.get_series_extended.assert_called_once_with(
        78804,
        include_characters=False,
        include_artworks=True,
    )


@pytest.mark.asyncio
async def test_get_series_extended_both(patched_tools) -> None:
    """tvdb_get_series_extended passes both include_ params as True."""
    await tvdb_get_series_extended(78804, include_characters=True, include_artworks=True)

    patched_tools.get_series_extended.assert_called_once_with(
        78804,
        include_characters=True,
        include_artworks=True,
    )


# ======================================================================
# tvdb_get_series_by_slug
# ======================================================================


@pytest.mark.asyncio
async def test_get_series_by_slug(patched_tools) -> None:
    """tvdb_get_series_by_slug calls client with slug."""
    result = await tvdb_get_series_by_slug("doctor-who")

    patched_tools.get_series_by_slug.assert_called_once_with("doctor-who")
    assert result["id"] == 1


# ======================================================================
# tvdb_get_season
# ======================================================================


@pytest.mark.asyncio
async def test_get_season(patched_tools) -> None:
    """tvdb_get_season calls client.get_season."""
    result = await tvdb_get_season(12345)

    patched_tools.get_season.assert_called_once_with(12345)
    assert result["id"] == 1


# ======================================================================
# tvdb_get_season_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_season_extended(patched_tools) -> None:
    """tvdb_get_season_extended calls client.get_season_extended."""
    result = await tvdb_get_season_extended(12345)

    patched_tools.get_season_extended.assert_called_once_with(12345)
    assert result["id"] == 1


# ======================================================================
# tvdb_get_artwork
# ======================================================================


@pytest.mark.asyncio
async def test_get_artwork(patched_tools) -> None:
    """tvdb_get_artwork calls client.get_artwork."""
    result = await tvdb_get_artwork(67890)

    patched_tools.get_artwork.assert_called_once_with(67890)
    assert result["id"] == 1


# ======================================================================
# tvdb_get_artwork_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_artwork_extended(patched_tools) -> None:
    """tvdb_get_artwork_extended calls client.get_artwork_extended."""
    result = await tvdb_get_artwork_extended(67890)

    patched_tools.get_artwork_extended.assert_called_once_with(67890)
    assert result["id"] == 1


# ======================================================================
# tvdb_get_episode
# ======================================================================


@pytest.mark.asyncio
async def test_get_episode(patched_tools) -> None:
    """tvdb_get_episode calls client.get_episode."""
    result = await tvdb_get_episode(11111)

    patched_tools.get_episode.assert_called_once_with(11111)
    assert result["id"] == 1


# ======================================================================
# tvdb_get_episode_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_episode_extended(patched_tools) -> None:
    """tvdb_get_episode_extended calls client.get_episode_extended."""
    result = await tvdb_get_episode_extended(11111)

    patched_tools.get_episode_extended.assert_called_once_with(11111)
    assert result["id"] == 1


# ======================================================================
# tvdb_get_person
# ======================================================================


@pytest.mark.asyncio
async def test_get_person(patched_tools) -> None:
    """tvdb_get_person calls client.get_person."""
    result = await tvdb_get_person(22222)

    patched_tools.get_person.assert_called_once_with(22222)
    assert result["id"] == 1


# ======================================================================
# tvdb_get_person_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_person_extended(patched_tools) -> None:
    """tvdb_get_person_extended calls client.get_person_extended."""
    result = await tvdb_get_person_extended(22222)

    patched_tools.get_person_extended.assert_called_once_with(22222)
    assert result["id"] == 1


# ======================================================================
# init_tools
# ======================================================================


def test_init_tools_creates_client() -> None:
    """init_tools creates and sets the shared client."""
    with patch("thetvdb_mcp_server.tools.TvdbClient") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        config = make_config()
        init_tools(config)

        MockClient.assert_called_once()
        args = MockClient.call_args
        assert args[1]["api_key"] == "test-key"
        assert args[1]["pin"] is None


# ======================================================================
# Error paths — _client is None
# ======================================================================


@pytest.mark.asyncio
async def test_search_raises_without_init() -> None:
    """tvdb_search raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_search("test")


@pytest.mark.asyncio
async def test_episodes_raises_without_init() -> None:
    """tvdb_get_series_episodes raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_series_episodes(78804, "default")


@pytest.mark.asyncio
async def test_get_series_raises_without_init() -> None:
    """tvdb_get_series raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_series(78804)


@pytest.mark.asyncio
async def test_get_series_extended_raises_without_init() -> None:
    """tvdb_get_series_extended raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_series_extended(78804)


@pytest.mark.asyncio
async def test_get_series_by_slug_raises_without_init() -> None:
    """tvdb_get_series_by_slug raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_series_by_slug("test")


@pytest.mark.asyncio
async def test_get_season_raises_without_init() -> None:
    """tvdb_get_season raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_season(12345)


@pytest.mark.asyncio
async def test_get_season_extended_raises_without_init() -> None:
    """tvdb_get_season_extended raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_season_extended(12345)


@pytest.mark.asyncio
async def test_get_artwork_raises_without_init() -> None:
    """tvdb_get_artwork raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_artwork(67890)


@pytest.mark.asyncio
async def test_get_artwork_extended_raises_without_init() -> None:
    """tvdb_get_artwork_extended raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_artwork_extended(67890)


@pytest.mark.asyncio
async def test_get_episode_raises_without_init() -> None:
    """tvdb_get_episode raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_episode(11111)


@pytest.mark.asyncio
async def test_get_episode_extended_raises_without_init() -> None:
    """tvdb_get_episode_extended raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_episode_extended(11111)


@pytest.mark.asyncio
async def test_get_person_raises_without_init() -> None:
    """tvdb_get_person raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_person(22222)


@pytest.mark.asyncio
async def test_get_person_extended_raises_without_init() -> None:
    """tvdb_get_person_extended raises RuntimeError if init_tools() not called."""
    with patch("thetvdb_mcp_server.tools._client", None):
        with pytest.raises(RuntimeError, match="init_tools"):
            await tvdb_get_person_extended(22222)
