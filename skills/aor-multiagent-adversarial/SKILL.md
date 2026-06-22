---
name: aor-multiagent-adversarial
description: Interactive generator/critic adversarial loop — guides the user through prompt, verifier script, and termination conditions, then runs the loop
---

# aor-multiagent-adversarial

Use this skill when the user wants to produce a high-quality artifact and enforce a measurable, executable quality bar before accepting the result.

## When to use

- User has a task with a clear acceptance bar they can describe (even loosely)
- The quality bar can be expressed as a runnable Python check (e.g. fetch data, compute a metric, validate structure)
- User wants iteration until output meets the bar, without doing it manually

---

## Interactive setup — walk the user through 3 steps

### Step 1: Generator prompt

Ask the user:
> "What is your task or question for the generator?"

**Important:** If the prompt involves pulling data (stocks, articles, results, etc.), check whether the user has specified a quantity. If not, ask:
> "How many candidates should the generator return? (e.g. 'top 5 NASDAQ stocks')"

Add the quantity to the prompt before storing it. Write the final prompt to `{run_dir}/generator_prompt.txt`.

Example — before:
> "Find good NASDAQ stocks to buy for long-term growth"

Example — after:
> "Find the top 5 NASDAQ stocks to buy for long-term growth"

---

### Step 2: Verifier script

Ask the user:
> "What does a good answer look like? Describe it in plain English."

Then work with the user to turn this into an executable Python verifier:

1. Ask: "Where does the data come from?" — options:
   - Local file (ask for path)
   - External API (ask which one, e.g. `yfinance`, `requests`, a URL)
   - The generator's artifact text itself (no external data needed)

2. Write `{run_dir}/verifier.py` with this contract:
   ```python
   # Called by the harness. artifact is the generator's full output text.
   # Must return (passed: bool, reason: str).
   import sys, json

   def verify(artifact: str) -> tuple[bool, str]:
       ...

   if __name__ == "__main__":
       artifact = sys.stdin.read()
       passed, reason = verify(artifact)
       print(json.dumps({"gate_passed": passed, "reason": reason}))
   ```

3. If the verifier needs packages (e.g. `yfinance`), write them to `{run_dir}/requirements.txt` and install:
   ```bash
   pip install -r {run_dir}/requirements.txt
   ```

4. Show the user the script. Ask for approval before proceeding.

#### The `reason` string is the generator's only feedback on retry

When `gate_passed` is `False`, the generator receives `reason` as its critique and rewrites based on it. A vague reason produces a vague rewrite.

**Bad reason** (generator cannot learn from this):
```
"Some stocks did not meet the criteria."
```

**Good reason** (generator knows exactly what to fix):
```
"AAPL: P/E=38 exceeds threshold of 30. MSFT: no earnings growth data available.
NVDA: passed. GOOGL: P/E=27, passed. AMZN: P/E=45, exceeds threshold.
Fix: replace AAPL and AMZN with stocks that have P/E < 30 and positive YoY earnings growth."
```

The verifier script must:
- Name each candidate that failed and the specific metric + actual value
- Explain what the generator must do differently on the next attempt
- Be as specific as possible — the generator has no other source of feedback

**Important:** If a verifier script cannot be written (criteria is purely subjective with no measurable signal), warn the user explicitly:
> "⚠️  No executable verifier could be defined. Falling back to LLM-as-critic. Results will be less reliable."

Only proceed with LLM critic after the user acknowledges this.

---

### Step 3: Termination conditions

Ask the user explicitly for **each** of the following. Do not use defaults silently — always wait for an answer. Accept "skip" or "no limit" as valid responses.

Ask these questions one at a time:

**3a. Generator retries**
> "How many times should the generator retry if the verifier rejects its output?
> (e.g. 3 — or 'no limit' to run until cost budget is exhausted)"

- `max_retries` controls how many times the generator rewrites its answer after the verifier rejects it — not how many stocks are evaluated (that is set by the quantity in the prompt).
- When retries are exhausted: the loop stops, a FAIL result is returned, and the last artifact is saved to `final_artifact.txt` in the run dir.
- If user says "no limit", set `max_retries` to 999 and require `max_cost_usd` to be set.

**3b. Cost budget**
> "Is there a maximum API cost budget in USD you want to enforce?
> (e.g. 0.50 — or 'skip' for no cost limit)"

- Optional. If set, the loop stops before the next generator call if cumulative estimated cost would exceed this.

Write `{run_dir}/termination.json` with the collected values, e.g.:
```json
{
  "max_retries": 3,
  "max_cost_usd": null
}
```

Do not proceed to running the loop until the user has answered both questions (even if the answer is "skip").

---

## Running the loop

Once all three steps are approved, invoke the pack.

**LLM provider, model, and API key are read from `lib/aor/.env` automatically.**
Copy `lib/aor/.env.example` → `lib/aor/.env` and set `LLM_API_KEY` before running.

```python
import asyncio
import sys
sys.path.insert(0, "/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/lib/aor")

from agent import config as aor_config
from packs.multiagent_adversarial import create_pack
from orchestrator.types import WorkflowRequest

async def run():
    aor_config.load()  # reads lib/aor/.env

    pack = create_pack()  # auto-creates run dir under /tmp/aor_runs/
    await pack.open()
    try:
        outcome = await pack.run_direct(WorkflowRequest(
            text="<generator_prompt.txt contents>",
            metadata={
                **aor_config.as_metadata(),          # provider, model, api_key, max_retries, max_cost_usd
                "verifier_script": "<run_dir>/verifier.py",
                "max_retries": 3,                    # overrides .env default if user specified one
            }
        ))
        print(outcome.result.output["artifact"])
    finally:
        await pack.close()

asyncio.run(run())
```

The run directory is printed at startup so the user can inspect all artifacts.

---

## Run directory layout

```
/tmp/aor_runs/aor_multiagent_adversarial_001_20260618_134200/
  generator_prompt.txt        ← step 1
  verifier.py                 ← step 2
  requirements.txt            ← step 2 (if needed)
  termination.json            ← step 3
  attempts/
    001_artifact.txt
    001_verifier_output.json  ← includes reason string fed back to generator
    002_artifact.txt
    002_verifier_output.json
  final_artifact.txt
  run_summary.json
```

---

## WorkflowRequest.metadata fields

| Field | Required | Description |
|---|---|---|
| `verifier_script` | yes* | Absolute path to `verifier.py`. Falls back to LLM critic with warning if omitted. |
| `max_retries` | yes | Max generator rewrites after verifier rejection. Must be set explicitly — no default. |
| `max_cost_usd` | no | Stop loop if estimated cost exceeds this |
| `provider` | no | LLM provider (default `anthropic`, or `AOR_PROVIDER`) |
| `model` | no | Model ID (default `claude-sonnet-4-5-20250929`, or `AOR_MODEL_ID`) |
| `api_key` | no | API key (falls back to `AOR_API_KEY`) |

---

## Output

`outcome.result.output` contains:
- `artifact` — final accepted artifact
- `gate_passed` — `true`
- `verifier_reason` — the verifier script's reason string
- `attempts` — number of generator attempts made
- `run_dir` — path to the run directory
