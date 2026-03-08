"""Tests for air_marshall.api.client."""

import json
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from air_marshall.api.client import AirMarshallClient
from air_marshall.api.models import (
    ControlRecord,
    FanRecord,
    HistoryResponse,
    HumidityRecord,
    LatestResponse,
)

_TS = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _humidity() -> HumidityRecord:
    return HumidityRecord(
        sensor_id="s1",
        sensor_serial_number="SN001",
        timestamp=_TS,
        temperature=22.5,
        humidity=45.0,
        is_touched=False,
    )


def _fan() -> FanRecord:
    return FanRecord(timestamp=_TS, is_on=True)


def _control() -> ControlRecord:
    return ControlRecord(timestamp=_TS, humidifier_on=True, fan_on=False)


class _MockTransport(httpx.AsyncBaseTransport):
    """Simple mock transport that returns a pre-configured response."""

    def __init__(
        self, status_code: int = 200, body: dict[str, Any] | None = None
    ) -> None:
        self.status_code = status_code
        self.body = body or {}
        self.last_request: httpx.Request | None = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Store the request and return the configured response.

        Args:
            request: The outgoing HTTP request.

        Returns:
            A synthetic httpx.Response with the configured status and body.
        """
        self.last_request = request
        content = json.dumps(self.body).encode()
        return httpx.Response(
            self.status_code,
            content=content,
            headers={"content-type": "application/json"},
        )


def _make_client(transport: _MockTransport) -> AirMarshallClient:
    client = AirMarshallClient.__new__(AirMarshallClient)
    client._client = httpx.AsyncClient(base_url="http://test", transport=transport)
    client._api_key = "test-key"
    return client


class TestInit:
    """Tests for AirMarshallClient.__init__."""

    @pytest.mark.asyncio
    async def test_stores_api_key(self) -> None:
        """__init__ stores the api_key and creates the internal httpx client."""
        client = AirMarshallClient("http://test", "my-key")
        try:
            assert client._api_key == "my-key"
        finally:
            await client.close()


class TestPostHumidity:
    """Tests for AirMarshallClient.post_humidity."""

    @pytest.mark.asyncio
    async def test_sends_post_to_correct_path(self) -> None:
        """post_humidity sends a POST to /data/humidity."""
        transport = _MockTransport(status_code=201)
        client = _make_client(transport)
        await client.post_humidity(_humidity())
        assert transport.last_request is not None
        assert transport.last_request.method == "POST"
        assert transport.last_request.url.path == "/data/humidity"

    @pytest.mark.asyncio
    async def test_sends_api_key_header(self) -> None:
        """post_humidity includes the X-API-Key header."""
        transport = _MockTransport(status_code=201)
        client = _make_client(transport)
        await client.post_humidity(_humidity())
        assert transport.last_request is not None
        assert transport.last_request.headers["x-api-key"] == "test-key"

    @pytest.mark.asyncio
    async def test_raises_on_error_status(self) -> None:
        """post_humidity raises HTTPStatusError on 4xx/5xx responses."""
        transport = _MockTransport(status_code=401)
        client = _make_client(transport)
        with pytest.raises(httpx.HTTPStatusError):
            await client.post_humidity(_humidity())


class TestPostFan:
    """Tests for AirMarshallClient.post_fan."""

    @pytest.mark.asyncio
    async def test_sends_post_to_correct_path(self) -> None:
        """post_fan sends a POST to /data/fan."""
        transport = _MockTransport(status_code=201)
        client = _make_client(transport)
        await client.post_fan(_fan())
        assert transport.last_request is not None
        assert transport.last_request.url.path == "/data/fan"


class TestPostControl:
    """Tests for AirMarshallClient.post_control."""

    @pytest.mark.asyncio
    async def test_sends_post_to_correct_path(self) -> None:
        """post_control sends a POST to /data/control."""
        transport = _MockTransport(status_code=201)
        client = _make_client(transport)
        await client.post_control(_control())
        assert transport.last_request is not None
        assert transport.last_request.url.path == "/data/control"


class TestGetLatest:
    """Tests for AirMarshallClient.get_latest."""

    @pytest.mark.asyncio
    async def test_returns_latest_response(self) -> None:
        """get_latest returns a LatestResponse parsed from JSON."""
        body = {"humidity": [], "fan": None, "control": None}
        transport = _MockTransport(status_code=200, body=body)
        client = _make_client(transport)
        result = await client.get_latest()
        assert isinstance(result, LatestResponse)
        assert result.humidity == []

    @pytest.mark.asyncio
    async def test_sends_sensor_id_param(self) -> None:
        """get_latest forwards sensor_id as a query parameter."""
        body = {"humidity": [], "fan": None, "control": None}
        transport = _MockTransport(status_code=200, body=body)
        client = _make_client(transport)
        await client.get_latest(sensor_id="s1")
        assert transport.last_request is not None
        assert "sensor_id=s1" in str(transport.last_request.url)

    @pytest.mark.asyncio
    async def test_no_sensor_id_omits_param(self) -> None:
        """get_latest without sensor_id does not add a query parameter."""
        body = {"humidity": [], "fan": None, "control": None}
        transport = _MockTransport(status_code=200, body=body)
        client = _make_client(transport)
        await client.get_latest()
        assert transport.last_request is not None
        assert "sensor_id" not in str(transport.last_request.url)

    @pytest.mark.asyncio
    async def test_raises_on_error_status(self) -> None:
        """get_latest raises HTTPStatusError on non-2xx response."""
        transport = _MockTransport(status_code=500)
        client = _make_client(transport)
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_latest()


class TestGetHistory:
    """Tests for AirMarshallClient.get_history."""

    @pytest.mark.asyncio
    async def test_returns_history_response(self) -> None:
        """get_history returns a HistoryResponse parsed from JSON."""
        body = {"humidity": [], "fan": [], "control": []}
        transport = _MockTransport(status_code=200, body=body)
        client = _make_client(transport)
        result = await client.get_history()
        assert isinstance(result, HistoryResponse)
        assert result.humidity == []

    @pytest.mark.asyncio
    async def test_sends_get_to_correct_path(self) -> None:
        """get_history sends a GET to /data/history."""
        body = {"humidity": [], "fan": [], "control": []}
        transport = _MockTransport(status_code=200, body=body)
        client = _make_client(transport)
        await client.get_history()
        assert transport.last_request is not None
        assert transport.last_request.method == "GET"
        assert transport.last_request.url.path == "/data/history"


class TestContextManager:
    """Tests for AirMarshallClient async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self) -> None:
        """Using async with calls close() on exit."""
        transport = _MockTransport()
        async with AirMarshallClient.__new__(AirMarshallClient) as cm_client:
            cm_client._client = httpx.AsyncClient(
                base_url="http://test", transport=transport
            )
            cm_client._api_key = "k"
        # If close() was not called, the client would still be open.
        # httpx marks the client as closed after aclose().
        assert cm_client._client.is_closed
