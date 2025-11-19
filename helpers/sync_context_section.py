#!/usr/bin/env python3
"""
Sync a markdown section from next-template to Sablier projects.

Usage:
    uv run sync_context_section.py [--section "## Section Name"]

Default section: ## Lint Rules
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Configuration
HOME = Path.home()
TEMPLATE_FILE = HOME / "work/templates/next-template/CLAUDE.md"
TARGET_FILES = [
    HOME / "sablier/backend/indexers/CLAUDE.md",
    HOME / "sablier/business/accounting/CLAUDE.md",
    HOME / "sablier/frontend/gh-searcher/CLAUDE.md",
    HOME / "sablier/new-ui/CLAUDE.md",
    HOME / "sablier/old-ui/CLAUDE.md",
]


def has_uncommitted_changes(file_path: Path) -> bool:
    """Check if file has uncommitted changes in git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", str(file_path)],
            capture_output=True,
            text=True,
            cwd=file_path.parent,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def extract_section(content: str, section_title: str) -> str | None:
    """
    Extract a markdown section by title.
    Returns content from section heading to next same-level heading or EOF.
    """
    # Match the section heading and capture everything until next ## heading
    pattern = rf"^({re.escape(section_title)}\s*\n)(.*?)(?=^##|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if not match:
        return None

    # Return heading + content
    return match.group(1) + match.group(2)


def remove_section(content: str, section_title: str) -> str:
    """
    Remove a markdown section by title.
    Returns content with section removed.
    """
    # Match the section and everything until next ## heading
    pattern = rf"^{re.escape(section_title)}\s*\n.*?(?=^##|\Z)"
    result = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)

    # Clean up excessive blank lines (more than 2 consecutive)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def insert_section_after_first_heading(content: str, section: str) -> str:
    """
    Insert section after the first markdown heading and any intro text.
    Preserves intro content before the section.
    """
    # Find first heading (any level)
    heading_match = re.search(r"^#.*\n", content, re.MULTILINE)

    if not heading_match:
        # No heading found, prepend section
        return section + "\n\n" + content

    # Check if there's content between first heading and first ## heading
    after_first_heading = content[heading_match.end() :]
    next_h2_match = re.search(r"^##\s", after_first_heading, re.MULTILINE)

    if next_h2_match:
        # There's content before the next ## heading - preserve it
        intro_content_end = heading_match.end() + next_h2_match.start()
        intro_content = content[heading_match.end() : intro_content_end]

        # Insert section after intro content
        # Strip trailing whitespace from intro
        intro_content = intro_content.rstrip() + "\n\n"

        return (
            content[: heading_match.end()]
            + intro_content
            + section
            + "\n"
            + after_first_heading[next_h2_match.start() :]
        )
    else:
        # No ## heading found, insert after first heading
        pos = heading_match.end()

        # Ensure proper spacing
        if not after_first_heading.startswith("\n"):
            section = "\n" + section

        if not section.endswith("\n\n"):
            section = section.rstrip("\n") + "\n\n"

        return content[:pos] + section + after_first_heading


def update_file(
    file_path: Path, new_section: str, section_title: str
) -> tuple[bool, str]:
    """
    Update a file by replacing its section with new_section.
    Returns (modified, result_message) tuple.
    """
    if not file_path.exists():
        return False, "⚠️  File not found"

    if has_uncommitted_changes(file_path):
        return False, "⚠️  Uncommitted changes"

    try:
        content = file_path.read_text()
        original_content = content

        # Find the target section
        section_pattern = rf"^({re.escape(section_title)}\s*\n)(.*?)(?=^##|\Z)"
        section_match = re.search(section_pattern, content, re.MULTILINE | re.DOTALL)

        if section_match:
            # Section exists - replace it in place
            old_section = section_match.group(0)
            new_section_clean = new_section.rstrip() + "\n\n"
            new_content = content.replace(old_section, new_section_clean, 1)
        else:
            # Section doesn't exist - insert after intro text
            heading_match = re.search(r"^#[^#].*\n", content, re.MULTILINE)
            if not heading_match:
                return False, "⚠️  Missing heading"

            after_heading = content[heading_match.end() :]
            first_h2_match = re.search(r"^##\s", after_heading, re.MULTILINE)

            if first_h2_match:
                # Insert before first ## section
                insert_pos = heading_match.end() + first_h2_match.start()
                intro_text = content[heading_match.end() : insert_pos].rstrip() + "\n\n"
                new_section_clean = new_section.rstrip() + "\n\n"
                new_content = (
                    content[: heading_match.end()]
                    + intro_text
                    + new_section_clean
                    + content[insert_pos:]
                )
            else:
                # No ## sections exist, append at end
                new_section_clean = "\n" + new_section.rstrip() + "\n"
                new_content = content.rstrip() + new_section_clean

        # Clean up excessive blank lines
        new_content = re.sub(r"\n{3,}", "\n\n", new_content)

        # Only write if content changed
        if new_content != original_content:
            file_path.write_text(new_content)
            return True, "✅ Updated"
        else:
            return False, "ℹ️  No changes"

    except Exception as e:
        return False, f"❌ Error: {e}"


def print_table(results: list[tuple[Path, str]]):
    """Print results in a nice ASCII table."""
    # Calculate relative paths for display
    rows = []
    for file_path, result in results:
        try:
            rel_path = file_path.relative_to(HOME)
            # Show only the project directory, not the CLAUDE.md file
            display_path = f"~/{rel_path.parent}"
        except ValueError:
            display_path = str(file_path.parent)
        rows.append((display_path, result))

    # Calculate column widths
    file_width = max(len(row[0]) for row in rows) + 2
    result_width = max(len(row[1]) for row in rows) + 2

    # Print table
    print(f"┌{'─' * file_width}┬{'─' * result_width}┐")
    print(f"│{'File'.center(file_width)}│{'Result'.center(result_width)}│")
    print(f"├{'─' * file_width}┼{'─' * result_width}┤")

    for display_path, result in rows:
        print(
            f"│ {display_path.ljust(file_width - 1)}│ {result.ljust(result_width - 1)}│"
        )

    print(f"└{'─' * file_width}┴{'─' * result_width}┘")


def main(section_title: str):
    # Extract section from template
    if not TEMPLATE_FILE.exists():
        print(f"❌ Template file not found: {TEMPLATE_FILE}", file=sys.stderr)
        sys.exit(1)

    template_content = TEMPLATE_FILE.read_text()
    section = extract_section(template_content, section_title)

    if not section:
        print(f"❌ Section '{section_title}' not found in template", file=sys.stderr)
        sys.exit(1)

    print(f"📋 Extracted '{section_title}' section from template")
    print(f"   ({len(section)} characters)\n")

    # Update each target file and collect results
    results = []
    updated_count = 0

    for target in TARGET_FILES:
        modified, result_msg = update_file(target, section, section_title)
        results.append((target, result_msg))
        if modified:
            updated_count += 1

    # Print results table
    print_table(results)

    print(f"\n✨ Done! Updated {updated_count}/{len(TARGET_FILES)} files")


if __name__ == "__main__":
    DEFAULT_SECTION = "## Lint Rules"

    parser = argparse.ArgumentParser(
        description="Sync a markdown section from next-template to Sablier projects."
    )
    parser.add_argument(
        "--section",
        type=str,
        default=DEFAULT_SECTION,
        help=f'Section name to sync (e.g., "## Lint Rules"). Default: {DEFAULT_SECTION}',
    )
    args = parser.parse_args()

    # Use default if section is empty string
    section = args.section if args.section else DEFAULT_SECTION
    main(section)
