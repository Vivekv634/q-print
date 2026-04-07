import json
import logging
import os
import sqlite3
from typing import Any

from server.utils.constants import DB_PATH, FILE_STORAGE_PATH

logger = logging.getLogger(__name__)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id   TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                position  INTEGER NOT NULL DEFAULT 0,
                filedata_array TEXT NOT NULL,
                estimated_time_of_print INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0
            )
        """)
        conn.commit()


def insert_job(job: dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO jobs
              (id, name, timestamp, position, filedata_array, estimated_time_of_print, completed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job["_id"],
                job["name"],
                job["timestamp"],
                job.get("position") if job.get("position") is not None else 0,
                json.dumps(job["filedataArray"]),
                job.get("estimated_time_of_print") or 0,
                int(job.get("completed", False)),
            ),
        )
        conn.commit()


def delete_job(user_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM jobs WHERE id = ?", (user_id,))
        conn.commit()


def get_job(user_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (user_id,)).fetchone()
        return _row_to_dict(row) if row else None


def get_all_jobs() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY timestamp ASC").fetchall()
        return [_row_to_dict(r) for r in rows]


def get_jobs_by_ids(id_list: list[str]) -> list[dict[str, Any]]:
    if not id_list:
        return []
    placeholders = ",".join("?" * len(id_list))
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM jobs WHERE id IN ({placeholders})", id_list
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def reassign_positions() -> None:
    with _connect() as conn:
        rows = conn.execute("SELECT id FROM jobs ORDER BY timestamp ASC").fetchall()
        params = [(i, row["id"]) for i, row in enumerate(rows, 1)]
        conn.executemany("UPDATE jobs SET position = ? WHERE id = ?", params)
        conn.commit()


def delete_job_files(job: dict[str, Any]) -> None:
    if not os.path.exists(FILE_STORAGE_PATH):
        return
    for filedata in job.get("filedataArray", []):
        if not isinstance(filedata, dict):
            continue
        file_id: str = filedata.get("_file_id", "")
        file_name: str = filedata.get("file_name", "")
        if not file_id or not file_name:
            continue
        try:
            for stored in os.listdir(FILE_STORAGE_PATH):
                if f"_{file_id}_" in stored:
                    path = os.path.join(FILE_STORAGE_PATH, stored)
                    os.remove(path)
                    logger.info(f"Deleted file: {path}")
        except OSError as e:
            logger.error(f"Failed to delete files for {job.get('_id', '')}: {e}")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["filedataArray"] = json.loads(d.pop("filedata_array"))
    d["_id"] = d.pop("id")
    d["completed"] = bool(d["completed"])
    return d
