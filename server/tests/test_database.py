import os
import pytest
import importlib


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr("server.utils.constants.DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr("server.utils.constants.FILE_STORAGE_PATH", str(tmp_path / "storage"))
    os.makedirs(str(tmp_path / "storage"))
    import server.src.database as database
    importlib.reload(database)  # picks up patched constants
    database.init_db()
    return database


def make_job(id="abc12345678", name="Alice", ts=1000):
    return {
        "_id": id,
        "name": name,
        "timestamp": ts,
        "position": None,
        "filedataArray": [
            {
                "_file_id": "xyz1234",
                "file_name": "doc.pdf",
                "page_count": 2,
                "no_of_copies": 1,
                "color_mode": "bw",
                "layout": "portrait",
                "paper_size": "A4",
                "background_graphics": False,
                "headers_footers": False,
                "margins": "normal",
            }
        ],
        "estimated_time_of_print": None,
        "completed": False,
    }


def test_insert_and_get_job(db):
    db.insert_job(make_job())
    result = db.get_job("abc12345678")
    assert result is not None
    assert result["_id"] == "abc12345678"
    assert result["name"] == "Alice"
    assert len(result["filedataArray"]) == 1
    assert result["completed"] is False


def test_insert_ignores_duplicate(db):
    db.insert_job(make_job())
    db.insert_job(make_job())
    assert len(db.get_all_jobs()) == 1


def test_delete_job(db):
    db.insert_job(make_job())
    db.delete_job("abc12345678")
    assert db.get_job("abc12345678") is None


def test_get_all_jobs_sorted_by_timestamp(db):
    db.insert_job(make_job("bbb12345678", ts=2000))
    db.insert_job(make_job("aaa12345678", ts=1000))
    jobs = db.get_all_jobs()
    assert jobs[0]["timestamp"] == 1000
    assert jobs[1]["timestamp"] == 2000


def test_reassign_positions(db):
    db.insert_job(make_job("aaa12345678", ts=1000))
    db.insert_job(make_job("bbb12345678", ts=2000))
    db.reassign_positions()
    jobs = db.get_all_jobs()
    assert jobs[0]["position"] == 1
    assert jobs[1]["position"] == 2


def test_get_jobs_by_ids(db):
    db.insert_job(make_job("aaa12345678", ts=1000))
    db.insert_job(make_job("bbb12345678", ts=2000))
    result = db.get_jobs_by_ids(["aaa12345678"])
    assert len(result) == 1
    assert result[0]["_id"] == "aaa12345678"


def test_get_jobs_by_ids_empty_list(db):
    db.insert_job(make_job())
    assert db.get_jobs_by_ids([]) == []


def test_delete_job_files_removes_matching_file(db, tmp_path, monkeypatch):
    storage = str(tmp_path / "storage")
    monkeypatch.setattr(db, "FILE_STORAGE_PATH", storage)
    fake = os.path.join(storage, "abc12345678_Alice_xyz1234_doc.pdf")
    open(fake, "w").close()
    db.delete_job_files(make_job())
    assert not os.path.exists(fake)


def test_cleanup_orphaned_files_deletes_unmatched(db, tmp_path, monkeypatch):
    storage = str(tmp_path / "storage")
    monkeypatch.setattr(db, "FILE_STORAGE_PATH", storage)
    # File whose file_id has NO matching job in DB → should be deleted
    orphan = os.path.join(storage, "abc12345678_Alice_orphan1_report.pdf")
    open(orphan, "w").close()
    deleted = db.cleanup_orphaned_files()
    assert deleted == 1
    assert not os.path.exists(orphan)


def test_cleanup_orphaned_files_keeps_matched(db, tmp_path, monkeypatch):
    storage = str(tmp_path / "storage")
    monkeypatch.setattr(db, "FILE_STORAGE_PATH", storage)
    db.insert_job(make_job())  # job has file_id "xyz1234"
    # File whose file_id matches a job entry → should be kept
    keeper = os.path.join(storage, "abc12345678_Alice_xyz1234_doc.pdf")
    open(keeper, "w").close()
    deleted = db.cleanup_orphaned_files()
    assert deleted == 0
    assert os.path.exists(keeper)


def test_cleanup_orphaned_files_empty_storage(db, tmp_path, monkeypatch):
    storage = str(tmp_path / "storage")
    monkeypatch.setattr(db, "FILE_STORAGE_PATH", storage)
    deleted = db.cleanup_orphaned_files()
    assert deleted == 0


def test_cleanup_orphaned_files_nonexistent_storage(db, monkeypatch):
    monkeypatch.setattr(db, "FILE_STORAGE_PATH", "/nonexistent/path/xyz")
    deleted = db.cleanup_orphaned_files()
    assert deleted == 0
