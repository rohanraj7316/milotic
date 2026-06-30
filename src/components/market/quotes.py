"""Market quote tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def market_get_quote(ctx: Context, symbol: str) -> dict:
    """
    Fetch a real-time quote for a single instrument.
    Use when the LLM needs the current price, bid/ask spread, or volume for one symbol.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("market")
    return await client.get(f"/quotes/{symbol}", headers=headers)


@tool()
@milotic_tool
async def market_get_quotes_batch(ctx: Context, symbols: list[str]) -> dict:
    """
    Fetch real-time quotes for multiple instruments in one request.
    Prefer this over repeated market_get_quote calls when handling more than one symbol.
    Rate limit: treated as a single request regardless of symbol count.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("market")
    return await client.post("/quotes/batch", json={"symbols": symbols}, headers=headers)
