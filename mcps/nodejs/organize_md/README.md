# Organize MD MCP Tool

Automatically organize markdown files: move images to companion directories and add sequential heading numbers.

## Purpose

When markdown files need organization, this tool:
1. **Images**: Scans for image references, creates `{filename}_images/` directory, moves images, updates references
2. **Headings**: Adds sequential numeric prefixes to top 2 heading levels if missing
   - Level 1: `# 1 Title`, `# 2 Next Title`
   - Level 2: `## 1.1 Subtitle`, `## 1.2 Another Subtitle`

## Usage

### Via Claude Code

Simply ask Claude:

```
"Organize Tool - Claude - V2.md"
"Organize all markdown files in references/cliff_notes/"
"Add heading numbers to my document"
```

Claude will automatically use the MCP tool.

### Manual Testing

```bash
# Full organization (images + heading numbers)
python3 scripts/organize_images.py "path/to/file.md"

# Images only (no heading numbers)
python3 scripts/organize_images.py "path/to/file.md" --no-numbers

# Dry run (preview changes)
python3 scripts/organize_images.py "path/to/file.md" --dry-run

# Custom search root for images
python3 scripts/organize_images.py "path/to/file.md" --search-root /repo/root

# Keep original image filenames
python3 scripts/organize_images.py "path/to/file.md" --no-normalize
```

## Features

### Heading Numbering

Automatically adds sequential numbers to headings levels 1-2:

**Before:**
```markdown
# The Essence
## Ian's Overview
## Claude catch up
### Principles
# Code And Security Review
## Background
```

**After:**
```markdown
# 1 The Essence
## 1.1 Ian's Overview
## 1.2 Claude catch up
### Principles
# 2 Code And Security Review
## 2.1 Background
```

**Smart Detection:**
- Skips headings that already have numbers
- Respects existing numbering sequences
- Only numbers top 2 levels (# and ##)
- Preserves level 3+ headings unchanged

### Image Organization

**Before:**
```
project/
├── references/cliff_notes/
│   ├── Tool - Claude - V2.md
│   └── ...
├── Pasted image 20260515102144.png
└── Screenshot 2026-05-15.png
```

**After:**
```
project/
└── references/cliff_notes/
    ├── Tool - Claude - V2.md
    └── Tool - Claude - V2_images/
        ├── pasted-image-20260515102144.png
        └── screenshot-2026-05-15.png
```

**Markdown Updates:**
```markdown
<!-- Before -->
![[Pasted image 20260515102144.png|477]]

<!-- After -->
![[Tool - Claude - V2_images/pasted-image-20260515102144.png|477]]
```

### Image Search Strategy

1. Same directory as markdown file
2. Parent directory (project root)
3. Recursively in `--search-root` if specified

### Filename Normalization

By default:
- `Pasted image 20260515102144.png` → `pasted-image-20260515102144.png`
- `Screenshot 2026-05-15 at 10.18.29 AM.png` → `screenshot-2026-05-15-at-10.18.29-am.png`

Disable with `--no-normalize`.

### Supported Formats

**Images:** PNG, JPG, JPEG, GIF, SVG, WebP

**Markdown:**
- Obsidian: `![[image.png|width]]`
- Standard: `![alt text](image.png)`

## Installation

### Prerequisites

- Python 3.8+
- Node.js 18+

### Method 1: Install as Claude Code Plugin (Recommended)

1. **Copy plugin to Claude plugins directory:**
   ```bash
   cp -r /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/plugins/organize_md \
     ~/.claude/plugins/organize-md
   ```

2. **Install Node dependencies:**
   ```bash
   cd ~/.claude/plugins/organize-md
   npm install
   ```

3. **Restart Claude Code**

4. **Verify installation:**
   Run `/mcp` in Claude Code to see `organize-md` server listed

### Method 2: Manual MCP Configuration

If not installing as a plugin, manually configure the MCP server:

1. **Install Node dependencies:**
   ```bash
   cd /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/plugins/organize_md
   npm install
   ```

2. **Make scripts executable:**
   ```bash
   chmod +x index.js
   chmod +x scripts/organize_images.py
   ```

3. **Add to `~/.claude/settings.json`:**
   ```json
   {
     "mcpServers": {
       "organize_md": {
         "command": "node",
         "args": ["/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/plugins/organize_md/index.js"],
         "env": {}
       }
     }
   }
   ```

4. **Restart Claude Code**

### Verification

Check Claude Code logs for:
```
[MCP] Starting server: organize-md (or organize_md)
[MCP] Server initialized successfully
```

Or run `/mcp` to list all MCP servers.

## Examples

### Full Organization

```bash
python3 scripts/organize_images.py \
  "references/cliff_notes/Tool - Claude - V2.md"
```

Output:
```
✅ Success!
📄 Markdown: /path/to/Tool - Claude - V2.md
📁 Companion directory: /path/to/Tool - Claude - V2_images
🖼️  Images processed: 14
🔢 Headings numbered: 12
```

### Heading Numbers Only

```bash
python3 scripts/organize_images.py \
  "references/cliff_notes/Tool - AWS - EKS.md" \
  --no-normalize
```

### Dry Run

```bash
python3 scripts/organize_images.py \
  "references/cliff_notes/Tool - Claude - V2.md" \
  --dry-run
```

## Batch Processing

Organize all markdown files:

```bash
find references/cliff_notes -name "*.md" -exec \
  python3 scripts/organize_images.py {} \;
```

Or ask Claude: "Organize all markdown files in references/cliff_notes/"

## Benefits

1. **Clear structure** - Numbered headings provide document outline
2. **Image ownership** - Clear which images belong to which document
3. **No collisions** - Each markdown file has isolated namespace
4. **Easy cleanup** - Delete markdown + image directory together
5. **Portable** - Move both as a unit
6. **Scalable** - Works for any number of files

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `markdown_path` | Path to markdown file | Required |
| `--search-root PATH` | Root directory to search for images | Markdown directory |
| `--no-normalize` | Keep original image filenames | false (normalizes) |
| `--no-numbers` | Don't add heading numbers | false (adds numbers) |
| `--dry-run` | Preview without making changes | false (makes changes) |

## Troubleshooting

**Images not found:**
- Specify `--search-root` to search broader directory tree
- Check image paths in markdown match actual filenames

**Heading numbers look wrong:**
- Tool respects existing numbering - manually adjust if needed
- Only modifies headings without numeric prefixes

**Permission errors:**
- Ensure write permissions on markdown file and parent directory

**Script not found:**
- Verify `scripts/organize_images.py` exists
- Check permissions: `chmod +x scripts/organize_images.py`

## Technical Details

### Heading Number Pattern

```python
# Detects existing numbers
r'^\d+(\.\d+)*\s+'

# Level 1: # 1 Title
# Level 2: ## 1.1 Subtitle
```

### Image Detection

```python
# Obsidian format
r'!\[\[([^\]]+\.(?:png|jpg|jpeg|gif|svg|webp))(?:\|[^\]]+)?\]\]'

# Standard markdown
r'!\[[^\]]*\]\(([^\)]+\.(?:png|jpg|jpeg|gif|svg|webp))\)'
```

### Safety

- Creates companion directory only if images exist
- Skips images already in companion directory
- Preserves existing heading numbers
- Dry run mode for previewing changes
- Maintains file timestamps
