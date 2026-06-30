"""Tests for research signal tools."""

import httpx
import pytest
import respx

from milotic.api.base import BaseClient


@pytest.mark.asyncio
async def test_research_get_signal_success(mock_env):
    with respx.mock(base_url="http://research.test") as router:
        router.get("/signals/AAPL").mock(
            return_value=httpx.Response(200, json={"symbol": "AAPL", "signal": "buy"})
        )
        client = await BaseClient.instance("research")
        result = await client.get("/signals/AAPL")
        assert result["signal"] == "buy"
