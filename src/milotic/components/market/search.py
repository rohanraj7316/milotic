"""Market symbol search tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def market_search_symbol(query: str, asset_class: str = "") -> dict:
    """
    Search for tradeable symbols by name or ticker fragment.
    Use when the user provides a company name or partial ticker and you need the canonical symbol.
    asset_class: optional filter e.g. 'equity', 'crypto', 'derivative'.
    """
    client = await BaseClient.instance("market")
    params: dict = {"q": query}
    if asset_class:
        params["asset_class"] = asset_class
    return await client.get("/symbols/search", params=params)
