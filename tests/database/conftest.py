"""Shared fixtures for database tests."""

import aiosqlite
import httpx
import pytest
import pytest_asyncio

from air_marshall.database.app import app
from air_marshall.database.config import Settings, get_settings
from air_marshall.database.db import create_tables, get_db_conn


@pytest_asyncio.fixture
async def db_conn() -> aiosqlite.Connection:
    """Provide an in-memory aiosqlite connection with tables created.

    Yields:
        An open aiosqlite connection backed by an in-memory SQLite database.
    """
    async with aiosqlite.connect(":memory:") as conn:  # noqa: S108
        await create_tables(conn)
        yield conn  # type: ignore[misc]


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Provide a Settings instance with test values via monkeypatching.

    Clears the lru_cache before and after the test to prevent leakage.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    Yields:
        A Settings object configured for testing.
    """
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "test-key")
    monkeypatch.setenv("AIR_MARSHALL_DB_DB_PATH", ":memory:")  # noqa: S108
    get_settings.cache_clear()
    settings = get_settings()
    yield settings  # type: ignore[misc]
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def test_client(
    db_conn: aiosqlite.Connection,
    test_settings: Settings,
) -> httpx.AsyncClient:
    """Provide an httpx AsyncClient wired to the FastAPI app with test overrides.

    The db connection and settings are injected via dependency_overrides so no
    real database file is created and no environment variable is needed.

    Args:
        db_conn: The in-memory aiosqlite connection fixture.
        test_settings: The test settings fixture.

    Yields:
        An httpx.AsyncClient pointed at the test app.
    """

    async def override_db() -> aiosqlite.Connection:
        return db_conn

    def override_settings() -> Settings:
        return test_settings

    app.dependency_overrides[get_db_conn] = override_db
    app.dependency_overrides[get_settings] = override_settings

    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client  # type: ignore[misc]

    app.dependency_overrides.clear()
