# Milotic — Trading MCP Gateway

Python MCP server (Strategic Analyst layer) for read-only market data and research.

**Phase 1 status:** Stub tools only. No Go backend calls yet. `GO_BACKEND_URL` in `.env` is documented for future use.

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Python** | **3.12+** (`requires-python` in `pyproject.toml`) |
| **uv** | [Install uv](https://docs.astral.sh/uv/getting-started/installation/) |

Check versions:

```bash
uv --version
uv python list    # ensure 3.12 is available
```

Install Python 3.12 via uv if needed:

```bash
uv python install 3.12
```

---

## 1. Enter the project

```bash
cd /path/to/fc/milotic
```

---

## 2. Install dependencies

Creates `.venv` and installs the `milotic` package in editable mode:

```bash
uv sync --all-extras --dev
```

This matches [CI](.github/workflows/ci.yml): FastMCP, httpx, pandas, pytest, ruff, and related packages.

---

## 3. Environment (optional for now)

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `GO_BACKEND_URL` | Future Go API base URL (not used yet) |
| `LOGIN_*` | Future auth (commented in `.env.example`) |
| `LOG_LEVEL` | Server logging level (default: `INFO`) |

The stub server does **not** call the backend even if `GO_BACKEND_URL` is set.

---

## 4. Verify the install

### Tests

```bash
uv run pytest
```

Expects tool `system_get_health` registered via `FileSystemProvider` (see `tests/test_server.py`).

### Lint

```bash
uv run ruff check .
```

---

## 5. Inspect tools (no stdio client needed)

The MCP app is defined in `src/milotic/app.py` (`mcp` object). Tools are auto-loaded from `src/milotic/components/`.

```bash
uv run fastmcp inspect src/milotic/app.py:mcp
```

JSON detail:

```bash
uv run fastmcp inspect src/milotic/app.py:mcp --format mcp
```

Expected tool (Phase 1):

- **`system_get_health`** — returns `status`, `phase`, `foundation`, `backend: not_connected`

---

## 6. Run the MCP server (stdio)

Default transport for Cursor / Claude Desktop:

```bash
uv run python src/milotic/server.py
```

Or as a module (after `uv sync`):

```bash
uv run python -m milotic.server
```

The process **blocks** on stdin/stdout (stdio MCP). That is normal — use an MCP client to talk to it.

Startup flow:

1. `load_dotenv()` — reads `.env` if present
2. Structured logging via `structlog`
3. `mcp.run()` — serves tools from `components/` (hot reload enabled in dev)

---

## 7. Connect from Cursor

Add to Cursor MCP settings (adjust the path to your machine):

```json
{
  "mcpServers": {
    "milotic": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/unio/go/src/fc/milotic",
        "python",
        "src/milotic/server.py"
      ]
    }
  }
}
```

Restart Cursor or reload MCP. You should see `system_get_health` in the tool list.

---

## 8. Optional: MCP Inspector

Use [MCP Inspector](https://github.com/modelcontextprotocol/inspector) with **stdio** transport and the same `uv run python src/milotic/server.py` command.

---

## Project layout

```
milotic/
├── fastmcp.json              # FastMCP project metadata
├── pyproject.toml
├── uv.lock
├── .env.example
├── src/milotic/
│   ├── app.py                # FastMCP + FileSystemProvider (tool discovery)
│   ├── server.py             # Entry: logging, dotenv, mcp.run()
│   ├── components/           # MCP tools (*.py) — auto-discovered
│   │   └── system.py         # e.g. system_get_health
│   ├── api/                  # Future httpx clients
│   ├── services/             # Future TA / signals
│   └── utils/                # logging, decorators, errors
└── tests/
    └── test_server.py
```

New tools belong under **`src/milotic/components/`** (discovered by `FileSystemProvider` in `app.py`). See [CONTRIBUTING.md](./CONTRIBUTING.md) for naming and decorator rules.

---

## Adding a new tool (quick)

1. Add a file under `src/milotic/components/` (e.g. `market.py`).
2. Use `@tool()` and `@milotic_tool`; name tools `category_action_entity` (e.g. `market_get_quote`).
3. Add a test in `tests/` and run `uv run pytest`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Python version rejected | Use **3.12+**: `uv python install 3.12` then `uv sync` |
| `ModuleNotFoundError: milotic` | Run from repo root after `uv sync` |
| Old paths like `src/server.py` | Use `src/milotic/server.py` and `src/milotic/app.py:mcp` |
| No tools listed | Ensure files under `components/` use `@tool()` + `@milotic_tool` |
| Server appears to hang | Expected for stdio; connect via Cursor or MCP Inspector |
| Tests fail on naming | Names must follow `category_action_entity` (e.g. `system_get_health`) |

---

## Roadmap

See [Phase-01.md](./Phase-01.md) for deferred work: Go auth, `BaseClient`, market tools, and live API verification.

---

## Quick reference

```bash
uv sync --all-extras --dev
cp .env.example .env          # optional
uv run pytest
uv run ruff check .
uv run fastmcp inspect src/milotic/app.py:mcp
uv run python src/milotic/server.py
```
