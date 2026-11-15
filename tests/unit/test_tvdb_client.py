"""Unit tests for TvdbClient wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from thetvdb_mcp_server.cache import tvdb_cache
from thetvdb_mcp_server.rate_limiter import AsyncRateLimiter
from thetvdb_mcp_server.tvdb_client import TvdbClient


def make_mock_tvdb():
    """Return a mock TVDB instance with all methods mocked."""
    mock_tvdb = MagicMock()
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
    mock_tvdb.get_season_extended = MagicMock(return_value={"id": 1, "name": "Season 1"})
    mock_tvdb.get_artwork_extended = MagicMock(return_value={"id": 1, "name": "Artwork 1"})
    mock_tvdb.get_episode_extended = MagicMock(return_value={"id": 1, "name": "Episode 1"})
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


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache before and after each test."""
    tvdb_cache.clear()
    yield
    tvdb_cache.clear()


# ======================================================================
# Recursive translate/strip
# ======================================================================


def test_translate_and_strip_recursive(client) -> None:
    """_translate_and_strip recursively walks nested dicts and lists."""
    data = {
        "name": "Original",
        "translations": {"eng": "English Name", "deu": "German Name"},
        "overviews": {"eng": "English Overview"},
        "seasons": [
            {
                "name": "Season 1",
                "translations": {"eng": "S1 Eng", "deu": "S1 Ger"},
                "episodes": [
                    {
                        "name": "Episode 1",
                        "translations": {"eng": "E1 Eng", "deu": "E1 Ger"},
                    }
                ],
            }
        ],
    }
    client._result_language = "eng"
    result = client._translate_and_strip(data)
    assert result["name"] == "English Name"
    assert result["overview"] == "English Overview"
    assert "translations" not in result
    assert "overviews" not in result
    s = result["seasons"][0]
    assert s["name"] == "S1 Eng"
    assert "translations" not in s
    e = s["episodes"][0]
    assert e["name"] == "E1 Eng"
    assert "translations" not in e


def test_normalize_tagoptions_to_tags(client) -> None:
    """tagOptions is normalized to tags."""
    record = {"tagOptions": [{"tag": "action"}]}
    client._normalize_and_translate_record(record)
    assert "tags" in record
    assert record["tags"] == [{"tag": "action"}]
    assert "tagOptions" not in record


def test_normalize_artwork_to_artworks(client) -> None:
    """artwork (singular) is normalized to artworks."""
    record = {"artwork": [{"id": 1}]}
    client._normalize_and_translate_record(record)
    assert "artworks" in record
    assert record["artworks"] == [{"id": 1}]
    assert "artwork" not in record


def test_strip_name_translations(client) -> None:
    """nameTranslations and overviewTranslations arrays are stripped."""
    record = {
        "nameTranslations": ["eng", "deu"],
        "overviewTranslations": ["eng"],
        "name": "Test",
    }
    client._result_language = "eng"
    client._normalize_and_translate_record(record)
    assert "nameTranslations" not in record
    assert "overviewTranslations" not in record


def test_filter_aliases_by_language(client) -> None:
    """aliases are filtered to result_language."""
    record = {
        "aliases": [
            {"language": "eng", "name": "English Alias"},
            {"language": "deu", "name": "German Alias"},
        ]
    }
    client._result_language = "eng"
    client._normalize_and_translate_record(record)
    assert len(record["aliases"]) == 1
    assert record["aliases"][0]["name"] == "English Alias"


def test_filter_trailers_by_language(client) -> None:
    """trailers are filtered to result_language."""
    record = {
        "trailers": [
            {"language": "eng", "name": "English Trailer"},
            {"language": "deu", "name": "German Trailer"},
        ]
    }
    client._result_language = "eng"
    client._normalize_and_translate_record(record)
    assert len(record["trailers"]) == 1
    assert record["trailers"][0]["name"] == "English Trailer"


def test_translate_no_language_set(client) -> None:
    """Without result_language, only normalization occurs."""
    record = {
        "tagOptions": [{"tag": "test"}],
        "translations": {"eng": "Eng Name"},
        "name": "Original",
    }
    client._result_language = None
    client._normalize_and_translate_record(record)
    assert "tags" in record  # normalized
    assert "translations" in record  # not stripped
    assert record["name"] == "Original"  # not translated


def test_include_filters_recursive(client) -> None:
    """include_* filters apply recursively to nested structures."""
    data = {
        "id": 1,
        "tags": [{"tag": "top"}],
        "characters": [{"id": 10, "tags": [{"tag": "char"}]}],
        "seasons": [
            {
                "id": 20,
                "tags": [{"tag": "season"}],
                "episodes": [
                    {
                        "id": 30,
                        "tags": [{"tag": "episode"}],
                        "characters": [{"id": 40, "tags": [{"tag": "epchar"}]}],
                    }
                ],
            }
        ],
    }
    result = client._apply_include_filters(data, include_tags=False, include_characters=True)
    assert "tags" not in result
    assert "tags" not in result["characters"][0]
    s = result["seasons"][0]
    assert "tags" not in s
    e = s["episodes"][0]
    assert "tags" not in e
    assert "characters" in e  # characters still included


def test_include_filters_nested_characters(client) -> None:
    """include_characters=False removes characters at all nesting levels."""
    data = {
        "id": 1,
        "characters": [{"id": 10}],
        "seasons": [
            {
                "id": 20,
                "episodes": [{"id": 30, "characters": [{"id": 40}]}],
            }
        ],
    }
    result = client._apply_include_filters(data, include_characters=False)
    assert "characters" not in result
    e = result["seasons"][0]["episodes"][0]
    assert "characters" not in e


# ======================================================================
# get_series_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_series_extended_always_uses_short_false(client, mock_tvdb) -> None:
    """API is always called with short=False regardless of include_ params."""
    mock_tvdb.get_series_extended.reset_mock()
    mock_tvdb.get_series_extended.return_value = {"id": 1, "name": "Extended"}

    await client.get_series_extended(78804, include_characters=False, include_artworks=False)

    mock_tvdb.get_series_extended.assert_called_once_with(78804, short=False, meta=None)


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


@pytest.mark.asyncio
async def test_get_series_extended_include_trailers(client, mock_tvdb) -> None:
    """include_trailers controls trailers in series extended."""
    mock_tvdb.get_series_extended.reset_mock()
    mock_tvdb.get_series_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "trailers": [{"id": 1}],
    }

    result = await client.get_series_extended(78804, include_trailers=True)
    assert "trailers" in result

    mock_tvdb.get_series_extended.reset_mock()
    mock_tvdb.get_series_extended.return_value = {"id": 1, "name": "Extended", "trailers": [{"id": 1}]}
    result = await client.get_series_extended(78804, include_trailers=False)
    assert "trailers" not in result


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
# get_season_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_season_extended(client, mock_tvdb) -> None:
    """get_season_extended forwards the season ID to TVDB."""
    result = await client.get_season_extended(12345)

    mock_tvdb.get_season_extended.assert_called_once_with(12345, meta=None)
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_get_season_extended_with_language(client, mock_tvdb) -> None:
    """get_season_extended passes meta when result_language is set."""
    client._result_language = "eng"
    await client.get_season_extended(12345)
    mock_tvdb.get_season_extended.assert_called_once_with(12345, meta="translations")


@pytest.mark.asyncio
async def test_get_season_extended_default_filters(client, mock_tvdb) -> None:
    """Season extended defaults: episodes True, companies True, tags True, artworks False, trailers False."""
    mock_tvdb.get_season_extended.reset_mock()
    mock_tvdb.get_season_extended.return_value = {
        "id": 1,
        "name": "Season 1",
        "episodes": [{"id": 10}],
        "companies": [{"id": 20}],
        "tags": [{"tag": "test"}],
        "artworks": [{"id": 30}],
        "trailers": [{"id": 40}],
    }
    result = await client.get_season_extended(12345)
    assert "episodes" in result
    assert "companies" in result
    assert "tags" in result
    assert "artworks" not in result
    assert "trailers" not in result


# ======================================================================
# get_artwork_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_artwork_extended(client, mock_tvdb) -> None:
    """get_artwork_extended forwards the artwork ID to TVDB."""
    result = await client.get_artwork_extended(67890)

    mock_tvdb.get_artwork_extended.assert_called_once_with(67890, meta=None)
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_get_artwork_extended_with_language(client, mock_tvdb) -> None:
    """get_artwork_extended passes meta when result_language is set."""
    client._result_language = "eng"
    await client.get_artwork_extended(67890)
    mock_tvdb.get_artwork_extended.assert_called_once_with(67890, meta="translations")


# ======================================================================
# get_episode_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_episode_extended(client, mock_tvdb) -> None:
    """get_episode_extended forwards the episode ID to TVDB."""
    result = await client.get_episode_extended(11111)

    mock_tvdb.get_episode_extended.assert_called_once_with(11111, meta=None)
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_get_episode_extended_default_filters(client, mock_tvdb) -> None:
    """Episode extended defaults: awards/characters/companies/seasons/tags/remoteIds True,
    contentRatings/trailers False."""
    mock_tvdb.get_episode_extended.reset_mock()
    mock_tvdb.get_episode_extended.return_value = {
        "id": 1,
        "name": "Episode 1",
        "awards": [{"id": 10}],
        "characters": [{"id": 20}],
        "companies": [{"id": 30}],
        "seasons": [{"id": 40}],
        "tags": [{"tag": "test"}],
        "remoteIds": [{"id": 50}],
        "contentRatings": [{"id": 60}],
        "trailers": [{"id": 70}],
    }
    result = await client.get_episode_extended(11111)
    assert "awards" in result
    assert "characters" in result
    assert "companies" in result
    assert "seasons" in result
    assert "tags" in result
    assert "remoteIds" in result
    assert "contentRatings" not in result
    assert "trailers" not in result


# ======================================================================
# get_person_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_person_extended(client, mock_tvdb) -> None:
    """get_person_extended forwards the person ID to TVDB."""
    result = await client.get_person_extended(22222)

    mock_tvdb.get_person_extended.assert_called_once_with(22222, meta=None)
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_get_person_extended_default_filters(client, mock_tvdb) -> None:
    """Person extended defaults: awards/characters/biographies/remoteIds/tags True."""
    mock_tvdb.get_person_extended.reset_mock()
    mock_tvdb.get_person_extended.return_value = {
        "id": 1,
        "name": "Person 1",
        "awards": [{"id": 10}],
        "characters": [{"id": 20}],
        "biographies": [{"id": 30}],
        "remoteIds": [{"id": 40}],
        "tags": [{"tag": "test"}],
    }
    result = await client.get_person_extended(22222)
    assert "awards" in result
    assert "characters" in result
    assert "biographies" in result
    assert "remoteIds" in result
    assert "tags" in result


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
# get_movie_extended
# ======================================================================


@pytest.mark.asyncio
async def test_get_movie_extended_always_uses_short_false(client, mock_tvdb) -> None:
    """API is always called with short=False regardless of include_ params."""
    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {"id": 1, "name": "Extended"}

    await client.get_movie_extended(
        1000,
        include_characters=False,
        include_artworks=False,
        include_trailers=False,
    )

    mock_tvdb.get_movie_extended.assert_called_once_with(1000, short=False, meta=None)


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


@pytest.mark.asyncio
async def test_get_movie_extended_include_awards(client, mock_tvdb) -> None:
    """include_awards controls awards in movie extended."""
    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "awards": [{"id": 1}],
    }
    result = await client.get_movie_extended(1000, include_awards=True)
    assert "awards" in result

    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {"id": 1, "name": "Extended", "awards": [{"id": 1}]}
    result = await client.get_movie_extended(1000, include_awards=False)
    assert "awards" not in result


@pytest.mark.asyncio
async def test_get_movie_extended_include_releases(client, mock_tvdb) -> None:
    """include_releases controls releases in movie extended."""
    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {
        "id": 1,
        "name": "Extended",
        "releases": [{"id": 1}],
    }
    result = await client.get_movie_extended(1000, include_releases=True)
    assert "releases" in result

    mock_tvdb.get_movie_extended.reset_mock()
    mock_tvdb.get_movie_extended.return_value = {"id": 1, "name": "Extended", "releases": [{"id": 1}]}
    result = await client.get_movie_extended(1000, include_releases=False)
    assert "releases" not in result


# ======================================================================
# get_movie_by_slug
# ======================================================================


@pytest.mark.asyncio
async def test_get_movie_by_slug(client, mock_tvdb) -> None:
    """get_movie_by_slug forwards the slug to TVDB."""
    result = await client.get_movie_by_slug("the-lord-of-the-rings")

    mock_tvdb.get_movie_by_slug.assert_called_once_with("the-lord-of-the-rings")
    assert result["id"] == 1
