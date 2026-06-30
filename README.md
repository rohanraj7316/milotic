# Milotic — Trading MCP Gateway

Python MCP server (Strategic Analyst layer) for read-only market data and research.

**Phase 2 status:** Multi-backend scaffolding complete. Tools are structured by category; real backend calls replace stubs as the API spec lands.

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Python** | **3.12+** (`requires-python` in `pyproject.toml`) |
| **uv** | [Install uv](https://docs.astral.sh/uv/getting-started/installation/) |

```bash
uv --version
uv python list    # ensure 3.12 is available
uv python install 3.12  # if not listed
```

---

## 1. Enter the project

```bash
cd /path/to/milotic
```

---

## 2. Install dependencies

```bash
uv sync --all-extras --dev
```

---

## 3. Environment

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `MARKET_BACKEND_URL` | Base URL for the market data backend |
| `ACCOUNT_BACKEND_URL` | Base URL for the account backend |
| `TRADING_BACKEND_URL` | Base URL for the trading backend |
| `RESEARCH_BACKEND_URL` | Base URL for the research/signals backend |
| `CRYPTO_ENABLED` | Master toggle for AES payload encryption (default: `true`) |
| `API_CLIENT_ID` | Sent as `X-API-Client-Id` header |
| `API_SESSION_SECRET` | 32+ byte AES key, client-held, never transmitted plaintext |
| `MAX_CONCURRENT_REQUESTS` | Per-client request concurrency cap (default: `20`) |
| `CIRCUIT_BREAKER_THRESHOLD` | Consecutive failures before circuit opens (default: `5`) |
| `LOG_LEVEL` | Server logging level (default: `INFO`) |

---

## 4. Verify the install

```bash
uv run pytest
uv run ruff check .
```

---

## 5. Inspect tools

```bash
uv run fastmcp inspect src/milotic/app.py:mcp
uv run fastmcp inspect src/milotic/app.py:mcp --format mcp  # JSON detail
```

---

## 6. Run the MCP server (stdio)

```bash
uv run python src/milotic/server.py
```

The process blocks on stdin/stdout — use an MCP client to talk to it.

---

## 7. Connect from Cursor

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

---

## Project layout

```
milotic/
├── pyproject.toml
├── .env.example
└── src/milotic/
    ├── app.py                # FastMCP + per-category FileSystemProviders
    ├── server.py             # Entry: logging, dotenv, mcp.run()
    ├── config.py             # Pydantic Settings + backend_url(category) helper
    ├── components/           # MCP tools — auto-discovered by category
    │   ├── system/           # system_get_health
    │   ├── market/           # market_get_quote, market_get_ohlcv, …
    │   ├── account/          # account_list_positions, account_get_balance, …
    │   ├── trading/          # trading_place_order, trading_cancel_order, …
    │   └── research/         # research_get_signal, research_get_rsi, …
    ├── api/
    │   ├── base.py           # BaseClient (per-category singleton, circuit breaker, rate limit)
    │   ├── handshake.py      # RSA public-key fetch with 1-hour cache
    │   └── session.py        # RSA-OAEP session key encryption
    ├── services/             # Business logic (TA indicators, aggregation helpers)
    │   ├── market.py
    │   ├── technicals.py     # pandas-ta wrappers
    │   ├── account.py
    │   └── research.py
    └── utils/                # logging, crypto (AES-256-GCM), errors, decorators
```

---

## Adding a new tool

1. Add a file under the correct category directory, e.g. `src/milotic/components/market/trades.py`.
2. Apply both decorators; follow `category_action_entity` naming:

```python
from fastmcp.tools import tool
from utils.decorators import milotic_tool
from api.base import BaseClient

@tool()
@milotic_tool
async def market_get_trades(symbol: str, limit: int = 50) -> dict:
    """Description for the LLM — what it does and why to call it."""
    client = await BaseClient.instance("market")
    return await client.get(f"/trades/{symbol}", params={"limit": limit})
```

3. Add a test in `tests/<category>/` and run `uv run pytest`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Python version rejected | Use **3.12+**: `uv python install 3.12` then `uv sync` |
| `ModuleNotFoundError: milotic` | Run from repo root after `uv sync` |
| `BackendConnectionError: No backend URL configured for category 'X'` | Set `X_BACKEND_URL` in `.env` |
| No tools listed | Ensure files under `components/<category>/` use `@tool()` + `@milotic_tool` |
| Server appears to hang | Expected for stdio; connect via Cursor or MCP Inspector |
| Tests fail on naming | Names must follow `category_action_entity` with an allowed category prefix |
| Circuit breaker open | Backend returned too many errors; restart server or wait for reset |

---

## Quick reference

```bash
uv sync --all-extras --dev
cp .env.example .env
uv run pytest
uv run ruff check .
uv run fastmcp inspect src/milotic/app.py:mcp
uv run python src/milotic/server.py
```
