"""Account position tools."""

from fastmcp import Context
from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool
from milotic.utils.session import get_session_headers


@tool()
@milotic_tool
async def account_list_positions(ctx: Context, account_id: str = "") -> dict:
    """
    List all open positions for the authenticated account.
    Use to get a full picture of current exposure across all instruments.
    account_id: optional — omit to use the default account.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("account")
    params = {"account_id": account_id} if account_id else {}
    return await client.get("/positions", params=params, headers=headers)


@tool()
@milotic_tool
async def account_get_position(ctx: Context, symbol: str, account_id: str = "") -> dict:
    """
    Fetch the current position for a single instrument.
    Use when the LLM needs quantity, average cost, or P&L for one specific holding.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("account")
    params = {"account_id": account_id} if account_id else {}
    return await client.get(f"/positions/{symbol}", params=params, headers=headers)
