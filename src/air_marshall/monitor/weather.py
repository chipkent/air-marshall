"""Open-Meteo outdoor temperature and humidity reader."""

from datetime import UTC, datetime

import httpx

from air_marshall.api.models import HumidityRecord

_BASE_URL = "https://api.open-meteo.com/v1/forecast"
"""Base URL for the Open-Meteo forecast API."""

_SENSOR_SERIAL_NUMBER = "open-meteo"
"""Sensor serial number stored in every record produced by this reader."""

_TIMEOUT = 10.0
"""Seconds before an Open-Meteo request is abandoned."""


class OpenMeteoReader:
    """Fetches current outdoor temperature and humidity from Open-Meteo.

    All requests time out after 10 seconds, raising httpx.TimeoutException.

    Args:
        latitude: Geographic latitude of the location to query.
        longitude: Geographic longitude of the location to query.
        sensor_id: Logical sensor identifier stored in each returned record.
    """

    def __init__(
        self,
        latitude: float,
        longitude: float,
        sensor_id: str,
    ) -> None:
        self._latitude = latitude
        self._longitude = longitude
        self._sensor_id = sensor_id
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def read(self) -> HumidityRecord:
        """Fetch current conditions and return a HumidityRecord.

        Returns:
            A record with ``timestamp`` set to the current UTC time,
            ``sensor_serial_number`` set to ``"open-meteo"``, and
            ``is_touched`` always ``False``.

        Raises:
            httpx.HTTPError: If the HTTP request fails or times out.
            ValueError: If the response cannot be parsed.
        """
        response = await self._client.get(
            _BASE_URL,
            params={
                "latitude": self._latitude,
                "longitude": self._longitude,
                # temperature_2m / relative_humidity_2m: WMO standard measurements
                # taken at 2 metres above ground level.
                "current": "temperature_2m,relative_humidity_2m",
                "temperature_unit": "celsius",
            },
        )
        response.raise_for_status()
        data = response.json()
        try:
            current = data["current"]
            temperature = float(current["temperature_2m"])
            humidity = float(current["relative_humidity_2m"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Unexpected Open-Meteo response: {data!r}") from exc
        return HumidityRecord(
            sensor_id=self._sensor_id,
            sensor_serial_number=_SENSOR_SERIAL_NUMBER,
            timestamp=datetime.now(UTC),
            temperature=temperature,
            humidity=humidity,
            is_touched=False,
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "OpenMeteoReader":
        """Enter the async context manager."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Exit the async context manager, closing the HTTP client."""
        await self.close()
