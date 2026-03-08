"""Entry point for the air-marshall database service."""

import uvicorn

from air_marshall.database.app import app
from air_marshall.database.config import get_settings


def main() -> None:
    """Start the uvicorn server."""
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
