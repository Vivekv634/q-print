import json
import logging
import os
import sqlite3
import time
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id          INTEGER PRIMARY KEY,
                event_type  TEXT    NOT NULL,
                job_id      TEXT    NOT NULL,
                files_count INTEGER NOT NULL DEFAULT 0,
                pages_color INTEGER NOT NULL DEFAULT 0,
                pages_bw    INTEGER NOT NULL DEFAULT 0,
                revenue     REAL    NOT NULL DEFAULT 0.0,
                hour        INTEGER NOT NULL DEFAULT 0,
                date        TEXT    NOT NULL,
                timestamp   INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                date      TEXT PRIMARY KEY,
                status    TEXT    NOT NULL DEFAULT 'pending',
                synced_at INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rejected_notifications (
                job_id     TEXT    PRIMARY KEY,
                created_at INTEGER NOT NULL
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


def cleanup_orphaned_files() -> int:
    """Delete files in FILE_STORAGE_PATH that have no matching job in the DB.

    A file is considered orphaned if its file_id segment (3rd underscore-delimited
    component) does not appear in any job's filedataArray.

    Returns the count of deleted files.
    """
    if not os.path.exists(FILE_STORAGE_PATH):
        return 0

    jobs = get_all_jobs()
    known_file_ids: set[str] = {
        fd["_file_id"]
        for job in jobs
        for fd in job.get("filedataArray", [])
        if isinstance(fd, dict) and fd.get("_file_id")
    }

    deleted = 0
    try:
        for filename in os.listdir(FILE_STORAGE_PATH):
            parts = filename.split("_", 3)
            if len(parts) < 4:
                continue  # unexpected format — skip
            file_id = parts[2]
            if file_id not in known_file_ids:
                try:
                    os.remove(os.path.join(FILE_STORAGE_PATH, filename))
                    logger.info(f"Cleaned up orphaned file: {filename}")
                    deleted += 1
                except OSError as e:
                    logger.error(f"Failed to delete orphaned file {filename}: {e}")
    except OSError as e:
        logger.error(f"Failed to scan storage directory: {e}")
    return deleted


def insert_analytics_event(
    event_type: str,
    job_id: str,
    files_count: int,
    pages_color: int,
    pages_bw: int,
    revenue: float,
    hour: int,
    date: str,
) -> None:
    if not (0 <= hour <= 23):
        raise ValueError(f"hour must be 0–23, got {hour}")
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO analytics_events
              (event_type, job_id, files_count, pages_color, pages_bw, revenue, hour, date, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (event_type, job_id, files_count, pages_color, pages_bw, revenue, hour, date, int(time.time())),
        )
        conn.execute(
            "INSERT OR IGNORE INTO sync_log (date, status) VALUES (?, 'pending')",
            (date,),
        )
        conn.commit()


def get_pending_sync_dates() -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT date FROM sync_log WHERE status = 'pending' ORDER BY date ASC"
        ).fetchall()
        return [row["date"] for row in rows]


def aggregate_day_analytics(date: str) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(CASE WHEN event_type = 'completed' THEN 1 END) AS jobs_completed,
                COUNT(CASE WHEN event_type = 'errored'   THEN 1 END) AS jobs_errored,
                COUNT(CASE WHEN event_type = 'dropped'   THEN 1 END) AS jobs_dropped,
                SUM(files_count) AS files_printed,
                SUM(pages_color) AS pages_color,
                SUM(pages_bw)    AS pages_bw,
                SUM(revenue)     AS revenue
            FROM analytics_events WHERE date = ?
            """,
            (date,),
        ).fetchone()
        hour_rows = conn.execute(
            "SELECT hour, COUNT(*) AS cnt FROM analytics_events WHERE date = ? GROUP BY hour",
            (date,),
        ).fetchall()

    peak_hours = [0] * 24
    for hr in hour_rows:
        peak_hours[hr["hour"]] = hr["cnt"]

    return {
        "date": date,
        "jobs_completed": row["jobs_completed"] or 0,
        "jobs_errored":   row["jobs_errored"]   or 0,
        "jobs_dropped":   row["jobs_dropped"]   or 0,
        "files_printed":  row["files_printed"]  or 0,
        "pages_color":    row["pages_color"]    or 0,
        "pages_bw":       row["pages_bw"]       or 0,
        "revenue":        row["revenue"]        or 0.0,
        "peak_hours":     peak_hours,
    }


def mark_dates_synced(dates: list[str]) -> None:
    if not dates:
        return
    with _connect() as conn:
        conn.executemany(
            "UPDATE sync_log SET status = 'synced', synced_at = ? WHERE date = ?",
            [(int(time.time()), d) for d in dates],
        )
        conn.commit()


def insert_rejection(job_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO rejected_notifications (job_id, created_at) VALUES (?, ?)",
            (job_id, int(time.time())),
        )
        conn.commit()


def get_rejections_for_ids(id_list: list[str]) -> list[str]:
    if not id_list:
        return []
    placeholders = ",".join("?" * len(id_list))
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT job_id FROM rejected_notifications WHERE job_id IN ({placeholders})",
            id_list,
        ).fetchall()
        return [row["job_id"] for row in rows]


def clear_rejections(job_ids: list[str]) -> None:
    if not job_ids:
        return
    placeholders = ",".join("?" * len(job_ids))
    with _connect() as conn:
        conn.execute(
            f"DELETE FROM rejected_notifications WHERE job_id IN ({placeholders})",
            job_ids,
        )
        conn.commit()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["filedataArray"] = json.loads(d.pop("filedata_array"))
    d["_id"] = d.pop("id")
    d["completed"] = bool(d["completed"])
    return d
