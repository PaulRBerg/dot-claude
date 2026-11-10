#!/usr/bin/env python3
"""Deny recursive rm of paths whose loss would be catastrophic.

Sessions run in bypassPermissions mode with CLAUDE_CODE_EVEN_MORE_DANGEROUSLY_SKIP_PERMISSIONS
set, which turns off Claude Code's own prompt for `rm` on critical paths. This PreToolUse
hook is the remaining guard. It denies `rm -r` of:

- the filesystem root and system top-level directories such as `/usr` or `/Volumes/<drive>`;
- the home directory, its visible top-level directories, and the dot-directories in
  HOME_DOTDIRS;
- a git repository root or its `.git` directory, outside temp, cache, and dependency
  directories. Submodules and linked worktrees, whose `.git` is a file, stay removable;
- the whole contents of any of these through a `*` or `.*` glob;
- a path under an unset variable that lands on one of these when the variable is empty,
  such as `"$DIR"/*`.

Every other rm runs unprompted. A denial cannot be approved from a prompt: Claude narrows
the path or asks the user to run the command.

The check is best-effort text parsing: it tracks `cd` and plain assignments within the
command and expands `~`, environment variables, `$(pwd)`, and globs. `xargs rm`,
`find -delete`, and other command substitutions pass through unchecked, so it guards
against mistakes, not adversarial commands.
"""

import glob
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePath

import shell_commands

GLOB_CHARS = set("*?[")
# A basename that selects a directory's whole contents.
WIPE = re.compile(r"\.?\*+")
VARIABLE = re.compile(r"\$(\w+)|\$\{(\w+)\}")
UNSET_PREFIX = re.compile(r"(\$\w+|\$\{\w+\})(/.*)")
ROOT_PARENTS = {"/", "/private", "/System", "/System/Volumes", "/Users", "/Volumes"}
HOME_DOTDIRS = {".agents", ".claude", ".codex", ".config", ".gnupg", ".local", ".omp", ".ssh"}
# Repositories under these directories are caches or dependencies, not working clones.
EXEMPT_SEGMENTS = {".cache", "Caches", "node_modules"}
# Builtins whose arguments are assignments, as in `export OUT=/tmp/build`.
DECLARATIONS = {"declare", "export", "local", "readonly", "typeset"}


def in_temp_dir(path: str) -> bool:
    roots = {"/tmp", "/private/tmp", "/var/folders", "/private/var/folders", tempfile.gettempdir()}
    return any(path == root or path.startswith(root.rstrip("/") + "/") for root in roots)


def protection_reason(path: str) -> str | None:
    home = str(Path.home())
    name = os.path.basename(path)
    if path == home:
        return "the home directory"
    if os.path.dirname(path) == home:
        protected = os.path.isdir(path) and (not name.startswith(".") or name in HOME_DOTDIRS)
        return "a top-level home directory" if protected else None
    if path == "/" or (os.path.dirname(path) in ROOT_PARENTS and os.path.lexists(path)):
        return "a system top-level directory"
    if in_temp_dir(path) or EXEMPT_SEGMENTS & set(PurePath(path).parts):
        return None
    if name == ".git" and os.path.isdir(path):
        return "a git repository's history"
    if os.path.isdir(os.path.join(path, ".git")):
        return "a git repository root"
    return None


def substitute(word: str, variables: dict[str, str]) -> str:
    """Expand a leading `~` and every variable whose value is known."""
    if word == "~" or word.startswith("~/"):
        word = str(Path.home()) + word[1:]
    return VARIABLE.sub(lambda match: variables.get(match[1] or match[2], match[0]), word)


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


def operand_denial(operand: str, cwd: str | None, variables: dict[str, str]) -> str | None:
    """Describe the protected path a recursive rm operand would delete, or None.

    `cwd` is None once the command has changed to a directory this hook cannot resolve.
    """
    word = substitute(operand, variables)
    note = ""
    unset = UNSET_PREFIX.fullmatch(word)
    if unset:
        # An unset variable expands to nothing, leaving only the path that follows it.
        word = unset[2]
        note = f", which `{operand}` becomes when {unset[1]} is empty; guard it as `${{VAR:?}}`"
    if "$" in word or "`" in word or (cwd is None and not word.startswith("/")):
        return None
    path = os.path.normpath(os.path.join(cwd or "/", word))
    path = path[1:] if path.startswith("//") else path

    candidates = [path]
    if GLOB_CHARS & set(path):
        candidates = glob.glob(path)
        if WIPE.fullmatch(os.path.basename(path)):
            candidates.insert(0, os.path.dirname(path))
    for candidate in candidates:
        reason = protection_reason(candidate)
        if reason:
            return f"{candidate} ({reason}{note})"
    return None


def change_directory(words: list[str], cwd: str | None, variables: dict[str, str]) -> str | None:
    """Return the working directory after a `cd`, or None when it cannot be resolved."""
    target = substitute(words[1], variables) if len(words) == 2 else "~"
    target = str(Path.home()) if target == "~" else target
    if "$" in target or "`" in target or target == "-" or (cwd is None and target[:1] != "/"):
        return None
    return os.path.normpath(os.path.join(cwd or "/", target))


def find_denials(command: str, cwd: str | None) -> list[str]:
    """Describe each protected path a recursive rm in `command` would delete."""
    variables = {**os.environ, "PWD": cwd or ""}
    command = command.replace("$(pwd)", "$PWD").replace("`pwd`", "$PWD")
    findings: list[str] = []
    for words in shell_commands.walk_commands(command):
        assignments = words[1:] if words[0] in DECLARATIONS else words
        if all(shell_commands.ASSIGNMENT.match(word) for word in assignments):
            for word in assignments:
                name, _, value = word.partition("=")
                variables[name] = substitute(value, variables)
            continue
        words = shell_commands.unwrap(words)
        if words and words[0] in {"cd", "pushd", "popd"}:
            cwd = change_directory(words, cwd, variables) if words[0] == "cd" else None
            variables["PWD"] = cwd or "$"  # a lone `$` never resolves, so the path stays unknown
            continue
        for operand in rm_targets(words) or []:
            finding = operand_denial(operand, cwd, variables)
            if finding:
                findings.append(finding)
    return list(dict.fromkeys(findings))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload["tool_input"]["command"]
        findings = find_denials(command, payload.get("cwd") or os.getcwd())
    except AttributeError, KeyError, TypeError, ValueError:
        return 0
    if not findings:
        return 0

    reason = (
        "Blocked: recursive rm targets "
        + "; ".join(findings)
        + ". This guard cannot be approved from a prompt. Remove a narrower path, or ask the "
        "user to run the command themselves."
    )
    output = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
    print(json.dumps({"hookSpecificOutput": output}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
