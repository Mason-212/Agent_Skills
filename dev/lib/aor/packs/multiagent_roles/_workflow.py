"""Role-based multi-agent workflow.

DAG shape (default):
    product_manager → engineer → reviewer

Each node is a CallableExecutor wrapping a fresh AgentSession with a role-specific
pack-prompt. Agents communicate via run_state.working_memory["thread"], a list of
{"role": str, "content": str} dicts appended by each node.

WorkflowRequest fields:
    text (str): the initial task brief
    metadata.role_sequence (list[str]): ordered role names (default: see DEFAULT_ROLES)
    metadata.role_prompts (dict[str, str]): optional overrides for individual role definitions
    metadata.model (str): LLM model ID
    metadata.provider (str): LLM provider
    metadata.api_key (str): API key (falls back to AOR_API_KEY env var)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

DEFAULT_ROLES = ["product_manager", "engineer", "reviewer"]
_AGENTS_DIR = Path(__file__).parent / "agents"
_MEM_THREAD = "thread"


class RolesWorkflowMixin:
    """Workflow nodes and WorkflowSpec wiring for RolesPack."""

    def _build_roles_workflow(self, role_sequence: list[str]) -> Any:
        from orchestrator import WorkflowBuilder
        from orchestrator.executors import CallableExecutor
        from orchestrator.node import WorkflowNode

        builder = WorkflowBuilder("roles")
        for i, role in enumerate(role_sequence):
            next_nodes = (role_sequence[i + 1],) if i + 1 < len(role_sequence) else ()
            builder.add_node(WorkflowNode(
                name=role,
                executor=CallableExecutor(self._make_role_node(role)),
                allowed_next_nodes=next_nodes,
            ))
        builder.set_start(role_sequence[0])
        return builder.build()

    def _make_role_node(self, role: str):
        """Return an async callable for this role."""
        async def _node(ctx: Any) -> Any:
            from orchestrator.types import StepResult, StepStatus

            metadata = ctx.request.metadata
            thread: list[dict] = ctx.run_state.working_memory.get(_MEM_THREAD, [])

            # Load system prompt: metadata override > file > fallback
            if metadata.get("role_prompts", {}).get(role):
                system_prompt = metadata["role_prompts"][role]
            else:
                prompt_file = _AGENTS_DIR / role / "ROLE.md"
                system_prompt = prompt_file.read_text() if prompt_file.exists() else f"You are the {role}."

            # Build user prompt from thread history
            if thread:
                history = "\n\n".join(f"## {entry['role']}\n{entry['content']}" for entry in thread)
                user_prompt = f"Thread so far:\n\n{history}\n\nOriginal task: {ctx.request.text}\n\nNow respond as the {role}."
            else:
                user_prompt = f"Task: {ctx.request.text}\n\nRespond as the {role}."

            from agent.tracing import node_span
            with node_span(role, thread_length=len(thread), prompt_length=len(user_prompt)) as span:
                content = await self._call_llm(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    metadata=metadata,
                )
                span.set_attribute("aor.response_length", len(content))

            thread = list(thread) + [{"role": role, "content": content}]
            ctx.run_state.working_memory[_MEM_THREAD] = thread

            return StepResult(
                status=StepStatus.SUCCESS,
                summary=f"{role}: {content[:120]}",
                output={"role": role, "content": content, "thread": thread},
            )
        _node.__name__ = f"_node_{role}"
        return _node

    async def _call_llm(self, *, system_prompt: str, user_prompt: str, metadata: dict) -> str:
        from agent import config as aor_config
        from agent.pi.ai import Context, UserMessage, complete_simple
        from agent.pi.ai.models_catalog.catalog import get_model
        from agent.pi.ai.types import SimpleStreamOptions, TextContent
        from agent.tracing import llm_span

        if not aor_config._loaded:
            aor_config.load()

        provider = metadata.get("provider", aor_config.PROVIDER)
        model_id = metadata.get("model", aor_config.MODEL)
        api_key = metadata.get("api_key", aor_config.API_KEY)

        model = get_model(provider, model_id)
        if model is None:
            raise ValueError(f"Model {provider}/{model_id} not found in catalog")

        context = Context(
            system_prompt=system_prompt,
            messages=[UserMessage(content=user_prompt, timestamp=0)],
        )
        options = SimpleStreamOptions(api_key=api_key) if api_key else None

        with llm_span(provider=provider, model=model_id, prompt_length=len(user_prompt)) as span:
            response = await complete_simple(model, context, options)
            text = " ".join(
                block.text for block in getattr(response, "content", [])
                if isinstance(block, TextContent)
            ).strip()
            span.set_attribute("aor.response_length", len(text))

        return text
