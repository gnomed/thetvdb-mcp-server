#!/usr/bin/env python
"""Generate JSON output files for all TVDB MCP tools for testing/development.

This script calls every tool in src/thetvdb_mcp_server/tools.py with known-good
IDs, saves each response to a well-named JSON file in tmp_test_output/, and
reports errors. It also exercises "options off" vs "options on" variants for
extended endpoints.

Usage:
    TVDB_API_KEY=your_key uv run python tests/manual/tool_output_generator.py

Requirements:
    - TVDB_API_KEY environment variable must be set
    - uv must be available to run the script in the project environment
"""

import asyncio
import json
import os
import sys
from typing import Any

# Add project src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from thetvdb_mcp_server import tools
from thetvdb_mcp_server.config import AppConfig, LoggingConfig, ServerConfig, TvdbConfig

OUTPUT_DIR = "tmp_test_output"
errors = []
calls = 0
file_num = 0

# IDs to discover at runtime
reacher_series_id = None
reacher_season_id = None
reacher_episode_id = None
reacher_person_id = None
reacher_artwork_id = None
matrix_movie_id = None


def next_file_num() -> int:
    global file_num
    file_num += 1
    return file_num


def save_json(name: str, data: Any, indent: int = 2) -> None:
    """Write data to a JSON file in the output directory."""
    num = next_file_num()
    padded = f"{num:02d}"
    path = os.path.join(OUTPUT_DIR, f"{padded}_{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    print(f"  -> {path}")


async def run_tool(name: str, func, *args, **kwargs) -> Any:
    """Run a tool, save its output, and track errors."""
    global calls
    calls += 1
    print(f"  [{calls}] {name}")
    try:
        result = await func(*args, **kwargs)
        save_json(name, result)
        return result
    except Exception as e:
        errors.append(f"{name}: {e}")
        print(f"    ERROR: {e}")
        return None


async def run_tests() -> int:
    global calls, file_num, reacher_series_id, reacher_season_id, reacher_episode_id
    global reacher_person_id, reacher_artwork_id, matrix_movie_id

    api_key = os.environ.get("TVDB_API_KEY")
    if not api_key:
        print("ERROR: TVDB_API_KEY environment variable not set")
        return 1

    config = AppConfig(
        server=ServerConfig(host="localhost", port=8000),
        logging=LoggingConfig(level="INFO"),
        tvdb=TvdbConfig(api_key=api_key, result_language="eng"),
    )
    tools.init_tools(config)

    # Clean output directory
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            os.remove(os.path.join(OUTPUT_DIR, f))
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    calls = 0
    file_num = 0

    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)

    def strip_id_prefix(id_str: str) -> str:
        """Strip type prefix from ID (e.g. 'series-366924' -> '366924')."""
        parts = str(id_str).split("-")
        return parts[-1]

    # 1. Search for Reacher to get series ID
    print("\nSearching for Reacher...")
    results = await tools.tvdb_search(query="Reacher", type="series", limit=5)
    save_json("reacher_search", results)
    for r in results:
        if r.get("type") == "series" and "reacher" in r.get("name", "").lower():
            reacher_series_id = strip_id_prefix(r["id"])
            break
    if not reacher_series_id:
        errors.append("Could not find Reacher series ID")
        return 1
    print(f"  Reacher series ID: {reacher_series_id}")

    # 2. Search for Matrix movie to get movie ID
    print("Searching for Matrix...")
    results = await tools.tvdb_search(query="The Matrix", type="movie", limit=5)
    save_json("matrix_search", results)
    for r in results:
        if r.get("type") == "movie" and "matrix" in r.get("name", "").lower():
            matrix_movie_id = strip_id_prefix(r["id"])
            break
    if not matrix_movie_id:
        errors.append("Could not find Matrix movie ID")
        return 1
    print(f"  Matrix movie ID: {matrix_movie_id}")

    # 3. Series tools
    print("\nSeries tools:")
    await run_tool(
        "series_reacher_options_off",
        tools.tvdb_get_series,
        reacher_series_id,
        include_characters=False,
        include_artworks=False,
        include_trailers=False,
        include_lists="none",
        include_tags=False,
        include_content_ratings=False,
        include_remote_ids=False,
        include_seasons="none",
        include_companies=False,
    )

    await run_tool(
        "series_reacher_options_on",
        tools.tvdb_get_series,
        reacher_series_id,
        include_characters=True,
        include_artworks=True,
        include_trailers=True,
        include_lists="all",
        include_tags=True,
        include_content_ratings=True,
        include_remote_ids=True,
        include_seasons="all",
        include_companies=True,
    )

    await run_tool("series_reacher_by_slug", tools.tvdb_get_series_by_slug, "reacher")

    # Extract season, episode, artwork, and person IDs from extended result
    extended = await tools.tvdb_get_series(
        reacher_series_id,
        include_characters=True,
        include_artworks=True,
        include_seasons="all",
    )
    if extended:
        # Pick first non-zero season (skip season 0)
        seasons = [s for s in extended.get("seasons", []) if s.get("number") is not None and s.get("number") > 0]
        if seasons:
            reacher_season_id = seasons[0]["id"]
        else:
            # Fall back to first season with an id
            for s in extended.get("seasons", []):
                if s.get("id"):
                    reacher_season_id = s["id"]
                    break
        artworks = extended.get("artworks", [])
        if artworks:
            reacher_artwork_id = artworks[0]["id"]
        characters = extended.get("characters", [])
        if characters:
            reacher_person_id = strip_id_prefix(characters[0].get("peopleId"))

    # 4. Season tools
    print("\nSeason tools:")
    if reacher_season_id:
        await run_tool(
            "season_reacher_options_off",
            tools.tvdb_get_season,
            reacher_season_id,
            include_artworks=False,
            include_companies=False,
            include_episodes=False,
            include_trailers=False,
            include_tags=False,
        )
        await run_tool(
            "season_reacher_options_on",
            tools.tvdb_get_season,
            reacher_season_id,
            include_artworks=True,
            include_companies=True,
            include_episodes=True,
            include_trailers=True,
            include_tags=True,
        )

    # 5. Episode tools
    print("\nEpisode tools:")
    episodes_result = await tools.tvdb_get_series_episodes(reacher_series_id)
    save_json("series_reacher_episodes", episodes_result)
    if episodes_result:
        episodes = episodes_result.get("episodes", [])
        if episodes:
            reacher_episode_id = episodes[0]["id"]

    if reacher_episode_id:
        await run_tool(
            "episode_reacher_options_off",
            tools.tvdb_get_episode,
            reacher_episode_id,
            include_awards=False,
            include_characters=False,
            include_companies=False,
            include_seasons=False,
            include_content_ratings=False,
            include_remote_ids=False,
            include_tags=False,
            include_trailers=False,
        )
        await run_tool(
            "episode_reacher_options_on",
            tools.tvdb_get_episode,
            reacher_episode_id,
            include_awards=True,
            include_characters=True,
            include_companies=True,
            include_seasons=True,
            include_content_ratings=True,
            include_remote_ids=True,
            include_tags=True,
            include_trailers=True,
        )

    # 6. Artwork tools
    print("\nArtwork tools:")
    if reacher_artwork_id:
        await run_tool(
            "artwork_reacher",
            tools.tvdb_get_artwork,
            reacher_artwork_id,
        )

    # 7. Person tools
    print("\nPerson tools:")
    if reacher_person_id:
        await run_tool(
            "person_reacher_options_off",
            tools.tvdb_get_person,
            reacher_person_id,
            include_awards=False,
            include_characters=False,
            include_biographies=False,
            include_remote_ids=False,
            include_tags=False,
        )
        await run_tool(
            "person_reacher_options_on",
            tools.tvdb_get_person,
            reacher_person_id,
            include_awards=True,
            include_characters=True,
            include_biographies=True,
            include_remote_ids=True,
            include_tags=True,
        )

    # 8. Movie tools
    print("\nMovie tools:")
    await run_tool(
        "movie_matrix_options_off",
        tools.tvdb_get_movie,
        matrix_movie_id,
        include_characters=False,
        include_artworks=False,
        include_trailers=False,
        include_lists="none",
        include_tags=False,
        include_content_ratings=False,
        include_remote_ids=False,
        include_companies=False,
        include_awards=False,
        include_releases=False,
    )
    await run_tool(
        "movie_matrix_options_on",
        tools.tvdb_get_movie,
        matrix_movie_id,
        include_characters=True,
        include_artworks=True,
        include_trailers=True,
        include_lists="all",
        include_tags=True,
        include_content_ratings=True,
        include_remote_ids=True,
        include_companies=True,
        include_awards=True,
        include_releases=True,
    )
    await run_tool("movie_matrix_by_slug", tools.tvdb_get_movie_by_slug, "the-matrix")

    # 9. Additional search/episodes tests
    print("\nAdditional search/episodes:")
    await run_tool("search_matrix_general", tools.tvdb_search, query="Matrix")
    await run_tool(
        "series_reacher_episodes_page1",
        tools.tvdb_get_series_episodes,
        reacher_series_id,
        season_type="default",
        page=1,
    )

    print("\n" + "=" * 60)
    print(f"Total tool calls: {calls}")
    print(f"Total output files: {file_num}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nAll tools executed successfully!")
    print(f"Output files written to: {OUTPUT_DIR}/")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
