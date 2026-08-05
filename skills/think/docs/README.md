# Think Skill Documentation

**Read this index first.** Each doc owns one concern. Do not duplicate content across files — link instead.

## Which doc to read

| Need | Read | Owns |
|------|------|------|
| What is a structure? How do we evaluate one? | [`framework.md`](framework.md) | Concepts, terminology, counterexample types, reasoning principles |
| Why did we build it this way? | [`principles.md`](principles.md) | Design evolution, compression insight, model-as-engine |
| How do domain plugins attach to the flow? | [`architecture.md`](architecture.md) | Two-layer design, plugin layout, authoring |
| Which technique runs at which step? Fail-fast? Logging? | [`reasoning-techniques.md`](reasoning-techniques.md) | Technique catalog, control flow, event schema |
| What should the agent actually do? | [`../SKILL.md`](../SKILL.md) | Operational spec (authoritative for thresholds) |

## Other docs (not in the core four)

| Doc | Role |
|-----|------|
| [`quality.md`](quality.md) | Taste and judgment — what excellence looks like |
| [`learning-to-do.md`](learning-to-do.md) | Observed execution gaps when applying the skill |
| [`terminology-guide.md`](terminology-guide.md) | Counterexamples vs consequence testing (disambiguation) |
| [`../ir/dag-spec.md`](../ir/dag-spec.md) | Formal pipeline contracts and artifact schemas |

## Suggested reading order

1. **User** — `architecture.md` → ask a question via `/think`
2. **Contributor** — `principles.md` → `framework.md` → `reasoning-techniques.md` → `SKILL.md`
3. **Plugin author** — `architecture.md` → `quality/equity/taste.md` (example)

## The six steps (defined once here)

```
Build → Validate → Test → Compress → Expand → Verify
  1        2         3        4         5        6
```

- Steps 1–5: construct and stress-test the mental model.
- Step 6: independent external verification (not the first time to check depth or evidence — see fail-fast gates in `reasoning-techniques.md`).
