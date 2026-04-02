import json
import pytest
from pathlib import Path
from server.src.queue_manager import QueueManager


# ── Job factory ───────────────────────────────────────────────────────────────

def make_job(
    user_id: str = "user_aaaaa",
    name: str = "Test User",
    timestamp: int = 1_000_000,
    file_id: str = "file001",
    file_name: str = "doc.pdf",
    estimated_time: int = 3,
) -> dict:
    return {
        "_id": user_id,
        "name": name,
        "timestamp": timestamp,
        "position": 1,
        "filedataArray": [
            {
                "_file_id": file_id,
                "file_name": file_name,
                "page_count": 2,
                "no_of_copies": 1,
                "color_mode": "black_&_white",
                "layout": "portrait",
                "paper_size": "a4",
                "background_graphics": False,
                "headers_footers": False,
                "margins": "default",
            }
        ],
        "estimated_time_of_print": estimated_time,
        "completed": False,
    }


# ── Shared path fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture
def queue_file(data_dir: Path) -> Path:
    return data_dir / "print_queue.json"


@pytest.fixture
def user_records_file(data_dir: Path) -> Path:
    p = data_dir / "user_records.json"
    p.write_text("{}")
    return p


@pytest.fixture
def storage_dir(data_dir: Path) -> Path:
    d = data_dir / "storage"
    d.mkdir()
    return d


@pytest.fixture
def qm(queue_file: Path, user_records_file: Path, storage_dir: Path) -> QueueManager:
    return QueueManager(
        queue_file_path=str(queue_file),
        user_record_file_path=str(user_records_file),
        file_storage_path=str(storage_dir),
    )
