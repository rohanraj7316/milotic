# ADR-0002: Per-trade consent via confirmed parameter (single tool)

**Status:** Accepted  
**Date:** 2026-06-30

## Context

Every order must require explicit Retail User approval before execution. Two implementation patterns were evaluated:

1. **Two-tool pattern** — `trading_preview_order` + `trading_confirm_order(preview_id)`. LLM must call preview first.
2. **Confirmed parameter** — single `trading_place_order(..., confirmed=False)`. First call returns preview; second call with `confirmed=True` executes.
3. **Server-side consent check** — MCP fires immediately; backend holds order in pending state; separate approval call needed.

## Decision

Use confirmed parameter (option 2).

## Reasons

- Two-tool pattern (1) exposes a footgun: LLM could call `trading_confirm_order` without a prior `trading_preview_order`. No enforcement mechanism in the tool signature.
- Server-side consent (3) requires a new backend API contract and a pending-order state machine — out of scope for v1.
- Single tool with `confirmed=False` default is the hardest to accidentally bypass: the LLM must explicitly pass `confirmed=True`, and the tool description makes this requirement explicit.
- One tool in the list is simpler for non-technical users to understand from tool descriptions.

## Consequences

- `trading_place_order` always returns an Order Preview on first call.
- LLM must call `trading_place_order` twice for every order: once to preview, once to execute.
- Day-pass (v2) will require revisiting this — when day-pass is active, the second call should be skipped. The consent gate check against backend state fits naturally here.
