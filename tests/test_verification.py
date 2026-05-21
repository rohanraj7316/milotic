"""Final verification task for the encryption layer implementation."""
import pytest
from unittest.mock import patch, AsyncMock
import httpx
import json
import importlib

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

@patch("milotic.api.session.SessionKeyProvider")
@patch("milotic.api.handshake.HandshakeClient.get_public_key", new_callable=AsyncMock)
async def test_base_client_full_flow(
    mock_get_public_key: AsyncMock,
    mock_session_provider: patch,
    respx_mock,
    monkeypatch,
):
    """
    An end-to-end test verifying the full crypto flow by mocking the
    SessionKeyProvider to isolate the BaseClient logic.
    """
    # 1. Setup Mocks
    mock_get_public_key.return_value = "mock-public-key"
    
    # Mock the instance of SessionKeyProvider to return a predictable header
    mock_provider_instance = mock_session_provider.return_value
    mock_provider_instance.encrypt_session_for_header.return_value = "encrypted-session-header"

    # 2. Setup Environment
    monkeypatch.setenv("CRYPTO_ENABLED", "true")
    monkeypatch.setenv("GO_BACKEND_URL", "https://test.backend.api")
    monkeypatch.setenv("API_CLIENT_ID", "test-client")
    monkeypatch.setenv("API_SESSION_SECRET", "a-very-secure-32-byte-secret-key")

    # 3. Reload Config and Import Modules
    import milotic.config
    importlib.reload(milotic.config)
    from milotic.config import settings

    from milotic.api.base import BaseClient
    from milotic.utils.crypto import MiloticCipher

    # 4. Run Test
    # This will trigger the bootstrap
    client = await BaseClient.instance()
    
    # Verify bootstrap calls
    mock_get_public_key.assert_awaited_once_with("test-client")
    mock_session_provider.assert_called_once_with("mock-public-key")
    mock_provider_instance.encrypt_session_for_header.assert_called_once_with(
        settings.API_SESSION_SECRET
    )

    # Setup for request/response mocking
    test_cipher = MiloticCipher(settings.API_SESSION_SECRET)
    test_path = "/v1/test-order"
    request_payload = {"symbol": "BTC", "qty": 1}
    response_payload = {"orderId": "12345", "status": "FILLED"}
    encrypted_response_wrapper = test_cipher.encrypt_json(response_payload)
    
    respx_mock.post(test_path).mock(return_value=httpx.Response(200, json=encrypted_response_wrapper))

    # Make the call
    decrypted_response = await client.post(test_path, json=request_payload)
    
    # 5. Assertions
    assert decrypted_response == response_payload
    
    sent_request = respx_mock.calls.last.request
    sent_payload_wrapper = json.loads(sent_request.content)
    decrypted_sent_payload = test_cipher.decrypt_json(sent_payload_wrapper)
    assert decrypted_sent_payload == request_payload
    
    assert sent_request.headers["x-api-client-id"] == "test-client"
    assert sent_request.headers["x-api-encryption-key"] == "encrypted-session-header"

    # 6. Cleanup
    BaseClient._instance = None
