"""Executor adapters for workflow nodes.

Choose the adapter based on where the execution loop already lives:
- `CallableExecutor` for deterministic Python orchestration.
- `LLMSingleShotExecutor` for one-shot calls into `agent.pi.ai`.
- `AgentLoopExecutor` for multi-turn `agent.pi.core` sessions.
- `MoiraiAgentExecutor` when a Moirai-style agent already owns its own loop.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

from agent.pi.ai import Context as PiContext
from agent.pi.ai import UserMessage as PiUserMessage
from agent.pi.ai import complete_simple
from agent.pi.ai.types import AssistantMessage, TextContent
from agent.pi.core import Agent as PiCoreAgent
from agent.pi.core import AgentMessage as PiCoreAgentMessage

from .context import WorkflowNodeExecutionContext
from .types import StepResult, StepStatus

_log = logging.getLogger(__name__)


@runtime_checkable
class ExecutorAdapter(Protocol):
    """Stable adapter boundary between workflow nodes and lower layers."""

    async def execute(self, context: WorkflowNodeExecutionContext) -> StepResult: ...

class CallableExecutor:
    """Adapter for deterministic Python callables and local business logic."""

    def __init__(
        self,
        func: Callable[[WorkflowNodeExecutionContext], StepResult | Awaitable[StepResult]],
    ) -> None:
        self._func = func

    async def execute(self, context: WorkflowNodeExecutionContext) -> StepResult:
        result = self._func(context)
        if inspect.isawaitable(result):
            return await result
        return result


class LLMSingleShotExecutor:
    """Single-turn executor backed directly by `agent.pi.ai`.

    ``options`` sets static call options (temperature, max_tokens, etc.).
    ``options_builder`` is a callable that receives the execution context and
    returns options at call time — use this when options depend on runtime
    values such as ``api_key`` stored in ``working_memory``. If both are
    provided, ``options_builder`` takes precedence.
    """

    def __init__(
        self,
        *,
        model: Any,
        prompt_builder: Callable[[WorkflowNodeExecutionContext], str],
        system_prompt: str | None = None,
        parser: Callable[[Any, WorkflowNodeExecutionContext], StepResult] | None = None,
        options: Any | None = None,
        options_builder: Callable[[WorkflowNodeExecutionContext], Any] | None = None,
    ) -> None:
        self._model = model
        self._prompt_builder = prompt_builder
        self._system_prompt = system_prompt
        self._parser = parser
        self._options = options
        self._options_builder = options_builder

    async def execute(self, context: WorkflowNodeExecutionContext) -> StepResult:
        prompt = self._prompt_builder(context)
        llm_context = PiContext(
            system_prompt=self._system_prompt,
            messages=[PiUserMessage(content=prompt, timestamp=0)],
        )
        options = self._options_builder(context) if self._options_builder is not None else self._options
        response = await complete_simple(self._model, llm_context, options)
        if self._parser is not None:
            return self._parser(response, context)

        return StepResult(
            status=StepStatus.SUCCESS,
            summary=_assistant_text(response.model_dump(by_alias=True)),
            output=response.model_dump(by_alias=True),
        )


class AgentLoopExecutor:
    """Adapter seam for multi-turn `agent.pi.core` sessions."""

    def __init__(
        self,
        runner: Callable[[WorkflowNodeExecutionContext], StepResult | Awaitable[StepResult]] | None = None,
        *,
        agent: PiCoreAgent | None = None,
        input_builder: Callable[
            [WorkflowNodeExecutionContext],
            str | PiCoreAgentMessage | list[PiCoreAgentMessage] | None,
        ]
        | None = None,
        parser: Callable[[PiCoreAgent, WorkflowNodeExecutionContext], StepResult] | None = None,
    ) -> None:
        self._runner = runner
        self._agent = agent
        self._input_builder = input_builder
        self._parser = parser

    async def execute(self, context: WorkflowNodeExecutionContext) -> StepResult:
        if self._runner is not None:
            result = self._runner(context)
            if inspect.isawaitable(result):
                return await result
            return result

        if self._agent is None:
            raise NotImplementedError(
                "AgentLoopExecutor requires either a runner or a pi.core Agent instance."
            )

        pi_events: list[dict[str, Any]] = []

        def _safe_collect(event: Any) -> None:
            try:
                pi_events.append(event.model_dump(by_alias=True))
            except Exception:  # noqa: BLE001 — best-effort collection; serialization failures must not crash the agent loop
                _log.warning("AgentLoopExecutor: failed to serialize AgentEvent %r", event)

        unsubscribe = self._agent.subscribe(_safe_collect)
        try:
            payload = self._input_builder(context) if self._input_builder is not None else context.request.text
            if payload is None:
                await self._agent.continue_()
            else:
                await self._agent.prompt(payload)
        finally:
            unsubscribe()

        working_memory = dict(context.run_state.working_memory)
        working_memory["pi_agent_events"] = pi_events
        context.run_state = context.run_state.model_copy(
            update={"working_memory": working_memory}
        )

        if self._parser is not None:
            return self._parser(self._agent, context)

        return _pi_agent_core_result(self._agent)


class MoiraiAgentExecutor:
    """Adapter for Moirai-style agents that already own tools, skills, or loops."""

    def __init__(
        self,
        *,
        agent: Any,
        input_builder: Callable[[WorkflowNodeExecutionContext], Any],
        parser: Callable[[Any, WorkflowNodeExecutionContext], StepResult] | None = None,
    ) -> None:
        self._agent = agent
        self._input_builder = input_builder
        self._parser = parser

    async def execute(self, context: WorkflowNodeExecutionContext) -> StepResult:
        payload = self._input_builder(context)
        response = await self._agent.run(payload)
        if self._parser is not None:
            return self._parser(response, context)

        response_content = getattr(response, "content", None)
        response_metadata = getattr(response, "metadata", {})
        return StepResult(
            status=StepStatus.SUCCESS,
            summary=str(response_content) if response_content is not None else None,
            output={
                "content": response_content,
                "metadata": response_metadata,
            },
            diagnostics={"executor": "moirai"},
        )


def _assistant_text(response: dict[str, Any]) -> str | None:
    content = response.get("content")
    if not isinstance(content, list):
        return None
    text_blocks = [
        block.get("text")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    joined = "".join(text for text in text_blocks if isinstance(text, str)).strip()
    return joined or None


def _pi_agent_core_result(agent: PiCoreAgent) -> StepResult:
    last_assistant = _last_assistant_message(agent)
    summary = _assistant_message_text(last_assistant)
    error_message = agent.state.error or (last_assistant.error_message if last_assistant else None)

    output: dict[str, Any] = {
        "messages": [message.model_dump(by_alias=True) for message in agent.state.messages],
        "error": agent.state.error,
        "pending_tool_calls": sorted(agent.state.pending_tool_calls),
        "session_id": agent.session_id,
    }
    if last_assistant is not None:
        output["last_assistant_message"] = last_assistant.model_dump(by_alias=True)

    return StepResult(
        status=StepStatus.FAILURE if error_message else StepStatus.SUCCESS,
        summary=error_message or summary,
        output=output,
        diagnostics={"executor": "pi_agent_core"},
    )


def _last_assistant_message(agent: PiCoreAgent) -> AssistantMessage | None:
    for message in reversed(agent.state.messages):
        if isinstance(message, AssistantMessage):
            return message
    return None


def _assistant_message_text(message: AssistantMessage | None) -> str | None:
    if message is None:
        return None
    text_blocks = [block.text for block in message.content if isinstance(block, TextContent)]
    joined = "".join(text_blocks).strip()
    return joined or None
