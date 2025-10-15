#!/usr/bin/env python3
"""General-purpose prompt flag parser for Claude Code hooks.

Parses trailing flags from prompts (e.g., "my prompt -s -c") and executes
corresponding actions. Flags must appear at the end with no other text after them.
"""

import json
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional


# ============================================================================
# FLAG HANDLERS
# ============================================================================


def handle_subagent_flag(script_dir: Path) -> str:
    """Handle -s flag: Append subagent orchestration instructions."""
    subagents_path = script_dir / "SUBAGENTS.md"

    try:
        with open(subagents_path, "r") as f:
            return f.read().rstrip()
    except FileNotFoundError:
        print(f"Warning: {subagents_path} not found", file=sys.stderr)
        return ""


def handle_commit_flag(script_dir: Path) -> str:
    """Handle -c flag: Instruct Claude to execute /commit."""
    return (
        "IMPORTANT: After completing your task, use the SlashCommand tool "
        "to execute the '/commit' slash command to create a git commit."
    )


def handle_test_flag(script_dir: Path) -> str:
    """Handle -t flag: Add testing emphasis context."""
    return (
        "IMPORTANT: Ensure comprehensive test coverage for this task. "
        "Include unit tests for core logic, integration tests for interactions, "
        "and edge case handling. Verify all tests pass before completing."
    )


def handle_debug_flag(script_dir: Path) -> str:
    """Handle -d flag: Invoke debugger agent for root cause analysis."""
    return (
        "IMPORTANT: Use the Task tool to invoke the debugger subagent "
        "for systematic root cause analysis. The debugger will:\n"
        "1. Capture error messages and stack traces\n"
        "2. Identify reproduction steps\n"
        "3. Isolate the failure location\n"
        "4. Implement minimal fix\n"
        "5. Verify solution works"
    )


# ============================================================================
# FLAG REGISTRY
# ============================================================================

# Map flag letter to handler function
RECOGNIZED_FLAGS: Dict[str, Callable[[Path], str]] = {
    "s": handle_subagent_flag,
    "c": handle_commit_flag,
    "t": handle_test_flag,
    "d": handle_debug_flag,
}


# ============================================================================
# CORE LOGIC
# ============================================================================


def parse_trailing_flags(prompt: str) -> Optional[tuple[str, List[str]]]:
    """Parse trailing flags from prompt.

    Args:
        prompt: The user's prompt text

    Returns:
        Tuple of (clean_prompt, flags_list) if flags found, None otherwise.
        Example: ("my task", ["s", "c"]) for "my task -s -c"
    """
    # Match: anything followed by one or more -X flags at the end
    # Pattern: (.*?) captures main prompt, ((?:-[a-z]\s*)+) captures flags
    pattern = r"^(.*?)\s+((?:-[a-z]\s*)+)$"
    match = re.match(pattern, prompt.strip())

    if not match:
        return None

    clean_prompt = match.group(1).strip()
    flags_str = match.group(2).strip()

    # Extract individual flag letters: "-s -c" -> ["s", "c"]
    flags = [flag.strip("-") for flag in flags_str.split() if flag.startswith("-")]

    return (clean_prompt, flags)


def validate_flags(flags: List[str]) -> bool:
    """Check if all flags are recognized."""
    return all(flag in RECOGNIZED_FLAGS for flag in flags)


def execute_flag_handlers(flags: List[str], script_dir: Path) -> List[str]:
    """Execute handlers for each flag and return context pieces."""
    contexts = []

    for flag in flags:
        handler = RECOGNIZED_FLAGS.get(flag)
        if handler:
            context = handler(script_dir)
            if context:  # Only add non-empty context
                contexts.append(context)

    return contexts


def build_output_context(
    flags: List[str], clean_prompt: str, flag_contexts: List[str]
) -> str:
    """Build the final context string to add to the prompt."""
    parts = []

    # Note which flags were processed
    flags_str = " ".join(f"-{flag}" for flag in flags)
    parts.append(f"Note: Processed flags {flags_str}")
    parts.append(f"Your actual task (without flags): {clean_prompt}")
    parts.append("")  # Blank line separator

    # Add all flag-generated contexts
    parts.extend(flag_contexts)

    return "\n".join(parts)


def main() -> None:
    """Main hook entry point."""
    # Parse input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    prompt = input_data.get("prompt", "")
    if not prompt:
        sys.exit(0)  # No prompt, nothing to do

    # Parse trailing flags
    result = parse_trailing_flags(prompt)
    if not result:
        sys.exit(0)  # No flags found, exit silently

    clean_prompt, flags = result

    # Validate all flags are recognized
    if not validate_flags(flags):
        sys.exit(0)  # Unrecognized flag, exit silently

    # Execute flag handlers
    script_dir = Path(__file__).parent
    flag_contexts = execute_flag_handlers(flags, script_dir)

    # Build final context
    additional_context = build_output_context(flags, clean_prompt, flag_contexts)

    # Output JSON for UserPromptSubmit hook
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context,
        }
    }

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
