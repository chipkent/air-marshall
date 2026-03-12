"""HTTP routes for the air-marshall database service.

All endpoints require a valid ``X-API-Key`` header.
"""

from datetime import UTC, datetime, timedelta

import aiosqlite
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from air_marshall.api.models import (
    ConfigRecord,
    ControlRecord,
    FanRecord,
    HistoryResponse,
    HumidityRecord,
    LatestResponse,
)
from air_marshall.database.auth import require_api_key
from air_marshall.database.config import Settings, get_settings
from air_marshall.database.db import (
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
)

router = APIRouter(prefix="/data", tags=["data"])
"""Router mounted at ``/data`` by the FastAPI application."""


@router.post("/humidity", status_code=201, response_class=Response)
async def post_humidity(
    record: HumidityRecord,
    conn: aiosqlite.Connection = Depends(get_db_conn),
    _: None = Depends(require_api_key),
) -> Response:
    """Store a new humidity reading."""
    await insert_humidity(conn, record)
    return Response(status_code=201)


@router.post("/fan", status_code=201, response_class=Response)
async def post_fan(
    record: FanRecord,
    conn: aiosqlite.Connection = Depends(get_db_conn),
    _: None = Depends(require_api_key),
) -> Response:
    """Store a new fan state event."""
    await insert_fan(conn, record)
    return Response(status_code=201)


@router.post("/control", status_code=201, response_class=Response)
async def post_control(
    record: ControlRecord,
    conn: aiosqlite.Connection = Depends(get_db_conn),
    _: None = Depends(require_api_key),
) -> Response:
    """Store a new control state event."""
    await insert_control(conn, record)
    return Response(status_code=201)


@router.post("/config", status_code=201, response_class=Response)
async def post_config(
    record: ConfigRecord,
    conn: aiosqlite.Connection = Depends(get_db_conn),
    _: None = Depends(require_api_key),
) -> Response:
    """Store a new configuration record."""
    await insert_config(conn, record)
    return Response(status_code=201)


@router.get("/latest")
async def get_latest(
    sensor_id: str | None = Query(default=None),
    conn: aiosqlite.Connection = Depends(get_db_conn),
    _: None = Depends(require_api_key),
) -> LatestResponse:
    """Return the most recent record of each type.

    Pass ``?sensor_id=<id>`` to filter the humidity result to one sensor.
    Any field is None if no data of that type has been posted yet.
    """
    humidity = await get_latest_humidity(conn, sensor_id=sensor_id)
    fan = await get_latest_fan(conn)
    control = await get_latest_control(conn)
    config = await get_latest_config(conn)
    return LatestResponse(humidity=humidity, fan=fan, control=control, config=config)


@router.get("/history")
async def get_history(
    conn: aiosqlite.Connection = Depends(get_db_conn),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_api_key),
) -> HistoryResponse:
    """Return all records within the configured retention window."""
    since = datetime.now(tz=UTC) - timedelta(days=settings.retention_days)
    humidity = await get_history_humidity(conn, since=since)
    fan = await get_history_fan(conn, since=since)
    control = await get_history_control(conn, since=since)
    config = await get_history_config(conn, since=since)
    return HistoryResponse(humidity=humidity, fan=fan, control=control, config=config)
