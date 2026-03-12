"""Integration tests for the air-marshall database service.

These tests start a real uvicorn server with a real SQLite database to verify
the full request-response cycle including the lifespan (table creation, pruning
task) and actual I/O.
"""

import asyncio
import socket
import threading
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import uvicorn

from air_marshall.api.client import AirMarshallClient
from air_marshall.api.models import ConfigRecord, HumidityRecord
from air_marshall.database.app import app
from air_marshall.database.config import get_settings

_TS = datetime.now(tz=UTC)


class _QuietServer(uvicorn.Server):
    """Uvicorn server subclass that suppresses signal handler installation."""

    def install_signal_handlers(self) -> None:
        """Skip signal handler setup (not safe outside the main thread)."""


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Full round-trip coverage through a live uvicorn server.

    Verifies humidity, fan, and control POST → GET cycles; multi-sensor
    latest; history; auth failures; and the Python AirMarshallClient.
    """
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "ikey")
    monkeypatch.setenv("AIR_MARSHALL_DB_DB_PATH", db_file)
    get_settings.cache_clear()

    sock: socket.socket | None = None
    server: _QuietServer | None = None
    thread: threading.Thread | None = None

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]

    try:
        config = uvicorn.Config(app, log_level="error")
        server = _QuietServer(config=config)
        thread = threading.Thread(
            target=server.run, kwargs={"sockets": [sock]}, daemon=True
        )
        thread.start()

        # Wait for the server to become ready
        base_url = f"http://127.0.0.1:{port}"
        for _ in range(20):
            try:
                async with httpx.AsyncClient() as probe:
                    await probe.get(
                        f"{base_url}/data/latest", headers={"X-API-Key": "ikey"}
                    )
                break
            except httpx.ConnectError:
                await asyncio.sleep(0.1)
        else:
            pytest.fail("Server did not become reachable within 2 seconds")

        async with httpx.AsyncClient(base_url=base_url) as client:
            # --- initial state: empty humidity list ---
            resp = await client.get("/data/latest", headers={"X-API-Key": "ikey"})
            assert resp.status_code == 200
            assert resp.json()["humidity"] == []

            # --- auth: GET without API key → 401 ---
            resp = await client.get("/data/latest")
            assert resp.status_code == 401

            # --- auth: POST with wrong API key → 401 ---
            resp = await client.post(
                "/data/humidity",
                json={
                    "sensor_id": "s1",
                    "sensor_serial_number": "SN001",
                    "timestamp": _TS.isoformat(),
                    "temperature": 21.0,
                    "humidity": 48.0,
                    "is_touched": False,
                },
                headers={"X-API-Key": "wrong"},
            )
            assert resp.status_code == 401

            # --- humidity: POST then verify in GET /data/latest ---
            resp = await client.post(
                "/data/humidity",
                json={
                    "sensor_id": "s1",
                    "sensor_serial_number": "SN001",
                    "timestamp": _TS.isoformat(),
                    "temperature": 21.0,
                    "humidity": 48.0,
                    "is_touched": False,
                },
                headers={"X-API-Key": "ikey"},
            )
            assert resp.status_code == 201

            resp = await client.get("/data/latest", headers={"X-API-Key": "ikey"})
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["humidity"]) > 0
            assert body["humidity"][0]["sensor_id"] == "s1"

            # --- fan: POST then verify in GET /data/latest ---
            resp = await client.post(
                "/data/fan",
                json={"timestamp": _TS.isoformat(), "is_on": True},
                headers={"X-API-Key": "ikey"},
            )
            assert resp.status_code == 201

            resp = await client.get("/data/latest", headers={"X-API-Key": "ikey"})
            body = resp.json()
            assert body["fan"]["is_on"] is True

            # --- control: POST then verify in GET /data/latest ---
            resp = await client.post(
                "/data/control",
                json={
                    "timestamp": _TS.isoformat(),
                    "humidifier_on": True,
                    "fan_on": False,
                },
                headers={"X-API-Key": "ikey"},
            )
            assert resp.status_code == 201

            resp = await client.get("/data/latest", headers={"X-API-Key": "ikey"})
            body = resp.json()
            assert body["control"]["humidifier_on"] is True

            # --- config: POST then verify in GET /data/latest ---
            resp = await client.post(
                "/data/config",
                json={
                    "timestamp": _TS.isoformat(),
                    "humidity_low": 30.0,
                    "humidity_high": 50.0,
                },
                headers={"X-API-Key": "ikey"},
            )
            assert resp.status_code == 201

            resp = await client.get("/data/latest", headers={"X-API-Key": "ikey"})
            body = resp.json()
            assert body["config"]["humidity_low"] == 30.0

            # --- multi-sensor: post s2, GET /data/latest returns both s1 and s2 ---
            resp = await client.post(
                "/data/humidity",
                json={
                    "sensor_id": "s2",
                    "sensor_serial_number": "SN002",
                    "timestamp": _TS.isoformat(),
                    "temperature": 22.0,
                    "humidity": 50.0,
                    "is_touched": False,
                },
                headers={"X-API-Key": "ikey"},
            )
            assert resp.status_code == 201

            resp = await client.get("/data/latest", headers={"X-API-Key": "ikey"})
            body = resp.json()
            assert len(body["humidity"]) == 2
            sensor_ids = {r["sensor_id"] for r in body["humidity"]}
            assert sensor_ids == {"s1", "s2"}

            # --- history: posted records appear in GET /data/history ---
            resp = await client.get("/data/history", headers={"X-API-Key": "ikey"})
            assert resp.status_code == 200
            history = resp.json()
            assert any(r["sensor_id"] == "s1" for r in history["humidity"])

        # --- Python AirMarshallClient end-to-end ---
        async with AirMarshallClient(base_url=base_url, api_key="ikey") as api_client:
            record = HumidityRecord(
                sensor_id="s_py",
                sensor_serial_number="SN_PY",
                timestamp=_TS,
                temperature=20.0,
                humidity=45.0,
                is_touched=False,
            )
            await api_client.post_humidity(record)
            latest = await api_client.get_latest(sensor_id="s_py")
            assert len(latest.humidity) == 1
            assert latest.humidity[0].sensor_id == "s_py"

            config_record = ConfigRecord(
                timestamp=_TS,
                humidity_low=30.0,
                humidity_high=50.0,
            )
            await api_client.post_config(config_record)

    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(timeout=5)
        if sock is not None:
            sock.close()
        get_settings.cache_clear()
