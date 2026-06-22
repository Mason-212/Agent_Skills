"""Skill discovery + validation + prompt formatting.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/skills.ts`.

Design notes
------------
- Skills are markdown files with YAML frontmatter. Discovery walks both a
  project-local `.pi/skills/` and a global `{agent_dir}/skills/` tree.
- Top-level `.md` files under a skills root are loaded; nested directories
  must carry a `SKILL.md` file (matches upstream recursive discovery).
- `disable_model_invocation: true` excludes a skill from the system prompt
  (it can still be invoked via explicit `/skill:name` commands in upstream;
  in this Python port those commands are out of scope but the flag is
  retained for parity).
- Validation diagnostics mirror upstream: name regex, length limits,
  description presence/length. Skills with missing descriptions are dropped
  entirely; other warnings are surfaced but skills still load.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Literal

from .config import CONFIG_DIR_NAME, get_agent_dir
from .utils.frontmatter import parse_frontmatter

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024

_NAME_RE = re.compile(r"^[a-z0-9-]+$")


DiagnosticType = Literal["warning", "collision"]


@dataclass
class ResourceDiagnostic:
    type: DiagnosticType
    message: str
    path: str


@dataclass
class Skill:
    name: str
    description: str
    file_path: str
    base_dir: str
    source: str
    disable_model_invocation: bool = False


@dataclass
class LoadSkillsResult:
    skills: list[Skill] = field(default_factory=list)
    diagnostics: list[ResourceDiagnostic] = field(default_factory=list)


def _validate_name(name: str, parent_dir_name: str) -> list[str]:
    errors: list[str] = []
    if name != parent_dir_name:
        errors.append(f'name "{name}" does not match parent directory "{parent_dir_name}"')
    if len(name) > MAX_NAME_LENGTH:
        errors.append(f"name exceeds {MAX_NAME_LENGTH} characters ({len(name)})")
    if not _NAME_RE.match(name):
        errors.append("name contains invalid characters (must be lowercase a-z, 0-9, hyphens only)")
    if name.startswith("-") or name.endswith("-"):
        errors.append("name must not start or end with a hyphen")
    if "--" in name:
        errors.append("name must not contain consecutive hyphens")
    return errors


def _validate_description(description: str | None) -> list[str]:
    errors: list[str] = []
    if not description or not description.strip():
        errors.append("description is required")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"description exceeds {MAX_DESCRIPTION_LENGTH} characters ({len(description)})")
    return errors


def _load_skill_file(file_path: str, source: str) -> tuple[Skill | None, list[ResourceDiagnostic]]:
    diagnostics: list[ResourceDiagnostic] = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError as exc:
        diagnostics.append(ResourceDiagnostic("warning", str(exc), file_path))
        return None, diagnostics

    parsed = parse_frontmatter(raw)
    fm = parsed.frontmatter
    skill_dir = os.path.dirname(file_path)
    parent = os.path.basename(skill_dir)

    desc = str(fm.get("description", "")) if fm.get("description") is not None else ""
    for err in _validate_description(desc or None):
        diagnostics.append(ResourceDiagnostic("warning", err, file_path))

    if not desc.strip():
        return None, diagnostics

    name = str(fm.get("name", "") or parent)
    for err in _validate_name(name, parent):
        diagnostics.append(ResourceDiagnostic("warning", err, file_path))

    disable = bool(fm.get("disable-model-invocation", False))

    return (
        Skill(
            name=name,
            description=desc,
            file_path=os.path.abspath(file_path),
            base_dir=os.path.abspath(skill_dir),
            source=source,
            disable_model_invocation=disable,
        ),
        diagnostics,
    )


def _load_from_dir(dir_path: str, source: str, include_root_md: bool) -> LoadSkillsResult:
    result = LoadSkillsResult()
    if not os.path.isdir(dir_path):
        return result
    try:
        entries = sorted(os.listdir(dir_path))
    except OSError:
        return result
    for name in entries:
        if name.startswith(".") or name == "node_modules" or name == "__pycache__":
            continue
        full = os.path.join(dir_path, name)
        if os.path.isdir(full):
            sub = _load_from_dir(full, source, include_root_md=False)
            result.skills.extend(sub.skills)
            result.diagnostics.extend(sub.diagnostics)
            continue
        if not os.path.isfile(full):
            continue
        if include_root_md and name.endswith(".md"):
            pass
        elif not include_root_md and name == "SKILL.md":
            pass
        else:
            continue
        skill, diags = _load_skill_file(full, source)
        result.diagnostics.extend(diags)
        if skill is not None:
            result.skills.append(skill)
    return result


def load_skills(
    *,
    cwd: str | None = None,
    agent_dir: str | None = None,
    skill_paths: list[str] | None = None,
    include_defaults: bool = True,
) -> LoadSkillsResult:
    """Discover skills from project-local, user-global, and explicit paths."""
    resolved_cwd = cwd or os.getcwd()
    resolved_agent = agent_dir or str(get_agent_dir())
    skill_paths = skill_paths or []

    merged: dict[str, Skill] = {}
    diagnostics: list[ResourceDiagnostic] = []

    def _add(res: LoadSkillsResult) -> None:
        diagnostics.extend(res.diagnostics)
        for s in res.skills:
            existing = merged.get(s.name)
            if existing:
                diagnostics.append(
                    ResourceDiagnostic(
                        "collision",
                        f'name "{s.name}" collision; winner={existing.file_path} loser={s.file_path}',
                        s.file_path,
                    )
                )
            else:
                merged[s.name] = s

    if include_defaults:
        _add(_load_from_dir(os.path.join(resolved_agent, "skills"), "user", include_root_md=True))
        _add(
            _load_from_dir(
                os.path.join(resolved_cwd, CONFIG_DIR_NAME, "skills"),
                "project",
                include_root_md=True,
            )
        )

    for raw in skill_paths:
        expanded = os.path.expanduser(raw.strip())
        resolved = expanded if os.path.isabs(expanded) else os.path.join(resolved_cwd, expanded)
        if not os.path.exists(resolved):
            diagnostics.append(ResourceDiagnostic("warning", "skill path does not exist", resolved))
            continue
        if os.path.isdir(resolved):
            _add(_load_from_dir(resolved, "path", include_root_md=True))
        elif resolved.endswith(".md"):
            skill, diags = _load_skill_file(resolved, "path")
            diagnostics.extend(diags)
            if skill is not None:
                _add(LoadSkillsResult(skills=[skill]))
        else:
            diagnostics.append(ResourceDiagnostic("warning", "skill path is not a markdown file", resolved))

    return LoadSkillsResult(skills=list(merged.values()), diagnostics=diagnostics)


def _escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def format_skills_for_prompt(skills: list[Skill]) -> str:
    """Render loaded skills into the `<available_skills>` block used by the system prompt."""
    visible = [s for s in skills if not s.disable_model_invocation]
    if not visible:
        return ""
    lines = [
        "\n\nThe following skills provide specialized instructions for specific tasks.",
        "Use the read tool to load a skill's file when the task matches its description.",
        "When a skill file references a relative path, resolve it against the skill directory (parent of SKILL.md / dirname of the path) and use that absolute path in tool commands.",
        "",
        "<available_skills>",
    ]
    for s in visible:
        lines.append("  <skill>")
        lines.append(f"    <name>{_escape_xml(s.name)}</name>")
        lines.append(f"    <description>{_escape_xml(s.description)}</description>")
        lines.append(f"    <location>{_escape_xml(s.file_path)}</location>")
        lines.append("  </skill>")
    lines.append("</available_skills>")
    return "\n".join(lines)


__all__ = [
    "LoadSkillsResult",
    "MAX_DESCRIPTION_LENGTH",
    "MAX_NAME_LENGTH",
    "ResourceDiagnostic",
    "Skill",
    "format_skills_for_prompt",
    "load_skills",
]
