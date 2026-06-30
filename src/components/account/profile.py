"""Account profile tools."""

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.decorators import milotic_tool
from utils.session import get_session_headers


@tool()
@milotic_tool
async def account_get_profile(ctx: Context) -> dict:
    """
    Fetch the authenticated user's account profile and settings.
    Use to retrieve account tier, enabled features, or KYC status.
    """
    headers = await get_session_headers(ctx)
    client = await BaseClient.instance("account")
    return await client.get("/profile", headers=headers)
