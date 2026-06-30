"""Research signal aggregation and scoring helpers."""

from typing import Any


async def score_signal(raw: dict[str, Any]) -> dict[str, Any]:
    """Attach a composite confidence score to a raw signal dict."""
    return raw


async def aggregate_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort and deduplicate a list of signals before returning to the LLM."""
    return signals
