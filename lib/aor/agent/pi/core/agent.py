"""Session façade over the stateless agent loop.

Python port of `vendor/pi-mono-upstream/packages/agent/src/agent.ts`.

Responsibilities
----------------
1. Entry points: `prompt` / `continue_` — normalize input and call `_drive_loop`.
2. Queues: `steer` / `follow_up` with `one-at-a-time` | `all` modes.
3. Lifecycle: `AbortController`, `running_prompt` future, `wait_for_idle`.
4. State mutation + listener fanout: each loop event updates `_state`
   in-place and is then broadcast to every subscriber.

`Agent` owns durable conversation state; the loop owns live turn structure.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Literal

from agent.pi.ai.stream import stream_simple
from agent.pi.ai.types import (
    AssistantMessage,
    Message,
    Model,
    TextContent,
    Usage,
    UsageCost,
)
from agent.pi.core._internal import now_ms
from agent.pi.core.agent_loop import AgentEventStream, agent_loop, agent_loop_continue
from agent.pi.core.types import (
    AbortController,
    AgentContext,
    AgentEvent,
    AgentLoopConfig,
    AgentMessage,
    AgentState,
    AgentTool,
    ConvertToLlmFn,
    GetApiKeyFn,
    StreamFn,
    ThinkingLevel,
    TransformContextFn,
    Transport,
)

_log = logging.getLogger(__name__)

QueueMode = Literal["all", "one-at-a-time"]


def _default_convert_to_llm(messages: list[AgentMessage]) -> list[Message]:
    """Default filter: keep only user / assistant / toolResult messages.

    Mirrors upstream's `defaultConvertToLlm`. Today `AgentMessage` is an alias
    for `Message`, so this is effectively an identity filter; keeping the
    filter in place preserves behaviour if downstream widens `AgentMessage`
    to include custom roles.
    """
    return [m for m in messages if m.role in ("user", "assistant", "toolResult")]


class Agent:
    """Long-lived agent session.

    See module docstring for responsibilities. Construct with `AgentOptions`
    keyword arguments; at minimum supply a `model` on `initial_state`.

    Thread-safety: not designed for concurrent `prompt()` calls. Call
    `wait_for_idle()` between runs, or use `steer()`/`follow_up()` to queue
    messages while a run is in progress.
    """

    def __init__(
        self,
        *,
        initial_state: AgentState | dict[str, Any] | None = None,
        convert_to_llm: ConvertToLlmFn | None = None,
        transform_context: TransformContextFn | None = None,
        steering_mode: QueueMode = "one-at-a-time",
        follow_up_mode: QueueMode = "one-at-a-time",
        stream_fn: StreamFn | None = None,
        session_id: str | None = None,
        get_api_key: GetApiKeyFn | None = None,
        on_payload: Callable[[str, Any], None] | None = None,
        thinking_budgets: dict[str, int] | None = None,
        transport: Transport = "sse",
        max_retry_delay_ms: int | None = None,
    ) -> None:
        if isinstance(initial_state, AgentState):
            state = initial_state.model_copy()
        elif isinstance(initial_state, dict):
            state = AgentState.model_validate(initial_state)
        else:
            state = AgentState()
        self._state: AgentState = state

        self._listeners: list[Callable[[AgentEvent], None]] = []
        self._abort_controller: AbortController | None = None
        self._run_task: asyncio.Task[None] | None = None
        # Reference to the in-flight agent_loop event stream. Held so that
        # `abort()` can cascade cancellation into the producer task — which in
        # turn propagates `CancelledError` into the active `stream_fn` await,
        # closing the underlying HTTP connection (httpx, etc.) immediately
        # rather than waiting for the next event-boundary check.
        self._active_stream: AgentEventStream | None = None
        self._convert_to_llm = convert_to_llm or _default_convert_to_llm
        self._transform_context = transform_context
        self._steering_queue: list[AgentMessage] = []
        self._follow_up_queue: list[AgentMessage] = []
        self._steering_mode: QueueMode = steering_mode
        self._follow_up_mode: QueueMode = follow_up_mode
        self.stream_fn: StreamFn = stream_fn or stream_simple  # type: ignore[assignment]
        self._session_id = session_id
        self.get_api_key = get_api_key
        self._on_payload = on_payload
        self._running_prompt: asyncio.Future[None] | None = None
        self._thinking_budgets = thinking_budgets
        self._transport: Transport = transport
        self._max_retry_delay_ms = max_retry_delay_ms

    # ------------------------------------------------------------------
    # Public read-only / mutable accessors
    # ------------------------------------------------------------------

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @session_id.setter
    def session_id(self, value: str | None) -> None:
        self._session_id = value

    @property
    def thinking_budgets(self) -> dict[str, int] | None:
        return self._thinking_budgets

    @thinking_budgets.setter
    def thinking_budgets(self, value: dict[str, int] | None) -> None:
        self._thinking_budgets = value

    @property
    def transport(self) -> Transport:
        return self._transport

    @transport.setter
    def transport(self, value: Transport) -> None:
        self._transport = value

    @property
    def max_retry_delay_ms(self) -> int | None:
        return self._max_retry_delay_ms

    @max_retry_delay_ms.setter
    def max_retry_delay_ms(self, value: int | None) -> None:
        self._max_retry_delay_ms = value

    # ------------------------------------------------------------------
    # State accessors (mutating any of these mid-prompt is unsafe; setters
    # raise if `is_streaming` is True. Snapshots taken at run start are
    # what the loop iterates over.)
    # ------------------------------------------------------------------

    @property
    def system_prompt(self) -> str:
        return self._state.system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        self._assert_not_streaming("system_prompt")
        self._state.system_prompt = value

    @property
    def model(self) -> Model | None:
        return self._state.model

    @model.setter
    def model(self, value: Model) -> None:
        self._assert_not_streaming("model")
        self._state.model = value

    @property
    def thinking_level(self) -> ThinkingLevel:
        return self._state.thinking_level

    @thinking_level.setter
    def thinking_level(self, value: ThinkingLevel) -> None:
        self._assert_not_streaming("thinking_level")
        self._state.thinking_level = value

    @property
    def tools(self) -> list[AgentTool]:
        return self._state.tools

    @tools.setter
    def tools(self, value: list[AgentTool]) -> None:
        self._assert_not_streaming("tools")
        self._state.tools = list(value)

    def replace_messages(self, ms: list[AgentMessage]) -> None:
        self._assert_not_streaming("messages")
        self._state.messages = list(ms)

    def append_message(self, m: AgentMessage) -> None:
        # Internally invoked from `_drive_loop` while `is_streaming=True`,
        # so this method does NOT assert. External callers should not call
        # it concurrently with a prompt; protect via `wait_for_idle()`.
        self._state.messages.append(m)

    def clear_messages(self) -> None:
        self._assert_not_streaming("messages")
        self._state.messages = []

    def _assert_not_streaming(self, what: str) -> None:
        if self._state.is_streaming:
            raise RuntimeError(
                f"Cannot mutate {what} while the agent is streaming. "
                "Call abort() and await wait_for_idle() first."
            )

    # ------------------------------------------------------------------
    # Subscribe / emit
    # ------------------------------------------------------------------

    def subscribe(self, fn: Callable[[AgentEvent], None]) -> Callable[[], None]:
        """Register a sync event listener. Returns an unsubscribe callable."""
        self._listeners.append(fn)

        def _unsubscribe() -> None:
            try:
                self._listeners.remove(fn)
            except ValueError:
                pass

        return _unsubscribe

    def _emit(self, event: AgentEvent) -> None:
        # Isolate listener exceptions: a buggy subscriber must not be able
        # to abort the loop or starve other subscribers. We log and move on.
        for listener in list(self._listeners):
            try:
                listener(event)
            except Exception:  # noqa: BLE001 — defensive fanout boundary
                _log.exception(
                    "Agent event listener raised on %s; continuing fanout.",
                    event.type,
                )

    # ------------------------------------------------------------------
    # Queues
    # ------------------------------------------------------------------

    @property
    def steering_mode(self) -> QueueMode:
        return self._steering_mode

    @steering_mode.setter
    def steering_mode(self, value: QueueMode) -> None:
        self._steering_mode = value

    @property
    def follow_up_mode(self) -> QueueMode:
        return self._follow_up_mode

    @follow_up_mode.setter
    def follow_up_mode(self, value: QueueMode) -> None:
        self._follow_up_mode = value

    def steer(self, m: AgentMessage) -> None:
        """Queue a user message to preempt the agent mid-run.

        Delivered after the current in-flight tool finishes; remaining queued
        tools are skipped.
        """
        self._steering_queue.append(m)

    def follow_up(self, m: AgentMessage) -> None:
        """Queue a user message to be processed after the agent otherwise stops."""
        self._follow_up_queue.append(m)

    def clear_steering_queue(self) -> None:
        self._steering_queue = []

    def clear_follow_up_queue(self) -> None:
        self._follow_up_queue = []

    def clear_all_queues(self) -> None:
        self._steering_queue = []
        self._follow_up_queue = []

    def has_queued_messages(self) -> bool:
        return bool(self._steering_queue or self._follow_up_queue)

    def _dequeue_steering_messages(self) -> list[AgentMessage]:
        if self._steering_mode == "one-at-a-time":
            if self._steering_queue:
                first = self._steering_queue[0]
                self._steering_queue = self._steering_queue[1:]
                return [first]
            return []
        out = list(self._steering_queue)
        self._steering_queue = []
        return out

    def _dequeue_follow_up_messages(self) -> list[AgentMessage]:
        if self._follow_up_mode == "one-at-a-time":
            if self._follow_up_queue:
                first = self._follow_up_queue[0]
                self._follow_up_queue = self._follow_up_queue[1:]
                return [first]
            return []
        out = list(self._follow_up_queue)
        self._follow_up_queue = []
        return out

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def abort(self) -> None:
        """Request abort of the currently-running prompt, if any.

        The semantics mirror the TS `AbortController.abort()`: callers who are
        `await`-ing `prompt()` see it resolve normally with an aborted
        assistant message appended.

        Three things happen, in order:

        1. The cooperative `AbortSignal` is set, so any code path that polls
           `signal.aborted` (the loop's `_stream_assistant_response`, custom
           tool implementations) breaks out at its next checkpoint.
        2. The in-flight agent-loop event stream's *producer* task is
           cancelled. This cascades `asyncio.CancelledError` into whatever
           coroutine the producer is currently awaiting — most importantly
           the user-supplied `stream_fn`, so that HTTP clients (`httpx`,
           `aiohttp`, ...) tear down the underlying socket immediately
           instead of waiting for the next provider event to arrive.
        3. The consumer task (`_body` inside `_drive_loop`) is cancelled so
           the awaiting `prompt()` returns promptly with a synthesized
           aborted assistant message.

        Cancellation paths (1) and (2) close the network resource; (3)
        unblocks the caller. All three are idempotent.
        """
        if self._abort_controller is not None:
            self._abort_controller.abort()
        if self._active_stream is not None:
            self._active_stream.cancel()
        if self._run_task is not None and not self._run_task.done():
            self._run_task.cancel()

    async def wait_for_idle(self) -> None:
        """Wait until the current `prompt`/`continue_` run (if any) finishes."""
        fut = self._running_prompt
        if fut is not None and not fut.done():
            await fut

    def reset(self) -> None:
        """Clear messages, queues, and transient run state."""
        self._state.messages = []
        self._state.is_streaming = False
        self._state.stream_message = None
        self._state.pending_tool_calls = set()
        self._state.error = None
        self._steering_queue = []
        self._follow_up_queue = []

    # ------------------------------------------------------------------
    # prompt / continue_
    # ------------------------------------------------------------------

    async def prompt(
        self,
        input_: str | AgentMessage | list[AgentMessage],
    ) -> None:
        """Send a user prompt and run the loop until it completes.

        Raises `RuntimeError` if a prompt is already in flight; queue messages
        with `steer()` or `follow_up()` instead. The method returns once the
        loop emits `agent_end` (or an error synthesizes one).
        """

        if self._state.is_streaming:
            raise RuntimeError(
                "Agent is already processing a prompt. Use steer() or follow_up() "
                "to queue messages, or await wait_for_idle() before prompting again."
            )

        if self._state.model is None:
            raise RuntimeError("No model configured")

        if isinstance(input_, list):
            msgs: list[AgentMessage] = list(input_)
        elif isinstance(input_, str):
            from agent.pi.ai.types import UserMessage

            msgs = [
                UserMessage(
                    role="user",
                    content=[TextContent(type="text", text=input_)],
                    timestamp=now_ms(),
                )
            ]
        else:
            msgs = [input_]

        await self._drive_loop(msgs)

    async def continue_(self) -> None:
        """Continue from existing state without a new user message.

        Behavior depends on whether the last message in `state.messages` is
        an assistant message:

        - **Last message is assistant** (typical mid-conversation state):
          drains the steering queue first, then the follow-up queue. If
          *both* queues are empty this raises `RuntimeError`, because LLM
          providers reject contexts that end with an assistant turn — there
          is no valid next step to take.
        - **Last message is anything else** (user / toolResult): re-enters
          the loop from the current context without injecting a new
          message. Useful when the previous run ended on a non-assistant
          message and you want the model to take the next turn.

        Note: a synthesized error from a prior abort/exception ends with an
        assistant message (`stop_reason="error"` / `"aborted"`), so calling
        `continue_()` immediately after an error without queueing anything
        will raise. To retry after an error, queue a follow-up first or
        call `prompt(...)` with a new user message.
        """

        if self._state.is_streaming:
            raise RuntimeError(
                "Agent is already processing. Wait for completion before continuing."
            )

        messages = self._state.messages
        if not messages:
            raise RuntimeError("No messages to continue from")

        if messages[-1].role == "assistant":
            queued_steering = self._dequeue_steering_messages()
            if queued_steering:
                await self._drive_loop(queued_steering, skip_initial_steering_poll=True)
                return
            queued_follow_up = self._dequeue_follow_up_messages()
            if queued_follow_up:
                await self._drive_loop(queued_follow_up)
                return
            raise RuntimeError("Cannot continue from message role: assistant")

        await self._drive_loop(None)

    # ------------------------------------------------------------------
    # Core driver
    # ------------------------------------------------------------------

    async def _drive_loop(
        self,
        messages: list[AgentMessage] | None,
        *,
        skip_initial_steering_poll: bool = False,
    ) -> None:
        model = self._state.model
        if model is None:
            raise RuntimeError("No model configured")

        loop = asyncio.get_running_loop()
        self._running_prompt = loop.create_future()

        self._abort_controller = AbortController()
        # Local alias so closures below don't trip pyright's optional-attribute
        # check on `self._abort_controller` (which is typed `| None`).
        abort_controller = self._abort_controller
        self._state.is_streaming = True
        self._state.stream_message = None
        self._state.error = None

        reasoning: ThinkingLevel | None = (
            None if self._state.thinking_level == "off" else self._state.thinking_level
        )

        context = AgentContext(
            system_prompt=self._state.system_prompt,
            messages=list(self._state.messages),
            tools=list(self._state.tools) or None,
        )

        # Closure-local flag so the Agent-level getSteeringMessages can skip
        # its first poll when `continue_()` already drained the queue.
        skip_first_poll = [skip_initial_steering_poll]

        async def _get_steering() -> list[AgentMessage]:
            if skip_first_poll[0]:
                skip_first_poll[0] = False
                return []
            return self._dequeue_steering_messages()

        async def _get_follow_up() -> list[AgentMessage]:
            return self._dequeue_follow_up_messages()

        config = AgentLoopConfig(
            model=model,
            reasoning=reasoning,
            session_id=self._session_id,
            on_payload=self._on_payload,
            transport=self._transport,
            thinking_budgets=self._thinking_budgets,
            max_retry_delay_ms=self._max_retry_delay_ms,
            convert_to_llm=self._convert_to_llm,
            transform_context=self._transform_context,
            get_api_key=self.get_api_key,
            get_steering_messages=_get_steering,
            get_follow_up_messages=_get_follow_up,
        )

        async def _body() -> None:
            partial: AgentMessage | None = None
            stream = (
                agent_loop(messages, context, config, abort_controller.signal, self.stream_fn)
                if messages
                else agent_loop_continue(
                    context, config, abort_controller.signal, self.stream_fn
                )
            )
            # Publish the stream so abort() can cascade cancellation into the
            # producer task (and from there into stream_fn / the underlying
            # HTTP connection).
            self._active_stream = stream

            async for event in stream:
                self._apply_event_to_state(event, partial_slot := [partial])
                partial = partial_slot[0]
                self._emit(event)

            # Flush any remaining non-empty partial assistant message into state.
            if (
                partial is not None
                and isinstance(partial, AssistantMessage)
                and partial.content
            ):
                only_empty = not any(
                    (c.type == "thinking" and c.thinking.strip())
                    or (c.type == "text" and c.text.strip())
                    or (c.type == "toolCall" and c.name.strip())
                    for c in partial.content
                )
                if not only_empty:
                    self.append_message(partial)
                elif abort_controller.signal.aborted:
                    raise RuntimeError("Request was aborted")

        task = asyncio.create_task(_body())
        self._run_task = task

        try:
            await task
        except asyncio.CancelledError:
            # Distinguish explicit `agent.abort()` from external cancellation
            # (`asyncio.wait_for` timeouts, parent-task cancel, etc.). User
            # aborts resolve `prompt()` normally with an aborted message;
            # external cancellations re-raise so outer machinery can unwind.
            user_aborted = (
                self._abort_controller is not None and self._abort_controller.signal.aborted
            )
            if user_aborted:
                error_msg = _synth_error_assistant(
                    model=model, aborted=True, error="Request aborted by user"
                )
                self.append_message(error_msg)
                self._state.error = "Request aborted by user"
                from agent.pi.core.types import AgentEnd

                self._emit(AgentEnd(messages=[error_msg]))
            else:
                raise
        except Exception as exc:  # noqa: BLE001
            error_msg = _synth_error_assistant(
                model=model,
                aborted=(
                    self._abort_controller is not None and self._abort_controller.signal.aborted
                ),
                error=str(exc),
            )
            self.append_message(error_msg)
            self._state.error = str(exc)
            from agent.pi.core.types import AgentEnd

            self._emit(AgentEnd(messages=[error_msg]))
        finally:
            self._run_task = None
            self._active_stream = None
            self._state.is_streaming = False
            self._state.stream_message = None
            self._state.pending_tool_calls = set()
            self._abort_controller = None
            if self._running_prompt is not None and not self._running_prompt.done():
                self._running_prompt.set_result(None)
            self._running_prompt = None

    # ------------------------------------------------------------------
    # Per-event state updates
    # ------------------------------------------------------------------

    def _apply_event_to_state(
        self,
        event: AgentEvent,
        partial_slot: list[AgentMessage | None],
    ) -> None:
        """Update `_state` for one event. `partial_slot` is a 1-elem mutable cell.

        Using a slot keeps the partial reference in sync across iterations
        without relying on the caller to re-assign after every branch.
        """
        etype = event.type
        if etype == "message_start":
            partial_slot[0] = event.message  # type: ignore[attr-defined]
            self._state.stream_message = event.message  # type: ignore[attr-defined]
            return
        if etype == "message_update":
            partial_slot[0] = event.message  # type: ignore[attr-defined]
            self._state.stream_message = event.message  # type: ignore[attr-defined]
            return
        if etype == "message_end":
            partial_slot[0] = None
            self._state.stream_message = None
            self.append_message(event.message)  # type: ignore[attr-defined]
            return
        if etype == "tool_execution_start":
            pending = set(self._state.pending_tool_calls)
            pending.add(event.tool_call_id)  # type: ignore[attr-defined]
            self._state.pending_tool_calls = pending
            return
        if etype == "tool_execution_update":
            # Partial tool result; subscribers may render progress but
            # nothing on AgentState changes for in-flight updates.
            return
        if etype == "tool_execution_end":
            pending = set(self._state.pending_tool_calls)
            pending.discard(event.tool_call_id)  # type: ignore[attr-defined]
            self._state.pending_tool_calls = pending
            return
        if etype == "turn_end":
            msg = event.message  # type: ignore[attr-defined]
            if isinstance(msg, AssistantMessage) and msg.error_message:
                self._state.error = msg.error_message
            return
        if etype == "agent_end":
            self._state.is_streaming = False
            self._state.stream_message = None
            return


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _synth_error_assistant(
    *,
    model: Model,
    aborted: bool,
    error: str,
) -> AssistantMessage:
    """Construct the assistant message used when the loop raises.

    Matches the TS `errorMsg` object shape in `agent.ts` — a single empty text
    block with `stop_reason` of `aborted`/`error` and the error message set.
    """
    return AssistantMessage(
        role="assistant",
        content=[TextContent(type="text", text="")],
        api=model.api,
        provider=model.provider,
        model=model.id,
        usage=Usage(cost=UsageCost()),
        stop_reason="aborted" if aborted else "error",
        error_message=error,
        timestamp=now_ms(),
    )


__all__ = ["Agent", "QueueMode"]
