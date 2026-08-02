---
name: organize-md
description: Organize markdown files - move images, add heading numbers
---

# Markdown Organizer

Organizes markdown files by moving images to subdirectories and adding sequential heading numbers.

## Usage

```
/organize-md path/to/file.md
```

or for a directory:

```
/organize-md path/to/docs/
```

## What This Does

Uses the `organize_markdown` MCP tool to:
1. **Move images** to `images/` subdirectory
2. **Update image links** in markdown
3. **Add heading numbers** (1.0, 1.1, 2.0, etc.)
4. **Preserve content** while improving structure

## Common Use Cases

**Single file:**
```
/organize-md notes.md
```
Moves `image1.png` → `images/image1.png` and updates links.

**Documentation directory:**
```
/organize-md docs/
```
Organizes all markdown files in the directory.

**After cloning a repo:**
```
/organize-md README.md
```
Clean up image paths for better organization.

## Options

Ask the user if they want:
- **Heading numbers** (default: yes)
- **Image relocation** (default: yes)
- **Backup original** (default: no, but you can suggest it)

Then call the `organize_markdown` tool with appropriate options.

## Notes

- Creates `images/` subdirectory automatically
- Updates all image references in the markdown file
- Preserves relative paths
- Safe to run multiple times (idempotent)
