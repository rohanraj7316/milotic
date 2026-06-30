"""Account balance tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def account_get_balance(ctx: Context, account_id: str = "") -> dict:
    """
    Fetch the cash balance and equity summary for the account.
    Use to determine available buying power before placing orders.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("account")
    params = {"account_id": account_id} if account_id else {}
    return await client.get("/balance", params=params, headers=headers)


@tool()
@milotic_tool
async def account_list_balances(ctx: Context) -> dict:
    """
    List balances across all sub-accounts or currency wallets.
    Use for a multi-account or multi-currency portfolio overview.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("account")
    return await client.get("/balances", headers=headers)
