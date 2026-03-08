"""Tests for air_marshall.database.auth."""

from datetime import UTC, datetime

import httpx
import pytest

_TS = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

_HUMIDITY_PAYLOAD = {
    "sensor_id": "s1",
    "sensor_serial_number": "SN001",
    "timestamp": _TS.isoformat(),
    "temperature": 22.5,
    "humidity": 45.0,
    "is_touched": False,
}


class TestRequireApiKey:
    """Tests for the require_api_key dependency."""

    @pytest.mark.asyncio
    async def test_correct_key_returns_201(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """A valid API key results in a 201 response."""
        response = await test_client.post(
            "/data/humidity",
            json=_HUMIDITY_PAYLOAD,
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_wrong_key_returns_401(self, test_client: httpx.AsyncClient) -> None:
        """An incorrect API key results in a 401 response."""
        response = await test_client.post(
            "/data/humidity",
            json=_HUMIDITY_PAYLOAD,
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_key_returns_401(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """A missing API key header results in a 401 response (auto_error=True)."""
        response = await test_client.post(
            "/data/humidity",
            json=_HUMIDITY_PAYLOAD,
        )
        assert response.status_code == 401
