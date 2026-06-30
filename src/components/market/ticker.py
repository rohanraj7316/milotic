"""Market ticker tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def market_get_ticker(ctx: Context, symbol: str) -> dict:
    """
    Fetch 24-hour ticker statistics for a symbol (open, high, low, close, volume, change%).
    Use for daily performance summaries or volatility assessment.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("market")
    return await client.get(f"/ticker/{symbol}", headers=headers)


@tool()
@milotic_tool
async def market_list_tickers(ctx: Context, exchange: str = "") -> dict:
    """
    List all available tickers, optionally filtered by exchange.
    Use to discover tradeable instruments or build a watchlist.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("market")
    params = {"exchange": exchange} if exchange else {}
    return await client.get("/tickers", params=params, headers=headers)
