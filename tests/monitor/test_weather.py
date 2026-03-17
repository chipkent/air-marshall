"""Tests for air_marshall.monitor.weather."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from air_marshall.monitor.weather import (
    _SENSOR_SERIAL_NUMBER,
    _TIMEOUT,
    OpenMeteoReader,
)

_VALID_RESPONSE = {
    "current": {
        "temperature_2m": 18.5,
        "relative_humidity_2m": 62,
    }
}

_LAT = 39.0
_LON = -104.9
_SENSOR_ID = "outdoor"


def _make_reader(
    json_data: object = _VALID_RESPONSE,
    sensor_id: str = _SENSOR_ID,
) -> tuple["OpenMeteoReader", AsyncMock]:
    """Return an OpenMeteoReader with a patched httpx client."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = json_data
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    with patch(
        "air_marshall.monitor.weather.httpx.AsyncClient", return_value=mock_client
    ):
        reader = OpenMeteoReader(_LAT, _LON, sensor_id)
    return reader, mock_client


class TestOpenMeteoReaderRead:
    """Tests for OpenMeteoReader.read."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_humidity_record(self) -> None:
        """read() returns a HumidityRecord with correct temperature and humidity."""
        reader, _ = _make_reader()
        record = await reader.read()

        assert record.temperature == 18.5
        assert record.humidity == 62.0

    @pytest.mark.asyncio
    async def test_sensor_serial_number_is_open_meteo(self) -> None:
        """read() sets sensor_serial_number to the module constant."""
        reader, _ = _make_reader()
        record = await reader.read()

        assert record.sensor_serial_number == _SENSOR_SERIAL_NUMBER
        assert record.sensor_serial_number == "open-meteo"

    @pytest.mark.asyncio
    async def test_is_touched_is_false(self) -> None:
        """read() always sets is_touched to False."""
        reader, _ = _make_reader()
        record = await reader.read()

        assert record.is_touched is False

    @pytest.mark.asyncio
    async def test_sensor_id_is_propagated(self) -> None:
        """read() stores the sensor_id passed at construction."""
        reader, _ = _make_reader(sensor_id="my-outdoor")
        record = await reader.read()

        assert record.sensor_id == "my-outdoor"

    @pytest.mark.asyncio
    async def test_timestamp_is_utc_aware(self) -> None:
        """read() sets timestamp to a UTC-aware datetime."""
        reader, _ = _make_reader()
        record = await reader.read()

        assert record.timestamp.tzinfo is not None
        assert record.timestamp.utcoffset().total_seconds() == 0  # type: ignore[union-attr]

    @pytest.mark.asyncio
    async def test_correct_query_params_sent(self) -> None:
        """read() passes latitude, longitude, and current fields to the API."""
        reader, mock_client = _make_reader()
        await reader.read()

        mock_client.get.assert_called_once()
        _, kwargs = mock_client.get.call_args
        params = kwargs["params"]
        assert params["latitude"] == _LAT
        assert params["longitude"] == _LON
        assert "temperature_2m" in params["current"]
        assert "relative_humidity_2m" in params["current"]

    @pytest.mark.asyncio
    async def test_raises_value_error_on_missing_current_key(self) -> None:
        """read() raises ValueError when the 'current' key is absent."""
        reader, _ = _make_reader(json_data={"something_else": {}})

        with pytest.raises(ValueError, match="Unexpected Open-Meteo response"):
            await reader.read()

    @pytest.mark.asyncio
    async def test_raises_value_error_on_missing_temperature_key(self) -> None:
        """read() raises ValueError when temperature_2m is absent."""
        reader, _ = _make_reader(json_data={"current": {"relative_humidity_2m": 55}})

        with pytest.raises(ValueError, match="Unexpected Open-Meteo response"):
            await reader.read()

    @pytest.mark.asyncio
    async def test_raises_value_error_when_current_is_none(self) -> None:
        """read() raises ValueError when 'current' is None."""
        reader, _ = _make_reader(json_data={"current": None})

        with pytest.raises(ValueError, match="Unexpected Open-Meteo response"):
            await reader.read()

    @pytest.mark.asyncio
    async def test_propagates_http_status_error(self) -> None:
        """read() propagates httpx.HTTPStatusError from raise_for_status."""
        reader, mock_client = _make_reader()
        mock_client.get.return_value.raise_for_status.side_effect = (
            httpx.HTTPStatusError("404", request=MagicMock(), response=MagicMock())
        )

        with pytest.raises(httpx.HTTPStatusError):
            await reader.read()

    @pytest.mark.asyncio
    async def test_humidity_coerced_from_int(self) -> None:
        """read() accepts relative_humidity_2m as an integer and stores it as float."""
        reader, _ = _make_reader(
            json_data={"current": {"temperature_2m": 20.0, "relative_humidity_2m": 55}}
        )
        record = await reader.read()

        assert record.humidity == 55.0
        assert isinstance(record.humidity, float)


class TestOpenMeteoReaderConstruction:
    """Tests for OpenMeteoReader construction."""

    def test_client_created_with_timeout(self) -> None:
        """Constructor creates an httpx.AsyncClient with the configured timeout."""
        with patch("air_marshall.monitor.weather.httpx.AsyncClient") as mock_cls:
            OpenMeteoReader(_LAT, _LON, _SENSOR_ID)
        _, kwargs = mock_cls.call_args
        assert kwargs["timeout"] == _TIMEOUT


class TestOpenMeteoReaderLifecycle:
    """Tests for OpenMeteoReader resource management."""

    @pytest.mark.asyncio
    async def test_close_calls_aclose(self) -> None:
        """close() always calls aclose() on the internal client."""
        reader, mock_client = _make_reader()
        await reader.close()
        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_returns_self(self) -> None:
        """__aenter__ returns the reader instance."""
        reader, _ = _make_reader()
        async with reader as ctx:
            assert ctx is reader

    @pytest.mark.asyncio
    async def test_context_manager_calls_close_on_exit(self) -> None:
        """__aexit__ closes the HTTP client."""
        reader, mock_client = _make_reader()
        async with reader:
            pass
        mock_client.aclose.assert_called_once()
