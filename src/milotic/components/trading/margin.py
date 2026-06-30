"""Trading margin tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def trading_get_margin() -> dict:
    """
    Fetch the account's current margin usage, available margin, and margin ratio.
    Use before placing leveraged orders to confirm sufficient margin exists.
    """
    client = await BaseClient.instance("trading")
    return await client.get("/margin")


@tool()
@milotic_tool
async def trading_calculate_margin(symbol: str, quantity: float, leverage: float) -> dict:
    """
    Calculate the required margin for a hypothetical position without placing an order.
    Use to pre-check whether the account can afford a leveraged position.
    """
    client = await BaseClient.instance("trading")
    return await client.get(
        "/margin/calculate",
        params={"symbol": symbol, "quantity": quantity, "leverage": leverage},
    )
