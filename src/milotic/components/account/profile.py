"""Account profile tools."""

from fastmcp.tools import tool

from milotic.api.base import BaseClient
from milotic.utils.decorators import milotic_tool


@tool()
@milotic_tool
async def account_get_profile() -> dict:
    """
    Fetch the authenticated user's account profile and settings.
    Use to retrieve account tier, enabled features, or KYC status.
    """
    client = await BaseClient.instance("account")
    return await client.get("/profile")
