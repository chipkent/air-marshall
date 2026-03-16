"""Tests for air_marshall.monitor.publisher."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from air_marshall.api.models import FanRecord, HumidityRecord
from air_marshall.monitor.publisher import MonitorPublisher

_TS = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

_HUMIDITY_RECORD = HumidityRecord(
    sensor_id="s1",
    sensor_serial_number="SN001",
    timestamp=_TS,
    temperature=22.5,
    humidity=45.0,
    is_touched=False,
)

_WEATHER_RECORD = HumidityRecord(
    sensor_id="outdoor",
    sensor_serial_number="open-meteo",
    timestamp=_TS,
    temperature=18.5,
    humidity=62.0,
    is_touched=False,
)

_FAN_RECORD = FanRecord(timestamp=_TS, is_on=True)


def _make_humidity_reader() -> MagicMock:
    reader = MagicMock()
    reader.read.return_value = _HUMIDITY_RECORD
    return reader


def _make_fan_reader() -> MagicMock:
    reader = MagicMock()
    reader.read.return_value = _FAN_RECORD
    return reader


def _make_weather_reader() -> MagicMock:
    reader = MagicMock()
    reader.read = AsyncMock(return_value=_WEATHER_RECORD)
    return reader


def _make_client() -> AsyncMock:
    client = AsyncMock()
    client.post_humidity = AsyncMock()
    client.post_fan = AsyncMock()
    return client


class TestPublishOnce:
    """Tests for MonitorPublisher.publish_once."""

    @pytest.mark.asyncio
    async def test_humidity_only_calls_post_humidity(self) -> None:
        """publish_once calls only post_humidity when only humidity_reader is set."""
        client = _make_client()
        publisher = MonitorPublisher(
            client=client,
            humidity_reader=_make_humidity_reader(),
        )
        await publisher.publish_once()
        client.post_humidity.assert_called_once_with(_HUMIDITY_RECORD)
        client.post_fan.assert_not_called()

    @pytest.mark.asyncio
    async def test_fan_only_calls_post_fan(self) -> None:
        """publish_once calls only post_fan when only fan_reader is set."""
        client = _make_client()
        publisher = MonitorPublisher(
            client=client,
            fan_reader=_make_fan_reader(),
        )
        await publisher.publish_once()
        client.post_fan.assert_called_once_with(_FAN_RECORD)
        client.post_humidity.assert_not_called()

    @pytest.mark.asyncio
    async def test_both_calls_both(self) -> None:
        """publish_once calls both post_humidity and post_fan when both readers are set."""
        client = _make_client()
        publisher = MonitorPublisher(
            client=client,
            humidity_reader=_make_humidity_reader(),
            fan_reader=_make_fan_reader(),
        )
        await publisher.publish_once()
        client.post_humidity.assert_called_once_with(_HUMIDITY_RECORD)
        client.post_fan.assert_called_once_with(_FAN_RECORD)

    @pytest.mark.asyncio
    async def test_no_readers_does_nothing(self) -> None:
        """publish_once skips posting when no readers are set."""
        client = _make_client()
        publisher = MonitorPublisher(client=client)
        await publisher.publish_once()
        client.post_humidity.assert_not_called()
        client.post_fan.assert_not_called()


class TestRun:
    """Tests for MonitorPublisher.run."""

    @pytest.mark.asyncio
    async def test_run_calls_publish_once_repeatedly(self) -> None:
        """run() calls publish_once on each iteration until cancelled."""
        client = _make_client()
        publisher = MonitorPublisher(
            client=client,
            humidity_reader=_make_humidity_reader(),
        )

        call_count = 0

        async def fake_sleep(_interval: float) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                raise asyncio.CancelledError

        with patch("air_marshall.monitor.publisher.asyncio.sleep", fake_sleep):
            with pytest.raises(asyncio.CancelledError):
                await publisher.run(sensor_interval=0.0, weather_interval=0.0)

        assert client.post_humidity.call_count == 3

    @pytest.mark.asyncio
    async def test_run_catches_publish_exception(self) -> None:
        """run() catches exceptions from publish_once and continues."""
        client = _make_client()
        client.post_humidity.side_effect = [RuntimeError("boom"), None]
        publisher = MonitorPublisher(
            client=client,
            humidity_reader=_make_humidity_reader(),
        )

        call_count = 0

        async def fake_sleep(_interval: float) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError

        with patch("air_marshall.monitor.publisher.asyncio.sleep", fake_sleep):
            with pytest.raises(asyncio.CancelledError):
                await publisher.run(sensor_interval=0.0, weather_interval=0.0)

        # Called twice — first raised, second succeeded
        assert client.post_humidity.call_count == 2


class TestPublishWeatherOnce:
    """Tests for MonitorPublisher.publish_weather_once."""

    @pytest.mark.asyncio
    async def test_calls_read_and_post_humidity(self) -> None:
        """publish_weather_once reads the weather reader and posts the record."""
        client = _make_client()
        weather_reader = _make_weather_reader()
        publisher = MonitorPublisher(client=client, weather_reader=weather_reader)

        await publisher.publish_weather_once()

        weather_reader.read.assert_called_once()
        client.post_humidity.assert_called_once_with(_WEATHER_RECORD)

    @pytest.mark.asyncio
    async def test_noop_without_weather_reader(self) -> None:
        """publish_weather_once does nothing when no weather reader is set."""
        client = _make_client()
        publisher = MonitorPublisher(client=client)

        await publisher.publish_weather_once()

        client.post_humidity.assert_not_called()


class TestRunTaskStructure:
    """Tests for MonitorPublisher.run task structure."""

    @pytest.mark.asyncio
    async def test_run_sensor_reader_creates_sensor_task(self) -> None:
        """run() launches the sensor loop when a hardware reader is set."""
        client = _make_client()
        publisher = MonitorPublisher(
            client=client, humidity_reader=_make_humidity_reader()
        )

        with (
            patch.object(
                publisher, "_run_sensor_loop", new_callable=AsyncMock
            ) as mock_sensor,
            patch.object(
                publisher, "_run_weather_loop", new_callable=AsyncMock
            ) as mock_weather,
        ):
            await publisher.run(sensor_interval=5.0, weather_interval=300.0)

        mock_sensor.assert_called_once_with(5.0)
        mock_weather.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_no_readers_creates_no_tasks(self) -> None:
        """run() completes immediately when no readers are set."""
        client = _make_client()
        publisher = MonitorPublisher(client=client)

        with (
            patch.object(
                publisher, "_run_sensor_loop", new_callable=AsyncMock
            ) as mock_sensor,
            patch.object(
                publisher, "_run_weather_loop", new_callable=AsyncMock
            ) as mock_weather,
        ):
            await publisher.run(sensor_interval=5.0, weather_interval=300.0)

        mock_sensor.assert_not_called()
        mock_weather.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_with_weather_reader_creates_two_tasks(self) -> None:
        """run() launches both loops when hardware and weather readers are set."""
        client = _make_client()
        publisher = MonitorPublisher(
            client=client,
            humidity_reader=_make_humidity_reader(),
            weather_reader=_make_weather_reader(),
        )

        with (
            patch.object(
                publisher, "_run_sensor_loop", new_callable=AsyncMock
            ) as mock_sensor,
            patch.object(
                publisher, "_run_weather_loop", new_callable=AsyncMock
            ) as mock_weather,
        ):
            await publisher.run(sensor_interval=5.0, weather_interval=300.0)

        mock_sensor.assert_called_once_with(5.0)
        mock_weather.assert_called_once_with(300.0)

    @pytest.mark.asyncio
    async def test_run_weather_interval_ignored_without_weather_reader(self) -> None:
        """run() does not start a weather loop even when weather_interval is provided."""
        client = _make_client()
        publisher = MonitorPublisher(
            client=client, humidity_reader=_make_humidity_reader()
        )

        with (
            patch.object(publisher, "_run_sensor_loop", new_callable=AsyncMock),
            patch.object(
                publisher, "_run_weather_loop", new_callable=AsyncMock
            ) as mock_weather,
        ):
            await publisher.run(sensor_interval=5.0, weather_interval=300.0)

        mock_weather.assert_not_called()


class TestRunWeatherLoop:
    """Tests for MonitorPublisher._run_weather_loop."""

    @pytest.mark.asyncio
    async def test_catches_exceptions_and_continues(self) -> None:
        """_run_weather_loop logs exceptions and keeps running."""
        client = _make_client()
        weather_reader = _make_weather_reader()
        weather_reader.read = AsyncMock(
            side_effect=[RuntimeError("network error"), _WEATHER_RECORD]
        )
        publisher = MonitorPublisher(client=client, weather_reader=weather_reader)

        call_count = 0

        async def fake_sleep(_: float) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError

        with patch("air_marshall.monitor.publisher.asyncio.sleep", fake_sleep):
            with pytest.raises(asyncio.CancelledError):
                await publisher._run_weather_loop(0.0)

        # read() called twice — first raised, second succeeded
        assert weather_reader.read.call_count == 2
