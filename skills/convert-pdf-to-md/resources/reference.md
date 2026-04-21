# Reference: PDF → Markdown conversion

## Decision tree

### Is it scanned?

Signs it is scanned:
- text extraction returns almost nothing
- pages are dominated by raster images
- obvious OCR artifacts when copying text from a viewer

If scanned:
- run OCR per page
- expect lower table accuracy; lean on confidence checks

If digital:
- extract text blocks + geometry first
- use OCR only for figures that contain essential text (optional)

## Tables

### Common failure modes

- **Merged cells**: markdown tables can’t represent true merges → either flatten or use CSV sidecar
- **Multi-line headers**: normalize whitespace and join with `\\n` inside a cell
- **Repeated headers per page**: detect duplicates and drop repeats
- **Sparse tables**: often false positives—use empty-cell ratio heuristic

### Confidence heuristics (suggested defaults)

- **Rectangularity**: all rows same length after normalization (hard requirement for Markdown table)
- **Empty-cell ratio**: if > 0.35 → low confidence
- **Header plausibility**: header row should have fewer empty cells than body rows
- **Stability across extractors** (optional): if two methods disagree heavily → low confidence

### Output rules

- **OK confidence**: markdown table
- **Low confidence but parseable**: write `tables/<table_id>.csv` and link it from markdown
- **Not parseable**: save a table image and add a “manual fix needed” note

## Diagrams / figures

### What to reconstruct vs what to describe

Reconstruct to Mermaid when:
- the figure is clearly a flowchart/box-arrow diagram
- labels are legible
- structure is not too dense (roughly < 30 nodes)

Prefer structured description when:
- it’s a chart/plot (reconstruction often requires underlying data)
- it’s a screenshot/photo
- it’s dense or ambiguous

### Mermaid patterns

**Flowcharts**
- Use `flowchart TD` for top-down layouts.
- Use short, stable node IDs (`A`, `B`, `node1`), labels in quotes if needed.

**Sequence diagrams**
- Use only when actors and message directions are clear.

### Validation checklist

- Mermaid syntax is valid (no stray characters, no invalid node IDs)
- Labels with special characters are quoted
- The diagram matches the visible edges and labels at least at a coarse level

## Output assembly

### Figure placement

Place figures and tables near:
- their caption text, if present
- otherwise nearest preceding paragraph

### Conversion report (end of file)

Include:
- summary counts
- low-confidence items list with anchors
- next-step guidance (e.g., “re-run with --use-api for diagram reconstruction”)
