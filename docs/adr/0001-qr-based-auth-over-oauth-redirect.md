# ADR-0001: QR-based authentication over OAuth redirect flow

**Status:** Accepted  
**Date:** 2026-06-30

## Context

Milotic needs to authenticate non-technical retail users and resolve their `subAccountId` before any API call. The broker's login microsite handles SSO. The MCP server must receive the resulting session credentials.

Three approaches were evaluated:
1. OAuth redirect callback to MCP server HTTP endpoint
2. Post-SSO token displayed on web app, pasted into MCP config
3. QR code displayed by MCP tool, scanned by the authenticated Mobile App

## Decision

Use QR-based device linking (option 3).

## Reasons

- OAuth redirect (option 1) requires HTTP transport, breaking the current stdio model. Local port conflicts and firewall issues are common for non-technical users.
- Token-paste (option 2) is manual friction on every token rotation (daily).
- The Mobile App already implements QR scan and device-link capability — no new mobile work required.
- QR flow works with stdio: `system_connect_start` returns the QR image, `system_connect_verify` polls for confirmation. No inbound HTTP port needed.
- Two-tool pattern solves the display-before-poll UX constraint: QR is shown to the user between tool calls.

## Consequences

- MCP transport stays stdio. No HTTP server required.
- Backend must expose: `POST /auth/qr-session`, `GET /auth/qr-status`, `POST /auth/qr-confirm` (mobile-side).
- If multi-user HTTP transport is needed later, `ctx.set_state()` already provides per-session isolation — zero migration cost for session state.
