# Apps

## Multi-agent generator / evaluator loop (Streamlit)

Headless `cursor-agent` runs for the implementer and evaluator, with a human review gate between iterations.

### Start the app

From the **skills repository root**:

```bash
uv sync --project dev/apps
uv run --project dev/apps multi-agent-generator-evaluator-loop
```

The first command installs dependencies into `dev/apps/.venv` (run again when `pyproject.toml` changes). The second starts Streamlit and opens the UI in your browser.

While `cursor-agent` runs, the app **auto-refreshes about once per second** so the page does not look frozen (the subprocess runs in a background thread).

### Optional

- **From inside `dev/apps/`:** `uv sync` then `uv run multi-agent-generator-evaluator-loop`.
- **Streamlit flags** (example):  
  `uv run --project dev/apps multi-agent-generator-evaluator-loop -- --server.headless true`

### Requirements

- [`uv`](https://docs.astral.sh/uv/) for installs and `uv run`.
- [`cursor-agent`](https://cursor.com/) on your `PATH` (or set `CURSOR_AGENT_CMD`) so implementer/evaluator steps can run.

Run artifacts are written under `multi_agent_generator_evaluator_loop/runs/` (gitignored).

### Artifacts in the UI

- During a run, open **“Live run folder (markdown preview)”** to see `goal.md`, `dod.md`, and any files the agent has already written (e.g. `reasoning.md`). New tabs appear as files show up on disk.
- **Live cursor-agent stream log** shows stdout/stderr as it is written to `logs/live-implement-iter-*.log` or `logs/live-evaluate-iter-*.log`.
- **Agent logs (`logs/*.log`)** lists every log file for the run (live streams plus `implementer-iter-*.log` / `evaluator-iter-*.log` after completion).
- **Workflow checkpoints** in the sidebar record **CP1–CP5** with timestamps so you can compare **CP2→CP3** (implementer duration) vs **CP4→CP5** (evaluator duration).
- After the implementer finishes, the **“Artifacts after implementer”** section lists the same `.md` files. If you only see goal/dod, the agent did not create `reasoning.md` / `plan.md` — check the logs under `runs/.../logs/`.

### Why runs can feel slow

`cursor-agent` runs a **full agent loop** (tools, codebase context), not one chat completion. For small tasks, point **Workspace root** at a **small directory** and optionally use a faster `CURSOR_AGENT_MODEL` (`cursor-agent --list-models`).

## Weather forecast CLI

Fetch a 7-day forecast for a named location using Open-Meteo's geocoding and forecast APIs.
The output includes daily high/low temperatures in Celsius plus daily low/max wind speeds.

### Run the CLI

From the skills repository root:

```bash
uv run --project dev/apps weather-forecast --location "Moraga, CA"
```

Optional flags:

- `--days 10` to request a different forecast window (up to the API limit).
- `--json` to print the resolved location and daily forecast as JSON.
