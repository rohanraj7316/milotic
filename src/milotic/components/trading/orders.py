"""Trading order management tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def trading_place_order(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str,
    price: float | None = None,
) -> dict:
    """
    Place a new order for an instrument.
    Use when the user wants to buy or sell. side: 'buy' or 'sell'.
    order_type: 'market', 'limit', 'stop_limit'. price required for limit/stop_limit.
    """
    client = await BaseClient.instance("trading")
    payload: dict = {
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
    }
    if price is not None:
        payload["price"] = price
    return await client.post("/orders", json=payload)


@tool()
@milotic_tool
async def trading_cancel_order(order_id: str) -> dict:
    """
    Cancel an open order by its ID.
    Use when the user wants to withdraw an unfilled order before execution.
    """
    client = await BaseClient.instance("trading")
    return await client.delete(f"/orders/{order_id}")


@tool()
@milotic_tool
async def trading_get_order(order_id: str) -> dict:
    """
    Fetch the current status and details of a specific order.
    Use to check whether an order is still open, filled, or cancelled.
    """
    client = await BaseClient.instance("trading")
    return await client.get(f"/orders/{order_id}")
