# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync --all-extras --dev   # install deps into .venv
uv run pytest                # run all tests
uv run pytest tests/test_server.py  # run a single test file
uv run ruff check .          # lint
uv run fastmcp inspect src/milotic/app.py:mcp  # list registered tools
uv run python src/milotic/server.py  # start the MCP server (blocks on stdio)
```

## Architecture

Milotic is a **FastMCP server** (Python, Phase 1) that acts as a Strategic Analyst layer between MCP clients (Cursor, Claude Desktop) and a Go trading backend. The server currently exposes stub tools; live backend calls are deferred to Phase 2.

### Layers

| Layer | Path | Purpose |
|-------|------|---------|
| Entry | `src/milotic/server.py` | `load_dotenv` → `structlog` setup → `mcp.run()` |
| App | `src/milotic/app.py` | Creates the `FastMCP` instance with `FileSystemProvider` for auto-discovery |
| Tools | `src/milotic/components/` | Each `.py` file here is auto-loaded; add new tools here |
| HTTP clients | `src/milotic/api/` | `BaseClient` (singleton), `HandshakeClient`, `SessionKeyProvider` |
| Services | `src/milotic/services/` | TA / signals logic (future) |
| Utils | `src/milotic/utils/` | `logging`, `crypto`, `errors`, `decorators` |
| Config | `src/milotic/config.py` | Pydantic `Settings` — loaded from `.env` |

### Tool auto-discovery

`app.py` mounts `FileSystemProvider(root=components/, reload=True)`. Any `.py` file dropped into `src/milotic/components/` is automatically scanned for tools decorated with `@tool()`.

### Crypto / "Vortex" pattern

`BaseClient` is a singleton that bootstraps on first use:
1. `HandshakeClient` calls `GET /handshake/get-public-key` (result cached 1 h via `alru_cache`).
2. `SessionKeyProvider` RSA-OAEP-SHA256-encrypts the `API_SESSION_SECRET` to produce the `X-API-Encryption-Key` header value.
3. `MiloticCipher` handles AES-256-GCM encryption of request bodies and decryption of responses. Wire format: `nonce.tag.ciphertext` (base64, dot-separated) — must match the Go `be-middlewares` implementation.

Crypto can be disabled for local dev with `CRYPTO_ENABLED=false`.

## Adding a new tool

1. Create `src/milotic/components/<category>.py`.
2. Apply both decorators; name with `category_action_entity` (e.g. `market_get_quote`):
   ```python
   from fastmcp.tools import tool
   from utils.decorators import milotic_tool

   @tool()
   @milotic_tool
   def market_get_quote(symbol: str) -> dict:
       """Description for the LLM including why it would call this."""
       ...
   ```
3. Allowed categories: `system`, `market`, `account`, `trading`, `research`.
4. Add a test in `tests/` and run `uv run pytest`.

`@milotic_tool` wraps sync and async functions, adds structured logging, timing, and converts `MiloticError` subclasses into `{"error": ..., "category": ...}` dicts instead of raising.

## Configuration

Copy `.env.example` to `.env`. Required vars when crypto is enabled:

| Variable | Notes |
|----------|-------|
| `API_CLIENT_ID` | Sent as `X-API-Client-Id` header |
| `API_SESSION_SECRET` | 32+ byte AES key (client-held) |
| `GO_BACKEND_URL` | Base URL for the Go API |
| `CRYPTO_ENABLED` | Default `true`; set `false` for local dev without a backend |

## Error hierarchy

All custom exceptions extend `MiloticError`. The `@milotic_tool` decorator catches `MiloticError` and returns a structured error dict; only unexpected exceptions produce `InternalError`.

```
MiloticError
├── BackendConnectionError
├── MarketDataError
├── ValidationError
├── HandshakeError
└── CryptoError
    └── DecryptionError
```
