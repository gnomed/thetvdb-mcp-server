"""Unit tests for TvdbClient wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from thetvdb_mcp_server.rate_limiter import AsyncRateLimiter
from thetvdb_mcp_server.tvdb_client import TvdbClient


def make_mock_tvdb():
    """Return a mock TVDB instance with all methods mocked."""
    mock_tvdb = MagicMock()
    mock_tvdb.get_movie = MagicMock(return_value={"id": 1, "name": "Test Movie"})
    mock_tvdb.get_movie_extended = MagicMock(
        return_value={
            "id": 1,
            "name": "Test Movie",
            "characters": [{"id": 10, "name": "Character 1"}],
            "artworks": [{"id": 20, "name": "Poster 1"}],
            "trailers": [{"id": 30, "name": "Trailer 1"}],
        }
    )
    mock_tvdb.get_movie_by_slug = MagicMock(return_value={"id": 1, "name": "Test Movie"})
    mock_tvdb.get_series = MagicMock(return_value={"id": 1, "name": "Test Series"})
    mock_tvdb.get_series_extended = MagicMock(
        return_value={
            "id": 1,
            "name": "Test Series",
            "characters": [{"id": 10, "name": "Character 1"}],
            "artworks": [{"id": 20, "name": "Poster 1"}],
        }
    )
    mock_tvdb.get_series_episodes = MagicMock(
        return_value={
            "series": {"id": 1, "name": "Test Series"},
            "episodes": [{"id": 100, "number": 1, "seasonNumber": 1}],
        }
    )
    mock_tvdb.get_series_by_slug = MagicMock(return_value={"id": 1, "name": "Test Series"})
    mock_tvdb.get_season = MagicMock(return_value={"id": 1, "name": "Season 1"})
    mock_tvdb.get_season_extended = MagicMock(return_value={"id": 1, "name": "Season 1"})
    mock_tvdb.get_artwork = MagicMock(return_value={"id": 1, "name": "Artwork 1"})
    mock_tvdb.get_artwork_extended = MagicMock(return_value={"id": 1, "name": "Artwork 1"})
    mock_tvdb.get_episode = MagicMock(return_value={"id": 1, "name": "Episode 1"})
    mock_tvdb.get_episode_extended = MagicMock(return_value={"id": 1, "name": "Episode 1"})
    mock_tvdb.get_person = MagicMock(return_value={"id": 1, "name": "Person 1"})
    mock_tvdb.get_person_extended = MagicMock(return_value={"id": 1, "name": "Person 1"})
    mock_tvdb.search = MagicMock(return_value=[{"tvdb_id": "1", "name": "Test"}])
    return mock_tvdb


@pytest.fixture
def mock_tvdb():
    """Mock TVDB instance fixture."""
    return make_mock_tvdb()


@pytest.fixture
def client(mock_tvdb):
    """TvdbClient fixture with mocked TVDB backend."""
    with patch("thetvdb_mcp_server.tvdb_client.tvdb_v4_official.TVDB", return_value=mock_tvdb):
        return TvdbClient("test-key", None, AsyncRateLimiter())


# ======================================================================
# get_series
# ======================================================================


@pytest.mark.asyncio
async def test_get_series_calls_tvdb_get_series(client, mock_tvdb) -> None:
    """get_series forwards the call to the TVDB client."""
    result = await client.get_series(78804)

    mock_tvdb.get_series.assert_called_once_with(78804)
    assert result["id"] == 1


# ======================================================================
# get_series_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_series_extended_both_false_uses_short(client, mock_tvdb) -> None:
    """When both include_ params are False, API is called with short=True."""
    mock_tvdb.get_series_extended.reset_mock()
    mock_tvdb.get_series_extended.return_value = {"id": 1, "name": "Short"}

    await client.get_series_extended(78804, include_characters=False, include_artworks=False)

    mock_tvdb.get_series_extended.assert_called_once_with(78804, short=True, meta=None)


@pytest.mark.asyncio
async def test_get_series_extended_both_false_no_filtering(client, mock_tvdb) -> None:
    """When short=True, response is returned without filtering."""
    mock_tvdb.get_series_extended.reset_mock()
    mock_tvdb.get_series_extended.return_value = {"id": 1, "name": "Short"}

    result = await client.get_series_extended(78804, include_characters=False, include_artworks=False)

    assert result == {"id": 1, "name": "Short"}


@pytest.mark.asyncio
async def test_get_series_extended_characters_only(client, mock_tvdb) -> None:
    """When only include_characters=True, artworks are stripped."""
    mock_tvdb.get_series_extended.reset_mock()
    mock_tvdb.get_series_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "characters": [{"id": 10}],
        "artworks": [{"id": 20}],
    }

    result = await client.get_series_extended(78804, include_characters=True, include_artworks=False)

    mock_tvdb.get_series_extended.assert_called_once_with(78804, short=False, meta=None)
    assert "characters" in result
    assert "artworks" not in result


@pytest.mark.asyncio
async def test_get_series_extended_artworks_only(client, mock_tvdb) -> None:
    """When only include_artworks=True, characters are stripped."""
    mock_tvdb.get_series_extended.reset_mock()
    mock_tvdb.get_series_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "characters": [{"id": 10}],
        "artworks": [{"id": 20}],
    }

    result = await client.get_series_extended(78804, include_characters=False, include_artworks=True)

    mock_tvdb.get_series_extended.assert_called_once_with(78804, short=False, meta=None)
    assert "characters" not in result
    assert "artworks" in result


@pytest.mark.asyncio
async def test_get_series_extended_both_true(client, mock_tvdb) -> None:
    """When both include_ params are True, both arrays are included."""
    mock_tvdb.get_series_extended.reset_mock()
    mock_tvdb.get_series_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "characters": [{"id": 10}],
        "artworks": [{"id": 20}],
    }

    result = await client.get_series_extended(78804, include_characters=True, include_artworks=True)

    mock_tvdb.get_series_extended.assert_called_once_with(78804, short=False, meta=None)
    assert "characters" in result
    assert "artworks" in result


# ======================================================================
# get_series_episodes
# ======================================================================


@pytest.mark.asyncio
async def test_get_series_episodes_without_lang(client, mock_tvdb) -> None:
    """get_series_episodes without lang does not pass lang to TVDB."""
    await client.get_series_episodes(78804, season_type="official")

    _, kwargs = mock_tvdb.get_series_episodes.call_args
    assert kwargs["lang"] is None


@pytest.mark.asyncio
async def test_get_series_episodes_with_explicit_lang(client, mock_tvdb) -> None:
    """get_series_episodes with explicit lang passes it to TVDB."""
    await client.get_series_episodes(78804, season_type="official", lang="deu")

    _, kwargs = mock_tvdb.get_series_episodes.call_args
    assert kwargs["lang"] == "deu"


@pytest.mark.asyncio
async def test_get_series_episodes_passes_page(client, mock_tvdb) -> None:
    """get_series_episodes passes page parameter."""
    await client.get_series_episodes(78804, season_type="default", page=5)

    _, kwargs = mock_tvdb.get_series_episodes.call_args
    assert kwargs["page"] == 5


# ======================================================================
# get_series_by_slug
# ======================================================================


@pytest.mark.asyncio
async def test_get_series_by_slug(client, mock_tvdb) -> None:
    """get_series_by_slug forwards the slug to TVDB."""
    result = await client.get_series_by_slug("doctor-who")

    mock_tvdb.get_series_by_slug.assert_called_once_with("doctor-who")
    assert result["id"] == 1


# ======================================================================
# get_season
# ======================================================================


@pytest.mark.asyncio
async def test_get_season(client, mock_tvdb) -> None:
    """get_season forwards the season ID to TVDB."""
    result = await client.get_season(12345)

    mock_tvdb.get_season.assert_called_once_with(12345)
    assert result["id"] == 1


# ======================================================================
# get_season_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_season_extended(client, mock_tvdb) -> None:
    """get_season_extended forwards the season ID to TVDB."""
    result = await client.get_season_extended(12345)

    mock_tvdb.get_season_extended.assert_called_once_with(12345)
    assert result["id"] == 1


# ======================================================================
# get_artwork
# ======================================================================


@pytest.mark.asyncio
async def test_get_artwork(client, mock_tvdb) -> None:
    """get_artwork forwards the artwork ID to TVDB."""
    result = await client.get_artwork(67890)

    mock_tvdb.get_artwork.assert_called_once_with(67890)
    assert result["id"] == 1


# ======================================================================
# get_artwork_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_artwork_extended(client, mock_tvdb) -> None:
    """get_artwork_extended forwards the artwork ID to TVDB."""
    result = await client.get_artwork_extended(67890)

    mock_tvdb.get_artwork_extended.assert_called_once_with(67890)
    assert result["id"] == 1


# ======================================================================
# get_episode
# ======================================================================


@pytest.mark.asyncio
async def test_get_episode(client, mock_tvdb) -> None:
    """get_episode forwards the episode ID to TVDB."""
    result = await client.get_episode(11111)

    mock_tvdb.get_episode.assert_called_once_with(11111)
    assert result["id"] == 1


# ======================================================================
# get_episode_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_episode_extended(client, mock_tvdb) -> None:
    """get_episode_extended forwards the episode ID to TVDB."""
    result = await client.get_episode_extended(11111)

    mock_tvdb.get_episode_extended.assert_called_once_with(11111, meta=None)
    assert result["id"] == 1


# ======================================================================
# get_person
# ======================================================================


@pytest.mark.asyncio
async def test_get_person(client, mock_tvdb) -> None:
    """get_person forwards the person ID to TVDB."""
    result = await client.get_person(22222)

    mock_tvdb.get_person.assert_called_once_with(22222)
    assert result["id"] == 1


# ======================================================================
# get_person_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_person_extended(client, mock_tvdb) -> None:
    """get_person_extended forwards the person ID to TVDB."""
    result = await client.get_person_extended(22222)

    mock_tvdb.get_person_extended.assert_called_once_with(22222, meta=None)
    assert result["id"] == 1


# ======================================================================
# search
# ======================================================================


@pytest.mark.asyncio
async def test_search_without_language(client, mock_tvdb) -> None:
    """search without language does not include it in params."""
    await client.search("doctor who", type_="series")

    _, kwargs = mock_tvdb.search.call_args
    assert "primaryLanguage" not in kwargs


@pytest.mark.asyncio
async def test_search_with_language(client, mock_tvdb) -> None:
    """search with language includes it in params."""
    await client.search("doctor who", type_="series", primary_language="eng")

    _, kwargs = mock_tvdb.search.call_args
    assert kwargs["primaryLanguage"] == "eng"


@pytest.mark.asyncio
async def test_search_passes_all_params(client, mock_tvdb) -> None:
    """search passes all provided params to TVDB."""
    await client.search("doctor who", type_="series", year=2005, offset=10, limit=5)

    _, kwargs = mock_tvdb.search.call_args
    assert kwargs["type"] == "series"
    assert kwargs["year"] == 2005
    assert kwargs["offset"] == 10
    assert kwargs["limit"] == 5


@pytest.mark.asyncio
async def test_search_defaults(client, mock_tvdb) -> None:
    """search uses default values for optional params."""
    await client.search("doctor who")

    _, kwargs = mock_tvdb.search.call_args
    assert kwargs["type"] is None
    assert kwargs["year"] is None
    assert kwargs["offset"] == 0
    assert kwargs["limit"] == 10


# ======================================================================
# get_movie
# ======================================================================


@pytest.mark.asyncio
async def test_get_movie_calls_tvdb_get_movie(client, mock_tvdb) -> None:
    """get_movie forwards the call to the TVDB client."""
    result = await client.get_movie(1000)

    mock_tvdb.get_movie.assert_called_once_with(1000)
    assert result["id"] == 1


# ======================================================================
# get_movie_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_movie_extended_all_false_uses_short(client, mock_tvdb) -> None:
    """When all include_ params are False, API is called with short=True."""
    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {"id": 1, "name": "Short"}

    await client.get_movie_extended(
        1000,
        include_characters=False,
        include_artworks=False,
        include_trailers=False,
    )

    mock_tvdb.get_movie_extended.assert_called_once_with(1000, short=True, meta=None)


@pytest.mark.asyncio
async def test_get_movie_extended_characters_only(client, mock_tvdb) -> None:
    """When only include_characters=True, artworks and trailers are stripped."""
    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "characters": [{"id": 10}],
        "artworks": [{"id": 20}],
        "trailers": [{"id": 30}],
    }

    result = await client.get_movie_extended(
        1000, include_characters=True, include_artworks=False, include_trailers=False
    )

    mock_tvdb.get_movie_extended.assert_called_once_with(1000, short=False, meta=None)
    assert "characters" in result
    assert "artworks" not in result
    assert "trailers" not in result


@pytest.mark.asyncio
async def test_get_movie_extended_artworks_only(client, mock_tvdb) -> None:
    """When only include_artworks=True, characters and trailers are stripped."""
    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "characters": [{"id": 10}],
        "artworks": [{"id": 20}],
        "trailers": [{"id": 30}],
    }

    result = await client.get_movie_extended(
        1000, include_characters=False, include_artworks=True, include_trailers=False
    )

    mock_tvdb.get_movie_extended.assert_called_once_with(1000, short=False, meta=None)
    assert "characters" not in result
    assert "artworks" in result
    assert "trailers" not in result


@pytest.mark.asyncio
async def test_get_movie_extended_trailers_only(client, mock_tvdb) -> None:
    """When only include_trailers=True, characters and artworks are stripped."""
    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "characters": [{"id": 10}],
        "artworks": [{"id": 20}],
        "trailers": [{"id": 30}],
    }

    result = await client.get_movie_extended(
        1000, include_characters=False, include_artworks=False, include_trailers=True
    )

    mock_tvdb.get_movie_extended.assert_called_once_with(1000, short=False, meta=None)
    assert "characters" not in result
    assert "artworks" not in result
    assert "trailers" in result


@pytest.mark.asyncio
async def test_get_movie_extended_all_true(client, mock_tvdb) -> None:
    """When all include_ params are True, all arrays are included."""
    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "characters": [{"id": 10}],
        "artworks": [{"id": 20}],
        "trailers": [{"id": 30}],
    }

    result = await client.get_movie_extended(
        1000,
        include_characters=True,
        include_artworks=True,
        include_trailers=True,
    )

    mock_tvdb.get_movie_extended.assert_called_once_with(1000, short=False, meta=None)
    assert "characters" in result
    assert "artworks" in result
    assert "trailers" in result


# ======================================================================
# get_movie_by_slug
# ======================================================================


@pytest.mark.asyncio
async def test_get_movie_by_slug(client, mock_tvdb) -> None:
    """get_movie_by_slug forwards the slug to TVDB."""
    result = await client.get_movie_by_slug("the-lord-of-the-rings")

    mock_tvdb.get_movie_by_slug.assert_called_once_with("the-lord-of-the-rings")
    assert result["id"] == 1
