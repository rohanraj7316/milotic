# Plan: Package Restructure + v1 Trading Architecture

Source: grill-with-docs session, 2026-07-01. Decisions recorded in
[CONTEXT.md](../CONTEXT.md), [ADR-0001](../docs/adr/0001-qr-based-auth-over-oauth-redirect.md),
[ADR-0002](../docs/adr/0002-per-trade-consent-via-confirmed-parameter.md).

Two independent tracks. Track A (restructure) has zero functional risk and should land
first so Track B is built on the final file layout. Track B depends on FastMCP `Context`
APIs that must be verified against installed docs before use — do not assume signatures.

---

## Phase 0: Documentation Discovery

**Goal:** confirm exact FastMCP 3.x APIs before any tool code is written. Do not invent
method names — `ctx.set_state`/`ctx.get_state` and `Image` return type were referenced in
prior discussion but must be verified against the installed package, not memory.

**Tasks:**
1. Locate installed FastMCP version: `uv run python -c "import fastmcp; print(fastmcp.__version__)"`
2. Find `Context` class source (likely `.venv/lib/python3.12/site-packages/fastmcp/server/context.py` —
   prior session referenced `context.py:1249-1303` for `set_state`/`get_state`). Read the actual
   method signatures, parameter names, return types, and TTL behavior.
3. Confirm how FastMCP injects `Context` into a tool function — by type annotation, by parameter
   name, or both. Check one existing example if FastMCP ships one in its own test suite.
4. Confirm the `Image` / `ImageContent` return type — exact import path and constructor signature
   for returning a base64 image from a tool.
5. Confirm `FileSystemProvider` behavior is unaffected by moving files within `src/` (it already
   points at `components/`, an absolute path under `__file__`).

**Output:** a short "Allowed APIs" list with file:line citations for:
- `Context.set_state(key, value)` — exact signature
- `Context.get_state(key)` — exact signature, return type when key is absent
- Image/content return type for QR display
- Confirmation that `ctx: Context` parameter injection works through the existing
  `@tool() @milotic_tool` decorator stack without changes

**Anti-pattern guard:** if `set_state`/`get_state` don't exist as described, STOP and report
back — do not substitute an invented alternative (e.g. don't assume `ctx.session.data[key] = x`).

---

## Phase 1: Package Restructure (`src/milotic/` → `src/`)

**Rationale:** project root is already named `milotic`; nesting `src/milotic/` duplicates the
name without benefit. Confirmed in prior discussion as low-risk given test/build verification.

**What to implement:**
1. Move all contents of `src/milotic/` up one level to `src/`:
   ```
   src/milotic/__init__.py       → src/__init__.py
   src/milotic/app.py            → src/app.py
   src/milotic/config.py         → src/config.py
   src/milotic/server.py         → src/server.py
   src/milotic/api/              → src/api/
   src/milotic/components/       → src/components/
   src/milotic/services/         → src/services/
   src/milotic/utils/            → src/utils/
   ```
   Use `git mv` for each, not delete+recreate, to preserve history.
2. Update `pyproject.toml`:
   ```toml
   [tool.hatch.build.targets.wheel]
   sources = {"src" = "milotic"}
   ```
   (replaces `packages = ["src/milotic"]`)
3. Do NOT touch any `from X import Y` or `import X` statements anywhere —
   in source or tests. The whole point of the `sources` remapping is that these stay valid.
4. Update `.vscode/settings.json` if it references `src/milotic` paths directly (check first;
   may only reference `src` as a pythonpath entry, in which case no change needed).

**Verification checklist:**
1. `uv sync` — must complete without error
2. `python -c "import milotic; print(__file__)"` (via `uv run`) — must print a path
   ending in `src/__init__.py`. If `ModuleNotFoundError`, STOP — do not proceed to Phase 2.
3. `uv run pytest` — all existing tests must pass unchanged (no test file edits in this phase)
4. `uv run fastmcp inspect src/app.py:mcp` — must list the same tools as before the move
   (confirms `FileSystemProvider` still resolves `components/` correctly)
5. `uv run ruff check .` — no new lint errors from the move

**Anti-pattern guard:** if Phase 0 didn't confirm the `sources` dict mapping works for editable
installs, do not proceed — fall back to keeping `packages = ["src/milotic"]` and report the
blocker instead of guessing at alternate hatchling config.

---

## Phase 2: Session Infrastructure (QR Auth + Context State)

**Depends on:** Phase 0 findings (exact `Context` API), Phase 1 (final file paths).

**What to implement:**

1. **`src/utils/session.py`** (new file):
   ```python
   from api.base import BaseClient
   from utils.errors import BackendConnectionError
   # exact ctx.get_state signature from Phase 0 findings — do not guess

   async def get_session_headers(ctx) -> dict[str, str]:
       """Resolve auth_token + sub_account_id from session state into request headers."""
       auth_token = await ctx.get_state("auth_token")
       sub_account_id = await ctx.get_state("sub_account_id")
       if not auth_token:
           raise BackendConnectionError("Not connected. Call system_connect_start first.")
       return {
           TRADING_AUTH_HEADER: auth_token,
           TRADING_SUB_ACCOUNT_HEADER: sub_account_id,
       }
   ```
   Header constant names are placeholders — confirmed TBD from Axis Direct RAPID API docs
   (Postman link provided by user; could not be machine-read, JS-rendered). Use placeholder
   constants in `config.py`, do not invent real header names.

2. **`src/config.py`** — add placeholder settings:
   ```python
   TRADING_AUTH_HEADER: str = "X-Auth-Token"        # TBD — confirm against API docs
   TRADING_SUB_ACCOUNT_HEADER: str = "X-Sub-Account-Id"  # TBD — confirm against API docs
   ```

3. **`src/components/system/system.py`** — replace/extend with two new tools:
   ```python
   @tool()
   @milotic_tool
   async def system_connect_start(ctx: Context) -> dict:
       """Initiate QR authentication. Returns a QR code to scan with your mobile trading app."""
       client = await BaseClient.instance("account")  # or whichever category owns /auth
       session = await client.post("/auth/qr-session")
       await ctx.set_state("qr_session_id", session["session_id"])
       return {
           "session_id": session["session_id"],
           "qr_image_base64": session["qr_image_base64"],
           "message": "Scan this QR code with your mobile trading app, then call system_connect_verify.",
       }

   @tool()
   @milotic_tool
   async def system_connect_verify(ctx: Context) -> dict:
       """Check if QR authentication has been confirmed on your mobile app."""
       session_id = await ctx.get_state("qr_session_id")
       if not session_id:
           return {"error": "No pending connection. Call system_connect_start first."}
       client = await BaseClient.instance("account")
       # poll loop: up to 120s, short sleep between attempts — exact endpoint TBD from API docs
       result = await poll_qr_confirmation(client, session_id, timeout_seconds=120)
       if result["status"] != "confirmed":
           return {"status": "pending", "message": "Not yet scanned. Try again shortly."}
       await ctx.set_state("auth_token", result["auth_token"])
       await ctx.set_state("sub_account_id", result["sub_account_id"])
       return {"status": "connected", "sub_account_id": result["sub_account_id"]}
   ```
   Endpoint paths (`/auth/qr-session`, poll endpoint) are placeholders pending API doc access —
   flag clearly in code comments as TBD, do not invent final paths as if confirmed.

**Documentation references:** Phase 0's "Allowed APIs" list for `set_state`/`get_state` exact
signatures and the Image return type if QR is returned as native image content instead of
base64 in the dict.

**Verification checklist:**
1. New unit test `tests/system/test_connect.py` — mock `BaseClient.post`, verify
   `system_connect_start` returns expected dict shape and calls `ctx.set_state("qr_session_id", ...)`
2. Mock the poll endpoint returning `status: confirmed` — verify `system_connect_verify` sets
   both `auth_token` and `sub_account_id` via `ctx.set_state`
3. Mock poll timeout — verify `system_connect_verify` returns `status: pending`, not an exception
4. `uv run pytest tests/system/` passes

**Anti-pattern guard:** don't hardcode real backend paths as if verified — every endpoint not
confirmed by Axis Direct docs must be a clearly-marked placeholder.

---

## Phase 3: Trading Tools — Consent, Validation, Reconciliation

**Depends on:** Phase 2 (`get_session_headers` helper exists).

**What to implement, in `src/components/trading/orders.py`:**

1. Remove `src/components/trading/basket.py` entirely (`trading_place_basket`,
   `trading_cancel_basket`) — deferred to v2 per [ADR scope decision]. Remove its test file
   `tests/trading/test_basket.py` if one exists (check first — not seen in current file
   inventory, so likely no-op).

2. Rewrite `trading_place_order`:
   ```python
   import uuid

   VALID_SIDES = {"buy", "sell"}
   VALID_ORDER_TYPES = {"market", "limit", "stop_limit"}

   @tool()
   @milotic_tool
   async def trading_place_order(
       ctx: Context,
       symbol: str,
       side: str,
       quantity: float,
       order_type: str,
       price: float | None = None,
       confirmed: bool = False,
   ) -> dict:
       """
       Place a new order. ALWAYS call with confirmed=False first to preview, then
       confirmed=True only after the user explicitly approves the previewed order.
       side: 'buy' or 'sell'. order_type: 'market', 'limit', 'stop_limit'.
       """
       symbol = symbol.strip().upper()
       side_norm = side.lower()
       order_type_norm = order_type.lower()

       if side_norm not in VALID_SIDES:
           return {"error": f"side must be 'buy' or 'sell', got '{side}'"}
       if order_type_norm not in VALID_ORDER_TYPES:
           return {"error": "order_type must be 'market', 'limit', or 'stop_limit'"}
       if quantity <= 0:
           return {"error": "quantity must be positive"}
       if order_type_norm in ("limit", "stop_limit") and price is None:
           return {"error": f"price is required for {order_type_norm} orders"}

       if not confirmed:
           return {
               "preview": True,
               "symbol": symbol,
               "side": side_norm,
               "quantity": quantity,
               "order_type": order_type_norm,
               "price": price,
               "message": "Call again with confirmed=True to place this order.",
           }

       headers = await get_session_headers(ctx)
       reference_id = str(uuid.uuid4())
       payload = {
           "symbol": symbol,
           "side": side_norm,
           "quantity": quantity,
           "order_type": order_type_norm,
           "reference_id": reference_id,  # field name TBD from API docs
       }
       if price is not None:
           payload["price"] = price

       client = await BaseClient.instance("trading")
       try:
           return await client.post("/orders", json=payload, headers=headers)
       except BackendConnectionError:
           # Doc-mandated rule: never retry on timeout/unknown-outcome.
           return {
               "status": "unknown",
               "reference_id": reference_id,
               "message": (
                   "Order status unknown due to a connection issue. "
                   f"Check status with trading_get_order(order_id='{reference_id}')."
               ),
           }
   ```
   Note the timeout branch catches `BackendConnectionError` specifically — confirm in Phase 0
   or via existing `utils/errors.py` that this is the correct exception type for a timeout vs.
   a deterministic rejection (`base.py:191-200` currently wraps both `httpx.HTTPStatusError`
   and generic exceptions into `BackendConnectionError` — this may need a narrower exception
   for "timeout/unknown" vs. "definite rejection" to follow the doc's distinction precisely;
   flag this as an open item if the existing error hierarchy doesn't already separate them).

   TODO comment to add above the function:
   ```python
   # TODO(v2): add advisory rate throttle here once day-pass consent lands (fail-open,
   # UX-only — server remains authoritative for the 10 orders/sec compliance cap).
   ```

3. `trading_cancel_order` and `trading_get_order` — add `ctx: Context`, call
   `get_session_headers(ctx)`, pass `headers=headers` to existing `client.delete`/`client.get`
   calls. No consent gate needed (per Q-and-A: cancellation/status-check don't execute trades).

4. `src/components/trading/margin.py` — add `ctx: Context`, wire `get_session_headers`.

**Verification checklist:**
1. Update `tests/trading/test_orders.py`:
   - Test `confirmed=False` returns preview dict, does not call `BaseClient.post`
   - Test `confirmed=True` calls `client.post` with a `reference_id` UUID in payload
   - Test invalid `side`/`order_type`/`quantity`/missing `price` each return an `error` dict
     without reaching `BaseClient`
   - Test timeout path returns `status: unknown` + `reference_id`, never retries
2. `uv run pytest tests/trading/` passes
3. `grep -r "trading_place_basket\|trading_cancel_basket" src/ tests/` — zero matches after removal

**Anti-pattern guard:** do not add idempotency-key hashing — explicitly rejected in favor of
the consent gate + reference_id reconciliation. Do not add a day-pass check — deferred to v2.

---

## Phase 4: Session Headers on Remaining Tools (account, market, research)

**Depends on:** Phase 2.

**What to implement:** for every tool below, add `ctx: Context` as first parameter, call
`headers = await get_session_headers(ctx)` at the top, pass `headers=headers` into the
existing `client.get`/`client.post` call. No other logic changes — these are read-only or
account-data tools, no consent gate needed.

Files (confirmed from current inventory):
- `src/components/account/balances.py`
- `src/components/account/history.py`
- `src/components/account/positions.py`
- `src/components/account/profile.py`
- `src/components/market/ohlcv.py`
- `src/components/market/orderbook.py`
- `src/components/market/quotes.py`
- `src/components/market/search.py`
- `src/components/market/ticker.py`
- `src/components/research/screener.py`
- `src/components/research/signals.py`
- `src/components/research/technicals.py`

**Verification checklist:**
1. For each modified file, confirm existing tests in `tests/account/`, `tests/market/`,
   `tests/research/` still pass after adding `ctx` + headers (update mocks to accept the new
   parameter and stub `ctx.get_state` returning fixed `auth_token`/`sub_account_id` test values)
2. `grep -L "ctx: Context" src/components/{account,market,research}/*.py` — should return
   zero files (confirms no tool was missed)
3. `uv run pytest` — full suite passes
4. `uv run fastmcp inspect src/app.py:mcp` — tool count matches pre-change count minus the two
   removed basket tools

---

## Phase 5: Final Verification

1. `uv sync --all-extras --dev`
2. `uv run ruff check .` — zero errors
3. `uv run pytest` — full suite green
4. `uv run fastmcp inspect src/app.py:mcp` — manually review tool list:
   - `system_connect_start`, `system_connect_verify` present
   - `trading_place_basket`, `trading_cancel_basket` absent
   - All trading/account/market/research tools show `ctx` in their signature (FastMCP inspect
     output should reflect this, or check via source grep)
5. `grep -rn "TBD" src/` — list every remaining placeholder (header names, endpoint paths) as
   a follow-up checklist item for when Axis Direct API docs are confirmed
6. Update `CONTEXT.md` if any term resolved differently during implementation than planned
   (e.g. actual header names once known)

**Definition of done:** all tests pass, lint is clean, tool inventory matches the architecture
decisions, and every TBD item is explicitly tracked rather than silently guessed.
