"""Account balance tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def account_get_balance(account_id: str = "") -> dict:
    """
    Fetch the cash balance and equity summary for the account.
    Use to determine available buying power before placing orders.
    """
    client = await BaseClient.instance("account")
    params = {"account_id": account_id} if account_id else {}
    return await client.get("/balance", params=params)


@tool()
@milotic_tool
async def account_list_balances() -> dict:
    """
    List balances across all sub-accounts or currency wallets.
    Use for a multi-account or multi-currency portfolio overview.
    """
    client = await BaseClient.instance("account")
    return await client.get("/balances")
