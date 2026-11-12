# Maintainers Guide

Developer reference for setting up and working on this project.

---

## Setup

### 1. Install uv

Follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Install dependencies

```bash
uv sync
```

---

## Code Quality

Run all quality checks:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src/
uv run pytest tests/unit/
```

---

## Running the Server

### Locally

```bash
uv run python -m thetvdb_mcp_server
```

Pass `--config <path>` to use a non-default config file location.

### Via Docker

Build the image:

```bash
docker build -t thetvdb-mcp-server .
```

Start the server (requires `config.toml` in the current directory):

```bash
docker compose up
```

---

## Running Tests

```bash
uv run pytest tests/unit/
```

---

## Managing Dependencies

### Add a runtime dependency

```bash
uv add <package>
```

### Add a dev dependency

```bash
uv add --dev <package>
```

### Upgrade all dependencies

```bash
uv lock --upgrade
```
