"""Trading basket (multi-leg) order tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def trading_place_basket(orders: list[dict]) -> dict:
    """
    Place multiple orders atomically as a basket.
    Use when rebalancing a portfolio or executing a strategy across several instruments.
    orders: list of order dicts each with symbol, side, quantity, order_type, and optional price.
    """
    client = await BaseClient.instance("trading")
    return await client.post("/orders/basket", json={"orders": orders})


@tool()
@milotic_tool
async def trading_cancel_basket(basket_id: str) -> dict:
    """
    Cancel all unfilled orders in a basket by basket ID.
    Use when aborting a multi-leg strategy mid-execution.
    """
    client = await BaseClient.instance("trading")
    return await client.delete(f"/orders/basket/{basket_id}")
