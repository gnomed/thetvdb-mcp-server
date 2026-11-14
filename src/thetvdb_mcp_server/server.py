"""FastMCP server entrypoint for the thetvdb-mcp-server server.

Run with::

    uv run python -m thetvdb_mcp_server

or via the installed script::

    thetvdb-mcp-server
"""

import argparse
from pathlib import Path

import fastmcp

from thetvdb_mcp_server.config import load_config
from thetvdb_mcp_server.logging import make_logger
from thetvdb_mcp_server.tools import (
    init_tools,
    tvdb_get_artwork,
    tvdb_get_artwork_extended,
    tvdb_get_episode,
    tvdb_get_episode_extended,
    tvdb_get_movie,
    tvdb_get_movie_by_slug,
    tvdb_get_movie_extended,
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

mcp = fastmcp.FastMCP("thetvdb-mcp-server")


def main() -> None:
    """Parse CLI arguments, load configuration, and start the MCP server."""
    parser = argparse.ArgumentParser(description="thetvdb-mcp-server MCP server")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.toml"),
        help="Path to config.toml (default: config.toml)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    logger = make_logger(config.logging.level)
    init_tools(config)

    # Register all 16 tools
    mcp.tool(name="tvdb_get_movie")(tvdb_get_movie)
    mcp.tool(name="tvdb_get_movie_extended")(tvdb_get_movie_extended)
    mcp.tool(name="tvdb_get_movie_by_slug")(tvdb_get_movie_by_slug)
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

    logger.info(
        "Starting thetvdb-mcp-server",
        host=config.server.host,
        port=config.server.port,
    )

    mcp.run(
        transport="streamable-http",
        host=config.server.host,
        port=config.server.port,
    )
