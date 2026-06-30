"""Account trade and order history tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def account_list_trades(ctx: Context, symbol: str = "", limit: int = 50) -> dict:
    """
    Fetch executed trade history for the account.
    Use to review past executions or compute realised P&L.
    symbol: optional filter. limit: max records to return.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("account")
    params: dict = {"limit": limit}
    if symbol:
        params["symbol"] = symbol
    return await client.get("/trades", params=params, headers=headers)


@tool()
@milotic_tool
async def account_list_orders(ctx: Context, status: str = "all", limit: int = 50) -> dict:
    """
    Fetch historical orders for the account.
    Use to audit past order activity. status: 'open', 'filled', 'cancelled', or 'all'.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("account")
    return await client.get(
        "/orders/history", params={"status": status, "limit": limit}, headers=headers
    )
