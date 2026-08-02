"""Async EventStream primitive.

Python port of vendor/pi-mono-upstream/packages/ai/src/utils/event-stream.ts.

Contract (mirrors pi-ai):
- push(event): enqueue an event. If is_complete(event) returns True, the final
  result is extracted from it and resolved, but the event itself is still
  delivered to consumers.
- end(result=None): signal end-of-stream. Optional result sets the final result
  if not already set (used when the producer ends without a terminal event).
- __aiter__: async iterate events until either a terminal event (is_complete)
  is consumed or end() is called.
- result(): await the final extracted result. Resolves when the first terminal
  event is pushed OR when end(result=...) supplies one.

Construction must happen inside a running asyncio event loop (providers always
satisfy this; tests run under pytest-asyncio). This mirrors pi-ai's assumption
that the stream is created inside the provider's async function.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Callable, Generic, TypeVar

from .types import AssistantMessage, AssistantMessageEvent

T = TypeVar("T")
R = TypeVar("R")


class _EndSentinel:
    """Marker pushed onto the internal queue to signal end-of-stream."""


_END = _EndSentinel()


class EventStream(Generic[T, R]):
    """Generic async event stream with a terminal extracted result.

    Parameters
    ----------
    is_complete:
        Predicate identifying a terminal event (e.g., `type in {"done", "error"}`).
    extract_result:
        Called on the first terminal event to produce the final result.
    """

    def __init__(
        self,
        is_complete: Callable[[T], bool],
        extract_result: Callable[[T], R],
    ) -> None:
        self._is_complete = is_complete
        self._extract_result = extract_result
        self._queue: asyncio.Queue[T | _EndSentinel] = asyncio.Queue()
        # Use the running loop explicitly; asyncio.get_event_loop() is
        # deprecated in 3.12+ when there is no running loop and is scheduled
        # for removal. Providers always construct this inside an async fn,
        # so a running loop is guaranteed.
        self._result: asyncio.Future[R] = asyncio.get_running_loop().create_future()
        self._done = False
        self._ended = False
        # Optional handle to the background task producing events. Providers
        # set this via `set_task` so callers can cancel the stream without
        # the task becoming unreachable (see asyncio docs on retaining
        # create_task references).
        self._task: asyncio.Task[None] | None = None

    def push(self, event: T) -> None:
        """Enqueue an event. Idempotent once the stream is done."""
        if self._done:
            return
        if self._is_complete(event):
            self._done = True
            if not self._result.done():
                try:
                    self._result.set_result(self._extract_result(event))
                except Exception as exc:
                    self._result.set_exception(exc)
        self._queue.put_nowait(event)

    def end(self, result: R | None = None) -> None:
        """Signal end-of-stream. Safe to call multiple times.

        If `result` is provided and the result-future is not yet resolved, it
        is used as the final value. If `result` is None and no terminal event
        was previously pushed, the result-future is resolved with a
        RuntimeError so `await stream.result()` raises rather than hanging
        forever (the docstring contract is that callers either push a
        terminal event or supply a result here).
        """
        if self._ended:
            return
        self._ended = True
        self._done = True
        if not self._result.done():
            if result is not None:
                self._result.set_result(result)
            else:
                self._result.set_exception(
                    RuntimeError(
                        "EventStream ended without a terminal event or explicit result"
                    )
                )
        self._queue.put_nowait(_END)

    def fail(self, error: BaseException) -> None:
        """Signal that the producer failed before a terminal event.

        Sets result() to raise and ends the stream. Not present in pi-ai (JS
        throws synchronously into the provider), but necessary in Python so
        callers awaiting result() don't hang forever on producer errors.
        """
        if self._done:
            return
        self._done = True
        self._ended = True
        if not self._result.done():
            self._result.set_exception(error)
        self._queue.put_nowait(_END)

    async def __aiter__(self) -> AsyncIterator[T]:
        while True:
            item = await self._queue.get()
            if isinstance(item, _EndSentinel):
                return
            yield item
            if self._done and self._is_complete(item):
                return

    async def result(self) -> R:
        """Await the final extracted result."""
        return await self._result

    def set_task(self, task: asyncio.Task[None]) -> None:
        """Attach the background producer task.

        Retains a strong reference to the task (asyncio only keeps weak
        refs via scheduling) and enables cancel().
        """
        self._task = task

    def cancel(self) -> None:
        """Cancel the background producer task, if any.

        The task's CancelledError handler is expected to push a terminal
        ErrorEvent(reason="aborted"), which ends the stream. Safe to call
        multiple times; a no-op once the stream is already done.
        """
        task = self._task
        if task is None or task.done():
            return
        task.cancel()


class AssistantMessageEventStream(EventStream[AssistantMessageEvent, AssistantMessage]):
    """Specialization for LLM streams (port of AssistantMessageEventStream).

    Terminal events are `done` and `error`; the final AssistantMessage is
    pulled from `event.message` or `event.error` respectively.
    """

    def __init__(self) -> None:
        super().__init__(
            is_complete=_is_assistant_terminal,
            extract_result=_extract_assistant_message,
        )


def create_assistant_message_event_stream() -> AssistantMessageEventStream:
    """Factory (mirrors pi-ai createAssistantMessageEventStream)."""
    return AssistantMessageEventStream()


def _is_assistant_terminal(event: AssistantMessageEvent) -> bool:
    return event.type in ("done", "error")


def _extract_assistant_message(event: AssistantMessageEvent) -> AssistantMessage:
    if event.type == "done":
        return event.message  # type: ignore[union-attr]
    if event.type == "error":
        return event.error  # type: ignore[union-attr]
    raise RuntimeError(f"Unexpected event type for final result: {event.type}")


__all__ = [
    "AssistantMessageEventStream",
    "EventStream",
    "create_assistant_message_event_stream",
]
