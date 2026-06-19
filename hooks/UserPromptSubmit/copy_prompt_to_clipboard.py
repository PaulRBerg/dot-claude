#!/usr/bin/env python3
"""Copy each submitted prompt to the macOS clipboard for Raycast history.

This UserPromptSubmit hook mirrors every prompt into the system clipboard via
``pbcopy`` so it surfaces in Raycast's clipboard history — a searchable log of
what was asked. Raw prompts are noisy, so the text is sanitized first: Claude
Code paste/image markers are normalized, fenced code blocks are dropped, and
oversized pastes are collapsed to short markers.

UserPromptSubmit hooks inject *stdout* into the model context on exit 0, so this
hook writes nothing to stdout — it only pbcopies as a side effect. Warnings go
to stderr and every error path exits 0 to avoid breaking the hook chain.

Set ``CLAUDE_CLIP_DEBUG=1`` to append raw stdin to ``.debug.jsonl`` (next to this
script) for a one-shot check of how prompts/pastes are represented.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Absolute path: PATH-independent in the non-interactive hook shell. The pbcopy
# on PATH is just an `exec /usr/bin/pbcopy` shim anyway.
PBCOPY = "/usr/bin/pbcopy"

# Sanitization tunables (module-level for easy adjustment after live pastes).
LONG_LINE_CHARS = 400  # A single line longer than this collapses to "[Pasted]".
MAX_CHARS = 1500  # Whole prompt longer than this keeps a bounded head.
MAX_LINES = 20  # Whole prompt with more lines than this keeps a bounded head.
SHORT_ID_CHARS = 8  # Length of the short session/ref id in the provenance prefix.
MAX_LABEL_CHARS = 32  # Max length of the repo label in the provenance prefix.

# Claude Code's own placeholder markers for pasted text, images, and truncated
# text. This mirrors the exact regex the live bundle uses to detect them.
CC_MARKER_RE = re.compile(
    r"\[(?:Pasted text|Image|\.\.\.Truncated text) #\d+(?: \+\d+ lines)?\.*\]"
)

# A complete fenced code block: an opening fence (3+ backticks) through the
# matching closing fence with the same backtick count.
FENCE_RE = re.compile(
    r"^[ \t]*(`{3,})[^\n]*\n.*?^[ \t]*\1[ \t]*$",
    re.MULTILINE | re.DOTALL,
)

# An unterminated fence (e.g. a paste cut off mid-block): an opening fence
# through end of input.
UNTERMINATED_FENCE_RE = re.compile(
    r"^[ \t]*`{3,}.*\Z",
    re.MULTILINE | re.DOTALL,
)

# Three or more consecutive newlines (excess blank lines).
BLANK_LINES_RE = re.compile(r"\n{3,}")

# Characters not allowed in a compact metadata value (stripped from the prefix).
METADATA_VALUE_RE = re.compile(r"[^A-Za-z0-9._/@:-]+")
# Leading 8 hex digits of a UUID-like id (e.g. a session_id), used as a short id.
UUID_RE = re.compile(r"\b([0-9a-fA-F]{8})-[0-9a-fA-F-]{8,}\b")
# Trailing repo name in a git remote URL (tolerates optional ".git" or slash).
GIT_REMOTE_PATH_RE = re.compile(r"[:/]([^/:]+?)(?:\.git)?/?$")

CWD_KEYS = ("cwd", "working_dir", "workingDirectory", "project_path", "projectPath")
SESSION_ID_KEYS = (
    "session_id",
    "sessionId",
    "conversation_id",
    "conversationId",
    "thread_id",
    "threadId",
)
NESTED_METADATA_KEYS = ("session", "conversation", "thread", "turn", "workspace")


def _collapse_size(text: str) -> str:
    """Collapse oversized content so large pastes don't flood the clipboard.

    Over-long single lines become ``[Pasted]``; if the prompt still has too many
    lines or characters, a bounded head is kept and the rest marked ``[Pasted]``.
    """
    lines = ["[Pasted]" if len(line) > LONG_LINE_CHARS else line for line in text.split("\n")]
    text = "\n".join(lines)

    if len(lines) > MAX_LINES or len(text) > MAX_CHARS:
        head = "\n".join(lines[:MAX_LINES])[:MAX_CHARS].rstrip()
        text = f"{head} … [Pasted]"

    return text


def sanitize_prompt(prompt: str) -> str:
    """Sanitize a submitted prompt for clipboard history.

    Pipeline: normalize Claude Code markers, strip fenced code blocks, collapse
    oversized content, then squeeze blank lines. Returns an empty string when
    nothing meaningful remains (the caller should then skip pbcopy).
    """
    text = CC_MARKER_RE.sub("Pasted", prompt)
    text = FENCE_RE.sub("[code]", text)
    text = UNTERMINATED_FENCE_RE.sub("[code]", text)
    text = _collapse_size(text)
    text = BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def _first_string(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    """Return the first non-empty string found at top level or one level deep."""
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for parent_key in NESTED_METADATA_KEYS:
        parent = data.get(parent_key)
        if not isinstance(parent, dict):
            continue
        for key in keys:
            value = parent.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def _safe_metadata_value(value: str, max_chars: int) -> str:
    """Normalize a metadata value for a compact bracketed prefix."""
    text = re.sub(r"\s+", "-", value.strip())
    text = METADATA_VALUE_RE.sub("", text)
    return text[:max_chars].strip("-")


def _short_identifier(value: str) -> str:
    """Return a short readable identifier from a session/thread-ish value."""
    match = UUID_RE.search(value)
    if match:
        return match.group(1).lower()

    return _safe_metadata_value(value, SHORT_ID_CHARS)


def _session_cwd(data: dict[str, Any]) -> Path:
    """Return the session cwd from hook data when present, otherwise process cwd."""
    value = _first_string(data, CWD_KEYS)
    if not value:
        return Path.cwd()

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _git_output(cwd: Path, *args: str) -> str:
    """Run a short git query and return stripped stdout, or empty on failure."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(cwd), *args],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _repo_root(cwd: Path) -> Path:
    """Return the git root for cwd, falling back to cwd."""
    root = _git_output(cwd, "rev-parse", "--show-toplevel")
    if root:
        return Path(root)
    return cwd


def _repo_label(cwd: Path, repo_root: Path) -> str:
    """Return a compact repo label, preferring remote origin over folder name."""
    remote = _git_output(cwd, "config", "--get", "remote.origin.url")
    match = GIT_REMOTE_PATH_RE.search(remote)
    if match:
        label = _safe_metadata_value(match.group(1), MAX_LABEL_CHARS)
        if label:
            return label

    return _safe_metadata_value(repo_root.name or str(repo_root), MAX_LABEL_CHARS)


def _transcript_identifier(data: dict[str, Any]) -> str:
    """Return a short identifier from Claude's transcript path when available."""
    value = data.get("transcript_path")
    if not isinstance(value, str) or not value.strip():
        return ""

    return _short_identifier(Path(value).stem)


def _path_reference(path: Path) -> str:
    """Return a short stable reference for non-git directories."""
    try:
        value = str(path.resolve())
    except OSError:
        value = str(path)
    return hashlib.sha1(value.encode("utf-8"), usedforsecurity=False).hexdigest()[:SHORT_ID_CHARS]


def build_metadata_prefix(data: dict[str, Any]) -> str:
    """Build a short provenance prefix for clipboard history."""
    cwd = _session_cwd(data)
    repo_root = _repo_root(cwd)
    project = _repo_label(cwd, repo_root)

    parts = []
    if project:
        parts.append(f"repo:{project}")

    session_id = _short_identifier(_first_string(data, SESSION_ID_KEYS))
    transcript_id = _transcript_identifier(data)
    if session_id:
        parts.append(f"session:{session_id}")
    elif transcript_id:
        parts.append(f"session:{transcript_id}")
    else:
        ref = _git_output(cwd, "rev-parse", "--short=8", "HEAD")
        parts.append(f"ref:{ref or _path_reference(repo_root)}")

    return f"[{' '.join(parts)}]" if parts else ""


def format_clipboard_prompt(prompt: str, data: dict[str, Any]) -> str:
    """Sanitize a prompt and prepend compact source metadata."""
    text = sanitize_prompt(prompt)
    if not text:
        return ""

    prefix = build_metadata_prefix(data)
    return f"{prefix}\n{text}" if prefix else text


def _maybe_debug(raw: str) -> None:
    """Append raw stdin to a debug log when CLAUDE_CLIP_DEBUG=1 (best effort)."""
    if os.environ.get("CLAUDE_CLIP_DEBUG") != "1":
        return
    try:
        debug_path = Path(__file__).parent / ".debug.jsonl"
        with debug_path.open("a", encoding="utf-8") as fh:
            fh.write(raw.strip() + "\n")
    except OSError:
        pass


def main() -> None:
    """Main hook entry point."""
    raw = sys.stdin.read()
    _maybe_debug(raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)  # Invalid input, don't break the hook chain.

    if not isinstance(data, dict):
        sys.exit(0)  # Valid JSON but not the expected object.

    prompt = data.get("prompt", "")
    if not isinstance(prompt, str):
        sys.exit(0)

    try:
        text = format_clipboard_prompt(prompt, data)
    except Exception as e:  # noqa: BLE001 - hook must fail open.
        print(f"Warning: metadata prefix failed: {e}", file=sys.stderr)
        text = sanitize_prompt(prompt)
    if not text:
        sys.exit(0)  # Nothing meaningful; don't clobber the clipboard.

    # capture_output keeps pbcopy's stdout/stderr off our stdout — hook stdout is
    # injected into the model context, so it must stay empty. encoding is pinned
    # to UTF-8 so non-ASCII prompts can't raise UnicodeEncodeError when the hook
    # shell lacks a UTF-8 locale.
    try:
        result = subprocess.run(
            [PBCOPY],
            input=text,
            encoding="utf-8",
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Warning: pbcopy failed: {e}", file=sys.stderr)
        sys.exit(0)

    if result.returncode != 0:
        print(
            f"Warning: pbcopy exited {result.returncode}: {result.stderr.strip()}",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
