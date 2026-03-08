"""Tests for air_marshall.database.app."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import patch

import aiosqlite
import httpx
import pytest
from fastapi import FastAPI

from air_marshall.database.app import _pruning_loop, app, lifespan
from air_marshall.database.config import Settings

_TS = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

_HUMIDITY_PAYLOAD = {
    "sensor_id": "s1",
    "sensor_serial_number": "SN001",
    "timestamp": _TS.isoformat(),
    "temperature": 22.5,
    "humidity": 45.0,
    "is_touched": False,
}

_FAN_PAYLOAD = {
    "timestamp": _TS.isoformat(),
    "is_on": True,
}

_CONTROL_PAYLOAD = {
    "timestamp": _TS.isoformat(),
    "humidifier_on": True,
    "fan_on": False,
}


class TestLifespan:
    """Tests for the lifespan context manager."""

    @pytest.mark.asyncio
    async def test_sets_db_conn_on_app_state(self, test_settings: Settings) -> None:
        """Lifespan opens a DB connection and stores it on app.state."""
        test_app = FastAPI()
        async with lifespan(test_app):
            assert hasattr(test_app.state, "db_conn")
            assert test_app.state.db_conn is not None


class TestPruningLoop:
    """Tests for the _pruning_loop background task."""

    @pytest.mark.asyncio
    async def test_calls_prune_and_continues_after_error(
        self, db_conn: aiosqlite.Connection, test_settings: Settings
    ) -> None:
        """_pruning_loop prunes on schedule and keeps running after errors."""
        sleep_count = 0
        prune_calls: list[int] = []

        async def fake_sleep(_: float) -> None:
            nonlocal sleep_count
            sleep_count += 1
            if sleep_count >= 3:
                raise asyncio.CancelledError

        async def fake_prune(_conn: aiosqlite.Connection, days: int) -> None:
            prune_calls.append(days)
            if len(prune_calls) == 2:
                raise RuntimeError("simulated failure")

        with patch("air_marshall.database.app.asyncio.sleep", fake_sleep):
            with patch("air_marshall.database.app.prune_old_records", fake_prune):
                with pytest.raises(asyncio.CancelledError):
                    await _pruning_loop(db_conn, test_settings)

        assert len(prune_calls) == 2
        assert prune_calls[0] == test_settings.retention_days

    @pytest.mark.asyncio
    async def test_cancellation_during_prune_propagates(
        self, db_conn: aiosqlite.Connection, test_settings: Settings
    ) -> None:
        """CancelledError raised inside prune_old_records propagates out."""

        async def fake_sleep(_: float) -> None:
            pass

        async def fake_prune(_conn: aiosqlite.Connection, _days: int) -> None:
            raise asyncio.CancelledError

        with patch("air_marshall.database.app.asyncio.sleep", fake_sleep):
            with patch("air_marshall.database.app.prune_old_records", fake_prune):
                with pytest.raises(asyncio.CancelledError):
                    await _pruning_loop(db_conn, test_settings)


class TestRouteRegistration:
    """Tests verifying expected routes are registered."""

    def test_routes_include_data_prefix(self) -> None:
        """The app exposes /data/humidity, /data/fan, /data/control."""
        paths = {route.path for route in app.routes}  # type: ignore[attr-defined]
        assert "/data/humidity" in paths
        assert "/data/fan" in paths
        assert "/data/control" in paths

    def test_routes_include_query_endpoints(self) -> None:
        """The app exposes /data/latest and /data/history."""
        paths = {route.path for route in app.routes}  # type: ignore[attr-defined]
        assert "/data/latest" in paths
        assert "/data/history" in paths


class TestGetLatest:
    """Tests for GET /data/latest."""

    @pytest.mark.asyncio
    async def test_latest_returns_200_empty(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """GET /data/latest returns 200 with null fields when DB is empty."""
        response = await test_client.get(
            "/data/latest", headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["humidity"] == []
        assert body["fan"] is None
        assert body["control"] is None

    @pytest.mark.asyncio
    async def test_latest_requires_auth(self, test_client: httpx.AsyncClient) -> None:
        """GET /data/latest requires a valid API key."""
        response = await test_client.get("/data/latest")
        assert response.status_code == 401

        response = await test_client.get(
            "/data/latest", headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200


class TestPostEndpoints:
    """Tests for POST /data/* endpoints."""

    @pytest.mark.asyncio
    async def test_post_humidity_201(self, test_client: httpx.AsyncClient) -> None:
        """POST /data/humidity with valid key returns 201."""
        response = await test_client.post(
            "/data/humidity",
            json=_HUMIDITY_PAYLOAD,
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 201
        assert response.content == b""

    @pytest.mark.asyncio
    async def test_post_fan_201(self, test_client: httpx.AsyncClient) -> None:
        """POST /data/fan with valid key returns 201."""
        response = await test_client.post(
            "/data/fan",
            json=_FAN_PAYLOAD,
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_post_control_201(self, test_client: httpx.AsyncClient) -> None:
        """POST /data/control with valid key returns 201."""
        response = await test_client.post(
            "/data/control",
            json=_CONTROL_PAYLOAD,
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_post_then_get_latest(self, test_client: httpx.AsyncClient) -> None:
        """Data posted is reflected in GET /data/latest."""
        await test_client.post(
            "/data/fan",
            json=_FAN_PAYLOAD,
            headers={"X-API-Key": "test-key"},
        )
        response = await test_client.get(
            "/data/latest", headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["fan"] is not None
        assert body["fan"]["is_on"] is True
