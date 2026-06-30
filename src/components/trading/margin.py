"""Trading margin tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def trading_get_margin(ctx: Context) -> dict:
    """
    Fetch the account's current margin usage, available margin, and margin ratio.
    Use before placing leveraged orders to confirm sufficient margin exists.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("trading")
    return await client.get("/margin", headers=headers)


@tool()
@milotic_tool
async def trading_calculate_margin(
    ctx: Context, symbol: str, quantity: float, leverage: float
) -> dict:
    """
    Calculate the required margin for a hypothetical position without placing an order.
    Use to pre-check whether the account can afford a leveraged position.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("trading")
    return await client.get(
        "/margin/calculate",
        params={"symbol": symbol, "quantity": quantity, "leverage": leverage},
        headers=headers,
    )
