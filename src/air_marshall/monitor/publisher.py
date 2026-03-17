"""Core async publish logic for the air-marshall monitor service."""

import asyncio
import logging

from air_marshall.api.client import AirMarshallClient
from air_marshall.monitor.fan import AutomationHatFanReader
from air_marshall.monitor.humidity import SHT45Reader
from air_marshall.monitor.weather import OpenMeteoReader

_logger = logging.getLogger(__name__)


class MonitorPublisher:
    """Reads sensors and POSTs data to the air-marshall database service.

    Args:
        client: HTTP client used to POST records to the database service.
        humidity_reader: Reader for SHT45 Trinkey humidity/temperature data.
        fan_reader: Reader for Automation HAT fan state.
        weather_reader: Reader for outdoor weather from Open-Meteo; when
            provided, ``run()`` starts an independent weather publish loop.
    """

    def __init__(
        self,
        client: AirMarshallClient,
        humidity_reader: SHT45Reader | None = None,
        fan_reader: AutomationHatFanReader | None = None,
        weather_reader: OpenMeteoReader | None = None,
    ) -> None:
        self._client = client
        self._humidity_reader = humidity_reader
        self._fan_reader = fan_reader
        self._weather_reader = weather_reader

    async def publish_once(self) -> None:
        """Read available sensors and POST one sample each.

        Only sensors whose readers were provided at construction time are published.
        """
        if self._humidity_reader is not None:
            humidity_record = await asyncio.to_thread(self._humidity_reader.read)
            await self._client.post_humidity(humidity_record)
        if self._fan_reader is not None:
            fan_record = await asyncio.to_thread(self._fan_reader.read)
            await self._client.post_fan(fan_record)

    async def publish_weather_once(self) -> None:
        """Fetch outdoor weather and POST one sample."""
        if self._weather_reader is not None:
            record = await self._weather_reader.read()
            await self._client.post_humidity(record)

    async def run(self, sensor_interval: float, weather_interval: float) -> None:
        """Publish sensor readings on fixed intervals until cancelled.

        Starts a sensor loop and, when a ``weather_reader`` was provided,
        an independent weather loop running at ``weather_interval``.  Each
        loop catches and logs any ``Exception`` so a single bad read does not
        kill the loop.  ``asyncio.CancelledError`` propagates to allow clean
        shutdown.

        Args:
            sensor_interval: Seconds to sleep between hardware sensor publishes.
            weather_interval: Seconds to sleep between weather publishes;
                ignored when no ``weather_reader`` was provided.
        """
        tasks: list[asyncio.Task[None]] = []
        if self._humidity_reader is not None or self._fan_reader is not None:
            tasks.append(asyncio.create_task(self._run_sensor_loop(sensor_interval)))
        if self._weather_reader is not None:
            tasks.append(asyncio.create_task(self._run_weather_loop(weather_interval)))
        await asyncio.gather(*tasks)

    async def _run_sensor_loop(self, sensor_interval: float) -> None:
        """Publish hardware sensor readings on a fixed interval."""
        while True:
            try:
                await self.publish_once()
            except Exception:
                _logger.exception("Error during publish_once")
            await asyncio.sleep(sensor_interval)

    async def _run_weather_loop(self, interval: float) -> None:
        """Publish outdoor weather readings on a fixed interval."""
        while True:
            try:
                await self.publish_weather_once()
            except Exception:
                _logger.exception("Error during publish_weather_once")
            await asyncio.sleep(interval)
