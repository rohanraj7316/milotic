"""System-related tools for Milotic Gateway."""

import contextlib
import json
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from fastmcp import Context
from fastmcp.tools import tool

from api.base import BaseClient
from utils.constants import VERSION
from utils.decorators import milotic_tool
from utils.loopback import default_loopback
from utils.session import get_session_headers


@tool()
@milotic_tool
def system_get_health() -> dict[str, str]:
    """
    Return server health status.
    Verifies the gateway is online and correctly configured.
    """
    return {"status": "ok", "version": VERSION, "foundation": "refined", "backend": "not_connected"}


@tool()
@milotic_tool
async def system_connect_start(ctx: Context) -> dict:
    """
    Initiate Single Sign-On (SSO) authentication. Starts a local loopback server to
    capture redirect, and returns the login redirect URL.
    """
    # ponytail: ephemeral loopback server with CSRF state verification and auto-expiry
    port, csrf_state = await default_loopback.start(timeout_seconds=180)
    local_redirect = f"http://127.0.0.1:{port}/callback?state={csrf_state}"

    client = await BaseClient.instance("login")
    payload = {
        "type": "LOGIN",
        "redirectURL": local_redirect,
        "metadata": {"name": "milotic", "state": csrf_state},
    }

    session = await client.post("/sso/initiate", json=payload)
    redirect_url = session.get("data", {}).get("redirectURL", "")

    # Best-effort automatic browser opening for desktop environments
    with contextlib.suppress(Exception):
        webbrowser.open(redirect_url)

    return {
        "redirect_url": redirect_url,
        "message": (
            "I can help with that, but let's establish a safety boundary first: "
            "I will never ask for your Axis Direct password or login credentials. "
            "Entering sensitive authentication details is something I cannot do on your behalf.\n\n"
            "To connect securely, we use Axis Direct's official Single Sign-On (SSO) microsite:\n\n"
            "🔒 **Security Check:**\n"
            "- A temporary, private loopback server was started on your machine "
            "to capture the callback token securely.\n"
            "- Your credentials never touch my AI context, "
            "nor are they transmitted in plaintext.\n\n"
            "⚠️ **Warning:** AI systems are non-deterministic. By continuing, you agree "
            "to interact with your Axis Direct account via AI at your own risk.\n\n"
            f"If you're ready, click here to log in:\n"
            f"👉 **[Authenticate with Axis Direct]({redirect_url})**\n\n"
            "Once logged in, your browser will redirect and authenticate automatically.\n"
            "*(If blocked, copy the final URL from your browser and paste it "
            "into: system_connect_verify(redirect_url='...'))*"
        ),
    }


@tool()
@milotic_tool
async def system_connect_verify(ctx: Context, redirect_url: str | None = None) -> dict:
    """
    Check whether Single Sign-On (SSO) authentication has been completed.
    redirect_url: Optional manual override. Paste the browser redirect URL here if blocked.
    """
    sso_id = (
        parse_qs(urlsplit(redirect_url).query).get("ssoId", [None])[0]
        if redirect_url
        else default_loopback.consume_sso_id()
    )

    if not sso_id:
        return {
            "status": "pending",
            "message": (
                "Login not yet confirmed. Paste the final browser redirect URL to verify manually."
            ),
        }

    # Stop loopback server since we captured the ssoId
    await default_loopback.close()

    client = await BaseClient.instance("login")
    try:
        # ponytail: call authenticate with captured ssoId
        response = await client.post("/sso/authenticate", json={"ssoId": sso_id})

        sso_data = response.get("data", {})
        auth_token = sso_data.get("authToken", {}).get("token")
        refresh_token = sso_data.get("refreshToken", {}).get("token")

        accounts = sso_data.get("accounts", [])
        primary = next((acc for acc in accounts if acc.get("isPrimary")), None)
        if not primary and accounts:
            primary = accounts[0]
        sub_account_id = primary.get("subAccountId") if primary else None

        if not auth_token or not sub_account_id:
            raise KeyError("Authentication payload was incomplete or invalid.")

        await ctx.set_state("auth_token", auth_token)
        await ctx.set_state("refresh_token", refresh_token)
        await ctx.set_state("sub_account_id", sub_account_id)
        return {"status": "connected", "sub_account_id": sub_account_id}

    except Exception as e:
        # ponytail: wipe sso_id context state to force user to restart on failure
        await ctx.set_state("sso_id", None)
        return {
            "status": "failed",
            "error": str(e),
            "message": "Authentication failed. Please start over using system_connect_start.",
        }


@tool()
@milotic_tool
async def system_get_profile(ctx: Context) -> dict:
    """
    Fetch the authenticated user's account profile, active subAccountId, name,
    account type, and linked sub-accounts.
    """
    sub_account_id = await ctx.get_state("sub_account_id")
    accounts: list = []

    p = Path(".session.json")
    if p.exists():
        with contextlib.suppress(Exception):
            session_data = json.loads(p.read_text())
            accounts = session_data.get("accounts", [])
            if not sub_account_id:
                sub_account_id = session_data.get("sub_account_id")

    primary = next((acc for acc in accounts if acc.get("isPrimary")), None)
    if not primary and accounts:
        primary = accounts[0]

    profile_data: dict = {
        "subAccountId": sub_account_id,
        "primaryAccount": primary,
        "allAccounts": accounts,
    }

    try:
        headers = await get_session_headers(ctx)
        client = await BaseClient.instance("investor")
        remote_profile = await client.get("/user/profile", headers=headers)
        if isinstance(remote_profile, dict) and "data" in remote_profile:
            profile_data["details"] = remote_profile.get("data")
    except Exception:
        pass

    return profile_data


@tool()
@milotic_tool
async def system_disconnect_session(ctx: Context) -> dict:
    """
    Terminate the active session, clear session tokens, and remove local session files.
    """
    await ctx.set_state("auth_token", None)
    await ctx.set_state("refresh_token", None)
    await ctx.set_state("sub_account_id", None)
    await ctx.set_state("sso_id", None)

    p = Path(".session.json")
    if p.exists():
        with contextlib.suppress(Exception):
            p.unlink()

    return {
        "status": "disconnected",
        "message": (
            "Successfully signed out. Session tokens and local session file have been cleared."
        ),
    }
