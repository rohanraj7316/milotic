"""Market OHLCV (candlestick) tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def market_get_ohlcv(symbol: str, interval: str, limit: int = 100) -> dict:
    """
    Fetch historical OHLCV (candlestick) data for a symbol.
    Use for charting, technical analysis, or trend detection.
    interval: e.g. '1m', '5m', '1h', '1d'. limit: number of candles (max 500).
    """
    client = await BaseClient.instance("market")
    return await client.get(f"/ohlcv/{symbol}", params={"interval": interval, "limit": limit})


@tool()
@milotic_tool
async def market_get_ohlcv_range(symbol: str, interval: str, from_ts: int, to_ts: int) -> dict:
    """
    Fetch OHLCV data for a symbol between two Unix timestamps.
    Use when a specific date range is required rather than the most recent N candles.
    """
    client = await BaseClient.instance("market")
    return await client.get(
        f"/ohlcv/{symbol}/range",
        params={"interval": interval, "from": from_ts, "to": to_ts},
    )
