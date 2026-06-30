"""Tests for market quote tools."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from milotic.api.base import BaseClient
from milotic.components.market.quotes import market_get_quote, market_get_quotes_batch
from milotic.utils.errors import BackendConnectionError, CircuitBreakerOpenError


def make_ctx() -> AsyncMock:
    """Build an AsyncMock ctx whose get_state resolves auth_token/sub_account_id."""
    ctx = AsyncMock()

    async def get_state(key: str):
        return {"auth_token": "tok123", "sub_account_id": "sub456"}.get(key)

    ctx.get_state.side_effect = get_state
    return ctx


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


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.get", new_callable=AsyncMock)
async def test_market_get_quote_uses_session_headers(mock_get: AsyncMock, mock_env):
    mock_get.return_value = {"symbol": "AAPL", "price": 150.0}
    ctx = make_ctx()

    result = await market_get_quote(ctx, symbol="AAPL")

    assert result["symbol"] == "AAPL"
    mock_get.assert_awaited_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "/quotes/AAPL"
    assert kwargs["headers"]["X-Auth-Token"] == "tok123"


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.post", new_callable=AsyncMock)
async def test_market_get_quotes_batch_uses_session_headers(mock_post: AsyncMock, mock_env):
    mock_post.return_value = {"quotes": []}
    ctx = make_ctx()

    result = await market_get_quotes_batch(ctx, symbols=["AAPL", "MSFT"])

    assert result == {"quotes": []}
    mock_post.assert_awaited_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "/quotes/batch"
    assert kwargs["json"] == {"symbols": ["AAPL", "MSFT"]}
    assert kwargs["headers"]["X-Auth-Token"] == "tok123"


@pytest.mark.asyncio
async def test_market_get_quote_not_connected_returns_error(mock_env):
    ctx = AsyncMock()
    ctx.get_state.return_value = None

    with patch("milotic.api.base.BaseClient.instance", new_callable=AsyncMock) as mock_instance:
        result = await market_get_quote(ctx, symbol="AAPL")

    assert "error" in result
    mock_instance.assert_not_awaited()
