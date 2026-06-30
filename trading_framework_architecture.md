# Trading API Framework — Architecture (v1)

## Problem Statement
Non-technical retail users — retail investors, traders, finance folks — need an easy way to interact with trading APIs through an AI assistant (Claude) without writing code or managing CLI commands. The solution must be safe enough for real money, compliant with regulatory mandates, and structured so the core logic stays stable as interfaces evolve over 2–3 years.

**Primary audience decision:** v1 targets non-technical retail users only. Developers/technical users are explicitly out of scope for now.

---

## Architecture Overview

### Layering

**Core backend / API layer (source of truth)**
- Owns all business logic, execution, and safety-critical controls
- Treats every order from the LLM path as *untrusted input*
- Authoritative for limits, rate caps, order status, and audit logging

**MCP server (the v1 product)**
- Wraps the backend and exposes trading operations as well-described tools
- Built for non-technical users on Claude.ai / Claude Desktop
- Holds only cheap, advisory, stateless checks — never authoritative state, never approves anything
- Connection flow kept dead-simple (ideally paste one link/token and go)

**Skills / npm distribution — NOT in v1**
- `npx skills add` and SKILL.md distribution targets coding-agent users (Claude Code, Cursor) — out of scope for a non-technical audience
- "Skill-style" instructions instead live *inside* the MCP tool descriptions
- Possible later developer-facing track

---

## Check Placement: MCP Layer vs Server Layer

**Guiding principle:** MCP-layer checks are for *fast feedback and UX*; server-layer checks are for *truth and safety*. Anything protecting money lives server-side, re-checked even if the MCP layer already looked. The MCP layer can be restarted, multi-instanced, or bypassed — never a security/compliance boundary.

**MCP layer (advisory, stateless, fail-open)**
- Schema/type validation, required-field presence
- Obvious sanity bounds (no negative/absurd quantities)
- Formatting/normalization (uppercase symbol, trim, coerce types)
- Translating server rejections into plain language for the user
- Advisory early rejection only; if unsure (e.g. just restarted), let it pass and rely on the server backstop

**Server layer (authoritative, stateful, fail-closed)**
- Authentication / authorization (does this session own this account)
- Position and exposure limits (against real holdings)
- Notional / order-value limits (against real balance)
- Authoritative rate limiting (source of truth)
- Idempotency / duplicate detection (new)
- Kill switch — global and per-account
- Market/trading-hours and instrument validity
- Immutable audit log of every accepted and rejected order

If the two layers ever disagree, the server always wins.

---

## Idempotency / Duplicate-Order Detection (new control)

- The **MCP server** generates a deterministic idempotency key from order intent: hash of (account ID + symbol + side + quantity + order type + coarse timestamp bucket, ~30–60s)
- Same logical order within the window → same key → server dedup catches it
- Key generated at MCP layer (not the LLM — the LLM is the most likely source of retries and the worst place to generate a stable key)
- Server stores seen keys with a TTL; rejects or returns prior result for duplicates
- Explicit override path (deliberate nonce) for intentional repeat orders, so legitimate second orders aren't silently swallowed

---

## Execution & Consent Model

**No YOLO mode in v1.**

- **Default: per-trade consent.** Customer approves each order before execution.
- **Optional day-pass consent**, bounded on multiple axes:
  - **Value & count caps** — covers up to N orders and a total notional for the day; once either is hit, reverts to per-trade approval (most important bound — caps a hallucinated flood or oversized order)
  - **Time** — expires end of trading day (not rolling 24h); fresh consent required each day
  - **Instantly revocable** at any time (ties to per-account kill switch)
  - **Scope** — v1 may keep simple (per-order size cap + daily total); design leaves room to narrow to specific symbols/sizes later
  - **Logged** — every order executed under day-pass is recorded as day-pass-authorized in the audit trail

**Compliance note:** standing consent edges toward discretionary trading authority and carries its own regulatory weight depending on business structure. To be confirmed against the actual regulatory setup — not treated as settled here. The tighter/capped/expiring/logged the envelope, the lower the exposure.

---

## Rate Limiting

- **Binding compliance cap: 10 orders/sec per client** (regulatory mandate)
- **Authoritative enforcement at the API layer** — current keying is IP + client, reviewed and approved by compliance
- **MCP layer:** advisory throttle on place-order path only, for early UX feedback; **fail-open** (if unsure, pass through and let the API layer be the backstop)
- Window behavior (fixed vs sliding/token-bucket) — **open item**, to decide at build; sliding-window/token-bucket preferred to avoid edge bursts
- Rejection over queuing for the hard cap; every rejection logged
- MCP throttle translates rejections into plain language for the user

---

## Authentication & Security
- Key rotation and credential management already handled (backend)
- LLM never holds credentials that can move money — it sends *intent*; server-side authenticates the session and executes
- Approval/consent gates layered on top of (not in place of) server-side limits

---

## Error Handling — deferred to build, with two non-negotiable foundations

Detailed error handling is **deferred to MCP development**, since it's best designed against concrete endpoints and real broker behavior. Two pieces are **foundational and must be baked into the data model from day one** (retrofitting is painful):

1. **Server-owned authoritative order status** — every order has a single status the server owns and can always reconcile against the broker. The LLM/MCP layer never infers an outcome; it only reports what the server says.
2. **Idempotency + client order ID** — so retries are safe and reconciliation is possible.

**Failure landscape to address at build (reference):**
- **Unknown outcome (most dangerous):** timeout/dropped connection after sending to broker — true state unknown. Never treat timeout as failure, never blindly retry. Reconcile by querying order status via client order ID, then act on broker truth.
- **Partial fills:** legitimate state, not an error. Plain-language account to the user + explicit disposition rule for the remainder (rest / cancel / ask).
- **Broker/API rejections:** deterministic, order definitely didn't happen. Safe to surface; translate codes to plain language; never auto-retry.
- **LLM-layer failures:** caught by the validation gate; must leave zero side effects so restart is always safe.

**Unifying rule:** the server owns the single authoritative order status; the LLM never guesses "probably worked / probably failed" and acts on the guess.

---

## Versioning Strategy
- Semantic versioning; major = breaking (maintain ≥2 versions live, opt-in upgrades), minor/patch = automatic
- Deprecation warnings with sunset dates

---

## Build Priorities (v1)
1. MCP server wrapping the backend, trading ops as well-described tools, simple connection flow
2. Idempotency / duplicate-order detection (server) + deterministic key generation (MCP)
3. Day-pass consent envelope (capped by count + notional, end-of-day expiry, revocable, logged); per-trade consent as default
4. Wire authoritative server-side controls into the MCP path (limits, kill switch, audit log)
5. Advisory MCP-layer throttle (fail-open) for place-order UX
6. Data model with server-owned order status + client order ID (foundation for later error handling)

**Already exists:** key rotation/credential management, some script validation, API-layer rate limiting (IP + client).
**New to build:** duplicate-order detection, day-pass consent envelope.
**Deferred:** detailed error-handling logic (per-endpoint, at build), rate-limiter window behavior decision.
