"""FastMCP server entrypoint for the thetvdb-mcp-server server.

Run with::

    uv run python -m thetvdb_mcp_server

or via the installed script::

    thetvdb-mcp-server
"""

import argparse
from pathlib import Path

import fastmcp
from fastmcp.server.lifespan import lifespan

from thetvdb_mcp_server.cache import tvdb_cache
from thetvdb_mcp_server.config import load_config
from thetvdb_mcp_server.logging import make_logger
from thetvdb_mcp_server.tools import (
    init_tools,
    tvdb_get_artwork,
    tvdb_get_episode,
    tvdb_get_movie,
    tvdb_get_movie_by_slug,
    tvdb_get_person,
    tvdb_get_season,
    tvdb_get_series,
    tvdb_get_series_by_slug,
    tvdb_get_series_episodes,
    tvdb_search,
)


@lifespan
async def cache_lifespan(server):
    """Manage the TVDB cache cleanup task lifecycle."""
    await tvdb_cache.start()
    yield {}
    await tvdb_cache.stop()


mcp = fastmcp.FastMCP("thetvdb-mcp-server", lifespan=cache_lifespan)

# Register all 10 tools
mcp.tool(name="tvdb_get_movie")(tvdb_get_movie)
mcp.tool(name="tvdb_get_movie_by_slug")(tvdb_get_movie_by_slug)
mcp.tool(name="tvdb_get_series")(tvdb_get_series)
mcp.tool(name="tvdb_get_series_by_slug")(tvdb_get_series_by_slug)
mcp.tool(name="tvdb_get_season")(tvdb_get_season)
mcp.tool(name="tvdb_get_artwork")(tvdb_get_artwork)
mcp.tool(name="tvdb_get_episode")(tvdb_get_episode)
mcp.tool(name="tvdb_get_person")(tvdb_get_person)
mcp.tool(name="tvdb_search")(tvdb_search)
mcp.tool(name="tvdb_get_series_episodes")(tvdb_get_series_episodes)


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
