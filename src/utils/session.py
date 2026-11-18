"""Helpers for resolving authenticated session state into request headers."""

from fastmcp import Context

from utils.constants import HEADER_AUTH_TOKEN, HEADER_SUB_ACCOUNT_ID
from utils.errors import BackendConnectionError


async def get_session_headers(ctx: Context) -> dict[str, str]:
    """Resolve auth_token + sub_account_id from session state into request headers."""
    auth_token = await ctx.get_state("auth_token")
    sub_account_id = await ctx.get_state("sub_account_id")
    if not auth_token:
        raise BackendConnectionError("Not connected. Call system_connect_start first.")
    headers = {
        HEADER_AUTH_TOKEN: auth_token,
    }
    if sub_account_id:
        headers[HEADER_SUB_ACCOUNT_ID] = sub_account_id
    return headers
