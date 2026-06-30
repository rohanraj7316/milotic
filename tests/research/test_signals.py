"""Tests for research signal tools."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from milotic.api.base import BaseClient
from milotic.components.research.signals import research_get_signal, research_list_signals


def make_ctx() -> AsyncMock:
    """Build an AsyncMock ctx whose get_state resolves auth_token/sub_account_id."""
    ctx = AsyncMock()

    async def get_state(key: str):
        return {"auth_token": "tok123", "sub_account_id": "sub456"}.get(key)

    ctx.get_state.side_effect = get_state
    return ctx


@pytest.mark.asyncio
async def test_research_get_signal_success(mock_env):
    with respx.mock(base_url="http://research.test") as router:
        router.get("/signals/AAPL").mock(
            return_value=httpx.Response(200, json={"symbol": "AAPL", "signal": "buy"})
        )
        client = await BaseClient.instance("research")
        result = await client.get("/signals/AAPL")
        assert result["signal"] == "buy"


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.get", new_callable=AsyncMock)
async def test_research_get_signal_uses_session_headers(mock_get: AsyncMock, mock_env):
    mock_get.return_value = {"symbol": "AAPL", "signal": "buy"}
    ctx = make_ctx()

    result = await research_get_signal(ctx, symbol="AAPL")

    assert result["signal"] == "buy"
    mock_get.assert_awaited_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "/signals/AAPL"
    assert kwargs["headers"]["X-Auth-Token"] == "tok123"


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.get", new_callable=AsyncMock)
async def test_research_list_signals_uses_session_headers(mock_get: AsyncMock, mock_env):
    mock_get.return_value = {"signals": []}
    ctx = make_ctx()

    result = await research_list_signals(ctx)

    assert result == {"signals": []}
    mock_get.assert_awaited_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "/signals"
    assert kwargs["headers"]["X-Auth-Token"] == "tok123"


@pytest.mark.asyncio
async def test_research_get_signal_not_connected_returns_error(mock_env):
    ctx = AsyncMock()
    ctx.get_state.return_value = None

    with patch("milotic.api.base.BaseClient.instance", new_callable=AsyncMock) as mock_instance:
        result = await research_get_signal(ctx, symbol="AAPL")

    assert "error" in result
    mock_instance.assert_not_awaited()
