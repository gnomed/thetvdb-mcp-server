"""Unit tests for server tool registration."""

from unittest.mock import MagicMock, patch

import fastmcp
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
    tvdb_get_series_episodes_with_lang,
    tvdb_get_series_episodes_without_lang,
    tvdb_get_series_extended,
    tvdb_search_with_lang,
    tvdb_search_without_lang,
)


def make_config(primary_language: str | None = None) -> AppConfig:
    """Create a test AppConfig."""
    return AppConfig(
        server=ServerConfig(host="localhost", port=8080),
        logging=LoggingConfig(level="info"),
        tvdb=TvdbConfig(api_key="test-key", pin=None, primary_language=primary_language),
    )


def register_tools(mcp, config, mock_client=None):
    """Register tools the same way main() does, for testing."""
    with patch("thetvdb_mcp_server.tools.TvdbClient") as MockClient:
        MockClient.return_value = mock_client or MagicMock()
        init_tools(config)

    mcp.tool(name="tvdb_get_series")(tvdb_get_series)
    mcp.tool(name="tvdb_get_series_extended")(tvdb_get_series_extended)
    mcp.tool(name="tvdb_get_series_by_slug")(tvdb_get_series_by_slug)
    mcp.tool(name="tvdb_get_season")(tvdb_get_season)
    mcp.tool(name="tvdb_get_season_extended")(tvdb_get_season_extended)
    mcp.tool(name="tvdb_get_artwork")(tvdb_get_artwork)
    mcp.tool(name="tvdb_get_artwork_extended")(tvdb_get_artwork_extended)
    mcp.tool(name="tvdb_get_episode")(tvdb_get_episode)
    mcp.tool(name="tvdb_get_episode_extended")(tvdb_get_episode_extended)
    mcp.tool(name="tvdb_get_person")(tvdb_get_person)
    mcp.tool(name="tvdb_get_person_extended")(tvdb_get_person_extended)

    if config.tvdb.primary_language:
        mcp.tool(name="tvdb_search")(tvdb_search_without_lang)
        mcp.tool(name="tvdb_get_series_episodes")(tvdb_get_series_episodes_without_lang)
    else:
        mcp.tool(name="tvdb_search")(tvdb_search_with_lang)
        mcp.tool(name="tvdb_get_series_episodes")(tvdb_get_series_episodes_with_lang)


async def get_registered_tool_names(mcp):
    """Get list of registered tool names."""
    tools = await mcp.list_tools()
    return [t.name for t in tools]


EXPECTED_TOOL_NAMES = [
    "tvdb_get_series",
    "tvdb_get_series_extended",
    "tvdb_get_series_by_slug",
    "tvdb_get_season",
    "tvdb_get_season_extended",
    "tvdb_get_artwork",
    "tvdb_get_artwork_extended",
    "tvdb_get_episode",
    "tvdb_get_episode_extended",
    "tvdb_get_person",
    "tvdb_get_person_extended",
    "tvdb_search",
    "tvdb_get_series_episodes",
]


@pytest.mark.asyncio
async def test_all_tools_registered_without_primary_language() -> None:
    """All 13 tools are registered when primary_language is not set."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config(primary_language=None))

    registered = await get_registered_tool_names(mcp)

    for tool_name in EXPECTED_TOOL_NAMES:
        assert tool_name in registered, f"Missing tool: {tool_name}"
    assert len(registered) == 13


@pytest.mark.asyncio
async def test_all_tools_registered_with_primary_language() -> None:
    """All 13 tools are registered when primary_language is set."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config(primary_language="eng"))

    registered = await get_registered_tool_names(mcp)

    for tool_name in EXPECTED_TOOL_NAMES:
        assert tool_name in registered, f"Missing tool: {tool_name}"
    assert len(registered) == 13


@pytest.mark.asyncio
async def test_search_has_language_param_without_primary_language() -> None:
    """tvdb_search has primary_language parameter when not configured."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config(primary_language=None))

    tools = await mcp.list_tools()
    search_tool = next(t for t in tools if t.name == "tvdb_search")

    assert "primary_language" in search_tool.parameters["properties"]


@pytest.mark.asyncio
async def test_search_no_language_param_with_primary_language() -> None:
    """tvdb_search has no primary_language parameter when configured."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config(primary_language="eng"))

    tools = await mcp.list_tools()
    search_tool = next(t for t in tools if t.name == "tvdb_search")

    assert "primary_language" not in search_tool.parameters["properties"]


@pytest.mark.asyncio
async def test_episodes_has_language_param_without_primary_language() -> None:
    """tvdb_get_series_episodes has lang parameter when not configured."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config(primary_language=None))

    tools = await mcp.list_tools()
    episodes_tool = next(t for t in tools if t.name == "tvdb_get_series_episodes")

    assert "lang" in episodes_tool.parameters["properties"]


@pytest.mark.asyncio
async def test_episodes_no_language_param_with_primary_language() -> None:
    """tvdb_get_series_episodes has no lang parameter when configured."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config(primary_language="eng"))

    tools = await mcp.list_tools()
    episodes_tool = next(t for t in tools if t.name == "tvdb_get_series_episodes")

    assert "lang" not in episodes_tool.parameters["properties"]


@pytest.mark.asyncio
async def test_search_without_lang_defaults() -> None:
    """tvdb_search_without_lang has correct default limit."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config(primary_language="eng"))

    tools = await mcp.list_tools()
    search_tool = next(t for t in tools if t.name == "tvdb_search")

    assert search_tool.parameters["properties"]["limit"]["default"] == 10
    assert search_tool.parameters["properties"]["offset"]["default"] == 0


@pytest.mark.asyncio
async def test_episodes_without_lang_defaults() -> None:
    """tvdb_get_series_episodes_without_lang has correct default page."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config(primary_language="eng"))

    tools = await mcp.list_tools()
    episodes_tool = next(t for t in tools if t.name == "tvdb_get_series_episodes")

    assert episodes_tool.parameters["properties"]["page"]["default"] == 0


@pytest.mark.asyncio
async def test_series_extended_defaults() -> None:
    """tvdb_get_series_extended has correct default include_ params."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config())

    tools = await mcp.list_tools()
    series_ext_tool = next(t for t in tools if t.name == "tvdb_get_series_extended")

    assert series_ext_tool.parameters["properties"]["include_characters"]["default"] is False
    assert series_ext_tool.parameters["properties"]["include_artworks"]["default"] is False
