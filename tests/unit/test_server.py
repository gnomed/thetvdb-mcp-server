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
    tvdb_get_series_episodes,
    tvdb_get_series_extended,
    tvdb_search,
)


def make_config() -> AppConfig:
    """Create a test AppConfig."""
    return AppConfig(
        server=ServerConfig(host="localhost", port=8080),
        logging=LoggingConfig(level="info"),
        tvdb=TvdbConfig(api_key="test-key", pin=None),
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
    mcp.tool(name="tvdb_search")(tvdb_search)
    mcp.tool(name="tvdb_get_series_episodes")(tvdb_get_series_episodes)


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
async def test_all_tools_registered() -> None:
    """All 13 tools are registered."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config())

    registered = await get_registered_tool_names(mcp)

    for tool_name in EXPECTED_TOOL_NAMES:
        assert tool_name in registered, f"Missing tool: {tool_name}"
    assert len(registered) == 13


@pytest.mark.asyncio
async def test_search_has_language_param() -> None:
    """tvdb_search has primary_language parameter."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config())

    tools = await mcp.list_tools()
    search_tool = next(t for t in tools if t.name == "tvdb_search")

    assert "primary_language" in search_tool.parameters["properties"]


@pytest.mark.asyncio
async def test_episodes_has_language_param() -> None:
    """tvdb_get_series_episodes has lang parameter."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config())

    tools = await mcp.list_tools()
    episodes_tool = next(t for t in tools if t.name == "tvdb_get_series_episodes")

    assert "lang" in episodes_tool.parameters["properties"]


@pytest.mark.asyncio
async def test_search_defaults() -> None:
    """tvdb_search has correct default limit."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config())

    tools = await mcp.list_tools()
    search_tool = next(t for t in tools if t.name == "tvdb_search")

    assert search_tool.parameters["properties"]["limit"]["default"] == 10
    assert search_tool.parameters["properties"]["offset"]["default"] == 0


@pytest.mark.asyncio
async def test_episodes_defaults() -> None:
    """tvdb_get_series_episodes has correct default page."""
    mcp = fastmcp.FastMCP("thetvdb-mcp-server")
    register_tools(mcp, make_config())

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
