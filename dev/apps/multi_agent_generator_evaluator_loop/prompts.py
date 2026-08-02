"""Prompt templates for headless cursor-agent invocations."""

from __future__ import annotations

from pathlib import Path


def rubric_line_from_selection(selected: list[int]) -> str:
    """Map 1–5 to critique-me style Rubrics: line; all five → Rubrics: all."""
    if not selected:
        return "Rubrics: 1,2,3"
    s = sorted(set(selected))
    if s == [1, 2, 3, 4, 5]:
        return "Rubrics: all"
    return "Rubrics: " + ",".join(str(x) for x in s)


def implementor_prompt(
    *,
    run_dir: Path,
    workspace: Path,
    iteration: int,
    repo_root: Path,
) -> str:
    run_dir = run_dir.resolve()
    workspace = workspace.resolve()
    repo_root = repo_root.resolve()
    prev = iteration - 1
    critique_path = run_dir / f"critique-iter-{prev}.md"
    critique_clause = ""
    if prev >= 1 and critique_path.exists():
        critique_clause = (
            f"\nRead the prior critique at {critique_path} and address **must-fix** "
            "items before new work. Do not argue with the critique in prose; implement fixes.\n"
        )

    return f"""You are the **implementer** agent (Pattern C — independent context).

**Workspace root** (make code and repo changes here): {workspace}
**Task folder** (artifacts only here unless you must reference paths): {run_dir}

Read:
- {run_dir / "goal.md"}
- {run_dir / "dod.md"}
{critique_clause}
**This is iteration {iteration}.**

Deliverables:
1. **Always** write **{run_dir / "reasoning.md"}** (create or overwrite) **early in your run**, even for tiny tasks — at least a short paragraph: what you changed, file paths, and how it maps to dod.md. The operator watches this file in the UI.
2. If the task is non-trivial, write or update **{run_dir / "plan.md"}** (approach, milestones, open questions). For tiny tasks you may skip plan.md.
3. Implement changes under **{workspace}** so that progress moves toward satisfying **dod.md**. Prefer minimal, reviewable diffs. For a trivial goal, do the **smallest** change that satisfies dod.md and stop — do not explore the whole repo unnecessarily.

Constraints:
- Keep narrative artifacts under {run_dir}; production code under {workspace}.
- If critique-me rubric **code-quality** will run later, ensure there is real code in scope when applicable.
- The critique-me skill and rubric files live under {repo_root / "skills" / "critique-me"} if you need context (do not duplicate entire rubrics into reasoning.md).

When finished, give a short summary of files touched and whether any must-fix items remain unaddressed.
"""


def evaluator_prompt(
    *,
    run_dir: Path,
    workspace: Path,
    iteration: int,
    repo_root: Path,
    rubric_line: str,
    extra_scan_paths: str,
) -> str:
    run_dir = run_dir.resolve()
    workspace = workspace.resolve()
    repo_root = repo_root.resolve()
    out_file = run_dir / f"critique-iter-{iteration}.md"

    scan_note = ""
    if extra_scan_paths.strip():
        scan_note = (
            "\n**Additional scan roots** (from operator; apply the same file caps):\n"
            f"{extra_scan_paths.strip()}\n"
        )

    return f"""You are the **evaluator** agent (Pattern C — independent context). Apply the **critique-me** skill procedure and output format.

{rubric_line}

**Rubric definitions** (read only those needed for the numbers above): directory
{repo_root / "skills" / "critique-me" / "resources" / "rubrics"}

**Artifacts to read first** (paths):
- {run_dir / "goal.md"}
- {run_dir / "dod.md"}
- {run_dir / "reasoning.md"}
- {run_dir / "plan.md"} (if it exists)

**Code / repo scope for critique:** start from workspace root **{workspace}**. Respect critique-me caps: at most **20 files** total and **depth 2** from each listed directory unless the operator raised the cap in this message.{scan_note}

**Output:** Write the **complete** critique to this file (overwrite if present): **{out_file}**

Use critique-me section order: **Framing**, then selected rubric sections (1–5), then **Recommendations** (numbered; tag **must-fix** vs **later**). In Framing, list rubrics used and which paths were read; note if caps truncated scope.

Do not implement fixes — critique only. After writing the file, print a one-line confirmation with the absolute path.
"""
