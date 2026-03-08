"""FastAPI application and lifespan for the air-marshall database service."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiosqlite
from fastapi import FastAPI

from air_marshall.database.config import Settings, get_settings
from air_marshall.database.db import create_tables, prune_old_records
from air_marshall.database.routes import router

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Open the database, create tables, and run the background pruning loop.

    Stores the connection on ``app.state.db_conn`` so route handlers can
    retrieve it via the ``get_db_conn`` dependency.
    """
    settings = get_settings()
    async with aiosqlite.connect(settings.db_path) as conn:
        await create_tables(conn)
        task = asyncio.create_task(_pruning_loop(conn, settings))
        app.state.db_conn = conn
        yield
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="air-marshall database", lifespan=lifespan)
"""The FastAPI application. Import this to embed the service in another process."""

app.include_router(router)


async def _pruning_loop(conn: aiosqlite.Connection, settings: Settings) -> None:
    """Periodically delete records older than the configured retention period.

    Logs and continues on errors so a transient failure does not kill the loop.
    """
    while True:
        await asyncio.sleep(settings.pruning_interval_hours * 3600)
        try:
            await prune_old_records(conn, settings.retention_days)
        except Exception:
            _log.exception("Pruning failed; will retry after next interval")
