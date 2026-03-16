"""Core async publish logic for the air-marshall monitor service."""

import asyncio
import logging

from air_marshall.api.client import AirMarshallClient
from air_marshall.monitor.fan import AutomationHatFanReader
from air_marshall.monitor.humidity import SHT45Reader

_logger = logging.getLogger(__name__)


class MonitorPublisher:
    """Reads sensors and POSTs data to the air-marshall database service.

    Args:
        client: HTTP client used to POST records to the database service.
        humidity_reader: Reader for SHT45 Trinkey humidity/temperature data.
        fan_reader: Reader for Automation HAT fan state.
    """

    def __init__(
        self,
        client: AirMarshallClient,
        humidity_reader: SHT45Reader | None = None,
        fan_reader: AutomationHatFanReader | None = None,
    ) -> None:
        self._client = client
        self._humidity_reader = humidity_reader
        self._fan_reader = fan_reader

    async def publish_once(self) -> None:
        """Read available sensors and POST one sample each.

        Only sensors whose readers were provided at construction time are published.
        """
        if self._humidity_reader is not None:
            humidity_record = self._humidity_reader.read()
            await self._client.post_humidity(humidity_record)
        if self._fan_reader is not None:
            fan_record = self._fan_reader.read()
            await self._client.post_fan(fan_record)

    async def run(self, interval: float) -> None:
        """Publish sensor readings on a fixed interval until cancelled.

        Each iteration catches and logs any Exception so a single bad read
        does not kill the loop. asyncio.CancelledError is not caught (it derives
        from BaseException, not Exception) and propagates to allow clean shutdown.

        Args:
            interval: Seconds to sleep between publishes.
        """
        while True:
            try:
                await self.publish_once()
            except Exception:
                _logger.exception("Error during publish_once")
            await asyncio.sleep(interval)
