# AGENTS.md

## Commands

```bash
uv sync                              # install deps
uv run python -m thetvdb_mcp_server  # run server (needs config.toml)
uv run pytest tests/unit/            # run tests
```

Quality check order:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src/
uv run pytest tests/unit/
```

## Architecture

- Single package: `src/thetvdb_mcp_server/`. Entry point is `server.py:main()` (also `__main__.py` for `python -m`).
- **Tools are NOT decorated with `@mcp.tool()`**. They are plain async functions in `tools.py` registered dynamically in `main()` via `mcp.tool(name="...")(func)`.
- All tools require `init_tools(config)` to be called at startup (sets the module-level `_client`). Calling a tool before that raises `RuntimeError`.

## Adding a tool

1. Add the async function to `tools.py` (Google-style docstring, full type hints).
2. Register it in `main()` in `server.py`.
3. Add unit tests in `tests/unit/`.
4. Add a row to the "Available Tools" table in `README.md`.

## Testing

- `pytest-asyncio` runs in `auto` mode — no `@pytest.mark.asyncio` needed.
- Tests mock the client by patching the module global: `patch("thetvdb_mcp_server.tools._client", mock)`. See `tests/unit/test_tools.py` for the pattern.
- No integration tests or external services required.

## Committing and pushing

- **Wait for user request**: Do not commit or push changes until the user explicitly asks for it.
- Give the user a chance to review, approve, or request changes to the work before it is committed.
- Only commit and push when the user says something like "commit and push" or "please commit this".

## Key quirks

- Rate limiting: a single shared `tvdb_rate_limiter` (1 call/sec) in `rate_limiter.py` wraps every TVDB API call.
- `TvdbClient.get_series_extended` always calls the API with `short=False` when any array is requested, then strips unrequested arrays client-side (the API only supports all-or-nothing).
- Config is TOML (`config.toml` by default, `--config <path>` to override). The `[tvdb]` section requires `api_key`; `pin` is optional.
- `mypy` is configured with `mypy_path = "src"` and checks only `thetvdb_mcp_server`.
