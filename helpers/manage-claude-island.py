#!/usr/bin/env python3
"""
Manage claude-island-state.py hooks in settings/hooks.jsonc.

Usage:
    manage-claude-island.py add      # Add hook to all events
    manage-claude-island.py remove   # Remove hook from all events
    manage-claude-island.py status   # Show which events have the hook
"""

import re
import sys
from pathlib import Path

HOOKS_FILE = Path.home() / ".claude" / "settings" / "hooks.jsonc"
HOOK_COMMAND = "~/.claude/hooks/claude-island-state.py"

# All hook event types that claude-island supports
ALL_EVENTS = [
    "Notification",
    "PermissionRequest",
    "PostToolUse",
    "PreCompact",
    "PreToolUse",
    "SessionEnd",
    "SessionStart",
    "Stop",
    "SubagentStop",
    "UserPromptSubmit",
]


def strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments for JSON parsing."""
    # Remove single-line comments
    text = re.sub(r"//.*$", "", text, flags=re.MULTILINE)
    # Remove multi-line comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def has_hook(content: str, event: str) -> bool:
    """Check if an event has the claude-island hook."""
    # Find the event section and check if it contains our hook
    pattern = rf'"{event}"\s*:\s*\['
    match = re.search(pattern, content)
    if not match:
        return False

    # Find the section for this event and check for our hook
    start = match.end()
    bracket_count = 1
    pos = start
    while pos < len(content) and bracket_count > 0:
        if content[pos] == "[":
            bracket_count += 1
        elif content[pos] == "]":
            bracket_count -= 1
        pos += 1

    section = content[start:pos]
    return "claude-island-state.py" in section


def get_status(content: str) -> dict[str, bool]:
    """Get status of hook for each event."""
    return {event: has_hook(content, event) for event in ALL_EVENTS}


def remove_hooks(content: str) -> str:
    """Remove claude-island hook entries using regex."""
    # Pattern matches the hook entry object with optional trailing comma
    # Handles both cases: entry with comma after, and entry as last item
    pattern = r',?\s*\{\s*"command"\s*:\s*"[^"]*claude-island-state\.py"\s*,\s*"type"\s*:\s*"command"\s*\},?'

    # Remove all matches
    new_content = re.sub(pattern, "", content)

    # Clean up: fix double commas or comma before ]
    new_content = re.sub(r",(\s*[}\]])", r"\1", new_content)
    # Fix leading comma after [
    new_content = re.sub(r"(\[)\s*,", r"\1", new_content)

    return new_content


def find_hooks_array_end(lines: list[str], event: str) -> int | None:
    """Find the line index of the LAST inner hooks array's closing bracket for an event."""
    # Find the event declaration
    event_pattern = rf'"{event}"\s*:'
    event_line_idx = None

    for i, line in enumerate(lines):
        if re.search(event_pattern, line):
            event_line_idx = i
            break

    if event_line_idx is None:
        return None

    # Find the end of this event's outer array (the ] that closes "EventName": [...])
    # by tracking bracket depth from the event line
    event_end_idx = None
    outer_depth = 0
    started = False
    for i in range(event_line_idx, len(lines)):
        for char in lines[i]:
            if char == "[":
                outer_depth += 1
                started = True
            elif char == "]":
                outer_depth -= 1
                if started and outer_depth == 0:
                    event_end_idx = i
                    break
        if event_end_idx is not None:
            break

    if event_end_idx is None:
        return None

    # Find ALL "hooks": [ arrays within this event section and return the last one's closing ]
    hooks_pattern = r'"hooks"\s*:\s*\['
    last_hooks_end = None

    for i in range(event_line_idx, event_end_idx + 1):
        line = lines[i]
        if re.search(hooks_pattern, line):
            # Found a hooks array, find its closing ]
            inner_depth = 0
            for j in range(i, event_end_idx + 1):
                for char in lines[j]:
                    if char == "[":
                        inner_depth += 1
                    elif char == "]":
                        inner_depth -= 1
                        if inner_depth == 0:
                            last_hooks_end = j
                            break
                if inner_depth == 0:
                    break

    return last_hooks_end


def add_hooks(lines: list[str], content: str) -> list[str]:
    """Add claude-island hook to events that don't have it."""
    status = get_status(content)
    result = lines.copy()

    # Process events in reverse order to maintain line indices
    events_to_add = [
        (e, find_hooks_array_end(result, e)) for e in ALL_EVENTS if not status[e]
    ]
    events_to_add = [(e, idx) for e, idx in events_to_add if idx is not None]
    events_to_add.sort(key=lambda x: x[1], reverse=True)

    for _event, closing_bracket_idx in events_to_add:
        # Determine indentation from surrounding lines
        bracket_line = result[closing_bracket_idx]
        indent = len(bracket_line) - len(bracket_line.lstrip())
        hook_indent = " " * (indent + 2)

        # Check if we need to add a comma to the previous entry
        prev_idx = closing_bracket_idx - 1
        while prev_idx >= 0 and not result[prev_idx].strip():
            prev_idx -= 1

        if prev_idx >= 0:
            prev_line = result[prev_idx].rstrip()
            if prev_line.endswith("}"):
                result[prev_idx] = prev_line + ",\n"

        # Create the hook entry
        hook_entry = [
            f"{hook_indent}{{\n",
            f'{hook_indent}  "command": "{HOOK_COMMAND}",\n',
            f'{hook_indent}  "type": "command"\n',
            f"{hook_indent}}}\n",
        ]

        # Insert before the closing bracket
        result = (
            result[:closing_bracket_idx] + hook_entry + result[closing_bracket_idx:]
        )

    return result


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("add", "remove", "status"):
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if not HOOKS_FILE.exists():
        print(f"Error: {HOOKS_FILE} not found")
        sys.exit(1)

    content = HOOKS_FILE.read_text()
    lines = content.splitlines(keepends=True)

    if command == "status":
        status = get_status(content)
        print("Claude Island hook status:")
        for event in ALL_EVENTS:
            symbol = "✓" if status[event] else "✗"
            print(f"  {symbol} {event}")
        enabled_count = sum(status.values())
        print(f"\nEnabled: {enabled_count}/{len(ALL_EVENTS)}")

    elif command == "remove":
        new_content = remove_hooks(content)
        if new_content != content:
            HOOKS_FILE.write_text(new_content)
            print("Removed claude-island hooks")
        else:
            print("No claude-island hooks found")

    elif command == "add":
        new_lines = add_hooks(lines, content)
        if new_lines != lines:
            HOOKS_FILE.write_text("".join(new_lines))
            print("Added claude-island hooks")
        else:
            print("All events already have claude-island hooks")


if __name__ == "__main__":
    main()
