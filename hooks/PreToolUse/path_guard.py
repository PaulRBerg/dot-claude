#!/usr/bin/env python3
"""Deny reads and edits of secrets and of files the user owns.

These were `permissions.deny` entries for Read and Edit. A deny or ask rule for Read or Edit
in `settings/` brings back Claude Code's prompt for dangerous `rm` commands (see
`settings/basics.jsonc`), so this PreToolUse hook enforces them instead:

- everything under the directories in SECRET_DIRS;
- any file named in USER_FILES, in any directory.

It checks the path a file tool names, the directory Grep and Glob search, and in Bash the
operands of the file commands in FILE_COMMANDS plus redirection targets. Like the rules it
replaces, it does not see a command that reads files without naming them, such as
`grep -r pattern .`, or a script that opens files itself. Unlike those rules, it does not
filter `@file` mentions or Grep and Glob results from a parent directory.
"""

import json
import os
import re
import sys
from collections.abc import Iterator
from pathlib import PurePath

import shell_commands

SECRET_DIRS = ("~/.ssh", "~/Drive/Secrets")
USER_FILES = {"PROMPT.md", "TODO.md"}
PATH_FIELDS = ("file_path", "notebook_path", "path")
FILE_COMMANDS = {
    "awk",
    "base64",
    "bat",
    "cat",
    "cp",
    "head",
    "less",
    "more",
    "mv",
    "sed",
    "tail",
    "tee",
}
REDIRECTION = re.compile(r"[<>]\s*([^\s;&|()<>]+)")


def denial_reason(path: str, cwd: str) -> str | None:
    """Return why a path is off limits, or None. Checks the path as written and resolved."""
    for prefix in ("${HOME}", "$HOME"):
        if path == prefix or path.startswith(prefix + "/"):
            path = "~" + path[len(prefix) :]
    written = os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))
    forms = {written, os.path.realpath(written)}
    if any(os.path.basename(form) in USER_FILES for form in forms):
        return f"{written} is a user-owned file that agents must not read or edit"
    for secret_dir in SECRET_DIRS:
        root = os.path.expanduser(secret_dir)
        roots = (root, os.path.realpath(root))
        if any(form == base or form.startswith(base + "/") for form in forms for base in roots):
            return f"{written} is inside {secret_dir}, which holds secrets"
    return None


def bash_paths(command: str) -> Iterator[str]:
    """Yield the paths a shell command reads or writes by name."""
    for target in REDIRECTION.findall(shell_commands.strip_heredocs(command)):
        yield target.strip("\"'")
    for words in shell_commands.walk_commands(command):
        words = shell_commands.unwrap(words)
        if words and PurePath(words[0]).name in FILE_COMMANDS:
            yield from (word for word in words[1:] if not word.startswith("-"))


def tool_denial(tool_input: dict[str, object], cwd: str) -> str | None:
    """Return the denial reason for one tool call, or None to allow it."""
    command = tool_input.get("command")
    paths = [tool_input[field] for field in PATH_FIELDS if field in tool_input]
    if isinstance(command, str):
        paths.extend(bash_paths(command))
    for path in paths:
        reason = denial_reason(path, cwd) if isinstance(path, str) and path else None
        if reason:
            return reason
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        reason = tool_denial(payload["tool_input"], payload.get("cwd") or os.getcwd())
    except KeyError, TypeError, ValueError, AttributeError:
        return 0
    if reason:
        output = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked: {reason}. Ask the user for what you need.",
        }
        print(json.dumps({"hookSpecificOutput": output}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
