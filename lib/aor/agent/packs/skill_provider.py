"""SkillProvider — pack-to-agent skill injection bridge.

A SkillProvider exposes a list of filesystem paths that AgentSession merges
into its skill discovery pass via AgentSessionOptions.skill_paths.  The Pi
Agent adds the referenced SKILL.md files to the <available_skills> block in
the system prompt; the LLM reads them on demand via the read tool.

Usage (host wiring):

    from agent.packs.skill_provider import collect_skill_paths_from_pack

    skill_paths = collect_skill_paths_from_pack(pack)
    session = AgentSession(AgentSessionOptions(
        tools=pack.get_tools(session_id=session_id),
        skill_paths=skill_paths,
    ))

Usage (pack author):

    from agent.packs.skill_provider import PackSkillProvider

    def get_skill_provider(self):
        return PackSkillProvider(Path(__file__).parent / "skills")
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from agent.packs.base import BoundDomainPack


@runtime_checkable
class SkillProvider(Protocol):
    """Protocol for objects that supply skill file paths to the Pi Agent.

    Each path returned by get_skill_paths() is passed to load_skills() as a
    skill_paths entry.  It may be:
      - An absolute path to a directory of skill subdirectories
      - An absolute path to a single SKILL.md file
      - A relative path resolved against cwd at session creation time
    """

    def get_skill_paths(self) -> list[str]:
        """Return paths passed to AgentSessionOptions.skill_paths."""
        ...


@dataclass
class PackSkillProvider:
    """Standard SkillProvider pointing at a skills/ directory beside a pack.

    The skills/ directory follows the same layout as ~/.claude/skills/:
    each skill lives in its own subdirectory containing a SKILL.md with
    YAML frontmatter (name, description).

    Example pack layout::

        agents/packs/moirai/
        ├── __init__.py
        └── skills/
            └── moirai-forecast/
                └── SKILL.md
    """

    skills_dir: Path

    def get_skill_paths(self) -> list[str]:
        """Return [str(skills_dir)] if it exists, else []."""
        return [str(self.skills_dir)] if self.skills_dir.exists() else []


def collect_skill_paths_from_pack(pack: "BoundDomainPack") -> list[str]:
    """Return skill paths from pack.get_skill_provider(), or [] if None.

    Safe to call unconditionally — packs that have no SkillProvider return
    None from get_skill_provider() and this helper returns [].

    Args:
        pack: An open or unopened BoundDomainPack instance.

    Returns:
        List of path strings suitable for AgentSessionOptions.skill_paths.
    """
    provider = pack.get_skill_provider()
    if provider is None:
        return []
    return provider.get_skill_paths()
