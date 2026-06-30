"""Market ticker tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def market_get_ticker(symbol: str) -> dict:
    """
    Fetch 24-hour ticker statistics for a symbol (open, high, low, close, volume, change%).
    Use for daily performance summaries or volatility assessment.
    """
    client = await BaseClient.instance("market")
    return await client.get(f"/ticker/{symbol}")


@tool()
@milotic_tool
async def market_list_tickers(exchange: str = "") -> dict:
    """
    List all available tickers, optionally filtered by exchange.
    Use to discover tradeable instruments or build a watchlist.
    """
    client = await BaseClient.instance("market")
    params = {"exchange": exchange} if exchange else {}
    return await client.get("/tickers", params=params)
