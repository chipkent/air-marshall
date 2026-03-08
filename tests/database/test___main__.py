"""Tests for air_marshall.database.__main__."""

from unittest.mock import patch

import pytest

from air_marshall.database.config import get_settings


def test_main_calls_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() calls uvicorn.run with the FastAPI app and settings-derived args."""
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "key")
    get_settings.cache_clear()
    try:
        with patch("air_marshall.database.__main__.uvicorn.run") as mock_run:
            from air_marshall.database.__main__ import main

            main()
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            # First positional arg is the app
            from air_marshall.database.app import app

            assert args[0] is app
            assert kwargs["host"] == "0.0.0.0"  # noqa: S104
            assert kwargs["port"] == 8000
            assert kwargs["log_level"] == "info"
    finally:
        get_settings.cache_clear()


def test_main_uses_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() passes the configured port and host to uvicorn."""
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "key2")
    monkeypatch.setenv("AIR_MARSHALL_DB_PORT", "9999")
    monkeypatch.setenv("AIR_MARSHALL_DB_HOST", "127.0.0.1")
    monkeypatch.setenv("AIR_MARSHALL_DB_LOG_LEVEL", "debug")
    get_settings.cache_clear()
    try:
        with patch("air_marshall.database.__main__.uvicorn.run") as mock_run:
            from air_marshall.database.__main__ import main

            main()
            _, kwargs = mock_run.call_args
            assert kwargs["port"] == 9999
            assert kwargs["host"] == "127.0.0.1"
            assert kwargs["log_level"] == "debug"
    finally:
        get_settings.cache_clear()
