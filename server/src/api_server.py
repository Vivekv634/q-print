import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from server.src import database as db
from server.src.write_queue import WriteQueue
from server.utils.constants import PYTHON_API_PORT

logger = logging.getLogger(__name__)
write_queue: WriteQueue = WriteQueue()

_shutdown_event: threading.Event = threading.Event()


class JobRequest(BaseModel):
    id: str = Field(alias="_id")
    name: str
    timestamp: int
    position: int | None = None
    filedataArray: list[dict[str, Any]] = []
    estimated_time_of_print: int | None = None
    completed: bool = False

    model_config = {"populate_by_name": True}


class IdListRequest(BaseModel):
    id_list: list[str]


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    orphans = await asyncio.to_thread(db.cleanup_orphaned_files)
    if orphans:
        logger.info(f"Startup: cleaned up {orphans} orphaned file(s)")
    await write_queue.start()

    async def _watch_shutdown() -> None:
        await asyncio.to_thread(_shutdown_event.wait)
        await write_queue.stop()

    watcher = asyncio.create_task(_watch_shutdown())
    yield
    watcher.cancel()
    await write_queue.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/jobs", status_code=201)
async def add_job(job: JobRequest) -> dict[str, str]:
    raw = {
        "_id": job.id,
        "name": job.name,
        "timestamp": job.timestamp,
        "position": job.position,
        "filedataArray": job.filedataArray,
        "estimated_time_of_print": job.estimated_time_of_print,
        "completed": job.completed,
    }

    def _add() -> None:
        db.insert_job(raw)
        db.reassign_positions()

    await write_queue.submit(_add)
    return {"status": "queued"}


@app.delete("/jobs/{user_id}")
async def remove_job(user_id: str) -> dict[str, str]:
    job = await asyncio.to_thread(db.get_job, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    def _remove() -> None:
        db.delete_job_files(job)
        db.delete_job(user_id)
        db.reassign_positions()

    await write_queue.submit(_remove)
    return {"status": "removed"}


@app.get("/jobs")
async def get_queue() -> list[dict[str, Any]]:
    return await asyncio.to_thread(db.get_all_jobs)


@app.post("/jobs/batch")
async def get_jobs_by_ids(body: IdListRequest) -> dict[str, Any]:
    jobs = await asyncio.to_thread(db.get_jobs_by_ids, body.id_list)
    found_ids = {j["_id"] for j in jobs}
    missing_ids = [jid for jid in body.id_list if jid not in found_ids]
    rejected_ids: list[str] = []
    if missing_ids:
        rejected_ids = await asyncio.to_thread(db.get_rejections_for_ids, missing_ids)
        if rejected_ids:
            await asyncio.to_thread(db.clear_rejections, rejected_ids)
    return {"jobs": jobs, "rejected_ids": rejected_ids}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/shutdown", status_code=202)
async def shutdown() -> dict[str, str]:
    """Signal the server to stop after draining the write queue."""
    _shutdown_event.set()
    return {"status": "shutting down"}


def start(port: int = PYTHON_API_PORT) -> None:
    """Blocking call — intended to run in a daemon thread from main.py."""
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
