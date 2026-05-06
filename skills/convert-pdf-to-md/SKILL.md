---
name: convert-pdf-to-md
description: Convert PDFs to Markdown with table extraction and diagram reconstruction.
---

# Convert PDF to Markdown

> **Note**: This skill provides orchestration instructions and workflow guidance. For direct execution via MCP tool, see [`plugins/pdf_to_md/`](../../plugins/pdf_to_md/). The MCP tool wraps the same Python script for atomic, fast execution.

## When to Use

**Use this skill when:**
- You need **guided workflow** with decision trees and best practices
- The MCP tool is not configured or available
- You want to **understand the conversion process** before automating

**Use the MCP tool when:**
- You have the tool configured in Claude Code/Cursor settings
- You want **immediate, atomic execution** ("convert this PDF now")
- The Python script and dependencies are already set up

## Original Use Cases

- The user asks to **convert a PDF to Markdown** (or `.md`)
- The user wants to **extract tables** from a PDF
- The user wants to **convert diagrams/figures** into editable text (e.g., Mermaid)
- The user mentions **OCR**, **scanned PDF**, **flowchart**, **architecture diagram**, **figure**

## Quick Start (recommended workflow)

- If using the local CLI script (`resources/pdf2md.py`), set up dependencies first (see **Prereqs / Install** below).
- Ask for:
  - the **PDF path**
  - whether it is **scanned** or **digital**
  - whether **network calls are allowed**
  - the expected output: **single markdown** vs **markdown + assets folder**
- Default behavior:
  - **offline-first** conversion
  - **data-first tables** (correct cells > perfect layout)
  - **diagram reconstruction when high-confidence**, otherwise embed image + structured caption

## Operating Procedure

### 0) Prereqs / Install (local CLI)

This skill ships a local script at `skills/convert-pdf-to-md/resources/pdf2md.py`.

Minimal required dependency:

```bash
python -m pip install pypdf
```

Recommended (avoid modifying global Python):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install pypdf
```

Optional enhancement (better table extraction):

```bash
python -m pip install pdfplumber
```

If `pdf2md.py` fails with `Missing dependency: ...`, install the missing package and rerun.

### 1) Decide the policy (offline-first + opt-in upgrades)

- Default: local/offline libraries only
- If the user allows it, enable an opt-in path:
  - `--use-llm`: local vision model (if available)
  - `--use-api`: hosted vision model

### 2) Identify PDF type

Use a small page sample (e.g., first 2–3 pages) and choose the track:

- **Digital-text PDF**: text extraction first
- **Scanned / image PDF**: OCR first

Heuristic:
- If extracted text is near-empty but the page contains a large raster image, treat as scanned.

### 3) Extract content into a stable intermediate representation (IR)

Build a per-page bundle that keeps geometry so you can place tables/figures near the right text:

- `text_blocks`: ordered text spans (with coords when possible)
- `tables`: regions + extracted grids + confidence
- `figures`: extracted images/diagrams + nearby captions
- `warnings`: anything uncertain (bad OCR, low table confidence, ambiguous reading order)

This IR is what enables deterministic markdown assembly and reliable fallbacks.

### 4) Convert text to Markdown

- Prefer clean paragraphs over preserving hard line breaks.
- Preserve code blocks only when clearly code-like.
- Normalize whitespace and hyphenation artifacts.
- Promote headings when supported by font/size cues; otherwise keep as paragraphs.

### 5) Convert tables (data-first)

Goal: **correct cells and headers**. Layout fidelity is secondary.

#### Table extraction defaults

- Prefer extractors that output a **cell grid** (rows × columns).
- Post-process:
  - infer header rows when consistent
  - trim empty rows/cols
  - normalize multi-line cells
  - ensure all rows have the same column count (rectangular)

#### Confidence checks (must run)

Mark a table as **low confidence** if any hold:

- row lengths differ after normalization
- too many empty cells (e.g., > 35%)
- header inference is ambiguous
- table region overlaps heavily with body text (likely false positive)

#### Output rules

- If confidence is OK: emit a Markdown table.
- If low confidence: emit a short note saying the table was not emitted as Markdown.
- Optional enhancement: emit CSV or a table image into an assets folder when the user asks for artifacts.

### 6) Convert diagrams / figures (semantic reconstruction)

Treat “diagram conversion” as a **best-effort reconstruction** with strict fallbacks.

#### A) Detect and classify figures

Extract candidate figures and classify each as:
- flowchart/process
- architecture boxes/arrows
- chart/plot
- equation/notation
- screenshot/photo

Attach nearby caption text (usually below the figure).

#### B) Reconstruction strategy

**Offline default**
- Only reconstruct when classification is high-confidence and the diagram is structurally simple:
  - box/arrow → Mermaid `flowchart TD`
  - simple interaction → Mermaid `sequenceDiagram`
- Otherwise: embed the image + structured caption (below).

**Opt-in LLM/API path**
- For diagrams needing interpretation, use the figure image + caption + surrounding text.
- Request one of:
  - valid Mermaid (preferred if representable)
  - else: structured description (entities, relationships, labels, constraints)

#### C) Mermaid validation + hygiene

- Ensure Mermaid compiles syntactically.
- Node IDs must be stable and safe: `CamelCase`/`snake_case`/`node1` (no spaces).
- Avoid styling directives.
- Quote labels containing special characters.

If validation fails: fall back to image + structured caption.

#### Structured caption template (fallback)

- **Figure**: what this is (flowchart, architecture, plot, etc.)
- **Key entities**: A, B, C…
- **Relationships**: A → B (label), B → C (label)…
- **Notes**: important constraints/assumptions

### 7) Assemble final Markdown + assets

Default output shape:

- `out.md`
- `out_assets/figures/*`
- `out_assets/tables/*` (CSV or images when needed)

At the end of the markdown, include a **Conversion Report** section:

- pages processed
- OCR used? (pages)
- tables extracted (count + low-confidence count)
- diagrams reconstructed vs images-only
- warnings and next steps

## Suggested local CLI interface (if implementing a script)

- `pdf2md input.pdf -o out.md --extract-assets out_assets/`
- `--pages 1-3,7`
- `--use-ocr` (force OCR)
- `--use-llm` (local model)
- `--use-api` (hosted model)
- `--table-format pipe|csv`

## Additional Resources

- For detailed decision trees and edge cases: [resources/reference.md](resources/reference.md)
- For prompts/templates (diagram → Mermaid, table QA): [resources/prompts.md](resources/prompts.md)
- For examples of good outputs: [resources/examples.md](resources/examples.md)
