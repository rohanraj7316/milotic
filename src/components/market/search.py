"""Market symbol search tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def market_search_symbol(ctx: Context, query: str, asset_class: str = "") -> dict:
    """
    Search for tradeable symbols by name or ticker fragment.
    Use when the user provides a company name or partial ticker and you need the canonical symbol.
    asset_class: optional filter e.g. 'equity', 'crypto', 'derivative'.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("market")
    params: dict = {"q": query}
    if asset_class:
        params["asset_class"] = asset_class
    return await client.get("/symbols/search", params=params, headers=headers)
