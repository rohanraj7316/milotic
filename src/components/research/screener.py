"""Research stock screener tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def research_screen_stocks(
    ctx: Context,
    asset_class: str = "equity",
    min_rsi: float | None = None,
    max_rsi: float | None = None,
    min_volume: int | None = None,
    limit: int = 20,
) -> dict:
    """
    Screen instruments using research-driven filters.
    Use to find symbols matching specific technical criteria without iterating manually.
    Returns a ranked list with supporting metrics.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("research")
    params: dict = {"asset_class": asset_class, "limit": limit}
    if min_rsi is not None:
        params["min_rsi"] = min_rsi
    if max_rsi is not None:
        params["max_rsi"] = max_rsi
    if min_volume is not None:
        params["min_volume"] = min_volume
    return await client.get("/screener", params=params, headers=headers)
