#!/usr/bin/env python
"""Manual end-to-end test of TVDB API integration and translation stripping.

This script tests all TVDB endpoints against the live API to verify that
the translation stripping logic works correctly when result_language is
configured.

Usage:
    TVDB_API_KEY=your_key uv run python tests/manual/test_e2e_translations.py

Requirements:
    - TVDB_API_KEY environment variable must be set
    - uv must be available to run the script in the project environment

This test is intentionally NOT part of the automated test suite because it
requires a live API key and makes real HTTP requests. Run it manually when
troubleshooting API integration or translation issues.
"""

import asyncio
import os
import sys

# Add project src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from thetvdb_mcp_server.rate_limiter import tvdb_rate_limiter
from thetvdb_mcp_server.tvdb_client import TvdbClient

errors = []


def check_record(record, endpoint):
    """Check that translation fields are stripped from a record."""
    if "translations" in record:
        errors.append(f"{endpoint}: 'translations' field not stripped")
    if "overviews" in record:
        errors.append(f"{endpoint}: 'overviews' field not stripped")
    if "nameTranslations" in record:
        errors.append(f"{endpoint}: 'nameTranslations' field not stripped")
    if "overviewTranslations" in record:
        errors.append(f"{endpoint}: 'overviewTranslations' field not stripped")


async def run_tests():
    api_key = os.environ.get("TVDB_API_KEY")
    if not api_key:
        print("ERROR: TVDB_API_KEY environment variable not set")
        sys.exit(1)

    # Use "eng" as result_language to test translation stripping
    client = TvdbClient(api_key, None, tvdb_rate_limiter, result_language="eng")

    print(f"Testing TVDB API integration with result_language='eng'")
    print(f"API key: {api_key[:4]}...{api_key[-4:]}")
    print()

    # Test get_series
    print("Testing get_series (ID: 362696)...")
    try:
        result = await client.get_series(362696)
        check_record(result, "get_series")
        print(f"  OK (name: {result.get('name', 'N/A')})")
    except Exception as e:
        errors.append(f"get_series: {e}")
        print(f"  FAILED: {e}")

    # Test get_series_extended
    print("Testing get_series_extended (ID: 362696)...")
    try:
        result = await client.get_series_extended(362696)
        check_record(result, "get_series_extended")
        print(f"  OK (name: {result.get('name', 'N/A')})")
    except Exception as e:
        errors.append(f"get_series_extended: {e}")
        print(f"  FAILED: {e}")

    # Test get_series_by_slug
    print("Testing get_series_by_slug (slug: the-witcher)...")
    try:
        result = await client.get_series_by_slug("the-witcher")
        check_record(result, "get_series_by_slug")
        print(f"  OK (name: {result.get('name', 'N/A')})")
    except Exception as e:
        errors.append(f"get_series_by_slug: {e}")
        print(f"  FAILED: {e}")

    # Test get_series_episodes
    print("Testing get_series_episodes (ID: 362696, season_type: default)...")
    try:
        result = await client.get_series_episodes(362696, "default")
        check_record(result.get("series", {}), "get_series_episodes.series")
        episodes = result.get("episodes", [])
        for i, ep in enumerate(episodes[:3]):
            check_record(ep, f"get_series_episodes.episode[{i}]")
        print(f"  OK ({len(episodes)} episodes)")
    except Exception as e:
        errors.append(f"get_series_episodes: {e}")
        print(f"  FAILED: {e}")

    # Test search
    print("Testing search (query: The Witcher, type: series)...")
    try:
        results = await client.search("The Witcher", type_="series", limit=1)
        for i, result in enumerate(results):
            check_record(result, f"search[{i}]")
        print(f"  OK ({len(results)} results)")
    except Exception as e:
        errors.append(f"search: {e}")
        print(f"  FAILED: {e}")

    # Test get_movie
    print("Testing get_movie (ID: 125759)...")
    try:
        result = await client.get_movie(125759)
        check_record(result, "get_movie")
        print(f"  OK (name: {result.get('name', 'N/A')})")
    except Exception as e:
        errors.append(f"get_movie: {e}")
        print(f"  FAILED: {e}")

    # Test get_movie_extended
    print("Testing get_movie_extended (ID: 125759)...")
    try:
        result = await client.get_movie_extended(125759)
        check_record(result, "get_movie_extended")
        print(f"  OK (name: {result.get('name', 'N/A')})")
    except Exception as e:
        errors.append(f"get_movie_extended: {e}")
        print(f"  FAILED: {e}")

    # Test get_movie_by_slug
    print("Testing get_movie_by_slug (slug: the-matrix)...")
    try:
        result = await client.get_movie_by_slug("the-matrix")
        check_record(result, "get_movie_by_slug")
        print(f"  OK (name: {result.get('name', 'N/A')})")
    except Exception as e:
        errors.append(f"get_movie_by_slug: {e}")
        print(f"  FAILED: {e}")

    # Find an episode ID for episode tests
    print("Searching for episode ID...")
    try:
        ep_search = await client.search("The Witcher S01E01", type_="episode", limit=1)
        if ep_search:
            ep_id = ep_search[0]["id"]
            print(f"  Found episode ID: {ep_id}")

            # Test get_episode
            print(f"Testing get_episode (ID: {ep_id})...")
            try:
                result = await client.get_episode(ep_id)
                check_record(result, "get_episode")
                print(f"  OK (name: {result.get('name', 'N/A')})")
            except Exception as e:
                errors.append(f"get_episode: {e}")
                print(f"  FAILED: {e}")

            # Test get_episode_extended
            print(f"Testing get_episode_extended (ID: {ep_id})...")
            try:
                result = await client.get_episode_extended(ep_id)
                check_record(result, "get_episode_extended")
                print(f"  OK (name: {result.get('name', 'N/A')})")
            except Exception as e:
                errors.append(f"get_episode_extended: {e}")
                print(f"  FAILED: {e}")
        else:
            print("  No episode found, skipping episode tests")
    except Exception as e:
        errors.append(f"episode search: {e}")
        print(f"  FAILED: {e}")

    if errors:
        print("\n" + "=" * 60)
        print(f"ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
