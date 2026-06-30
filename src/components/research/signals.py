"""Research signal tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def research_get_signal(ctx: Context, symbol: str, signal_type: str = "") -> dict:
    """
    Fetch the latest research signal for a symbol.
    Use when the LLM needs a buy/sell/hold recommendation or sentiment score.
    signal_type: optional filter e.g. 'momentum', 'mean_reversion', 'sentiment'.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("research")
    params: dict = {}
    if signal_type:
        params["type"] = signal_type
    return await client.get(f"/signals/{symbol}", params=params, headers=headers)


@tool()
@milotic_tool
async def research_list_signals(ctx: Context, asset_class: str = "", limit: int = 20) -> dict:
    """
    List recent signals across all tracked instruments.
    Use to surface the highest-conviction ideas from the research engine.
    asset_class: optional filter. limit: max results to return.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("research")
    params: dict = {"limit": limit}
    if asset_class:
        params["asset_class"] = asset_class
    return await client.get("/signals", params=params, headers=headers)
