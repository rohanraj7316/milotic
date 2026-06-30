"""Tests for trading order tools."""

import httpx
import pytest
import respx

from milotic.api.base import BaseClient
from milotic.utils.errors import RateLimitError


@pytest.mark.asyncio
async def test_trading_place_order_success(mock_env):
    with respx.mock(base_url="http://trading.test") as router:
        router.post("/orders").mock(
            return_value=httpx.Response(200, json={"order_id": "abc123", "status": "pending"})
        )
        client = await BaseClient.instance("trading")
        result = await client.post(
            "/orders",
            json={"symbol": "AAPL", "side": "buy", "quantity": 10, "order_type": "market"},
        )
        assert result["order_id"] == "abc123"


@pytest.mark.asyncio
async def test_trading_rate_limit_raises(mock_env):
    with respx.mock(base_url="http://trading.test") as router:
        router.post("/orders").mock(return_value=httpx.Response(429))
        client = await BaseClient.instance("trading")
        with pytest.raises(RateLimitError):
            await client.post("/orders", json={})
