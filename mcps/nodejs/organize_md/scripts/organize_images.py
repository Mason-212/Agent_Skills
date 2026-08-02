#!/usr/bin/env python3
"""
Organize markdown images into companion directories and number headings.

Scans a markdown file for:
1. Image references - creates companion directory, moves images, updates paths
2. Headings (levels 1-2) - adds sequential numeric prefixes if missing
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Tuple, Optional


def extract_image_references(markdown_content: str) -> List[Tuple[str, str]]:
    """
    Extract image references from markdown content.

    Returns:
        List of tuples (full_match, image_path)
    """
    # Match both ![[image.png]] and ![alt](image.png) formats
    patterns = [
        r'!\[\[([^\]]+\.(?:png|jpg|jpeg|gif|svg|webp))(?:\|[^\]]+)?\]\]',  # Obsidian style
        r'!\[[^\]]*\]\(([^\)]+\.(?:png|jpg|jpeg|gif|svg|webp))\)',  # Standard markdown
    ]

    references = []
    for pattern in patterns:
        matches = re.finditer(pattern, markdown_content, re.IGNORECASE)
        for match in matches:
            references.append((match.group(0), match.group(1)))

    return references


def normalize_image_filename(filename: str) -> str:
    """
    Normalize image filename for consistency.

    Converts spaces to hyphens and lowercases the extension.
    """
    path = Path(filename)
    stem = path.stem.replace(' ', '-').replace('_', '-')
    ext = path.suffix.lower()
    return f"{stem}{ext}"


def create_companion_directory(markdown_path: Path) -> Path:
    """
    Create companion directory for markdown file.

    Returns:
        Path to the companion directory
    """
    companion_dir = markdown_path.parent / f"{markdown_path.stem}_images"
    companion_dir.mkdir(exist_ok=True)
    return companion_dir


def find_image_file(image_ref: str, markdown_dir: Path, search_root: Optional[Path]) -> Optional[Path]:
    """
    Find the actual image file on disk.

    Searches in:
    1. Same directory as markdown
    2. Parent directory (repo root)
    3. Recursively in search_root if provided
    """
    image_name = Path(image_ref).name

    # Search locations in priority order
    search_paths = [
        markdown_dir / image_name,
        markdown_dir.parent / image_name,
    ]

    # Check direct paths first
    for path in search_paths:
        if path.exists():
            return path

    # Search recursively in search_root if provided
    if search_root and search_root.exists():
        for root, _, files in os.walk(search_root):
            if image_name in files:
                return Path(root) / image_name

    return None


def move_image_to_companion(
    image_path: Path,
    companion_dir: Path,
    normalize_names: bool = True
) -> Path:
    """
    Move image to companion directory.

    Returns:
        Path to the new image location
    """
    if normalize_names:
        new_name = normalize_image_filename(image_path.name)
    else:
        new_name = image_path.name

    new_path = companion_dir / new_name

    # Avoid overwriting if file already exists
    if new_path.exists() and new_path.samefile(image_path):
        return new_path

    shutil.move(str(image_path), str(new_path))
    return new_path


def update_markdown_references(
    content: str,
    references: List[Tuple[str, str]],
    companion_dir_name: str,
    image_mapping: dict
) -> str:
    """
    Update markdown content with new image paths.

    Args:
        content: Original markdown content
        references: List of (full_match, image_path) tuples
        companion_dir_name: Name of companion directory
        image_mapping: Dict mapping old image names to new names
    """
    updated_content = content

    for full_match, image_ref in references:
        image_name = Path(image_ref).name

        if image_name in image_mapping:
            new_name = image_mapping[image_name]
            new_path = f"{companion_dir_name}/{new_name}"

            # Replace the image path while preserving format
            if '![[' in full_match:
                # Obsidian format: ![[image.png|width]]
                width_match = re.search(r'\|([^\]]+)\]\]', full_match)
                if width_match:
                    new_match = f"![[{new_path}|{width_match.group(1)}]]"
                else:
                    new_match = f"![[{new_path}]]"
            else:
                # Standard markdown: ![alt](image.png)
                alt_match = re.search(r'!\[([^\]]*)\]', full_match)
                alt_text = alt_match.group(1) if alt_match else ""
                new_match = f"![{alt_text}]({new_path})"

            updated_content = updated_content.replace(full_match, new_match)

    return updated_content


def add_heading_numbers(content: str) -> Tuple[str, int]:
    """
    Add sequential numeric prefixes to top 2 heading levels if missing.

    Returns:
        Tuple of (updated_content, number_of_headings_numbered)
    """
    lines = content.split('\n')
    updated_lines = []

    # Track counters for each level
    h1_counter = 0
    h2_counter = 0
    changes_made = 0

    for line in lines:
        # Match headings (## or #)
        heading_match = re.match(r'^(#{1,2})\s+(.*)$', line)

        if heading_match:
            hashes = heading_match.group(1)
            heading_text = heading_match.group(2).strip()
            level = len(hashes)

            # Only process levels 1 and 2
            if level <= 2:
                # Check if heading already has numeric prefix
                has_number = re.match(r'^\d+(\.\d+)*\s+', heading_text)

                if not has_number:
                    if level == 1:
                        h1_counter += 1
                        h2_counter = 0  # Reset h2 counter for new h1 section
                        new_line = f"{hashes} {h1_counter} {heading_text}"
                    else:  # level == 2
                        h2_counter += 1
                        new_line = f"{hashes} {h1_counter}.{h2_counter} {heading_text}"

                    updated_lines.append(new_line)
                    changes_made += 1
                else:
                    # Heading already numbered, update counters based on existing number
                    if level == 1:
                        match = re.match(r'^(\d+)', heading_text)
                        if match:
                            h1_counter = int(match.group(1))
                            h2_counter = 0
                    else:  # level == 2
                        match = re.match(r'^(\d+)\.(\d+)', heading_text)
                        if match:
                            h2_counter = int(match.group(2))

                    updated_lines.append(line)
            else:
                # Level 3+ headings - don't modify
                updated_lines.append(line)
        else:
            # Not a heading
            updated_lines.append(line)

    return '\n'.join(updated_lines), changes_made


def organize_markdown_images(
    markdown_path: str,
    search_root: Optional[str] = None,
    normalize_names: bool = True,
    add_numbers: bool = True,
    dry_run: bool = False
) -> dict:
    """
    Main function to organize markdown images and add heading numbers.

    Returns:
        Dict with operation results
    """
    markdown_path_obj = Path(markdown_path).resolve()

    if not markdown_path_obj.exists():
        return {
            "success": False,
            "error": f"Markdown file not found: {markdown_path_obj}"
        }

    if not markdown_path_obj.is_file():
        return {
            "success": False,
            "error": f"Path is not a file: {markdown_path_obj}"
        }

    # Read markdown content
    with open(markdown_path_obj, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Extract image references
    references = extract_image_references(content)

    image_mapping = {}
    moved_images = []
    missing_images = []
    companion_dir = None
    companion_dir_name = None

    # Process images if any found
    if references:
        # Create companion directory
        companion_dir = create_companion_directory(markdown_path_obj)
        companion_dir_name = companion_dir.name

        # Process images
        search_root_path = Path(search_root).resolve() if search_root else markdown_path_obj.parent

        for full_match, image_ref in references:
            image_name = Path(image_ref).name

            # Find the image file
            image_path = find_image_file(image_ref, markdown_path_obj.parent, search_root_path)

            if not image_path:
                missing_images.append(image_name)
                continue

            # Skip if already in companion directory
            if image_path.parent == companion_dir:
                new_name = image_path.name
                image_mapping[image_name] = new_name
                continue

            # Move image
            if not dry_run:
                new_path = move_image_to_companion(image_path, companion_dir, normalize_names)
                new_name = new_path.name
            else:
                new_name = normalize_image_filename(image_name) if normalize_names else image_name

            image_mapping[image_name] = new_name
            moved_images.append(f"{image_path} -> {companion_dir / new_name}")

        # Update markdown file with new image paths
        if image_mapping:
            content = update_markdown_references(
                content, references, companion_dir_name, image_mapping
            )

    # Add heading numbers if requested
    headings_numbered = 0
    if add_numbers:
        content, headings_numbered = add_heading_numbers(content)

    # Write updated content if changes were made
    if content != original_content and not dry_run:
        with open(markdown_path_obj, 'w', encoding='utf-8') as f:
            f.write(content)

    return {
        "success": True,
        "markdown_file": str(markdown_path_obj),
        "companion_directory": str(companion_dir) if companion_dir else None,
        "images_processed": len(moved_images),
        "images_moved": moved_images,
        "images_missing": missing_images,
        "headings_numbered": headings_numbered,
        "dry_run": dry_run
    }


def main():
    parser = argparse.ArgumentParser(
        description="Organize markdown images and add heading numbers"
    )
    parser.add_argument(
        "markdown_path",
        help="Path to the markdown file"
    )
    parser.add_argument(
        "--search-root",
        help="Root directory to search for images (defaults to markdown directory)"
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Don't normalize image filenames (keep original names)"
    )
    parser.add_argument(
        "--no-numbers",
        action="store_true",
        help="Don't add numeric prefixes to headings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    result = organize_markdown_images(
        args.markdown_path,
        search_root=args.search_root,
        normalize_names=not args.no_normalize,
        add_numbers=not args.no_numbers,
        dry_run=args.dry_run
    )

    if result["success"]:
        print(f"✅ Success!")
        print(f"📄 Markdown: {result['markdown_file']}")

        if result.get('companion_directory'):
            print(f"📁 Companion directory: {result['companion_directory']}")
            print(f"🖼️  Images processed: {result['images_processed']}")

            if result.get("images_moved"):
                print(f"\n✅ Moved images:")
                for move in result["images_moved"]:
                    print(f"  - {move}")

            if result.get("images_missing"):
                print(f"\n⚠️  Missing images (not found):")
                for missing in result["images_missing"]:
                    print(f"  - {missing}")

        if result.get('headings_numbered', 0) > 0:
            print(f"\n🔢 Headings numbered: {result['headings_numbered']}")

        if result.get("dry_run"):
            print(f"\n🔍 DRY RUN - No changes were made")
    else:
        print(f"❌ Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
