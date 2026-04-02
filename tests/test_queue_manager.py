"""
Persistence tests for QueueManager.
Every assertion reads back from the JSON file directly so that the tests
verify on-disk state, not in-memory state.
"""

import json
from pathlib import Path

import pytest
from tests.conftest import make_job
from server.src.queue_manager import QueueManager


def read_queue(path: str) -> list[dict]:
    return json.loads(Path(path).read_text())


def read_user_records(path: str) -> dict:
    return json.loads(Path(path).read_text())


# ── Init ─────────────────────────────────────────────────────────────────────

class TestInit:
    def test_creates_queue_file_when_missing(self, queue_file, user_records_file, storage_dir):
        assert not queue_file.exists()
        QueueManager(str(queue_file), str(user_records_file), str(storage_dir))
        assert queue_file.exists()

    def test_initial_queue_is_empty_list(self, qm, queue_file):
        assert read_queue(qm.queue_file_path) == []

    def test_does_not_overwrite_existing_queue(self, queue_file, user_records_file, storage_dir):
        job = make_job()
        queue_file.write_text(json.dumps([job]))
        qm = QueueManager(str(queue_file), str(user_records_file), str(storage_dir))
        assert len(read_queue(qm.queue_file_path)) == 1


# ── add_job ──────────────────────────────────────────────────────────────────

class TestAddJob:
    def test_persists_job_to_file(self, qm):
        qm.add_job(make_job(user_id="u001"))
        on_disk = read_queue(qm.queue_file_path)
        assert len(on_disk) == 1
        assert on_disk[0]["_id"] == "u001"

    def test_assigns_position_1_to_first_job(self, qm):
        qm.add_job(make_job(user_id="u001"))
        on_disk = read_queue(qm.queue_file_path)
        assert on_disk[0]["position"] == 1

    def test_deduplicates_same_id(self, qm):
        job = make_job(user_id="u001")
        qm.add_job(job)
        qm.add_job(job)
        assert len(read_queue(qm.queue_file_path)) == 1

    def test_sorts_by_timestamp(self, qm):
        qm.add_job(make_job(user_id="u002", timestamp=2_000_000))
        qm.add_job(make_job(user_id="u001", timestamp=1_000_000))
        on_disk = read_queue(qm.queue_file_path)
        assert [j["_id"] for j in on_disk] == ["u001", "u002"]

    def test_assigns_contiguous_positions(self, qm):
        for i in range(1, 5):
            qm.add_job(make_job(user_id=f"u{i:03d}", timestamp=i * 1000))
        on_disk = read_queue(qm.queue_file_path)
        assert [j["position"] for j in on_disk] == [1, 2, 3, 4]

    def test_multiple_jobs_all_persisted(self, qm):
        for i in range(3):
            qm.add_job(make_job(user_id=f"u{i:03d}", timestamp=i * 1000))
        assert len(read_queue(qm.queue_file_path)) == 3


# ── remove_job ───────────────────────────────────────────────────────────────

class TestRemoveJob:
    def test_removes_job_from_file(self, qm):
        qm.add_job(make_job(user_id="u001"))
        qm.remove_job("u001")
        assert read_queue(qm.queue_file_path) == []

    def test_reassigns_positions_after_removal(self, qm):
        for i in range(1, 4):
            qm.add_job(make_job(user_id=f"u{i:03d}", timestamp=i * 1000))
        qm.remove_job("u001")  # remove position-1 job
        on_disk = read_queue(qm.queue_file_path)
        assert [j["position"] for j in on_disk] == [1, 2]

    def test_nonexistent_id_is_noop(self, qm):
        qm.add_job(make_job(user_id="u001"))
        qm.remove_job("does_not_exist")
        assert len(read_queue(qm.queue_file_path)) == 1

    def test_leaves_other_jobs_intact(self, qm):
        qm.add_job(make_job(user_id="u001", timestamp=1000))
        qm.add_job(make_job(user_id="u002", timestamp=2000))
        qm.remove_job("u001")
        on_disk = read_queue(qm.queue_file_path)
        assert on_disk[0]["_id"] == "u002"

    def test_deletes_associated_files(self, qm, storage_dir):
        # Plant a fake file matching the expected naming convention
        fake_file = storage_dir / "u001_TestUser_file001_doc.pdf"
        fake_file.write_text("fake pdf content")

        job = make_job(user_id="u001", file_id="file001", file_name="doc.pdf")
        qm.add_job(job)
        qm.remove_job("u001")

        assert not fake_file.exists()


# ── complete_job ──────────────────────────────────────────────────────────────

class TestCompleteJob:
    def test_removes_from_queue(self, qm):
        qm.add_job(make_job(user_id="u001"))
        qm.complete_job("u001")
        assert read_queue(qm.queue_file_path) == []

    def test_removes_from_user_records(self, qm, user_records_file):
        job = make_job(user_id="u001")
        # Pre-populate user_records as if upload had happened
        user_records_file.write_text(json.dumps({"u001": job}))
        qm.add_job(job)
        qm.complete_job("u001")
        assert "u001" not in read_user_records(str(user_records_file))

    def test_leaves_other_user_records_intact(self, qm, user_records_file):
        job_a = make_job(user_id="u001")
        job_b = make_job(user_id="u002", timestamp=2000)
        user_records_file.write_text(json.dumps({"u001": job_a, "u002": job_b}))
        qm.add_job(job_a)
        qm.add_job(job_b)
        qm.complete_job("u001")
        records = read_user_records(str(user_records_file))
        assert "u002" in records

    def test_deletes_associated_files(self, qm, storage_dir):
        fake_file = storage_dir / "u001_TestUser_file001_doc.pdf"
        fake_file.write_text("fake pdf content")

        job = make_job(user_id="u001", file_id="file001", file_name="doc.pdf")
        qm.add_job(job)
        qm.complete_job("u001")

        assert not fake_file.exists()

    def test_reassigns_positions_for_remaining_jobs(self, qm):
        for i in range(1, 4):
            qm.add_job(make_job(user_id=f"u{i:03d}", timestamp=i * 1000))
        qm.complete_job("u001")
        on_disk = read_queue(qm.queue_file_path)
        assert [j["position"] for j in on_disk] == [1, 2]


# ── get_queue ────────────────────────────────────────────────────────────────

class TestGetQueue:
    def test_returns_empty_list_initially(self, qm):
        assert qm.get_queue() == []

    def test_reflects_added_jobs(self, qm):
        qm.add_job(make_job(user_id="u001"))
        assert len(qm.get_queue()) == 1

    def test_reflects_removed_jobs(self, qm):
        qm.add_job(make_job(user_id="u001"))
        qm.remove_job("u001")
        assert qm.get_queue() == []

    def test_returns_list_not_reference(self, qm):
        qm.add_job(make_job(user_id="u001"))
        result = qm.get_queue()
        result.clear()
        # Mutating the returned list must not affect the persisted queue
        assert len(qm.get_queue()) == 1


# ── Resilience ───────────────────────────────────────────────────────────────

class TestResilience:
    def test_recovers_from_corrupted_queue_file(self, qm, queue_file):
        queue_file.write_text("not valid json {{{")
        # Should not raise; returns empty
        assert qm.get_queue() == []

    def test_recovers_from_non_list_root(self, qm, queue_file):
        queue_file.write_text('{"accidental": "object"}')
        assert qm.get_queue() == []

    def test_skips_non_dict_entries(self, qm, queue_file):
        queue_file.write_text('[{"_id": "u001"}, "bad_entry", null, 42]')
        result = qm.get_queue()
        assert len(result) == 1
        assert result[0]["_id"] == "u001"
