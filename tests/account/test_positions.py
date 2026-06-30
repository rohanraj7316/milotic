"""Tests for account position tools."""

import httpx
import pytest
import respx

from milotic.api.base import BaseClient


@pytest.mark.asyncio
async def test_account_list_positions_success(mock_env):
    with respx.mock(base_url="http://account.test") as router:
        router.get("/positions").mock(
            return_value=httpx.Response(200, json={"positions": []})
        )
        client = await BaseClient.instance("account")
        result = await client.get("/positions")
        assert "positions" in result
