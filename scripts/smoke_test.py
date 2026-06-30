"""
Smoke test for BaseClient HTTP integration.
Run via: uv run python scripts/smoke_test.py
Or use the "Debug: Smoke Test" launch config in VS Code.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv

load_dotenv()


async def main():
    from milotic.api.base import BaseClient
    from milotic.config import settings

    print(f"CRYPTO_ENABLED : {settings.CRYPTO_ENABLED}")
    print(f"MARKET_BACKEND_URL: {settings.MARKET_BACKEND_URL}")
    print()

    print("1. Bootstrapping market client (handshake + crypto)...")
    client = await BaseClient.instance("market")
    print(f"   cipher ready         : {client._cipher is not None}")
    print(f"   session header set   : {client._encrypted_session_header is not None}")
    print(f"   circuit open         : {client._circuit_open}")
    print()

    print("2. GET /quotes/AAPL ...")
    try:
        result = await client.get("/quotes/AAPL")
        print(f"   response: {result}")
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")

    print()
    print("Done.")


asyncio.run(main())
