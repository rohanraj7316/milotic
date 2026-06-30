"""Research technical indicator tools (computed server-side)."""

from fastmcp import Context
from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool
from milotic.utils.session import get_session_headers


@tool()
@milotic_tool
async def research_get_rsi(
    ctx: Context, symbol: str, interval: str = "1d", length: int = 14
) -> dict:
    """
    Fetch the current RSI value for a symbol from the research backend.
    Use to assess overbought (>70) or oversold (<30) conditions.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("research")
    return await client.get(
        f"/indicators/{symbol}/rsi",
        params={"interval": interval, "length": length},
        headers=headers,
    )


@tool()
@milotic_tool
async def research_get_macd(
    ctx: Context,
    symbol: str,
    interval: str = "1d",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict:
    """
    Fetch the current MACD line, signal line, and histogram for a symbol.
    Use to identify trend direction changes or momentum shifts.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("research")
    return await client.get(
        f"/indicators/{symbol}/macd",
        params={"interval": interval, "fast": fast, "slow": slow, "signal": signal},
        headers=headers,
    )


@tool()
@milotic_tool
async def research_get_sma(
    ctx: Context, symbol: str, interval: str = "1d", length: int = 20
) -> dict:
    """
    Fetch the Simple Moving Average for a symbol.
    Use to determine trend support/resistance levels or price crossover conditions.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("research")
    return await client.get(
        f"/indicators/{symbol}/sma",
        params={"interval": interval, "length": length},
        headers=headers,
    )
