#!/usr/bin/env python3
"""Deny git commands that sweep other agents' work in a shared worktree.

This PreToolUse hook is the only enforcement of these rules: a deny or ask rule for Bash in
``settings/`` would bring back Claude Code's prompt for dangerous ``rm`` commands (see
``settings/basics.jsonc``). It parses every git invocation in a shell command and checks its
options in any order:

- bare ``git stash`` and stash push/save/clear, while ``git stash list/show/pop`` stay usable;
- ``git add -A/--all/-u`` without paths, ``git add .``, and ``git commit -a/--all`` anywhere;
- ``git checkout .``, ``git restore .``, ``git reset --hard``, ``git clean``;
- ``--autostash`` (flag or config) on pull, rebase, and merge.

Force pushes in any form, including ``git -C <repo> push --force``, get an "ask" decision,
which still prompts in bypass mode. A script that cannot be lexed as a whole is checked line
by line.
"""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import PurePath

from shell_commands import unwrap, walk_commands

GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--config-env", "--git-dir", "--namespace", "--work-tree"}
TREE_PATHSPECS = {".", "./", ":/", ":/."}
STASH_READ_SUBCOMMANDS = {"apply", "branch", "create", "drop", "list", "pop", "show", "store"}
AUTOSTASH_CONFIG_KEYS = {"merge.autostash", "rebase.autostash"}
FALSE_VALUES = {"0", "false", "no", "off"}

# Short options whose value is attached or the next argument; they end an option cluster.
SHORT_VALUE_OPTIONS = {
    "checkout": "bB",
    "commit": "mFCct",
    "push": "o",
    "restore": "s",
}
# Short options whose optional value can only be attached, such as `git commit -S<keyid>`.
SHORT_ATTACHED_OPTIONS = {"commit": "Su"}
LONG_VALUE_OPTIONS = {
    "commit": {
        "--author",
        "--cleanup",
        "--date",
        "--file",
        "--fixup",
        "--message",
        "--reedit-message",
        "--reuse-message",
        "--squash",
        "--template",
        "--trailer",
    },
    "push": {"--push-option", "--receive-pack", "--repo"},
    "restore": {"--source"},
}

SHARED_WORK = "including other agents' uncommitted work"
REASONS = {
    "add": f"stages every change in the shared worktree, {SHARED_WORK}; stage the paths you "
    "edited instead",
    "commit": f"commits every tracked modification in the shared worktree, {SHARED_WORK}; "
    "stage the paths you edited and commit with `ai-commit`",
    "stash": f"moves uncommitted changes into the shared stash, {SHARED_WORK}. Read-only "
    "`git stash list` and `git stash show` stay available",
    "checkout": f"discards every uncommitted change in the shared worktree, {SHARED_WORK}; "
    "restore only paths you edited",
    "restore": f"resets every path in the shared worktree or index, {SHARED_WORK}; restore "
    "only paths you edited",
    "reset": f"discards every uncommitted change in the shared worktree, {SHARED_WORK}; "
    "revert only paths you edited",
    "clean": f"deletes untracked files in the shared worktree, {SHARED_WORK}; remove only "
    "paths you created",
    "autostash": f"stashes the shared worktree, {SHARED_WORK}; pull or rebase with "
    "`--no-autostash` on a clean tree",
    "push": "force-pushes, which rewrites remote history and can drop other agents' or "
    "collaborators' commits; confirm the branch and intent first",
}


def parse_options(subcommand: str, args: list[str]) -> tuple[set[str], list[str]]:
    """Return the options (``--long`` names or ``-x`` letters) and operands of a subcommand."""
    short_values = SHORT_VALUE_OPTIONS.get(subcommand, "")
    short_attached = SHORT_ATTACHED_OPTIONS.get(subcommand, "")
    long_values = LONG_VALUE_OPTIONS.get(subcommand, set())
    options: set[str] = set()
    operands: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        index += 1
        if arg == "--":
            operands.extend(args[index:])
            break
        if arg.startswith("--"):
            name = arg.split("=", 1)[0]
            options.add(name)
            if "=" not in arg and name in long_values:
                index += 1
        elif arg.startswith("-") and len(arg) > 1:
            for position, letter in enumerate(arg[1:], start=2):
                options.add(f"-{letter}")
                if letter in short_values:
                    if position == len(arg):
                        index += 1
                    break
                if letter in short_attached:
                    break
        else:
            operands.append(arg)
    return options, operands


def git_denial(args: list[str]) -> str | None:
    """Return the denial reason for one git invocation's arguments, or None to allow it."""
    autostash_config = False
    while args and args[0].startswith("-"):
        option, args = args[0], args[1:]
        if option in GIT_OPTIONS_WITH_VALUE and args:
            value, args = args[0], args[1:]
            key, _, setting = value.partition("=")
            if option == "-c" and key.lower() in AUTOSTASH_CONFIG_KEYS:
                autostash_config = setting.lower() not in FALSE_VALUES
    if not args:
        return None
    subcommand, args = args[0], args[1:]
    options, operands = parse_options(subcommand, args)
    tree_operand = any(operand in TREE_PATHSPECS for operand in operands)

    if subcommand == "add":
        tree_wide = bool({"-A", "--all"} & options) or (
            bool({"-u", "--update"} & options) and not operands
        )
        denied = tree_wide or tree_operand
    elif subcommand == "commit":
        denied = bool({"-a", "--all"} & options) or tree_operand
    elif subcommand == "stash":
        denied = (
            not args
            or args[0] in {"clear", "push", "save"}
            or (args[0] not in STASH_READ_SUBCOMMANDS and args[0].startswith("-"))
        )
    elif subcommand in {"checkout", "restore"}:
        denied = tree_operand
    elif subcommand == "reset":
        denied = "--hard" in options
    elif subcommand == "clean":
        denied = True
    elif subcommand in {"merge", "pull", "rebase"}:
        if "--no-autostash" in options:
            return None
        return REASONS["autostash"] if "--autostash" in options or autostash_config else None
    elif subcommand == "push":
        denied = bool(
            {"--force", "--force-with-lease", "--force-if-includes", "-f"} & options
        ) or any(operand.startswith("+") for operand in operands)
    else:
        denied = False
    return REASONS[subcommand] if denied else None


def command_decision(script: str) -> tuple[str, str] | None:
    """Return the first (decision, reason) for any git invocation in a shell script.

    Force pushes get "ask" so the user can approve them; every other match is denied.
    """
    for words in walk_commands(script):
        words = unwrap(words)
        if words and PurePath(words[0]).name == "git":
            reason = git_denial(words[1:])
            if reason:
                decision = "ask" if reason == REASONS["push"] else "deny"
                return decision, f"`{shlex.join(words)}` {reason}."
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload["tool_input"]["command"]
        script = shlex.join(command) if isinstance(command, list) else command
        result = command_decision(script)
    except KeyError, TypeError, ValueError:
        return 0
    if result:
        decision, reason = result
        output = {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
        print(json.dumps({"hookSpecificOutput": output}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
