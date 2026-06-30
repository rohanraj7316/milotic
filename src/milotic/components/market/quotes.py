"""Market quote tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def market_get_quote(symbol: str) -> dict:
    """
    Fetch a real-time quote for a single instrument.
    Use when the LLM needs the current price, bid/ask spread, or volume for one symbol.
    """
    client = await BaseClient.instance("market")
    return await client.get(f"/quotes/{symbol}")


@tool()
@milotic_tool
async def market_get_quotes_batch(symbols: list[str]) -> dict:
    """
    Fetch real-time quotes for multiple instruments in one request.
    Prefer this over repeated market_get_quote calls when handling more than one symbol.
    Rate limit: treated as a single request regardless of symbol count.
    """
    client = await BaseClient.instance("market")
    return await client.post("/quotes/batch", json={"symbols": symbols})
