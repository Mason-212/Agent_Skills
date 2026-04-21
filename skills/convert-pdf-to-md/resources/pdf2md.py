#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class ExtractedTable:
    table_id: str
    grid: list[list[str]]
    confidence: float
    warnings: list[str]


@dataclass
class ExtractedFigure:
    figure_id: str
    path: str
    caption: str
    classification: str
    reconstruction: Optional[str]
    warnings: list[str]


@dataclass
class PageBundle:
    page_number: int
    text: str
    tables: list[ExtractedTable]
    figures: list[ExtractedFigure]
    warnings: list[str]


def _parse_pages(pages: str | None) -> Optional[list[int]]:
    if not pages:
        return None
    result: list[int] = []
    for part in pages.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a)
            end = int(b)
            if end < start:
                start, end = end, start
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))
    return sorted(set(result))


def _clean_text(text: str) -> str:
    """
    PDFs often extract as layout-driven tokens (extra newlines/spaces).
    Prefer readable paragraphs and preserve obvious structure (headings, bullets).
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize bullet markers (common in exported PDFs) and tag them so
    # we don't accidentally convert normal hyphens into list items later.
    text = text.replace("\u25cf", "\n- ")
    text = re.sub(r"\n[ \t]*- ", "\n- ", text)
    text = text.replace("\n- ", "<<BULLET>>")

    # Collapse runs of spaces/tabs but keep newlines for structure recovery.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)

    # Fix spacing around punctuation.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)

    # Remove common hyphenation artifacts across line breaks.
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # If the extraction produced "one word per line" fragments, flatten lines first.
    raw_lines = [ln.strip() for ln in text.split("\n")]
    non_empty = [ln for ln in raw_lines if ln]
    if non_empty:
        short = sum(1 for ln in non_empty if len(ln) <= 12)
        if short / len(non_empty) > 0.55:
            text = re.sub(r"\s+", " ", " ".join(non_empty)).strip()
        else:
            text = "\n".join(raw_lines).strip()
    else:
        text = ""

    if not text:
        return ""

    # From here, operate on a mostly single-line text while reinserting structure.
    text = re.sub(r"\s+", " ", text).strip()

    # Restore tagged bullets as real newlines.
    text = text.replace("<<BULLET>>", "\n- ")

    # Fix common concatenations caused by PDF layout extraction.
    # (This doc has a numbered list that can get glued to the next header.)
    text = text.replace(
        "Pair Programming Technical Deep Dive Interview:",
        "Pair Programming\n\nTechnical Deep Dive Interview:",
    )

    # Headings: promote only when the phrase is followed soon by a section label.
    # This avoids false positives in table-of-contents style lists.
    headings = [
        "Technical Deep Dive Interview:",
        "Leadership Journey Interview:",
        "Pair Programming Interview:",
        "Problem Solving: ML Modelling",
        "Problem Solving: ML Systems Design",
    ]
    label_lookahead = r"(?=.{0,160}(TL;?DR:|Duration:|Preparation:|Interview Day:|Pro Tips?:))"
    for h in headings:
        if h.endswith(":"):
            heading_pat = re.escape(h)
        else:
            heading_pat = rf"\b{re.escape(h)}\b"
        text = re.sub(
            rf"{heading_pat}{label_lookahead}\s*",
            f"\n\n### {h}\n\n",
            text,
        )

    # Promote common section labels into Markdown-friendly blocks.
    def _label(name: str) -> str:
        return f"\n\n**{name}:** "

    text = re.sub(r"\bTL;?DR:\s*", _label("TLDR"), text)
    text = re.sub(r"\bDuration:\s*", _label("Duration"), text)
    text = re.sub(r"\bPreparation:\s*", _label("Preparation"), text)
    text = re.sub(r"\bInterview Day:\s*", _label("Interview Day"), text)
    text = re.sub(r"\bPro Tips?:\s*", "\n\n**Pro Tips:**\n", text)

    text = re.sub(r"\bFrequently Asked Questions\b", "\n\n### Frequently Asked Questions\n\n", text)
    text = re.sub(r"\bWhat is pair programming\?\b", "\n\n### What is pair programming?\n\n", text)

    # Tidy blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return text + "\n"


def extract_text_pdfplumber(pdf_path: Path, pages: Optional[list[int]]) -> Optional[list[str]]:
    try:
        import pdfplumber  # type: ignore
    except Exception:
        return None

    out: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            if pages is not None and idx not in pages:
                continue
            out.append(page.extract_text() or "")
    return out


def _safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def extract_text_pypdf(pdf_path: Path, pages: Optional[list[int]]) -> list[str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Missing dependency: pypdf. Install with `python -m pip install pypdf`."
        ) from e

    reader = PdfReader(str(pdf_path))
    out: list[str] = []
    for idx, page in enumerate(reader.pages, start=1):
        if pages is not None and idx not in pages:
            continue
        out.append(page.extract_text() or "")
    return out


def extract_tables_pdfplumber(pdf_path: Path, pages: Optional[list[int]]) -> list[list[ExtractedTable]]:
    try:
        import pdfplumber  # type: ignore
    except Exception:
        return []

    bundles: list[list[ExtractedTable]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            if pages is not None and idx not in pages:
                continue
            tables: list[ExtractedTable] = []
            for t_idx, tbl in enumerate(page.extract_tables() or [], start=1):
                grid = [[(c or "").strip() for c in row] for row in tbl]
                warnings: list[str] = []
                confidence = score_table_confidence(grid, warnings)
                tables.append(
                    ExtractedTable(
                        table_id=f"p{idx:04d}_t{t_idx:02d}",
                        grid=grid,
                        confidence=confidence,
                        warnings=warnings,
                    )
                )
            bundles.append(tables)
    return bundles


def score_table_confidence(grid: list[list[str]], warnings: list[str]) -> float:
    if not grid or not any(any(cell.strip() for cell in row) for row in grid):
        warnings.append("empty_table")
        return 0.0

    row_lens = [len(r) for r in grid]
    if len(set(row_lens)) != 1:
        warnings.append("non_rectangular_rows")
        return 0.2

    cells = [c for r in grid for c in r]
    empty = sum(1 for c in cells if not c.strip())
    empty_ratio = empty / max(1, len(cells))
    if empty_ratio > 0.35:
        warnings.append(f"high_empty_ratio:{empty_ratio:.2f}")
        return 0.4

    # Mild prior: a plausible table has at least 2 rows and 2 cols.
    if len(grid) < 2 or len(grid[0]) < 2:
        warnings.append("too_small")
        return 0.4

    return 0.8


def render_markdown_table(grid: list[list[str]]) -> str:
    if not grid:
        return ""
    cols = len(grid[0])
    header = grid[0]
    body = grid[1:] if len(grid) > 1 else []

    def esc(cell: str) -> str:
        return cell.replace("|", "\\|").replace("\n", "<br>")

    lines: list[str] = []
    lines.append("| " + " | ".join(esc(c) for c in header[:cols]) + " |")
    lines.append("| " + " | ".join(["---"] * cols) + " |")
    for row in body:
        if len(row) != cols:
            row = (row + [""] * cols)[:cols]
        lines.append("| " + " | ".join(esc(c) for c in row) + " |")
    return "\n".join(lines) + "\n"


def write_csv(path: Path, grid: list[list[str]]) -> None:
    import csv

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(grid)


def build_markdown(
    pages: list[PageBundle],
    assets_dir: Optional[Path],
    *,
    title: str,
    include_page_headings: bool,
) -> str:
    parts: list[str] = []
    parts.append(f"# {title}\n")

    for pb in pages:
        if include_page_headings:
            parts.append(f"## Page {pb.page_number}\n")
        if pb.text.strip():
            parts.append(pb.text.strip() + "\n")

        for t in pb.tables:
            parts.append(f"### Table {t.table_id}\n")
            if t.confidence >= 0.6:
                parts.append(render_markdown_table(t.grid))
            else:
                parts.append("_Low confidence table. Not emitted as Markdown._\n")
            if t.warnings:
                parts.append(f"_Warnings_: `{', '.join(t.warnings)}`\n")

        for fig in pb.figures:
            parts.append(f"### Figure {fig.figure_id}\n")
            if fig.reconstruction:
                parts.append("```mermaid\n")
                parts.append(fig.reconstruction.strip() + "\n")
                parts.append("```\n")
            if fig.path:
                parts.append(f"![{fig.caption or fig.figure_id}]({fig.path})\n")
            if fig.caption:
                parts.append(f"_Caption_: {fig.caption}\n")
            if fig.warnings:
                parts.append(f"_Warnings_: `{', '.join(fig.warnings)}`\n")

    parts.append("## Conversion Report\n")
    parts.append(f"- Pages: {len(pages)}\n")
    parts.append(
        f"- Tables: {sum(len(p.tables) for p in pages)} (low confidence: {sum(sum(1 for t in p.tables if t.confidence < 0.6) for p in pages)})\n"
    )
    parts.append(f"- Figures: {sum(len(p.figures) for p in pages)}\n")
    return "\n".join(parts).strip() + "\n"


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="pdf2md")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--title", type=str, default=None, help="Markdown document title.")
    ap.add_argument("--pages", type=str, default=None, help="e.g. 1-3,7")
    ap.add_argument("--extract-assets", type=Path, default=None)
    ap.add_argument("--report-json", type=Path, default=None, help="Optional structured extraction report.")
    ap.add_argument(
        "--include-page-headings",
        action="store_true",
        help="Include '## Page N' headings in the output Markdown.",
    )
    ap.add_argument("--use-llm", action="store_true", help="Optional; not implemented here.")
    ap.add_argument("--use-api", action="store_true", help="Optional; not implemented here.")
    args = ap.parse_args(argv)

    pages = _parse_pages(args.pages)

    # Text: prefer pdfplumber when available (better structure), fallback to pypdf.
    texts = extract_text_pdfplumber(args.pdf, pages) or extract_text_pypdf(args.pdf, pages)
    texts = [_clean_text(t) if t.strip() else "" for t in texts]

    # Tables (best-effort if pdfplumber is installed).
    tables_by_page = extract_tables_pdfplumber(args.pdf, pages)
    if tables_by_page and len(tables_by_page) != len(texts):
        # If page filtering differs between extractors, avoid misalignment.
        tables_by_page = []

    page_bundles: list[PageBundle] = []
    for i, text in enumerate(texts, start=1):
        page_tables = tables_by_page[i - 1] if tables_by_page else []
        page_bundles.append(
            PageBundle(
                page_number=i,
                text=text,
                tables=page_tables,
                figures=[],
                warnings=[],
            )
        )

    assets_dir = args.extract_assets
    if assets_dir:
        _safe_mkdir(assets_dir)
        _safe_mkdir(assets_dir / "figures")

    title = args.title or args.pdf.stem
    md = build_markdown(
        page_bundles,
        assets_dir,
        title=title,
        include_page_headings=args.include_page_headings,
    )
    args.output.write_text(md, encoding="utf-8")

    if args.report_json:
        report = {
            "pdf": str(args.pdf),
            "output": str(args.output),
            "assets_dir": str(assets_dir) if assets_dir else None,
            "pages": [asdict(p) for p in page_bundles],
        }
        args.report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

