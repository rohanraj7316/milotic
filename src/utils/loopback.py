"""Ephemeral loopback HTTP server for capturing OAuth/SSO redirects securely."""

import asyncio
import contextlib
import secrets
from urllib.parse import parse_qs, urlsplit

from utils.logging import logger

_HTML_PAGE = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width, initial-scale=1'>"
    "<title>{title}</title></head>"
    "<body style='font-family:-apple-system,BlinkMacSystemFont,sans-serif;text-align:center;"
    "padding:50px 20px;background:#f8fafc;color:#1e293b;'>"
    "<div style='max-width:460px;margin:0 auto;background:#fff;padding:36px;"
    "border-radius:12px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);'>"
    "<h1 style='color:{color};margin-bottom:8px;'>{title}</h1>"
    "<p style='color:#64748b;font-size:16px;line-height:1.5;'>{msg}</p>"
    "</div></body></html>"
)


def _http_response(status: str, html: str) -> bytes:
    body = html.encode("utf-8")
    return (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode() + body


class SSOLoopbackSession:
    """
    Manages an ephemeral, auto-closing loopback HTTP server (RFC 8252) on 127.0.0.1:0.
    Validates CSRF state, avoids buffer truncation, and auto-terminates after a timeout.
    """

    def __init__(self) -> None:
        self.server: asyncio.AbstractServer | None = None
        self.port: int = 0
        self.csrf_state: str = ""
        self.captured_sso_id: str | None = None
        self._timeout_task: asyncio.Task | None = None

    async def start(self, timeout_seconds: int = 180) -> tuple[int, str]:
        """Start the loopback server on a random port, returning (port, csrf_state)."""
        await self.close()

        self.captured_sso_id = None
        self.csrf_state = secrets.token_urlsafe(32)

        self.server = await asyncio.start_server(self._handle_client, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]

        # ponytail: single in-flight loopback server per process;
        # upgrade path: keyed session registry if multi-user concurrent MCP needed
        self._timeout_task = asyncio.create_task(self._auto_close_after(timeout_seconds))
        logger.info("loopback_server_started", port=self.port, timeout=timeout_seconds)
        return self.port, self.csrf_state

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle incoming HTTP request and verify CSRF state."""
        try:
            # Buffer-safe header read: stream until \r\n\r\n up to 64KB (avoids 1KB truncation)
            buffer = bytearray()
            while b"\r\n\r\n" not in buffer and len(buffer) < 65536:
                chunk = await reader.read(4096)
                if not chunk:
                    break
                buffer.extend(chunk)

            raw_request = buffer.decode("utf-8", errors="ignore")
            first_line = raw_request.split("\r\n")[0] if raw_request else ""
            parts = first_line.split(" ")
            path = parts[1] if len(parts) > 1 else "/"

            query_params = parse_qs(urlsplit(path).query)
            incoming_state = query_params.get("state", [None])[0]
            sso_id = query_params.get("ssoId", [None])[0]

            # Enforce CSRF verification: incoming state must match generated csrf_state
            if not incoming_state or incoming_state != self.csrf_state or not sso_id:
                logger.warning(
                    "loopback_validation_failed",
                    state_match=incoming_state == self.csrf_state,
                    has_sso=bool(sso_id),
                )
                html = _HTML_PAGE.format(
                    title="Authentication Failed",
                    color="#dc2626",
                    msg=(
                        "Invalid or expired CSRF state. "
                        "Please return to the chat and start a new connection session."
                    ),
                )
                writer.write(_http_response("400 Bad Request", html))
            else:
                self.captured_sso_id = sso_id
                logger.info("loopback_sso_id_captured")
                html = _HTML_PAGE.format(
                    title="Login Successful!",
                    color="#059669",
                    msg=(
                        "Your session is authenticated. "
                        "You can close this tab and return to your AI assistant."
                    ),
                )
                writer.write(_http_response("200 OK", html))

            await writer.drain()

        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    async def _auto_close_after(self, seconds: int) -> None:
        """Automatically shut down the server after the specified timeout."""
        try:
            await asyncio.sleep(seconds)
            logger.info("loopback_server_timeout_expired", port=self.port)
            await self.close()
        except asyncio.CancelledError:
            pass

    def consume_sso_id(self) -> str | None:
        """Retrieve and clear the captured SSO ID."""
        sso_id = self.captured_sso_id
        self.captured_sso_id = None
        return sso_id

    async def close(self) -> None:
        """Gracefully shut down the loopback server and cancel expiry timer."""
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()
            self._timeout_task = None

        if self.server:
            self.server.close()
            with contextlib.suppress(Exception):
                await self.server.wait_closed()
            self.server = None
            self.port = 0


# Module-level default session manager
default_loopback = SSOLoopbackSession()
