"""Market order book tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def market_get_orderbook(ctx: Context, symbol: str, depth: int = 20) -> dict:
    """
    Fetch the current order book for a symbol.
    Returns bids and asks up to the requested depth.
    Use to assess liquidity or spread before placing an order.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("market")
    return await client.get(f"/orderbook/{symbol}", params={"depth": depth}, headers=headers)


@tool()
@milotic_tool
async def market_get_depth(ctx: Context, symbol: str) -> dict:
    """
    Fetch aggregated market depth (cumulative bid/ask volume by price level).
    Use to identify significant support/resistance levels in the order book.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("market")
    return await client.get(f"/orderbook/{symbol}/depth", headers=headers)
