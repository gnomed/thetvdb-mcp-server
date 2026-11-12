<!-- This file is copy-pasted into Docker Hub as the repository overview.
     It is NOT developer documentation. Do not read this for project context.
     Edit it only when tools, config, Docker Compose examples, or endpoints change. -->
# thetvdb-mcp-server

A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes [TVDB](https://thetvdb.com/) TV series data to AI assistants via the Model Context Protocol.

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/) is an open standard that lets AI assistants call external tools and services. This server implements MCP over HTTP so any MCP-compatible AI application can query TV series information from TVDB.

---

## Quick Start

### Docker Compose

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

---

## Configuration

Create a `config.toml` in the working directory (or pass `--config <path>`):

```toml
[server]
host = "0.0.0.0"  # address for the MCP server to listen on (0.0.0.0 = all interfaces)
port = 8080        # port for the MCP server to listen on

[logging]
level = "info"     # log verbosity: trace, debug, info, warning, error, critical

[tvdb]
api_key = "YOUR_API_KEY"  # TVDB API key from https://thetvdb.com/dashboard/account/apikey (required)
# Optional: subscriber PIN for extended access
# pin = ""
# Optional: 3-character ISO 639-2 language code (e.g. "eng"); when set, language params are hidden from tool schemas and applied automatically
# primary_language = ""
```

---

## Connecting an AI Application

Point your MCP-compatible AI application at the server's MCP endpoint:

```
http://<host>:<port>/mcp
```

For example, if the server is running on `192.168.1.10` with the default port:

```
http://192.168.1.10:8080/mcp
```

Consult your AI application's documentation for how to register an MCP server.

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

## Example System Prompt

Copy and adapt this prompt to give your AI assistant clear guidance on using the tools.

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

## License

Copyright (c) Sean Esopenko 2026

Licensed under the [GNU General Public License v3.0](LICENSE.txt).

---

## Acknowledgement: Riding on the Backs of Giants

This project was built with the assistance of [Claude Code](https://claude.ai/code), an AI coding assistant developed by Anthropic.

AI assistants like Claude are trained on enormous amounts of data — much of it written by the open-source community: the libraries, tools, documentation, and decades of shared knowledge that developers have contributed freely. Without that foundation, tools like this would not be possible.

In recognition of that debt, this project is released under the [GNU General Public License v3.0](LICENSE.txt). The GPL ensures that this code — and any derivative work — remains open source. It is a small act of reciprocity: giving back to the commons that made it possible.

To every developer who ever pushed a commit to a public repo, wrote a Stack Overflow answer, or published a package under an open license — thank you.
