"""Tests for air_marshall.database.routes."""

from datetime import UTC, datetime

import httpx
import pytest

_TS = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

_HUMIDITY = {
    "sensor_id": "s1",
    "sensor_serial_number": "SN001",
    "timestamp": _TS.isoformat(),
    "temperature": 22.5,
    "humidity": 45.0,
    "is_touched": False,
}

_FAN = {
    "timestamp": _TS.isoformat(),
    "is_on": True,
}

_CONTROL = {
    "timestamp": _TS.isoformat(),
    "humidifier_on": True,
    "fan_on": False,
}


class TestPostHumidity:
    """Tests for POST /data/humidity."""

    @pytest.mark.asyncio
    async def test_returns_201_no_content(self, test_client: httpx.AsyncClient) -> None:
        """Valid request returns 201 with no response body."""
        response = await test_client.post(
            "/data/humidity",
            json=_HUMIDITY,
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 201
        assert response.content == b""

    @pytest.mark.asyncio
    async def test_persists_record(self, test_client: httpx.AsyncClient) -> None:
        """Posted humidity record appears in GET /data/latest."""
        await test_client.post(
            "/data/humidity",
            json=_HUMIDITY,
            headers={"X-API-Key": "test-key"},
        )
        resp = await test_client.get("/data/latest", headers={"X-API-Key": "test-key"})
        assert resp.json()["humidity"][0]["sensor_id"] == "s1"

    @pytest.mark.asyncio
    async def test_missing_field_returns_422(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """Missing required field returns 422."""
        payload = {k: v for k, v in _HUMIDITY.items() if k != "sensor_id"}
        response = await test_client.post(
            "/data/humidity",
            json=payload,
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_wrong_type_returns_422(self, test_client: httpx.AsyncClient) -> None:
        """Wrong type for a strict field returns 422 (no silent coercion)."""
        payload = {**_HUMIDITY, "temperature": "not-a-number", "is_touched": 0}
        response = await test_client.post(
            "/data/humidity",
            json=payload,
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, test_client: httpx.AsyncClient) -> None:
        """Empty body returns 422."""
        response = await test_client.post(
            "/data/humidity",
            json={},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422


class TestPostFan:
    """Tests for POST /data/fan."""

    @pytest.mark.asyncio
    async def test_returns_201(self, test_client: httpx.AsyncClient) -> None:
        """Valid request returns 201."""
        response = await test_client.post(
            "/data/fan",
            json=_FAN,
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_missing_field_returns_422(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """Missing required field returns 422."""
        response = await test_client.post(
            "/data/fan",
            json={"timestamp": _TS.isoformat()},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_wrong_type_returns_422(self, test_client: httpx.AsyncClient) -> None:
        """Integer instead of boolean is rejected (StrictBool)."""
        response = await test_client.post(
            "/data/fan",
            json={"timestamp": _TS.isoformat(), "is_on": 1},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_persists_record(self, test_client: httpx.AsyncClient) -> None:
        """Posted fan record appears in GET /data/latest."""
        await test_client.post(
            "/data/fan",
            json=_FAN,
            headers={"X-API-Key": "test-key"},
        )
        resp = await test_client.get("/data/latest", headers={"X-API-Key": "test-key"})
        assert resp.json()["fan"]["is_on"] is True


class TestPostControl:
    """Tests for POST /data/control."""

    @pytest.mark.asyncio
    async def test_returns_201(self, test_client: httpx.AsyncClient) -> None:
        """Valid request returns 201."""
        response = await test_client.post(
            "/data/control",
            json=_CONTROL,
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_missing_field_returns_422(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """Missing required field returns 422."""
        response = await test_client.post(
            "/data/control",
            json={"timestamp": _TS.isoformat(), "humidifier_on": True},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_wrong_type_returns_422(self, test_client: httpx.AsyncClient) -> None:
        """Integer instead of boolean is rejected (StrictBool)."""
        response = await test_client.post(
            "/data/control",
            json={"timestamp": _TS.isoformat(), "humidifier_on": 1, "fan_on": 0},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_persists_record(self, test_client: httpx.AsyncClient) -> None:
        """Posted control record appears in GET /data/latest."""
        await test_client.post(
            "/data/control",
            json=_CONTROL,
            headers={"X-API-Key": "test-key"},
        )
        resp = await test_client.get("/data/latest", headers={"X-API-Key": "test-key"})
        assert resp.json()["control"]["humidifier_on"] is True


class TestGetLatest:
    """Tests for GET /data/latest."""

    @pytest.mark.asyncio
    async def test_empty_db_returns_nulls(self, test_client: httpx.AsyncClient) -> None:
        """Returns 200 with empty humidity list and null fan/control when database is empty."""
        response = await test_client.get(
            "/data/latest", headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["humidity"] == []
        assert body["fan"] is None
        assert body["control"] is None

    @pytest.mark.asyncio
    async def test_returns_posted_humidity(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """Returns the humidity record that was posted."""
        await test_client.post(
            "/data/humidity",
            json=_HUMIDITY,
            headers={"X-API-Key": "test-key"},
        )
        response = await test_client.get(
            "/data/latest", headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["humidity"][0]["sensor_id"] == "s1"
        assert body["humidity"][0]["temperature"] == 22.5

    @pytest.mark.asyncio
    async def test_sensor_id_query_param(self, test_client: httpx.AsyncClient) -> None:
        """sensor_id query parameter filters humidity results."""
        payload_s1 = {**_HUMIDITY, "sensor_id": "s1"}
        payload_s2 = {**_HUMIDITY, "sensor_id": "s2"}
        await test_client.post(
            "/data/humidity",
            json=payload_s1,
            headers={"X-API-Key": "test-key"},
        )
        await test_client.post(
            "/data/humidity",
            json=payload_s2,
            headers={"X-API-Key": "test-key"},
        )
        response = await test_client.get(
            "/data/latest?sensor_id=s2", headers={"X-API-Key": "test-key"}
        )
        body = response.json()
        assert body["humidity"][0]["sensor_id"] == "s2"


class TestGetHistory:
    """Tests for GET /data/history."""

    @pytest.mark.asyncio
    async def test_empty_db_returns_empty_lists(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """Returns 200 with empty lists when database is empty."""
        response = await test_client.get(
            "/data/history", headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["humidity"] == []
        assert body["fan"] == []
        assert body["control"] == []

    @pytest.mark.asyncio
    async def test_history_includes_recent_records(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """Recently posted records appear in /data/history."""
        recent_ts = datetime.now(tz=UTC)
        payload = {**_HUMIDITY, "timestamp": recent_ts.isoformat()}
        await test_client.post(
            "/data/humidity",
            json=payload,
            headers={"X-API-Key": "test-key"},
        )
        response = await test_client.get(
            "/data/history", headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["humidity"]) == 1
        assert body["humidity"][0]["sensor_id"] == "s1"

    @pytest.mark.asyncio
    async def test_history_excludes_old_records(
        self, test_client: httpx.AsyncClient
    ) -> None:
        """Records older than the retention window do not appear in /data/history."""
        # _TS is 2024-06-01, more than 30 days before today
        await test_client.post(
            "/data/fan",
            json={**_FAN, "is_on": False},
            headers={"X-API-Key": "test-key"},
        )
        response = await test_client.get(
            "/data/history", headers={"X-API-Key": "test-key"}
        )
        body = response.json()
        assert body["fan"] == []
