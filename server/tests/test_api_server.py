import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_db(monkeypatch):
    """In-memory store replacing all database.py functions."""
    store: dict = {}

    import server.src.database as db_module

    monkeypatch.setattr(db_module, "init_db", lambda: None)
    monkeypatch.setattr(db_module, "insert_job", lambda job: store.update({job["_id"]: job}))
    monkeypatch.setattr(db_module, "delete_job", lambda uid: store.pop(uid, None))
    monkeypatch.setattr(db_module, "delete_job_files", lambda job: None)
    monkeypatch.setattr(db_module, "get_job", lambda uid: store.get(uid))
    monkeypatch.setattr(db_module, "get_all_jobs", lambda: list(store.values()))
    monkeypatch.setattr(
        db_module,
        "get_jobs_by_ids",
        lambda ids: [store[i] for i in ids if i in store],
    )
    monkeypatch.setattr(db_module, "reassign_positions", lambda: None)
    return store


@pytest_asyncio.fixture
async def client(mock_db):
    from server.src.api_server import app, write_queue

    await write_queue.start()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    await write_queue.stop()


def make_job(id="abc12345678"):
    return {
        "_id": id,
        "name": "Alice",
        "timestamp": 1000,
        "position": None,
        "filedataArray": [],
        "estimated_time_of_print": None,
        "completed": False,
    }


async def test_add_job_returns_201(client):
    res = await client.post("/jobs", json=make_job())
    assert res.status_code == 201
    assert res.json()["status"] == "queued"


async def test_add_job_stores_in_db(client, mock_db):
    await client.post("/jobs", json=make_job())
    assert "abc12345678" in mock_db


async def test_remove_job_returns_200(client, mock_db):
    mock_db["abc12345678"] = make_job()
    res = await client.delete("/jobs/abc12345678")
    assert res.status_code == 200
    assert res.json()["status"] == "removed"


async def test_remove_job_not_found_returns_404(client):
    res = await client.delete("/jobs/notexist123")
    assert res.status_code == 404


async def test_get_queue_returns_all_jobs(client, mock_db):
    mock_db["abc12345678"] = make_job()
    res = await client.get("/jobs")
    assert res.status_code == 200
    assert len(res.json()) == 1


async def test_batch_get_filters_by_ids(client, mock_db):
    mock_db["abc12345678"] = make_job("abc12345678")
    mock_db["xyz12345678"] = make_job("xyz12345678")
    res = await client.post("/jobs/batch", json={"id_list": ["abc12345678"]})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["_id"] == "abc12345678"


async def test_batch_get_empty_list(client):
    res = await client.post("/jobs/batch", json={"id_list": []})
    assert res.status_code == 200
    assert res.json() == []


async def test_health_returns_ok(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


async def test_shutdown_returns_202(client):
    res = await client.post("/shutdown")
    assert res.status_code == 202
    assert res.json()["status"] == "shutting down"
