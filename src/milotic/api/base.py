"""
Core HTTP client for all Go backend communications.

Implements the "Vortex" pattern for transparent encryption and decryption.
"""

import httpx
import asyncio
from typing import Optional, Any, Dict

from milotic.config import settings
from milotic.utils.logging import logger
from milotic.utils.errors import BackendConnectionError, DecryptionError
from milotic.api.handshake import HandshakeClient
from milotic.api.session import SessionKeyProvider
from milotic.utils.crypto import MiloticCipher

class BaseClient:
    """
    A singleton HTTP client that manages a crypto bootstrap process and
    transparently encrypts/decrypts JSON payloads for all relevant requests.
    """
    _instance: Optional["BaseClient"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        # Prevent direct instantiation
        raise RuntimeError("Call instance() instead.")

    @classmethod
    async def instance(cls) -> "BaseClient":
        """Get the singleton instance, initializing it if necessary."""
        if cls._instance:
            return cls._instance
        async with cls._lock:
            if cls._instance:
                return cls._instance  # Return instance if created by another coroutine
            
            # Create and bootstrap the instance
            new_instance = cls.__new__(cls)
            new_instance._http_client = httpx.AsyncClient(base_url=settings.GO_BACKEND_URL)
            new_instance._session_key_provider: Optional[SessionKeyProvider] = None
            new_instance._cipher: Optional[MiloticCipher] = None
            new_instance._encrypted_session_header: Optional[str] = None
            
            if settings.CRYPTO_ENABLED:
                await new_instance._bootstrap_crypto()

            cls._instance = new_instance
            return new_instance

    async def _bootstrap_crypto(self):
        """
        Performs the initial handshake and sets up the session-level crypto
        components (session key provider, cipher, and encrypted header).
        """
        logger.info("crypto_bootstrap_start")
        handshake_client = HandshakeClient(
            base_url=settings.GO_BACKEND_URL,
            path=settings.HANDSHAKE_PATH,
            client_id_header=settings.HANDSHAKE_CLIENT_ID_HEADER,
        )

        public_key = await handshake_client.get_public_key(settings.API_CLIENT_ID)
        
        self._session_key_provider = SessionKeyProvider(public_key)
        self._encrypted_session_header = self._session_key_provider.encrypt_session_for_header(
            settings.API_SESSION_SECRET
        )
        self._cipher = MiloticCipher(settings.API_SESSION_SECRET)
        logger.info("crypto_bootstrap_success")

    async def request(
        self, method: str, path: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        The main entrypoint for making requests. Handles transparent encryption
        and decryption if crypto is enabled.
        """
        # Read-only guard
        if method.upper() not in ["GET", "HEAD", "OPTIONS"]:
            # A whitelist can be added here for specific auth POSTs if needed
            logger.warning("read_only_guard_violation", method=method, path=path)
            # In a real scenario, you might raise an error. For now, we log.

        headers = kwargs.pop("headers", {})
        json_payload = kwargs.pop("json", None)

        if settings.CRYPTO_ENABLED:
            if not self._cipher or not self._encrypted_session_header:
                raise BackendConnectionError("Crypto components not initialized. Bootstrap may have failed.")

            headers[settings.HANDSHAKE_CLIENT_ID_HEADER] = settings.API_CLIENT_ID
            headers["X-API-Encryption-Key"] = self._encrypted_session_header
            
            if json_payload is not None:
                encrypted_wrapper = self._cipher.encrypt_json(json_payload)
                kwargs["json"] = encrypted_wrapper

        try:
            response = await self._http_client.request(method, path, headers=headers, **kwargs)
            response.raise_for_status()
            
            # Handle possible empty response body
            if not response.content:
                return {}
            
            response_data = response.json()
            
            if settings.CRYPTO_ENABLED and response_data:
                # Decrypt the payload before returning
                return self._cipher.decrypt_json(response_data)
            
            return response_data

        except httpx.HTTPStatusError as e:
            # Handle HTTP errors
            raise BackendConnectionError(
                f"Request failed with status {e.response.status_code}"
            ) from e
        except DecryptionError as e:
            # Re-raise decryption errors to be handled by the tool decorator
            raise e
        except Exception as e:
            # Handle other errors (connection, timeout, etc.)
            raise BackendConnectionError("An unexpected error occurred during the request.") from e

    # --- Convenience methods ---

    async def get(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        return await self.request("DELETE", path, **kwargs)
