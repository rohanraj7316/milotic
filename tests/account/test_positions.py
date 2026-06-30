"""Tests for account position tools."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from milotic.api.base import BaseClient
from milotic.components.account.positions import (
    account_get_position,
    account_list_positions,
)


def make_ctx() -> AsyncMock:
    """Build an AsyncMock ctx whose get_state resolves auth_token/sub_account_id."""
    ctx = AsyncMock()

    async def get_state(key: str):
        return {"auth_token": "tok123", "sub_account_id": "sub456"}.get(key)

    ctx.get_state.side_effect = get_state
    return ctx


@pytest.mark.asyncio
async def test_account_list_positions_success(mock_env):
    with respx.mock(base_url="http://account.test") as router:
        router.get("/positions").mock(
            return_value=httpx.Response(200, json={"positions": []})
        )
        client = await BaseClient.instance("account")
        result = await client.get("/positions")
        assert "positions" in result


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.get", new_callable=AsyncMock)
async def test_account_list_positions_uses_session_headers(mock_get: AsyncMock, mock_env):
    mock_get.return_value = {"positions": []}
    ctx = make_ctx()

    result = await account_list_positions(ctx)

    assert result == {"positions": []}
    mock_get.assert_awaited_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "/positions"
    assert kwargs["headers"]["X-Auth-Token"] == "tok123"


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.get", new_callable=AsyncMock)
async def test_account_get_position_uses_session_headers(mock_get: AsyncMock, mock_env):
    mock_get.return_value = {"symbol": "AAPL", "quantity": 10}
    ctx = make_ctx()

    result = await account_get_position(ctx, symbol="AAPL")

    assert result["symbol"] == "AAPL"
    mock_get.assert_awaited_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "/positions/AAPL"
    assert kwargs["headers"]["X-Auth-Token"] == "tok123"


@pytest.mark.asyncio
async def test_account_list_positions_not_connected_returns_error(mock_env):
    ctx = AsyncMock()
    ctx.get_state.return_value = None

    with patch("milotic.api.base.BaseClient.instance", new_callable=AsyncMock) as mock_instance:
        result = await account_list_positions(ctx)

    assert "error" in result
    mock_instance.assert_not_awaited()
