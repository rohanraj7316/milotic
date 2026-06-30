"""Tests for trading margin tools."""

from unittest.mock import AsyncMock, patch

import pytest

from milotic.components.trading.margin import trading_calculate_margin, trading_get_margin


def make_ctx() -> AsyncMock:
    """Build an AsyncMock ctx whose get_state resolves auth_token/sub_account_id."""
    ctx = AsyncMock()

    async def get_state(key: str):
        return {"auth_token": "tok123", "sub_account_id": "sub456"}.get(key)

    ctx.get_state.side_effect = get_state
    return ctx


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.get", new_callable=AsyncMock)
async def test_trading_get_margin_uses_session_headers(mock_get: AsyncMock, mock_env):
    mock_get.return_value = {"available_margin": 1000}
    ctx = make_ctx()

    result = await trading_get_margin(ctx)

    assert result["available_margin"] == 1000
    mock_get.assert_awaited_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "/margin"
    assert kwargs["headers"]["X-Auth-Token"] == "tok123"


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.get", new_callable=AsyncMock)
async def test_trading_calculate_margin_uses_session_headers(mock_get: AsyncMock, mock_env):
    mock_get.return_value = {"required_margin": 500}
    ctx = make_ctx()

    result = await trading_calculate_margin(ctx, symbol="AAPL", quantity=10, leverage=2)

    assert result["required_margin"] == 500
    mock_get.assert_awaited_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "/margin/calculate"
    assert kwargs["params"] == {"symbol": "AAPL", "quantity": 10, "leverage": 2}
    assert kwargs["headers"]["X-Auth-Token"] == "tok123"


@pytest.mark.asyncio
async def test_trading_get_margin_not_connected_returns_error(mock_env):
    ctx = AsyncMock()
    ctx.get_state.return_value = None

    with patch("milotic.api.base.BaseClient.instance", new_callable=AsyncMock) as mock_instance:
        result = await trading_get_margin(ctx)

    assert "error" in result
    mock_instance.assert_not_awaited()
