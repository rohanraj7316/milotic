"""Tests for market quote tools."""

import httpx
import pytest
import respx

from milotic.api.base import BaseClient
from milotic.utils.errors import BackendConnectionError, CircuitBreakerOpenError


@pytest.mark.asyncio
async def test_market_get_quote_success(mock_env):
    with respx.mock(base_url="http://market.test") as router:
        router.get("/quotes/AAPL").mock(
            return_value=httpx.Response(200, json={"symbol": "AAPL", "price": 150.0})
        )
        client = await BaseClient.instance("market")
        result = await client.get("/quotes/AAPL")
        assert result["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold(mock_env):
    import milotic.config as cfg

    with respx.mock(base_url="http://market.test") as router:
        router.get("/quotes/ERR").mock(return_value=httpx.Response(500))

        threshold = cfg.settings.CIRCUIT_BREAKER_THRESHOLD
        client = await BaseClient.instance("market")

        for _ in range(threshold):
            with pytest.raises(BackendConnectionError):
                await client.get("/quotes/ERR")

        assert client._circuit_open is True

        with pytest.raises(CircuitBreakerOpenError):
            await client.get("/quotes/ERR")
