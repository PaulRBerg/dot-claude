#!/usr/bin/env python3
"""Deny system-level commands that no agent session should run.

These were `permissions.deny` entries for Bash. A deny or ask rule for Bash in `settings/`
brings back Claude Code's prompt for dangerous `rm` commands (see `settings/basics.jsonc`),
so this PreToolUse hook enforces them instead. It checks every simple command in a shell
script, including `sh -c` scripts and commands behind wrappers such as `env` or `timeout`:

- privilege escalation and account changes: `sudo`, `doas`, `su`, `passwd`, `userdel`,
  `usermod`;
- disk and machine control: `dd`, `mkfs`, `reboot`, `shutdown`, `systemctl`;
- process sweeps: `killall` and `kill -9`;
- recursive `chmod` and `chown`;
- `npm publish`.

It matches the program a command names, so it guards against mistakes, not against a
command that hides the program behind `xargs`, `eval`, or an interpreter.
"""

import json
import re
import shlex
import sys
from pathlib import PurePath

import shell_commands

DENIED_PROGRAMS = {
    "dd": "writes raw blocks and can overwrite a disk",
    "doas": "escalates privileges",
    "killall": "kills processes by name, including other agents' processes",
    "mkfs": "formats a filesystem",
    "passwd": "changes account credentials",
    "reboot": "restarts the machine",
    "shutdown": "powers off the machine",
    "su": "escalates privileges",
    "sudo": "escalates privileges",
    "systemctl": "controls system services",
    "userdel": "changes user accounts",
    "usermod": "changes user accounts",
}
RECURSIVE_OPTION = re.compile(r"-[A-Za-z]*R[A-Za-z]*|--recursive")
SIGKILL = re.compile(r"(?:^| )-(?:s ?)?(?:SIG)?(?:9|KILL)(?: |$)")


def denial(words: list[str]) -> str | None:
    """Return why one simple command is denied, or None to allow it."""
    inner = shell_commands.unwrap(words)
    wrappers = {PurePath(word).name for word in words[: len(words) - len(inner)]}
    if "sudo" in wrappers:
        return DENIED_PROGRAMS["sudo"]
    if not inner:
        return None
    program, args = PurePath(inner[0]).name, inner[1:]
    if program in DENIED_PROGRAMS:
        return DENIED_PROGRAMS[program]
    if program.startswith("mkfs."):
        return DENIED_PROGRAMS["mkfs"]
    if program in {"chmod", "chown"} and any(RECURSIVE_OPTION.fullmatch(arg) for arg in args):
        return "changes permissions or ownership for a whole tree; name the files instead"
    if program == "kill" and SIGKILL.search(" ".join(args)):
        return "kills without cleanup; send the default SIGTERM first"
    if program == "npm" and next((arg for arg in args if not arg.startswith("-")), "") == "publish":
        return "publishes a package to the npm registry"
    return None


def command_denial(script: str) -> str | None:
    """Return the denial message for the first denied command in a shell script."""
    for words in shell_commands.walk_commands(script):
        reason = denial(words)
        if reason:
            return (
                f"Blocked: `{shlex.join(words)}` {reason}. This guard cannot be approved from "
                "a prompt; ask the user to run the command themselves."
            )
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        reason = command_denial(payload["tool_input"]["command"])
    except AttributeError, KeyError, TypeError, ValueError:
        return 0
    if reason:
        output = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
        print(json.dumps({"hookSpecificOutput": output}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
