# PDF to Markdown MCP Server

MCP server that converts PDFs to Markdown with table extraction and diagram reconstruction.

## Installation

### Option 1: Via npx from GitHub (Recommended for sharing)

**Claude Code** (`~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "pdf_to_md": {
      "command": "npx",
      "args": ["-y", "github:thomaschangsf/skills#tools/pdf_to_md"],
      "env": {}
    }
  }
}
```

**Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "pdf_to_md": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "github:thomaschangsf/skills#tools/pdf_to_md"]
    }
  }
}
```

### Option 2: Local Development

**Claude Code** (`.claude/settings.json`):
```json
{
  "mcpServers": {
    "pdf_to_md": {
      "command": "node",
      "args": ["/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/tools/pdf_to_md/index.js"],
      "env": {}
    }
  }
}
```

**Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "pdf_to_md": {
      "type": "stdio",
      "command": "node",
      "args": ["/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/tools/pdf_to_md/index.js"]
    }
  }
}
```

## Prerequisites

Python dependencies (required by the underlying pdf2md.py script):

```bash
# Minimal setup
python -m pip install pypdf

# Recommended (better table extraction)
python -m pip install pypdf pdfplumber
```

## Usage

Once configured, your AI assistant (Claude Code or Cursor) will automatically use the `convert_pdf_to_md` tool when you ask:

```
"Convert this PDF to markdown"
"Extract tables from report.pdf"
"Turn this scanned PDF into markdown"
```

## Tool Parameters

- `pdf_path` (required): Path to the PDF file
- `output_path` (optional): Output markdown file path
- `extract_assets` (optional): Directory for extracted tables/figures
- `pages` (optional): Page range like "1-3,7"
- `use_ocr` (optional): Force OCR for scanned PDFs
- `use_llm` (optional): Use local vision model for diagrams
- `use_api` (optional): Use hosted API for diagrams
- `table_format` (optional): "pipe" or "csv"

## Features

- ✅ Extract text from digital and scanned PDFs
- ✅ Data-first table extraction with confidence checks
- ✅ Diagram reconstruction to Mermaid (when high-confidence)
- ✅ Fallback to structured captions for complex diagrams
- ✅ Comprehensive conversion reports
- ✅ Offline-first with opt-in enhancements

## Related

- Parent skill: `convert-pdf-to-md` in `skills/convert-pdf-to-md/`
- Python script: `scripts/pdf2md.py`
