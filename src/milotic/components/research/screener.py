"""Research stock screener tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def research_screen_stocks(
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
    client = await BaseClient.instance("research")
    params: dict = {"asset_class": asset_class, "limit": limit}
    if min_rsi is not None:
        params["min_rsi"] = min_rsi
    if max_rsi is not None:
        params["max_rsi"] = max_rsi
    if min_volume is not None:
        params["min_volume"] = min_volume
    return await client.get("/screener", params=params)
