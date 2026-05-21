"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Load variables from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Backend Connection ---
    GO_BACKEND_URL: str = "https://api.example.com"

    # --- Crypto Settings ---
    CRYPTO_ENABLED: bool = True
    
    # Client identification for handshake and headers
    API_CLIENT_ID: str

    # 32+ byte AES session secret (client-held)
    API_SESSION_SECRET: str

    # --- Handshake Settings ---
    # Dev fallback ONLY, for when the handshake endpoint is unavailable
    API_RSA_PUBLIC_KEY: Optional[str] = None
    
    HANDSHAKE_PATH: str = "/handshake/get-public-key"
    HANDSHAKE_PUBLIC_KEY_TTL_SECONDS: int = 3600
    HANDSHAKE_CLIENT_ID_HEADER: str = "X-API-Client-Id"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

# Create a singleton instance of the settings
settings = Settings()
