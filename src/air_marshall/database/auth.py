"""API key authentication for the air-marshall database service."""

import secrets

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from air_marshall.database.config import Settings, get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)
"""FastAPI security scheme that extracts the ``X-API-Key`` request header."""


async def require_api_key(
    api_key: str = Security(API_KEY_HEADER),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate the X-API-Key header against the configured API key.

    Uses constant-time comparison to prevent timing attacks.

    Raises:
        HTTPException: 401 if the key does not match.
    """
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
