#!/usr/bin/env python3
"""Ask for confirmation before recursive rm of high-value directories.

Sessions run in bypassPermissions mode, and Claude Code's built-in critical-path
check only covers the filesystem root, its top-level directories, the home
directory, and the working directory with its parents. This PreToolUse hook also
prompts when `rm -r` targets a direct child of the home directory (e.g. ~/work),
a git repository root or `.git` directory outside temp dirs, or the contents of
any of these via a trailing glob. A hook "ask" still prompts in bypass mode.

The check is best-effort text parsing: it tracks `cd` within the command and
expands `~`, `$HOME`, and globs, but skips other variables and fails open on
commands it cannot tokenize.
"""

# ruff: noqa: D103

import glob
import json
import os
import shlex
import sys
import tempfile
from pathlib import Path

OPERATORS = {";", "&&", "||", "|", "|&", "&", "(", ")"}
WRAPPERS = {"builtin", "command", "env", "nice", "nohup", "noglob", "time"}
GLOB_CHARS = set("*?[")


def split_commands(command: str) -> list[list[str]]:
    """Split a shell command into simple commands, or [] if it can't be tokenized."""
    lexer = shlex.shlex(command.replace("\n", ";"), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return []

    commands: list[list[str]] = [[]]
    for token in tokens:
        if token in OPERATORS:
            commands.append([])
        else:
            commands[-1].append(token)
    return [strip_prefixes(words) for words in commands if words]


def strip_prefixes(words: list[str]) -> list[str]:
    """Drop leading VAR=value assignments and transparent wrappers such as `command`."""
    while words and ("=" in words[0].split("/")[0] or words[0] in WRAPPERS):
        words = words[1:]
    return words


def expand(word: str, cwd: str) -> str | None:
    """Expand ~ and $HOME and resolve against cwd; None when another variable is involved."""
    home = str(Path.home())
    for prefix in ("${HOME}", "$HOME", "~"):
        if word == prefix or word.startswith(prefix + "/"):
            word = home + word[len(prefix) :]
            break
    if "$" in word or "`" in word:
        return None
    return os.path.normpath(os.path.join(cwd, word))


def in_temp_dir(path: str) -> bool:
    roots = {"/tmp", "/private/tmp", "/var/folders", "/private/var/folders", tempfile.gettempdir()}
    return any(path == root or path.startswith(root.rstrip("/") + "/") for root in roots)


def protection_reason(path: str) -> str | None:
    home = str(Path.home())
    if path == home or os.path.dirname(path) == home:
        return "the home directory or one of its top-level entries"
    if in_temp_dir(path):
        return None
    if os.path.basename(path) == ".git" or os.path.lexists(os.path.join(path, ".git")):
        return "a git repository"
    return None


def rm_targets(words: list[str]) -> list[str] | None:
    """Return the operands of a recursive rm, or None when it isn't one."""
    if not words or os.path.basename(words[0]) != "rm":
        return None
    recursive = False
    operands: list[str] = []
    options_done = False
    for word in words[1:]:
        if options_done or not word.startswith("-") or word == "-":
            operands.append(word)
        elif word == "--":
            options_done = True
        elif word == "--recursive" or (not word.startswith("--") and ("r" in word or "R" in word)):
            recursive = True
    return operands if recursive else None


def find_protected(command: str, cwd: str) -> list[str]:
    """Describe each protected path a recursive rm in `command` would delete."""
    findings: list[str] = []
    for words in split_commands(command):
        if words[0] == "cd" and len(words) == 2 and words[1] != "-":
            cwd = expand(words[1], cwd) or cwd
            continue
        for operand in rm_targets(words) or []:
            path = expand(operand, cwd)
            if path is None:
                continue
            candidates = [path]
            if GLOB_CHARS & set(path):
                candidates = glob.glob(path)
                if GLOB_CHARS & set(os.path.basename(path)):
                    # A trailing glob wipes the parent directory's contents
                    candidates.append(os.path.dirname(path))
            for candidate in candidates:
                reason = protection_reason(candidate)
                if reason:
                    findings.append(f"{candidate} ({reason})")
    return list(dict.fromkeys(findings))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    cwd = payload.get("cwd") or os.getcwd()
    findings = find_protected(command, cwd)
    if not findings:
        return 0

    reason = "Recursive rm targets " + "; ".join(findings) + ". Confirm to proceed."
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
