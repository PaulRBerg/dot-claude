"""Shell-command parsing shared by the PreToolUse guards.

The guards read the Bash tool's command as text. These helpers split it into simple
commands and strip what stands between a guard and the program a command runs: heredoc
bodies, redirections, assignments, shell keywords, and wrappers such as ``env``. The parsing
is best-effort, so the guards catch mistakes, not commands built to evade them.
"""

from __future__ import annotations

import contextlib
import re
import shlex
from collections.abc import Iterator
from pathlib import PurePath

SEPARATOR_CHARS = ";&|()`\n"
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
REDIRECTION = re.compile(r"^\d*(?:>>?|<<?|>&|<&)(.*)$")
HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_]\w*)\1")
SHELL_HEREDOC = re.compile(r"(?:^|[;&|(])\s*(?:[\w./-]*/)?(?:bash|dash|sh|zsh)\b[^|;&]*<<")
# Wrapper commands mapped to their options that take the next argument as a value.
WRAPPERS = {
    "builtin": set(),
    "command": set(),
    "env": {"-C", "-S", "-u", "--chdir", "--split-string", "--unset"},
    "exec": {"-a"},
    "nice": {"-n"},
    "nohup": set(),
    "noglob": set(),
    "sudo": {"-C", "-g", "-h", "-p", "-u"},
    "time": set(),
    "timeout": {"-k", "-s"},
}
SHELLS = {"bash", "dash", "sh", "zsh"}
# Reserved words that precede a command in a compound statement, as in `then rm -rf x`.
KEYWORDS = {"!", "{", "do", "elif", "else", "if", "then", "until", "while"}


def split_commands(script: str) -> list[list[str]]:
    """Split a shell script into simple commands; raise ValueError when it cannot be lexed."""
    lexer = shlex.shlex(script, posix=True, punctuation_chars=SEPARATOR_CHARS)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    commands: list[list[str]] = [[]]
    for token in lexer:
        if token and all(char in SEPARATOR_CHARS for char in token):
            commands.append([])
        else:
            commands[-1].append(token)
    return [strip_redirections(words) for words in commands if words]


def strip_redirections(words: list[str]) -> list[str]:
    kept: list[str] = []
    skip_next = False
    for word in words:
        if skip_next:
            skip_next = False
            continue
        match = REDIRECTION.match(word)
        if match:
            skip_next = not match.group(1)
            continue
        kept.append(word)
    return kept


def unwrap(words: list[str]) -> list[str]:
    """Drop leading keywords, assignments, and wrapper commands such as ``env`` or ``sudo``."""
    index = 0
    while index < len(words):
        word = words[index]
        if ASSIGNMENT.match(word) or word in KEYWORDS:
            index += 1
        elif PurePath(word).name in WRAPPERS:
            wrapper = PurePath(word).name
            index += 1
            while index < len(words) and words[index].startswith("-"):
                index += 2 if words[index] in WRAPPERS[wrapper] else 1
            if wrapper == "timeout":
                index += 1  # duration
        else:
            break
    return words[index:]


def shell_script(words: list[str]) -> str | None:
    """Return the ``-c`` script of a shell invocation such as ``bash -lc '...'``."""
    for index, word in enumerate(words[1:], start=1):
        if not word.startswith("-"):
            return None
        if not word.startswith("--") and word.endswith("c"):
            return words[index + 1] if index + 1 < len(words) else None
    return None


def strip_heredocs(script: str) -> str:
    """Drop heredoc bodies, which are data, unless the heredoc feeds a shell."""
    kept: list[str] = []
    delimiter = None
    for line in script.split("\n"):
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        kept.append(line)
        match = HEREDOC.search(line)
        if match and not SHELL_HEREDOC.search(line):
            delimiter = match[2]
    return "\n".join(kept)


def walk_commands(script: str, depth: int = 0) -> Iterator[list[str]]:
    """Yield the words of every simple command, descending into ``sh -c`` scripts.

    Heredoc bodies are skipped. A script that still cannot be lexed as a whole, such as
    one with an unbalanced quote, is lexed line by line and its unlexable lines are skipped.
    """
    script = strip_heredocs(script)
    try:
        commands = split_commands(script)
    except ValueError:
        commands = []
        for line in script.splitlines():
            with contextlib.suppress(ValueError):
                commands += split_commands(line)
    for words in commands:
        if not words:
            continue
        yield words
        inner = unwrap(words)
        if depth < 3 and inner and PurePath(inner[0]).name in SHELLS:
            nested = shell_script(inner)
            if nested:
                yield from walk_commands(nested, depth + 1)
