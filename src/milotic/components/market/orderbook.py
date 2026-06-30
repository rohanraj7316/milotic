"""Market order book tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def market_get_orderbook(symbol: str, depth: int = 20) -> dict:
    """
    Fetch the current order book for a symbol.
    Returns bids and asks up to the requested depth.
    Use to assess liquidity or spread before placing an order.
    """
    client = await BaseClient.instance("market")
    return await client.get(f"/orderbook/{symbol}", params={"depth": depth})


@tool()
@milotic_tool
async def market_get_depth(symbol: str) -> dict:
    """
    Fetch aggregated market depth (cumulative bid/ask volume by price level).
    Use to identify significant support/resistance levels in the order book.
    """
    client = await BaseClient.instance("market")
    return await client.get(f"/orderbook/{symbol}/depth")
