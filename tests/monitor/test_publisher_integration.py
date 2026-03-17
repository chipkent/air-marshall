"""Integration test for MonitorPublisher against a live uvicorn DB server."""

import asyncio
import socket
import threading
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import uvicorn

from air_marshall.api.client import AirMarshallClient
from air_marshall.api.models import FanRecord, HumidityRecord
from air_marshall.database.app import app
from air_marshall.database.config import get_settings
from air_marshall.monitor.publisher import MonitorPublisher

_TS = datetime.now(tz=UTC)

_HUMIDITY_RECORD = HumidityRecord(
    sensor_id="pub-test",
    sensor_serial_number="SN-PUB",
    timestamp=_TS,
    temperature=21.5,
    humidity=49.0,
    is_touched=False,
)

_FAN_RECORD = FanRecord(
    timestamp=_TS,
    is_on=True,
)


class _QuietServer(uvicorn.Server):
    """Uvicorn server subclass that suppresses signal handler installation."""

    def install_signal_handlers(self) -> None:
        """Skip signal handler setup (not safe outside the main thread)."""


@pytest.mark.integration
@pytest.mark.asyncio
async def test_publish_once_posts_to_live_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """publish_once() delivers humidity and fan records to a live DB server."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "pub-key")
    monkeypatch.setenv("AIR_MARSHALL_DB_DB_PATH", db_file)
    get_settings.cache_clear()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]

    config = uvicorn.Config(app, log_level="error")
    server = _QuietServer(config=config)
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [sock]}, daemon=True
    )
    thread.start()

    base_url = f"http://127.0.0.1:{port}"

    import httpx

    for _ in range(20):
        try:
            async with httpx.AsyncClient() as probe:
                await probe.get(
                    f"{base_url}/data/latest", headers={"X-API-Key": "pub-key"}
                )
            break
        except httpx.ConnectError:
            await asyncio.sleep(0.1)
    else:
        pytest.fail("Server did not become reachable within 2 seconds")

    try:
        humidity_reader = MagicMock()
        humidity_reader.read.return_value = _HUMIDITY_RECORD

        fan_reader = MagicMock()
        fan_reader.read.return_value = _FAN_RECORD

        async with AirMarshallClient(base_url=base_url, api_key="pub-key") as client:
            publisher = MonitorPublisher(
                client=client,
                humidity_reader=humidity_reader,
                fan_reader=fan_reader,
            )
            await publisher.publish_once()

            latest = await client.get_latest()

        assert len(latest.humidity) == 1
        assert latest.humidity[0].sensor_id == "pub-test"
        assert latest.humidity[0].temperature == 21.5
        assert latest.humidity[0].humidity == 49.0

        assert latest.fan is not None
        assert latest.fan.is_on is True

    finally:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()
        get_settings.cache_clear()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_publish_weather_once_posts_to_live_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """publish_weather_once() delivers a weather record to a live DB server."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("AIR_MARSHALL_DB_API_KEY", "weather-key")
    monkeypatch.setenv("AIR_MARSHALL_DB_DB_PATH", db_file)
    get_settings.cache_clear()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]

    config = uvicorn.Config(app, log_level="error")
    server = _QuietServer(config=config)
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [sock]}, daemon=True
    )
    thread.start()

    base_url = f"http://127.0.0.1:{port}"

    import httpx

    for _ in range(20):
        try:
            async with httpx.AsyncClient() as probe:
                await probe.get(
                    f"{base_url}/data/latest", headers={"X-API-Key": "weather-key"}
                )
            break
        except httpx.ConnectError:
            await asyncio.sleep(0.1)
    else:
        pytest.fail("Server did not become reachable within 2 seconds")

    try:
        weather_record = HumidityRecord(
            sensor_id="weather-test",
            sensor_serial_number="",
            timestamp=_TS,
            temperature=5.0,
            humidity=70.0,
            is_touched=False,
        )
        weather_reader = AsyncMock()
        weather_reader.read.return_value = weather_record

        async with AirMarshallClient(
            base_url=base_url, api_key="weather-key"
        ) as client:
            publisher = MonitorPublisher(client=client, weather_reader=weather_reader)
            await publisher.publish_weather_once()
            latest = await client.get_latest(sensor_id="weather-test")

        assert len(latest.humidity) == 1
        assert latest.humidity[0].sensor_id == "weather-test"
        assert latest.humidity[0].temperature == 5.0
        assert latest.humidity[0].humidity == 70.0

    finally:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()
        get_settings.cache_clear()
