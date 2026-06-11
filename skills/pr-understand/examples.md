# PR Understand Examples

## Example 1: Big Picture First

```markdown
### Big Picture

This change turns hill-climb from a config-only option into a real causal-discovery path. Before this patch, the trainer only supported the causal-learn-backed algorithms. After the patch, hill-climb has its own discovery module, its own trainer registration, and its own DAG construction path.
```

Use this pattern when the user first needs orientation, not implementation detail.

## Example 2: High-Overhead Function Walkthrough

```markdown
### Important Implementation Details

- `discover_hill_climb_graph()` is the center of the new flow. It starts from an empty parent map, inserts hard required edges, optionally warms the graph with seed edges when they improve the score, then repeatedly applies the best add/delete/reverse move until no score-improving move remains.
- `_build_search_constraints()` only matters for seeded runs. It narrows the search space by building an MMPC-style skeleton first, then converting that skeleton into allowed directed candidate edges.
```

Why this works:

- focuses on the functions that carry the idea
- avoids spending time on tiny helpers until needed

## Example 3: Tests As Examples

```markdown
### Tests As Examples

- `tests/test_hill_climb.py` is the best executable example because it shows how required edges are enforced even before the search starts.
- The seed-edge tests are useful because they clarify that seed edges are guidance, not hard constraints: the edge is only kept when it is both legal and score-improving.
```

Use tests when they explain semantics better than prose.

## Example 4: Navigation Map

```markdown
### How To Navigate This After Landing

- Start in `causal_graph_trainer.py` to see where the algorithm is registered and how the result is turned into a trained model.
- Read `hill_climb.py` next for the actual search logic.
- Read `graph_utils.py` after that for background-knowledge and graph-conversion helpers.
- Use `tests/test_hill_climb.py` to confirm the intended rules around required, forbidden, and seed edges.
```

## Example 5: Boilerplate Compression

```markdown
### Important Implementation Details

- The new registry decorator is mostly boilerplate; the interesting part is not the decorator itself but the custom `fit()` path it enables.
```

This is the right move when a piece of code matters structurally but is easy to understand on sight.

## Example 6: Restatement Gate

```markdown
Before I close this walkthrough — can you state the load-bearing invariant
of this change in one sentence in your own words?
```

User: "Hill-climb now runs its own search loop instead of delegating to causal-learn, and required edges are enforced before the search starts."

```markdown
Correct. The one thing to add: seed edges are also evaluated before search,
but unlike required edges they are only kept when score-improving. That
distinction matters if you ever need to debug why a seed edge disappeared.
```

Use this gate at the end of every walkthrough. A walkthrough that ends
without the user reconstructing the *why* has produced familiarity, not
understanding.
