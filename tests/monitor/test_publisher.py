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

_FAN_RECORD = FanRecord(timestamp=_TS, is_on=True)


def _make_humidity_reader() -> MagicMock:
    reader = MagicMock()
    reader.read.return_value = _HUMIDITY_RECORD
    return reader


def _make_fan_reader() -> MagicMock:
    reader = MagicMock()
    reader.read.return_value = _FAN_RECORD
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
                await publisher.run(interval=0.0)

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
                await publisher.run(interval=0.0)

        # Called twice — first raised, second succeeded
        assert client.post_humidity.call_count == 2
