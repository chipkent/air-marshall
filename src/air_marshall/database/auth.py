"""API key authentication for the air-marshall database service."""

import secrets

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from air_marshall.database.config import Settings, get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
"""FastAPI security scheme that extracts the ``X-API-Key`` request header.

``auto_error=False`` lets the header be absent (yielding ``None``) so that
``require_api_key`` can return a consistent 401 for both missing and wrong keys
rather than the 403 FastAPI would raise automatically.
"""


async def require_api_key(
    api_key: str | None = Security(API_KEY_HEADER),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate the X-API-Key header against the configured API key.

    Uses constant-time comparison to prevent timing attacks.

    Raises:
        HTTPException: 401 if the header is absent or the key does not match.
    """
    if api_key is None or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
