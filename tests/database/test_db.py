"""Tests for air_marshall.database.db."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import aiosqlite
import pytest

from air_marshall.api.models import (
    ConfigRecord,
    ControlRecord,
    FanRecord,
    HumidityRecord,
)
from air_marshall.database.db import (
    _parse_datetime,
    create_tables,
    get_db_conn,
    get_history_config,
    get_history_control,
    get_history_fan,
    get_history_humidity,
    get_latest_config,
    get_latest_control,
    get_latest_fan,
    get_latest_humidity,
    insert_config,
    insert_control,
    insert_fan,
    insert_humidity,
    prune_old_records,
)

_TS = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _humidity(
    sensor_id: str = "s1",
    ts: datetime = _TS,
    temperature: float = 22.5,
    humidity: float = 45.0,
    is_touched: bool = False,
) -> HumidityRecord:
    return HumidityRecord(
        sensor_id=sensor_id,
        sensor_serial_number="SN001",
        timestamp=ts,
        temperature=temperature,
        humidity=humidity,
        is_touched=is_touched,
    )


def _fan(ts: datetime = _TS, is_on: bool = True) -> FanRecord:
    return FanRecord(timestamp=ts, is_on=is_on)


def _control(
    ts: datetime = _TS, humidifier_on: bool = True, fan_on: bool = False
) -> ControlRecord:
    return ControlRecord(timestamp=ts, humidifier_on=humidifier_on, fan_on=fan_on)


def _config(
    ts: datetime = _TS, humidity_low: float = 30.0, humidity_high: float = 50.0
) -> ConfigRecord:
    return ConfigRecord(
        timestamp=ts, humidity_low=humidity_low, humidity_high=humidity_high
    )


class TestCreateTables:
    """Tests for create_tables."""

    @pytest.mark.asyncio
    async def test_idempotent(self, db_conn: aiosqlite.Connection) -> None:
        """Calling create_tables twice does not raise an error."""
        await create_tables(db_conn)  # second call

    @pytest.mark.asyncio
    async def test_tables_exist(self, db_conn: aiosqlite.Connection) -> None:
        """After create_tables, all expected tables are present."""
        cursor = await db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in await cursor.fetchall()}
        assert {"humidity", "fan", "control", "config"}.issubset(tables)


class TestInsertAndGetLatest:
    """Tests for insert_* and get_latest_* functions."""

    @pytest.mark.asyncio
    async def test_get_latest_humidity_empty(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_latest_humidity returns empty list on empty table."""
        result = await get_latest_humidity(db_conn)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_latest_fan_empty(self, db_conn: aiosqlite.Connection) -> None:
        """get_latest_fan returns None on empty table."""
        result = await get_latest_fan(db_conn)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_control_empty(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_latest_control returns None on empty table."""
        result = await get_latest_control(db_conn)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_config_empty(self, db_conn: aiosqlite.Connection) -> None:
        """get_latest_config returns None on empty table."""
        result = await get_latest_config(db_conn)
        assert result is None

    @pytest.mark.asyncio
    async def test_humidity_roundtrip(self, db_conn: aiosqlite.Connection) -> None:
        """Inserted humidity record is returned by get_latest_humidity."""
        record = _humidity(temperature=21.0, humidity=50.0, is_touched=True)
        await insert_humidity(db_conn, record)
        results = await get_latest_humidity(db_conn)
        assert len(results) == 1
        result = results[0]
        assert result.sensor_id == "s1"
        assert result.temperature == pytest.approx(21.0)
        assert result.humidity == pytest.approx(50.0)
        assert result.is_touched is True
        assert result.timestamp.tzinfo is not None

    @pytest.mark.asyncio
    async def test_fan_roundtrip(self, db_conn: aiosqlite.Connection) -> None:
        """Inserted fan record is returned by get_latest_fan."""
        await insert_fan(db_conn, _fan(is_on=False))
        result = await get_latest_fan(db_conn)
        assert result is not None
        assert result.is_on is False
        assert result.timestamp.tzinfo is not None

    @pytest.mark.asyncio
    async def test_control_roundtrip(self, db_conn: aiosqlite.Connection) -> None:
        """Inserted control record is returned by get_latest_control."""
        await insert_control(db_conn, _control(humidifier_on=True, fan_on=True))
        result = await get_latest_control(db_conn)
        assert result is not None
        assert result.humidifier_on is True
        assert result.fan_on is True

    @pytest.mark.asyncio
    async def test_config_roundtrip(self, db_conn: aiosqlite.Connection) -> None:
        """Inserted config record is returned by get_latest_config."""
        await insert_config(db_conn, _config(humidity_low=35.0, humidity_high=55.0))
        result = await get_latest_config(db_conn)
        assert result is not None
        assert result.humidity_low == pytest.approx(35.0)
        assert result.humidity_high == pytest.approx(55.0)
        assert result.timestamp.tzinfo is not None

    @pytest.mark.asyncio
    async def test_get_latest_returns_newest(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_latest_fan returns the most recently timestamped record."""
        ts1 = datetime(2024, 1, 1, tzinfo=UTC)
        ts2 = datetime(2024, 1, 2, tzinfo=UTC)
        await insert_fan(db_conn, _fan(ts=ts1, is_on=False))
        await insert_fan(db_conn, _fan(ts=ts2, is_on=True))
        result = await get_latest_fan(db_conn)
        assert result is not None
        assert result.is_on is True

    @pytest.mark.asyncio
    async def test_get_latest_humidity_sensor_id_filter(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_latest_humidity with sensor_id returns only matching records."""
        await insert_humidity(db_conn, _humidity(sensor_id="s1"))
        await insert_humidity(db_conn, _humidity(sensor_id="s2"))
        results = await get_latest_humidity(db_conn, sensor_id="s2")
        assert len(results) == 1
        assert results[0].sensor_id == "s2"

    @pytest.mark.asyncio
    async def test_get_latest_humidity_sensor_id_filter_no_match(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_latest_humidity returns empty list when sensor_id has no records."""
        await insert_humidity(db_conn, _humidity(sensor_id="s1"))
        results = await get_latest_humidity(db_conn, sensor_id="s99")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_latest_humidity_no_filter_returns_latest_per_sensor(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_latest_humidity without sensor_id returns one record per sensor."""
        ts1 = datetime(2024, 1, 1, tzinfo=UTC)
        ts2 = datetime(2024, 1, 2, tzinfo=UTC)
        ts3 = datetime(2024, 1, 3, tzinfo=UTC)
        await insert_humidity(db_conn, _humidity(sensor_id="s1", ts=ts1))
        await insert_humidity(
            db_conn, _humidity(sensor_id="s1", ts=ts2)
        )  # newer for s1
        await insert_humidity(db_conn, _humidity(sensor_id="s2", ts=ts3))
        results = await get_latest_humidity(db_conn)
        assert len(results) == 2
        by_id = {r.sensor_id: r for r in results}
        assert by_id["s1"].timestamp == ts2
        assert by_id["s2"].timestamp == ts3


class TestGetHistory:
    """Tests for get_history_* functions."""

    @pytest.mark.asyncio
    async def test_history_humidity_filters_by_date(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_history_humidity excludes records before the since cutoff."""
        old = datetime(2024, 1, 1, tzinfo=UTC)
        new = datetime(2024, 6, 1, tzinfo=UTC)
        await insert_humidity(db_conn, _humidity(ts=old))
        await insert_humidity(db_conn, _humidity(ts=new))
        since = datetime(2024, 3, 1, tzinfo=UTC)
        results = await get_history_humidity(db_conn, since=since)
        assert len(results) == 1
        assert results[0].timestamp == new

    @pytest.mark.asyncio
    async def test_history_fan_filters_by_date(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_history_fan excludes records before the since cutoff."""
        old = datetime(2024, 1, 1, tzinfo=UTC)
        new = datetime(2024, 6, 1, tzinfo=UTC)
        await insert_fan(db_conn, _fan(ts=old))
        await insert_fan(db_conn, _fan(ts=new))
        since = datetime(2024, 3, 1, tzinfo=UTC)
        results = await get_history_fan(db_conn, since=since)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_history_control_filters_by_date(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_history_control excludes records before the since cutoff."""
        old = datetime(2024, 1, 1, tzinfo=UTC)
        new = datetime(2024, 6, 1, tzinfo=UTC)
        await insert_control(db_conn, _control(ts=old))
        await insert_control(db_conn, _control(ts=new))
        since = datetime(2024, 3, 1, tzinfo=UTC)
        results = await get_history_control(db_conn, since=since)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_history_config_filters_by_date(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_history_config excludes records before the since cutoff."""
        old = datetime(2024, 1, 1, tzinfo=UTC)
        new = datetime(2024, 6, 1, tzinfo=UTC)
        await insert_config(db_conn, _config(ts=old))
        await insert_config(db_conn, _config(ts=new))
        since = datetime(2024, 3, 1, tzinfo=UTC)
        results = await get_history_config(db_conn, since=since)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_history_empty(self, db_conn: aiosqlite.Connection) -> None:
        """get_history_humidity returns empty list when table is empty."""
        since = datetime(2024, 1, 1, tzinfo=UTC)
        results = await get_history_humidity(db_conn, since=since)
        assert results == []

    @pytest.mark.asyncio
    async def test_history_includes_boundary(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """get_history_humidity includes records exactly at the since boundary."""
        ts = datetime(2024, 3, 1, tzinfo=UTC)
        await insert_humidity(db_conn, _humidity(ts=ts))
        results = await get_history_humidity(db_conn, since=ts)
        assert len(results) == 1


class TestPruneOldRecords:
    """Tests for prune_old_records."""

    @pytest.mark.asyncio
    async def test_prune_removes_old_records(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """prune_old_records deletes records older than retention_days."""
        old_ts = datetime.now(tz=UTC) - timedelta(days=40)
        new_ts = datetime.now(tz=UTC) - timedelta(days=5)
        await insert_humidity(db_conn, _humidity(ts=old_ts))
        await insert_humidity(db_conn, _humidity(ts=new_ts))
        await prune_old_records(db_conn, retention_days=30)
        cursor = await db_conn.execute("SELECT COUNT(*) FROM humidity")
        row = await cursor.fetchone()
        assert row is not None
        assert int(row[0]) == 1

    @pytest.mark.asyncio
    async def test_prune_keeps_recent_records(
        self, db_conn: aiosqlite.Connection
    ) -> None:
        """prune_old_records keeps records within retention_days."""
        recent_ts = datetime.now(tz=UTC) - timedelta(days=5)
        await insert_fan(db_conn, _fan(ts=recent_ts))
        await prune_old_records(db_conn, retention_days=30)
        cursor = await db_conn.execute("SELECT COUNT(*) FROM fan")
        row = await cursor.fetchone()
        assert row is not None
        assert int(row[0]) == 1

    @pytest.mark.asyncio
    async def test_prune_all_tables(self, db_conn: aiosqlite.Connection) -> None:
        """prune_old_records applies to humidity, fan, control, and config tables."""
        old_ts = datetime.now(tz=UTC) - timedelta(days=40)
        await insert_humidity(db_conn, _humidity(ts=old_ts))
        await insert_fan(db_conn, _fan(ts=old_ts))
        await insert_control(db_conn, _control(ts=old_ts))
        await insert_config(db_conn, _config(ts=old_ts))
        await prune_old_records(db_conn, retention_days=30)
        for table in ("humidity", "fan", "control", "config"):
            cursor = await db_conn.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
            row = await cursor.fetchone()
            assert row is not None
            assert int(row[0]) == 0, f"Expected 0 rows in {table}"


class TestGetDbConn:
    """Tests for get_db_conn."""

    @pytest.mark.asyncio
    async def test_returns_conn_from_app_state(self) -> None:
        """get_db_conn returns the connection stored on request.app.state."""
        mock_conn = MagicMock(spec=aiosqlite.Connection)
        request = MagicMock()
        request.app.state.db_conn = mock_conn
        result = await get_db_conn(request)
        assert result is mock_conn


class TestParseDatetime:
    """Tests for _parse_datetime."""

    def test_aware_datetime_is_unchanged(self) -> None:
        """_parse_datetime preserves timezone info on aware datetime strings."""
        result = _parse_datetime("2024-06-01T12:00:00+00:00")
        assert result.tzinfo is not None
        assert result == datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

    def test_naive_datetime_gets_utc(self) -> None:
        """_parse_datetime adds UTC timezone to naive datetime strings."""
        result = _parse_datetime("2024-06-01T12:00:00")
        assert result.tzinfo is not None
        assert result == datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
