---
name: pdf-to-md
description: Convert PDF to Markdown with table extraction
---

# PDF to Markdown Converter

Converts PDF files to Markdown format with intelligent table extraction and image handling.

## Usage

```
/pdf-to-md path/to/file.pdf
```

## What This Does

Uses the `convert_pdf_to_md` MCP tool to:
1. Extract text content from PDF
2. Preserve document structure
3. Extract and convert tables
4. Handle images (inline or as separate files)

## Common Options

Ask the user if they want:
- **OCR** for scanned/image-based PDFs
- **Table extraction** for documents with complex tables
- **Image extraction** (inline or separate files)

Then call the `convert_pdf_to_md` tool with appropriate options.

## Examples

**Simple conversion:**
```
/pdf-to-md report.pdf
```

**With OCR (scanned document):**
```
/pdf-to-md scanned-doc.pdf
```
(Ask if OCR is needed, then enable it)

**Research paper with images:**
```
/pdf-to-md paper.pdf
```
(Extract images to separate files for clarity)

## Notes

- For best results with tables, use `pdfplumber` backend (requires Python package)
- OCR requires additional dependencies
- Large PDFs may take time to process
