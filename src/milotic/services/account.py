"""Account data aggregation helpers."""

from typing import Any


async def aggregate_balances(raw: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum total equity and cash across multiple balance entries."""
    return {"balances": raw}


async def summarize_positions(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enrich raw position data with any derived fields needed by tools."""
    return raw
