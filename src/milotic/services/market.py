"""Market data normalization and parsing helpers."""

from typing import Any


async def normalize_quote(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw quote response from the backend into a consistent shape."""
    return raw


async def parse_ohlcv(raw: list[Any]) -> list[dict[str, Any]]:
    """Parse a raw OHLCV list from the backend into structured dicts."""
    return raw
