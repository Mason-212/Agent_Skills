# Examples

## Example 1: digital PDF with one simple table

**Input**
- `report.pdf` (digital text)

**Output**
- `report.md` contains:
  - extracted headings and paragraphs
  - a markdown table with correct headers and cells
  - a conversion report noting 1 table, 0 figures

## Example 2: scanned PDF with a table (OCR)

**Input**
- `invoice_scan.pdf` (scanned)

**Output**
- `invoice_scan.md` contains:
  - OCR’d text
  - a low-confidence table exported as `out_assets/tables/table_001.csv` and linked
  - a conversion report warning about OCR noise

## Example 3: flowchart figure

**Input**
- `architecture.pdf` with a box-arrow diagram labeled “Request Flow”

**Offline default output**
- the figure is embedded as an image with a structured caption

**With `--use-llm` / `--use-api`**
- the diagram is reconstructed as Mermaid (validated); image is optionally kept as reference
