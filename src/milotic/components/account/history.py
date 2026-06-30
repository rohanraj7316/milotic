"""Account trade and order history tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def account_list_trades(symbol: str = "", limit: int = 50) -> dict:
    """
    Fetch executed trade history for the account.
    Use to review past executions or compute realised P&L.
    symbol: optional filter. limit: max records to return.
    """
    client = await BaseClient.instance("account")
    params: dict = {"limit": limit}
    if symbol:
        params["symbol"] = symbol
    return await client.get("/trades", params=params)


@tool()
@milotic_tool
async def account_list_orders(status: str = "all", limit: int = 50) -> dict:
    """
    Fetch historical orders for the account.
    Use to audit past order activity. status: 'open', 'filled', 'cancelled', or 'all'.
    """
    client = await BaseClient.instance("account")
    return await client.get("/orders/history", params={"status": status, "limit": limit})
