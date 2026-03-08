"""SQLite data access layer for the air-marshall database service.

All functions accept an ``aiosqlite.Connection`` explicitly and avoid global
state so tests can inject an in-memory connection via
``app.dependency_overrides``.

Storage conventions:
- Datetimes are stored as ISO 8601 strings (``datetime.isoformat()``).
- Booleans are stored as INTEGER (0/1).
"""

from datetime import UTC, datetime

import aiosqlite
from fastapi import Request

from air_marshall.api.models import ControlRecord, FanRecord, HumidityRecord


async def get_db_conn(request: Request) -> aiosqlite.Connection:
    """FastAPI dependency: return the shared DB connection from app state.

    Override with ``app.dependency_overrides`` in tests to inject an
    in-memory connection without starting the full lifespan.

    Returns:
        The ``aiosqlite.Connection`` stored on ``app.state.db_conn``.
    """
    conn: aiosqlite.Connection = request.app.state.db_conn
    return conn


async def create_tables(conn: aiosqlite.Connection) -> None:
    """Create the ``humidity``, ``fan``, and ``control`` tables if absent.

    Idempotent — safe to call on every startup. Also sets WAL journal mode.
    """
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS humidity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            sensor_serial_number TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            is_touched INTEGER NOT NULL
        )"""
    )
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS fan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            is_on INTEGER NOT NULL
        )"""
    )
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS control (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            humidifier_on INTEGER NOT NULL,
            fan_on INTEGER NOT NULL
        )"""
    )
    await conn.commit()


async def insert_humidity(conn: aiosqlite.Connection, record: HumidityRecord) -> None:
    """Insert a humidity record."""
    await conn.execute(
        """INSERT INTO humidity
           (sensor_id, sensor_serial_number, timestamp, temperature, humidity, is_touched)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            record.sensor_id,
            record.sensor_serial_number,
            record.timestamp.isoformat(),
            record.temperature,
            record.humidity,
            1 if record.is_touched else 0,
        ),
    )
    await conn.commit()


async def insert_fan(conn: aiosqlite.Connection, record: FanRecord) -> None:
    """Insert a fan state record."""
    await conn.execute(
        "INSERT INTO fan (timestamp, is_on) VALUES (?, ?)",
        (record.timestamp.isoformat(), 1 if record.is_on else 0),
    )
    await conn.commit()


async def insert_control(conn: aiosqlite.Connection, record: ControlRecord) -> None:
    """Insert a control state record."""
    await conn.execute(
        "INSERT INTO control (timestamp, humidifier_on, fan_on) VALUES (?, ?, ?)",
        (
            record.timestamp.isoformat(),
            1 if record.humidifier_on else 0,
            1 if record.fan_on else 0,
        ),
    )
    await conn.commit()


def _parse_datetime(value: str) -> datetime:
    """Parse an ISO 8601 string into a timezone-aware datetime, assuming UTC if naive."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


async def get_latest_humidity(
    conn: aiosqlite.Connection, sensor_id: str | None = None
) -> list[HumidityRecord]:
    """Return the most recent humidity record for each sensor.

    Pass ``sensor_id`` to restrict results to a single sensor (returns a list
    of zero or one record). Without ``sensor_id``, returns one record per
    distinct sensor, ordered by sensor_id ascending.
    """
    if sensor_id is not None:
        cursor = await conn.execute(
            """SELECT sensor_id, sensor_serial_number, timestamp, temperature,
                      humidity, is_touched
               FROM humidity
               WHERE sensor_id = ?
               ORDER BY timestamp DESC
               LIMIT 1""",
            (sensor_id,),
        )
    else:
        cursor = await conn.execute(
            # ROW_NUMBER() partitions rows by sensor_id and numbers them 1, 2, …
            # in descending timestamp order, so rn=1 is always the latest reading
            # for that sensor. Using a window function instead of GROUP BY + JOIN
            # avoids returning duplicate rows when two readings share a timestamp.
            """SELECT sensor_id, sensor_serial_number, timestamp,
                      temperature, humidity, is_touched
               FROM (
                   SELECT *,
                          ROW_NUMBER() OVER (
                              PARTITION BY sensor_id
                              ORDER BY timestamp DESC
                          ) AS rn
                   FROM humidity
               ) ranked
               WHERE rn = 1
               ORDER BY sensor_id ASC"""
        )
    rows = await cursor.fetchall()
    return [
        HumidityRecord(
            sensor_id=str(row[0]),
            sensor_serial_number=str(row[1]),
            timestamp=_parse_datetime(str(row[2])),
            temperature=float(row[3]),
            humidity=float(row[4]),
            is_touched=bool(int(row[5])),
        )
        for row in rows
    ]


async def get_latest_fan(conn: aiosqlite.Connection) -> FanRecord | None:
    """Return the most recent fan state record, or None if the table is empty."""
    cursor = await conn.execute(
        "SELECT timestamp, is_on FROM fan ORDER BY timestamp DESC LIMIT 1"
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return FanRecord(
        timestamp=_parse_datetime(str(row[0])),
        is_on=bool(int(row[1])),
    )


async def get_latest_control(conn: aiosqlite.Connection) -> ControlRecord | None:
    """Return the most recent control state record, or None if the table is empty."""
    cursor = await conn.execute(
        "SELECT timestamp, humidifier_on, fan_on FROM control ORDER BY timestamp DESC LIMIT 1"
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return ControlRecord(
        timestamp=_parse_datetime(str(row[0])),
        humidifier_on=bool(int(row[1])),
        fan_on=bool(int(row[2])),
    )


async def get_history_humidity(
    conn: aiosqlite.Connection, since: datetime
) -> list[HumidityRecord]:
    """Return all humidity records at or after ``since``, ordered by timestamp ascending."""
    cursor = await conn.execute(
        """SELECT sensor_id, sensor_serial_number, timestamp, temperature,
                  humidity, is_touched
           FROM humidity
           WHERE timestamp >= ?
           ORDER BY timestamp ASC""",
        (since.isoformat(),),
    )
    rows = await cursor.fetchall()
    return [
        HumidityRecord(
            sensor_id=str(row[0]),
            sensor_serial_number=str(row[1]),
            timestamp=_parse_datetime(str(row[2])),
            temperature=float(row[3]),
            humidity=float(row[4]),
            is_touched=bool(int(row[5])),
        )
        for row in rows
    ]


async def get_history_fan(
    conn: aiosqlite.Connection, since: datetime
) -> list[FanRecord]:
    """Return all fan state records at or after ``since``, ordered by timestamp ascending."""
    cursor = await conn.execute(
        "SELECT timestamp, is_on FROM fan WHERE timestamp >= ? ORDER BY timestamp ASC",
        (since.isoformat(),),
    )
    rows = await cursor.fetchall()
    return [
        FanRecord(
            timestamp=_parse_datetime(str(row[0])),
            is_on=bool(int(row[1])),
        )
        for row in rows
    ]


async def get_history_control(
    conn: aiosqlite.Connection, since: datetime
) -> list[ControlRecord]:
    """Return all control state records at or after ``since``, ordered by timestamp ascending."""
    cursor = await conn.execute(
        """SELECT timestamp, humidifier_on, fan_on
           FROM control
           WHERE timestamp >= ?
           ORDER BY timestamp ASC""",
        (since.isoformat(),),
    )
    rows = await cursor.fetchall()
    return [
        ControlRecord(
            timestamp=_parse_datetime(str(row[0])),
            humidifier_on=bool(int(row[1])),
            fan_on=bool(int(row[2])),
        )
        for row in rows
    ]


async def prune_old_records(conn: aiosqlite.Connection, retention_days: int) -> None:
    """Delete records older than ``retention_days`` days from all tables."""
    cutoff = f"datetime('now', '-{retention_days} days')"
    await conn.execute(f"DELETE FROM humidity WHERE timestamp < {cutoff}")  # noqa: S608
    await conn.execute(f"DELETE FROM fan WHERE timestamp < {cutoff}")  # noqa: S608
    await conn.execute(f"DELETE FROM control WHERE timestamp < {cutoff}")  # noqa: S608
    await conn.commit()
