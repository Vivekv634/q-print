import asyncio
import time
import pytest
from server.src.write_queue import WriteQueue


@pytest.fixture
async def queue():
    wq = WriteQueue()
    await wq.start()
    yield wq
    await wq.stop()


async def test_single_operation_returns_result(queue):
    result = await queue.submit(lambda: 99)
    assert result == 99


async def test_operations_are_serialized(queue):
    order: list[str] = []

    def slow():
        time.sleep(0.05)
        order.append("first")

    def fast():
        order.append("second")

    # create_task so both are submitted before either is processed
    t1 = asyncio.create_task(queue.submit(slow))
    t2 = asyncio.create_task(queue.submit(fast))
    await asyncio.gather(t1, t2)
    assert order == ["first", "second"]


async def test_exception_propagates(queue):
    def raise_error():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await queue.submit(raise_error)


async def test_subsequent_operations_work_after_exception(queue):
    def raise_error():
        raise RuntimeError("oops")

    def ok():
        return "fine"

    with pytest.raises(RuntimeError):
        await queue.submit(raise_error)
    result = await queue.submit(ok)
    assert result == "fine"
