"""Tests for QR-based authentication session tools."""

from unittest.mock import AsyncMock, patch

import pytest

from milotic.components.system.system import system_connect_start, system_connect_verify


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.post", new_callable=AsyncMock)
async def test_system_connect_start_success(mock_post: AsyncMock, mock_env):
    mock_post.return_value = {"session_id": "abc123", "qr_image_base64": "fakedata"}

    ctx = AsyncMock()

    result = await system_connect_start(ctx)

    assert result["session_id"] == "abc123"
    assert result["qr_image_base64"] == "fakedata"
    ctx.set_state.assert_awaited_once_with("qr_session_id", "abc123")


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.get", new_callable=AsyncMock)
async def test_system_connect_verify_confirmed(mock_get: AsyncMock, mock_env):
    mock_get.return_value = {
        "status": "confirmed",
        "auth_token": "tok123",
        "sub_account_id": "sub456",
    }

    ctx = AsyncMock()
    ctx.get_state.return_value = "abc123"

    result = await system_connect_verify(ctx)

    assert result == {"status": "connected", "sub_account_id": "sub456"}
    assert ctx.set_state.await_count == 2
    ctx.set_state.assert_any_await("auth_token", "tok123")
    ctx.set_state.assert_any_await("sub_account_id", "sub456")


@pytest.mark.asyncio
@patch("milotic.api.base.BaseClient.get", new_callable=AsyncMock)
async def test_system_connect_verify_pending(mock_get: AsyncMock, mock_env):
    mock_get.return_value = {"status": "pending"}

    ctx = AsyncMock()
    ctx.get_state.return_value = "abc123"

    result = await system_connect_verify(ctx)

    assert result["status"] == "pending"
    ctx.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_system_connect_verify_no_session(mock_env):
    ctx = AsyncMock()
    ctx.get_state.return_value = None

    with patch("milotic.api.base.BaseClient.instance", new_callable=AsyncMock) as mock_instance:
        result = await system_connect_verify(ctx)

    assert result == {"error": "No pending connection. Call system_connect_start first."}
    mock_instance.assert_not_awaited()
    ctx.set_state.assert_not_awaited()
