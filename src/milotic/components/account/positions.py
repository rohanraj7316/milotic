"""Account position tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def account_list_positions(account_id: str = "") -> dict:
    """
    List all open positions for the authenticated account.
    Use to get a full picture of current exposure across all instruments.
    account_id: optional — omit to use the default account.
    """
    client = await BaseClient.instance("account")
    params = {"account_id": account_id} if account_id else {}
    return await client.get("/positions", params=params)


@tool()
@milotic_tool
async def account_get_position(symbol: str, account_id: str = "") -> dict:
    """
    Fetch the current position for a single instrument.
    Use when the LLM needs quantity, average cost, or P&L for one specific holding.
    """
    client = await BaseClient.instance("account")
    params = {"account_id": account_id} if account_id else {}
    return await client.get(f"/positions/{symbol}", params=params)
