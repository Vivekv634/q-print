import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class WriteQueue:
    """Single-worker asyncio queue that serializes all DB write operations."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._start_lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        """Lazy-init lock — must be created inside a running event loop."""
        if self._start_lock is None:
            self._start_lock = asyncio.Lock()
        return self._start_lock

    async def start(self) -> None:
        """Start the worker coroutine. Idempotent — safe to call multiple times."""
        async with self._get_lock():
            if self._worker_task is None or self._worker_task.done():
                self._worker_task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        """Cancel the worker and wait for it to finish."""
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        # Reset lock and queue so start() can create fresh objects on the next
        # event loop (important when the same singleton is reused across tests).
        self._start_lock = None
        self._queue = asyncio.Queue()

    async def submit(self, fn: Callable[..., Any], *args: Any) -> Any:
        """Enqueue a sync callable and await its result.

        Raises any exception thrown by fn.
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Any] = loop.create_future()
        await self._queue.put((fn, args, future))
        return await future

    async def run(self) -> None:
        """Worker coroutine — call once via start().

        Processes operations one at a time in submission order.
        Each sync callable is executed in a thread pool to avoid blocking
        the event loop.
        """
        while True:
            fn, args, future = await self._queue.get()
            try:
                result = await asyncio.to_thread(fn, *args)
                if not future.done():
                    future.set_result(result)
            except Exception as exc:
                if not future.done():
                    future.set_exception(exc)
            finally:
                self._queue.task_done()
