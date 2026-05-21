"""Custom Milotic exceptions."""

class MiloticError(Exception):
    """Base exception for all Milotic errors."""
    message: str = "An unexpected error occurred in Milotic."

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)

class BackendConnectionError(MiloticError):
    """Raised when the Go backend is unreachable or returns a 5xx error."""
    message = "Unable to connect to the trading backend."

class MarketDataError(MiloticError):
    """Raised when market data is unavailable or malformed."""
    message = "Failed to retrieve market data."

class ValidationError(MiloticError):
    """Raised when input parameters fail validation."""
    message = "Invalid input parameters provided."

class HandshakeError(MiloticError):
    """Raised when the public key handshake fails."""
    message = "Failed to complete security handshake with the backend."

class CryptoError(MiloticError):
    """Raised for general cryptographic failures, e.g., during header creation."""
    message = "A security or encryption operation failed."

class DecryptionError(CryptoError):
    """Raised specifically when response body decryption fails."""
    message = "Failed to decrypt the response from the backend."
