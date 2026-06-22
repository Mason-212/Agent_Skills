"""Command-line entry point for `agent.pi.coding_agent`.

Usage:

    python -m agent.pi.coding_agent [--cwd DIR]
                                         [--model PROVIDER/MODEL]
                                         [--tools read,bash,edit,write]
                                         [--extension PATH] [--extension PATH]
                                         [--skill-path PATH]
                                         [--print]
                                         [--json]
                                         [--api-key KEY]
                                         [--system-prompt TEXT]
                                         [--append-system-prompt TEXT]
                                         PROMPT

Only non-interactive "print" mode is shipped. The optional ``--json``
flag switches the output format to newline-delimited JSON events.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Iterable

from ..ai.models_catalog.catalog import get_model
from ..ai.types import Model
from .defaults import ALL_TOOL_NAMES
from .modes.print_mode import PrintModeOptions, run_print_mode


def _resolve_model(spec: str) -> Model:
    """Resolve `provider/model` spec via the pi-ai catalog."""
    if "/" not in spec:
        raise SystemExit(f"Model spec must be 'provider/model_id', got: {spec}")
    provider, model_id = spec.split("/", 1)
    model = get_model(provider, model_id)
    if model is None:
        raise SystemExit(f"Unknown model: {spec}")
    return model


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pi-coding-agent-py",
        description="Non-interactive Python port of pi-coding-agent.",
    )
    p.add_argument("prompt", help="Prompt text (use - to read from stdin)")
    p.add_argument("--cwd", help="Working directory (default: current dir)")
    p.add_argument(
        "--model",
        default="anthropic/claude-sonnet-4-20250514",
        help="Provider/model id (default: anthropic/claude-sonnet-4-20250514)",
    )
    p.add_argument(
        "--tools",
        help=f"Comma-separated pi tool names to enable. Known: {', '.join(ALL_TOOL_NAMES)}. Default: all enabled.",
    )
    p.add_argument("--extension", action="append", default=[], help="Path to extension .py file (repeatable)")
    p.add_argument("--skill-path", action="append", default=[], help="Path to skill file or dir (repeatable)")
    p.add_argument("--print", action="store_true", help="Print mode (default; kept for compat)")
    p.add_argument("--json", action="store_true", help="Emit newline-delimited JSON event stream")
    p.add_argument("--api-key", help="API key override (otherwise resolved by provider env vars)")
    p.add_argument("--system-prompt", help="Replace the default system prompt")
    p.add_argument("--append-system-prompt", help="Append to the default system prompt")
    return p


def _read_prompt(raw: str) -> str:
    if raw == "-":
        return sys.stdin.read()
    return raw


def _main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    prompt = _read_prompt(args.prompt)
    model = _resolve_model(args.model)
    options = PrintModeOptions(
        prompt=prompt,
        model=model,
        cwd=args.cwd,
        include_pi_tools=args.tools != "none" if args.tools else True,
        output_format="json" if args.json else "text",
        stream_events=args.json,
        extension_paths=list(args.extension),
        skill_paths=list(args.skill_path),
        api_key=args.api_key,
        custom_system_prompt=args.system_prompt,
        append_system_prompt=args.append_system_prompt,
    )
    return asyncio.run(run_print_mode(options))


def main() -> None:
    raise SystemExit(_main())


if __name__ == "__main__":
    main()


__all__ = ["build_parser", "main"]
