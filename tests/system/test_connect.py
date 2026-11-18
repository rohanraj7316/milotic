"""Tests for SSO-based authentication session tools and ephemeral loopback server."""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from components.system.system import system_connect_start, system_connect_verify
from utils.loopback import SSOLoopbackSession, default_loopback


@pytest.mark.asyncio
@patch("api.base.BaseClient.post", new_callable=AsyncMock)
async def test_system_connect_start_success(mock_post: AsyncMock, mock_env):
    mock_post.return_value = {
        "data": {"redirectURL": "https://auth.uat.asldt.com/sso/validate?ssoId=abc123"}
    }

    ctx = AsyncMock()

    result = await system_connect_start(ctx)

    assert result["redirect_url"] == "https://auth.uat.asldt.com/sso/validate?ssoId=abc123"
    ctx.set_state.assert_not_awaited()
    await default_loopback.close()


@pytest.mark.asyncio
@patch("api.base.BaseClient.post", new_callable=AsyncMock)
async def test_system_connect_verify_confirmed(mock_post: AsyncMock, mock_env):
    mock_post.return_value = {
        "statusCode": 200,
        "status": "OK",
        "data": {
            "authToken": {"token": "tok123"},
            "refreshToken": {"token": "ref456"},
            "accounts": [{"subAccountId": "sub456", "isPrimary": True}],
        },
    }

    ctx = AsyncMock()

    result = await system_connect_verify(ctx, redirect_url="https://google.com?ssoId=abc123")

    assert result == {"status": "connected", "sub_account_id": "sub456"}
    assert ctx.set_state.await_count == 3
    ctx.set_state.assert_any_await("auth_token", "tok123")
    ctx.set_state.assert_any_await("refresh_token", "ref456")
    ctx.set_state.assert_any_await("sub_account_id", "sub456")


@pytest.mark.asyncio
@patch("api.base.BaseClient.post", new_callable=AsyncMock)
async def test_system_connect_verify_failure(mock_post: AsyncMock, mock_env):
    mock_post.side_effect = Exception("Invalid SSO token")

    ctx = AsyncMock()

    result = await system_connect_verify(ctx, redirect_url="https://google.com?ssoId=abc123")

    assert result["status"] == "failed"
    assert "Invalid SSO token" in result["error"]
    ctx.set_state.assert_awaited_once_with("sso_id", None)


@pytest.mark.asyncio
async def test_system_connect_verify_no_session(mock_env):
    ctx = AsyncMock()

    with patch("api.base.BaseClient.instance", new_callable=AsyncMock) as mock_instance:
        result = await system_connect_verify(ctx, redirect_url=None)

    assert result["status"] == "pending"
    mock_instance.assert_not_awaited()
    ctx.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_system_loopback_server_success():
    """Verify loopback server successfully captures ssoId when CSRF state matches."""
    session = SSOLoopbackSession()
    port, csrf_state = await session.start(timeout_seconds=60)
    assert port > 0
    assert len(csrf_state) > 16

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://127.0.0.1:{port}/callback?ssoId=capture123&state={csrf_state}"
            )
            assert response.status_code == 200
            assert "Login Successful" in response.text

        assert session.consume_sso_id() == "capture123"
        assert session.consume_sso_id() is None
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_system_loopback_server_csrf_mismatch():
    """Verify loopback server rejects callback when CSRF state is invalid or missing."""
    session = SSOLoopbackSession()
    port, _ = await session.start(timeout_seconds=60)

    try:
        async with httpx.AsyncClient() as client:
            # 1. Wrong state
            resp_wrong = await client.get(
                f"http://127.0.0.1:{port}/callback?ssoId=capture123&state=wrong_state"
            )
            assert resp_wrong.status_code == 400
            assert "Authentication Failed" in resp_wrong.text
            assert session.captured_sso_id is None

            # 2. Missing state
            resp_no_state = await client.get(f"http://127.0.0.1:{port}/callback?ssoId=capture123")
            assert resp_no_state.status_code == 400
            assert session.captured_sso_id is None
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_system_loopback_server_large_headers():
    """Verify loopback server handles request with large headers without truncation."""
    session = SSOLoopbackSession()
    port, csrf_state = await session.start(timeout_seconds=60)

    try:
        large_headers = {"X-Large-Header": "A" * 4096}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://127.0.0.1:{port}/callback?ssoId=big_payload_sso&state={csrf_state}",
                headers=large_headers,
            )
            assert response.status_code == 200
            assert "Login Successful" in response.text

        assert session.consume_sso_id() == "big_payload_sso"
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_system_loopback_server_timeout():
    """Verify loopback server terminates automatically after timeout expires."""
    session = SSOLoopbackSession()
    _port, _ = await session.start(timeout_seconds=1)

    assert session.server is not None
    await asyncio.sleep(1.1)

    assert session.server is None
    assert session.port == 0


@pytest.mark.asyncio
async def test_system_connect_verify_from_loopback_capture(mock_env):
    """Verify system_connect_verify picks up ssoId captured by loopback server."""
    port, csrf_state = await default_loopback.start(timeout_seconds=60)

    try:
        async with httpx.AsyncClient() as client:
            await client.get(
                f"http://127.0.0.1:{port}/callback?ssoId=captured_sso_999&state={csrf_state}"
            )

        with patch("api.base.BaseClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {
                "statusCode": 200,
                "data": {
                    "authToken": {"token": "tok999"},
                    "refreshToken": {"token": "ref999"},
                    "accounts": [{"subAccountId": "sub999", "isPrimary": True}],
                },
            }
            ctx = AsyncMock()
            result = await system_connect_verify(ctx)

            assert result == {"status": "connected", "sub_account_id": "sub999"}
            mock_post.assert_awaited_once_with(
                "/sso/authenticate", json={"ssoId": "captured_sso_999"}
            )
            ctx.set_state.assert_any_await("auth_token", "tok999")
            ctx.set_state.assert_any_await("sub_account_id", "sub999")
    finally:
        await default_loopback.close()
