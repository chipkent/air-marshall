"""Configuration for the air-marshall database service."""

import functools

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration loaded from ``AIR_MARSHALL_DB_*`` environment variables.

    ``api_key`` is required; all other fields have defaults.
    """

    model_config = SettingsConfigDict(env_prefix="AIR_MARSHALL_DB_")

    api_key: str
    """Shared secret required in the ``X-API-Key`` header of every request."""

    db_path: str = "air_marshall.db"
    """Path to the SQLite database file. Use ``:memory:`` in tests."""

    retention_days: int = 30
    """Records older than this many days are deleted by the pruning loop."""

    pruning_interval_hours: int = 6
    """How often the pruning loop runs, in hours."""

    host: str = "0.0.0.0"  # noqa: S104
    """Host address passed to uvicorn. Binds all interfaces by default."""

    port: int = 8000
    """TCP port passed to uvicorn."""

    log_level: str = "info"
    """Uvicorn log level (debug, info, warning, error, critical)."""


@functools.lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance.

    Cached so repeated calls (e.g. via FastAPI ``Depends``) share one object.
    Call ``get_settings.cache_clear()`` in tests to reset between cases.
    """
    # pydantic-settings populates all fields from environment variables at
    # runtime, so no constructor arguments are needed. mypy cannot see this
    # and incorrectly flags the call as missing the required api_key argument.
    return Settings()  # type: ignore[call-arg]
