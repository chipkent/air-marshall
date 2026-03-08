"""Tests for air_marshall.database.config."""

import pytest
from pydantic import ValidationError

from air_marshall.database.config import Settings, get_settings


def test_missing_api_key_raises() -> None:
    """Settings raises ValidationError when api_key is not provided."""
    with pytest.raises(ValidationError):
        Settings()


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings has correct default values when only api_key is provided."""
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "mykey")
    s = Settings()
    assert s.api_key == "mykey"
    assert s.db_path == "air_marshall.db"
    assert s.retention_days == 30
    assert s.pruning_interval_hours == 6
    assert s.host == "0.0.0.0"  # noqa: S104
    assert s.port == 8000
    assert s.log_level == "info"


def test_env_prefix_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings ignores env vars without the AIR_MARSHALL_DB_ prefix."""
    monkeypatch.setenv("API_KEY", "noprefix")
    with pytest.raises(ValidationError):
        Settings()


def test_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings accepts all fields from environment variables."""
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "k")
    monkeypatch.setenv("AIR_MARSHALL_DB_DB_PATH", "/tmp/test.db")  # noqa: S108
    monkeypatch.setenv("AIR_MARSHALL_DB_RETENTION_DAYS", "7")
    monkeypatch.setenv("AIR_MARSHALL_DB_PRUNING_INTERVAL_HOURS", "12")
    monkeypatch.setenv("AIR_MARSHALL_DB_HOST", "127.0.0.1")
    monkeypatch.setenv("AIR_MARSHALL_DB_PORT", "9000")
    monkeypatch.setenv("AIR_MARSHALL_DB_LOG_LEVEL", "debug")
    s = Settings()
    assert s.db_path == "/tmp/test.db"  # noqa: S108
    assert s.retention_days == 7
    assert s.pruning_interval_hours == 12
    assert s.host == "127.0.0.1"
    assert s.port == 9000
    assert s.log_level == "debug"


def test_lru_cache_returns_same_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings() returns the same object on repeated calls."""
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "cachekey")
    get_settings.cache_clear()
    try:
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
    finally:
        get_settings.cache_clear()


def test_monkeypatch_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cache can be cleared to reflect new environment values."""
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "first")
    get_settings.cache_clear()
    try:
        s1 = get_settings()
        assert s1.api_key == "first"

        get_settings.cache_clear()
        monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "second")
        s2 = get_settings()
        assert s2.api_key == "second"
        assert s1 is not s2
    finally:
        get_settings.cache_clear()
