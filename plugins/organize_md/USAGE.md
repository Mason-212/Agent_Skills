# Quick Start Guide - organize_md Plugin

## What It Does

The `organize_md` plugin provides **scalable markdown organization**:

1. **Image Organization**
   - Moves scattered images into `{markdown-filename}_images/` subdirectories
   - Updates all markdown image references automatically
   - Normalizes image filenames for consistency

2. **Heading Numbering**
   - Adds sequential numeric prefixes to heading levels 1-2
   - Level 1: `# 1 Title`, `# 2 Next`
   - Level 2: `## 1.1 Subtitle`, `## 1.2 Another`
   - Preserves existing numbers and skips level 3+ headings

## Installation

```bash
# 1. Navigate to skills directory
cd /Users/thomaschang/Documents/dev/git/thomaschangsf/skills

# 2. Run setup script
./scripts/dev_refresh_skills_and_tools.sh

# 3. Restart Claude Code
```

## Quick Usage

### Via Claude Code (Recommended)

Just ask Claude naturally:

```
"Organize Tool - Claude - V2.md"
"Organize all markdown files in references/cliff_notes/"
"Add heading numbers to my document"
```

### Direct Command Line

```bash
# Full organization (images + headings)
python3 scripts/organize_images.py "/path/to/file.md"

# Preview changes first
python3 scripts/organize_images.py "/path/to/file.md" --dry-run

# Images only (no heading numbers)
python3 scripts/organize_images.py "/path/to/file.md" --no-numbers

# Custom image search location
python3 scripts/organize_images.py "/path/to/file.md" --search-root /repo/root
```

## Example Output

```
✅ Success!
📄 Markdown: /path/to/Tool - Claude - V2.md
📁 Companion directory: /path/to/Tool - Claude - V2_images
🖼️  Images processed: 14
🔢 Headings numbered: 12
```

## File Organization Pattern

**Before:**
```
project/
├── references/cliff_notes/
│   └── Tool - Claude - V2.md
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

## Heading Transformation

**Before:**
```markdown
# The Essence
## Ian's Overview
## Claude catch up
# Code Review
```

**After:**
```markdown
# 1 The Essence
## 1.1 Ian's Overview
## 1.2 Claude catch up
# 2 Code Review
```

## Common Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview without making changes |
| `--no-numbers` | Skip heading numbering |
| `--no-normalize` | Keep original image filenames |
| `--search-root PATH` | Where to search for images |

## Batch Processing

```bash
# Organize all markdown files in a directory
find references/cliff_notes -name "*.md" -exec \
  python3 /path/to/organize_md/scripts/organize_images.py {} \;
```

## Benefits

✅ **Scalable** - Works for any number of markdown files  
✅ **Safe** - Dry-run mode to preview changes  
✅ **Smart** - Preserves existing numbering, skips duplicates  
✅ **Clean** - Companion directories keep images organized  
✅ **Portable** - Move markdown + images together as a unit  

## Full Documentation

See [README.md](README.md) for complete details.
