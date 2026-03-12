"""HTTP client for the air-marshall database service."""

import httpx

from air_marshall.api.models import (
    ConfigRecord,
    ControlRecord,
    FanRecord,
    HistoryResponse,
    HumidityRecord,
    LatestResponse,
)


class AirMarshallClient:
    """Async HTTP client for the air-marshall database service.

    All requests time out after 30 seconds, raising httpx.TimeoutException.

    Args:
        base_url: Base URL of the database service (e.g. "http://pi4:8000").
        api_key: Shared secret sent as the ``X-API-Key`` header.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self._api_key = api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self._api_key}

    async def __aenter__(self) -> "AirMarshallClient":
        """Enter the async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the async context manager, closing the HTTP client."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    def _check_response(self, response: httpx.Response) -> None:
        response.raise_for_status()

    async def post_humidity(self, record: HumidityRecord) -> None:
        """POST a humidity reading.

        Raises:
            httpx.HTTPStatusError: On a non-2xx response.
            httpx.TimeoutException: If no response is received within 30 seconds.
        """
        response = await self._client.post(
            "/data/humidity",
            json=record.model_dump(mode="json"),
            headers=self._headers,
        )
        self._check_response(response)

    async def post_fan(self, record: FanRecord) -> None:
        """POST a fan state event.

        Raises:
            httpx.HTTPStatusError: On a non-2xx response.
            httpx.TimeoutException: If no response is received within 30 seconds.
        """
        response = await self._client.post(
            "/data/fan",
            json=record.model_dump(mode="json"),
            headers=self._headers,
        )
        self._check_response(response)

    async def post_control(self, record: ControlRecord) -> None:
        """POST a control state event.

        Raises:
            httpx.HTTPStatusError: On a non-2xx response.
            httpx.TimeoutException: If no response is received within 30 seconds.
        """
        response = await self._client.post(
            "/data/control",
            json=record.model_dump(mode="json"),
            headers=self._headers,
        )
        self._check_response(response)

    async def post_config(self, record: ConfigRecord) -> None:
        """POST a configuration record.

        Raises:
            httpx.HTTPStatusError: On a non-2xx response.
            httpx.TimeoutException: If no response is received within 30 seconds.
        """
        response = await self._client.post(
            "/data/config",
            json=record.model_dump(mode="json"),
            headers=self._headers,
        )
        self._check_response(response)

    async def get_latest(self, sensor_id: str | None = None) -> LatestResponse:
        """Fetch the most recent record of each type.

        Args:
            sensor_id: When set, filters the humidity result to this sensor only.

        Returns:
            Latest records; any field is None if no data has been posted yet.

        Raises:
            httpx.HTTPStatusError: On a non-2xx response.
            httpx.TimeoutException: If no response is received within 30 seconds.
        """
        params: dict[str, str] = {}
        if sensor_id is not None:
            params["sensor_id"] = sensor_id
        response = await self._client.get(
            "/data/latest", params=params, headers=self._headers
        )
        self._check_response(response)
        result: LatestResponse = LatestResponse.model_validate(response.json())
        return result

    async def get_history(self) -> HistoryResponse:
        """Fetch all records within the service's retention window.

        Returns:
            All stored records within the configured retention period.

        Raises:
            httpx.HTTPStatusError: On a non-2xx response.
            httpx.TimeoutException: If no response is received within 30 seconds.
        """
        response = await self._client.get("/data/history", headers=self._headers)
        self._check_response(response)
        result: HistoryResponse = HistoryResponse.model_validate(response.json())
        return result
