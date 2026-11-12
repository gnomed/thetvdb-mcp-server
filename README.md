# thetvdb-mcp-server

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE.txt)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/)

A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes [TVDB](https://thetvdb.com/) v4 API endpoints as tools for AI assistants.

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/) is an open standard that lets AI assistants call external tools and services. This server implements MCP over HTTP so any MCP-compatible AI application can query TV series information from TVDB.

---

## Prerequisites

- **Docker** — for the Docker Compose deployment path
- **uv** — for the source deployment path (see [Installing uv](https://docs.astral.sh/uv/getting-started/installation/))

---

## Quick Start

### Option A — Docker Compose

1. Create a `docker-compose.yml`:

   ```yaml
   services:
     thetvdb-mcp-server:
       image: thetvdb-mcp-server:latest
       ports:
         - "8080:8080"
       volumes:
         - ./config.toml:/config/config.toml:ro
       restart: unless-stopped
   ```

2. Copy the example config and edit it:

   ```bash
   cp config.toml.example config.toml
   ```

3. Start the server:

   ```bash
   docker compose up -d
   ```

### Option B — Run from Source

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already.

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Copy the example config and edit it:

   ```bash
   cp config.toml.example config.toml
   ```

4. Start the server:

   ```bash
   uv run python -m thetvdb_mcp_server
   ```

---

## Security

This server has **no authentication** on its MCP endpoint. It is designed for LAN use only.

**Do not expose this server directly to the internet.**

If you need to access it remotely, place it behind a reverse proxy that handles TLS termination and access control. Configuring a reverse proxy is outside the scope of this project.

---

## Configuration

Create a `config.toml` in the working directory (or pass `--config <path>`):

```toml
[server]
host = "0.0.0.0"
port = 8080

[logging]
level = "info"

[tvdb]
api_key = "YOUR_API_KEY"
```

### [server]

| Key | Default | Description |
|---|---|---|
| `host` | `"0.0.0.0"` | Address for the MCP server to listen on. `0.0.0.0` binds all interfaces. |
| `port` | `8080` | Port for the MCP server to listen on. |

### [logging]

| Key | Default | Description |
|---|---|---|
| `level` | `"info"` | Log verbosity. One of: `trace`, `debug`, `info`, `warning`, `error`, `critical`. |

### [tvdb]

| Key | Default | Description |
|---|---|---|
| `api_key` | *(required)* | Your TVDB API key. |
| `pin` | `null` | Optional subscriber PIN for extended access. |

---

## Connecting an AI Application

This server uses the **Streamable HTTP** MCP transport. Clients communicate via HTTP POST with streaming responses — opening the endpoint in a browser will return a `Not Acceptable` error, which is expected.

Point your MCP-compatible AI application at the server's MCP endpoint:

```
http://<host>:<port>/mcp
```

For example, if the server is running on `192.168.1.10` with the default port:

```
http://192.168.1.10:8080/mcp
```

Consult your AI application's documentation for how to register an MCP server. Ensure it supports the Streamable HTTP transport (most modern MCP clients do).

---

## Example System Prompt

XML is preferred over markdown for system prompts because explicit named tags give unambiguous semantic meaning — the AI always knows exactly what each block contains. Markdown headings require inference and are more likely to be misinterpreted.

Copy and adapt this prompt to give your AI assistant clear guidance on using the tools.

> **Tip — let an LLM write this for you.** XML-structured system prompts are effective but unfamiliar to most developers and tedious to write by hand. A quick conversation with any capable LLM (describe your tools, what they do, and how you want the assistant to behave) will produce a well-structured prompt you can drop straight in. The results are often better than anything written manually as plain text or markdown.
>
> * XML tags act like labeled folders — the model knows exactly where each piece of information starts and ends
> * Training data is full of structured markup, so models already "think" in tags naturally
> * Tags prevent the model from confusing your instructions with the content it's working on
```xml
<system>
  <role>
    You are a helpful assistant with access to a TVDB MCP server. Use the available
    tools to look up TV series information accurately and efficiently.
  </role>
  <tools>
    <tool name="tvdb_search">Search TVDB for series, movies, people, episodes, and more by title, alias, or translation. Returns up to 10 results by default.</tool>
    <tool name="tvdb_get_series">Fetch a series base record by its numeric TVDB ID.</tool>
    <tool name="tvdb_get_series_extended">Fetch a series extended record with optional characters and artworks arrays.</tool>
    <tool name="tvdb_get_series_episodes">Fetch all episodes for a series by season ordering type.</tool>
    <tool name="tvdb_get_series_by_slug">Fetch a series record by its slug (e.g. "doctor-who").</tool>
    <tool name="tvdb_get_season">Fetch a season base record by its numeric TVDB ID.</tool>
    <tool name="tvdb_get_season_extended">Fetch a season extended record by its numeric TVDB ID.</tool>
    <tool name="tvdb_get_artwork">Fetch an artwork base record by its numeric TVDB ID.</tool>
    <tool name="tvdb_get_artwork_extended">Fetch an artwork extended record by its numeric TVDB ID.</tool>
    <tool name="tvdb_get_episode">Fetch an episode base record by its numeric TVDB ID.</tool>
    <tool name="tvdb_get_episode_extended">Fetch an episode extended record by its numeric TVDB ID.</tool>
    <tool name="tvdb_get_person">Fetch a person base record by their numeric TVDB ID.</tool>
    <tool name="tvdb_get_person_extended">Fetch a person extended record by their numeric TVDB ID.</tool>
  </tools>
  <guidelines>
    <item>Use tvdb_search to find a TVDB ID before calling other tools that require one.</item>
    <item>Use tvdb_get_series_extended with include_characters or include_artworks only when the user needs that data, as those arrays can be large.</item>
    <item>Use tvdb_get_series_episodes to retrieve episode lists; specify season_type (e.g. "default", "aired", "dvd") as needed.</item>
    <item>If you only have a series title and not an ID, search first — never guess IDs.</item>
  </guidelines>
</system>
```

---

## Available Tools

| Tool | Description |
|---|---|
| `tvdb_search` | Search TVDB for series, movies, people, episodes, and more. Returns up to 10 results by default. |
| `tvdb_get_series` | Fetch a series base record by its numeric TVDB ID. |
| `tvdb_get_series_extended` | Fetch a series extended record with optional characters and artworks arrays. |
| `tvdb_get_series_episodes` | Fetch all episodes for a series by season ordering type. |
| `tvdb_get_series_by_slug` | Fetch a series record by its slug (e.g. "doctor-who"). |
| `tvdb_get_season` | Fetch a season base record by its numeric TVDB ID. |
| `tvdb_get_season_extended` | Fetch a season extended record by its numeric TVDB ID. |
| `tvdb_get_artwork` | Fetch an artwork base record by its numeric TVDB ID. |
| `tvdb_get_artwork_extended` | Fetch an artwork extended record by its numeric TVDB ID. |
| `tvdb_get_episode` | Fetch an episode base record by its numeric TVDB ID. |
| `tvdb_get_episode_extended` | Fetch an episode extended record by its numeric TVDB ID. |
| `tvdb_get_person` | Fetch a person base record by their numeric TVDB ID. |
| `tvdb_get_person_extended` | Fetch a person extended record by their numeric TVDB ID. |

---

## Architecture

The server follows a clean separation of concerns:

| File | Purpose |
|---|---|
| `src/thetvdb_mcp_server/tools.py` | Tool implementations — one function per tool, no framework coupling |
| `src/thetvdb_mcp_server/server.py` | FastMCP wiring — dynamic tool registration and server entrypoint |
| `src/thetvdb_mcp_server/tvdb_client.py` | TVDB API client — wraps the official library with rate limiting |
| `src/thetvdb_mcp_server/rate_limiter.py` | Async rate limiter — enforces 1 TVDB API call per second |
| `src/thetvdb_mcp_server/config.py` | TOML config loading — typed dataclasses for `[server]`, `[logging]`, and `[tvdb]` sections |
| `src/thetvdb_mcp_server/logging.py` | Structured JSON logger |

### Dynamic tool registration

Tools are not registered via `@mcp.tool()` decorators at import time. Instead, `main()` in `server.py` loads configuration, initialises the shared TVDB client, and then explicitly registers each tool.

### Adding a tool

1. Add a function to `src/thetvdb_mcp_server/tools.py` with a Google-style docstring and full type annotations.
2. Register it in `main()` in `src/thetvdb_mcp_server/server.py` via `mcp.tool(name="...")(function)`.
3. Add a unit test in `tests/unit/`.
4. Add a row to the **Available Tools** table in this README.

---

## Running Tests

```bash
uv run pytest tests/unit/
```

---

## Contributing / Maintaining

See [MAINTAINERS.md](MAINTAINERS.md) for setup, development commands, and how to run tests.

---

## License

Copyright (c) Sean Esopenko 2026

This project is licensed under the [GNU General Public License v3.0](LICENSE.txt).

---

## Acknowledgement: Riding on the Backs of Giants

This project was built with the assistance of [Claude Code](https://claude.ai/code), an AI coding assistant developed by Anthropic.

AI assistants like Claude are trained on enormous amounts of data — much of it written by the open-source community: the libraries, tools, documentation, and decades of shared knowledge that developers have contributed freely. Without that foundation, tools like this would not be possible.

In recognition of that debt, this project is released under the [GNU General Public License v3.0](LICENSE.txt). The GPL ensures that this code — and any derivative work — remains open source. It is a small act of reciprocity: giving back to the commons that made it possible.

To every developer who ever pushed a commit to a public repo, wrote a Stack Overflow answer, or published a package under an open license — thank you.
