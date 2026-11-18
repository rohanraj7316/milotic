# Milotic — Trading MCP Gateway

Python Model Context Protocol (MCP) server providing secure gateway integration for trading systems, account portfolio management, and market books.

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Python** | **3.12+** (`requires-python` in `pyproject.toml`) |
| **uv** | Fast Python package installer and resolution tool ([Install uv](https://docs.astral.sh/uv/getting-started/installation/)) |

```bash
uv --version
uv python list          # Ensure 3.12+ is available
uv python install 3.12  # Install Python 3.12 if needed
```

---

## 1. Environment Setup

Clone the repository and sync the development environment:

```bash
cd /path/to/milotic
uv sync --all-extras --dev
```

---

## 2. Configuration

Create your local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

### Required Credentials

| Variable | Purpose | Header | Example |
|----------|---------|--------|---------|
| `API_CLIENT_ID` | Client app identifier registered with Axis Direct | `x-api-client-id` | `GALAXY_WEBAPP` |
| `AUTHORIZATION` | Master client authorization token | `authorization` | `your-authorization-token` |

### Backend Endpoints & Defaults (Optional Overrides)

| Variable | Purpose | Default |
|----------|---------|---------|
| `LOGIN_BACKEND_URL` | Base URL for SSO login & authentication | `https://welcome-api.axisdirect.in` |
| `INVESTOR_BACKEND_URL` | Base URL for portfolio, books & trading orders | `https://invest-api.axisdirect.in` |
| `HANDSHAKE_URL` | RSA public key handshake endpoint | `https://welcome-api.axisdirect.in/handshake` |
| `CRYPTO_ENABLED` | Master toggle for AES/RSA payload encryption | `true` |
| `API_SESSION_SECRET` | 32-char hex AES session key | Auto-generated random secret |
| `MAX_CONCURRENT_REQUESTS` | Per-client request concurrency cap | `20` |
| `CIRCUIT_BREAKER_THRESHOLD` | Consecutive failures before circuit opens | `5` |
| `LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

---

## 3. Testing & MCP Inspector

For a full testing guide, see [docs/TESTING.md](file:///Users/unio/go/src/ds/milotic/docs/TESTING.md).

### Interactive UI Testing (MCP Inspector)

Launch the interactive FastMCP Inspector in your browser:

```bash
uv run fastmcp dev inspector src/app.py:mcp
```

This starts the MCP Inspector Web UI at `http://localhost:6274` with an auto-generated `MCP_INSPECTOR_API_TOKEN`. Open `http://localhost:6274` in your browser to interactively test all 8 active MCP tools.

### CLI Inspection & Validation

```bash
# Verify tool registration
uv run fastmcp inspect src/app.py:mcp

# View full JSON schema for all tools
uv run fastmcp inspect src/app.py:mcp --format mcp

# Run automated tests and linter
uv run pytest
uv run ruff check .
```

---

## 4. Run MCP Server

Start the MCP server using stdio transport:

```bash
uv run python src/server.py
```

Or in SSE (HTTP) mode:

```bash
MCP_TRANSPORT=sse MCP_PORT=8000 uv run python src/server.py
```

---

## 5. MCP Client Integration

### Cursor Integration

Add to your Cursor settings (`.cursor/mcp.json` or Global MCP Settings):

```json
{
  "mcpServers": {
    "milotic": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/milotic",
        "python",
        "src/server.py"
      ],
      "env": {
        "PYTHONPATH": "src",
        "API_CLIENT_ID": "GALAXY_WEBAPP",
        "AUTHORIZATION": "your-authorization-token"
      }
    }
  }
}
```

### Claude Desktop / Claude Code Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "milotic": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/milotic",
        "python",
        "src/server.py"
      ],
      "env": {
        "PYTHONPATH": "src",
        "API_CLIENT_ID": "GALAXY_WEBAPP",
        "AUTHORIZATION": "your-authorization-token"
      }
    }
  }
}
```

### Antigravity Integration

Milotic is configured as a workspace plugin under `.agents/plugins/milotic/` (or via `.agents/mcp_config.json`):

```json
{
  "mcpServers": {
    "milotic": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/unio/go/src/ds/milotic",
        "python",
        "src/server.py"
      ],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

*For global Antigravity access across all workspaces, merge the `milotic` server block into `~/.gemini/config/mcp_config.json`.*

---

## Project Layout

```
milotic/
├── pyproject.toml         # Project dependencies and configuration
├── uv.lock                # Locked dependency tree
├── .env.example           # Example environment variables
├── README.md              # Project documentation
├── LICENSE                # License information
├── src/
│   ├── app.py             # FastMCP application & tool auto-discovery
│   ├── server.py          # Server entrypoint (logging & stdio runner)
│   ├── config.py          # Pydantic Settings & backend URL mapping
│   ├── components/        # MCP tools organized by category
│   │   ├── system/        # system_get_health, system_connect_start, …
│   │   ├── books/         # books_get_portfolio, books_get_orders, …
│   │   └── trading/       # trading_place_order, trading_cancel_order, …
│   ├── api/               # API BaseClient, RSA handshake, & session encryption
│   └── utils/             # Redacted logging, AES-GCM crypto, errors, decorators
└── tests/                 # Pytest test suite matching component categories
```

---

## Adding a New Tool

1. Create a Python file under `src/components/<category>/`, for example `src/components/books/holdings.py`.
2. Define the tool using `@tool()` and `@milotic_tool` decorators following the `category_action_entity` naming pattern:

```python
from fastmcp.tools import tool
from utils.decorators import milotic_tool
from api.base import BaseClient


@tool()
@milotic_tool
async def books_get_holdings(symbol: str | None = None) -> dict:
    """Retrieve holdings from books account with optional symbol filtering."""
    client = await BaseClient.instance("investor")
    params = {"symbol": symbol} if symbol else {}
    return await client.get("/holdings", params=params)
```

3. Add corresponding unit/contract tests under `tests/<category>/` and verify:

```bash
uv run pytest
```

---

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `ModuleNotFoundError: src` | Ensure commands are executed from the repo root with `uv run` and `PYTHONPATH=src` |
| `BackendConnectionError` | Verify network access to `LOGIN_BACKEND_URL` / `INVESTOR_BACKEND_URL` and valid credentials in `.env` |
| Tools not showing in MCP client | Verify tool files in `src/components/` use both `@tool()` and `@milotic_tool` |
| Server process blocks | Expected behavior for stdio transport; connect via an MCP client or Inspector |
| Circuit breaker opens | Backend endpoint exceeded failure threshold; inspect backend status |

---

## Quick Reference Commands

```bash
uv sync --all-extras --dev      # Install dependencies
cp .env.example .env            # Configure environment
uv run pytest                   # Run test suite
uv run ruff check .             # Run linter
uv run fastmcp inspect src/app.py:mcp  # Inspect MCP tools
uv run python src/server.py     # Run MCP server
```
