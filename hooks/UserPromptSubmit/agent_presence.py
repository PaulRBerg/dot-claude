#!/usr/bin/env python3
"""Inject a one-line cross-agent presence notice on UserPromptSubmit.

Runs ``agent_session_status.py status --json`` (see
https://github.com/PaulRBerg/dot-codex) and reports, in one line, how many
*other* sessions share this repo and how many pending notes exist for it.
Note *content* is never surfaced — only counts — and session labels/names
(cross-session text, stored verbatim by the helper) are collapsed to a single
line and truncated before injection, so neither channel can be used to inject
arbitrary text into another session's context (prompt-injection guard).

Silent (no stdout, exit 0) when solo with no notes, or on any error/timeout —
a hook must never break a prompt. UserPromptSubmit hooks inject plain stdout
into the model context on exit 0 (see ../README.md).
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

AGENT_STATUS_SCRIPT = (
    Path.home() / ".codex" / "hooks" / "AgentSessionStatus" / "agent_session_status.py"
)
STATUS_TIMEOUT_SECONDS = 2.0
GIT_TIMEOUT_SECONDS = 2.0
# Matches plan_claim.py's claim truncation so labels written by that hook
# survive intact; anything longer is hostile or degenerate input.
MAX_LABEL_CHARS = 80


def _repo_root(cwd: str) -> str:
    """Return the git root for cwd, falling back to cwd itself."""
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return cwd
    if result.returncode != 0:
        return cwd
    return result.stdout.strip() or cwd


def _load_status() -> dict[str, Any] | None:
    """Run the agent-session-status helper and parse its JSON inventory."""
    if not AGENT_STATUS_SCRIPT.is_file():
        return None
    try:
        result = subprocess.run(
            [str(AGENT_STATUS_SCRIPT), "status", "--json"],
            capture_output=True,
            text=True,
            timeout=STATUS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    # Exit 0 = complete coverage, 2 = partial (one provider errored) but the
    # JSON that did come back is still usable.
    if result.returncode not in (0, 2):
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _path_within(path: Path, root: Path) -> bool:
    """Return whether path is root itself or nested under it."""
    try:
        path, root = path.resolve(), root.resolve()
    except OSError:
        pass
    return path.is_relative_to(root)


def _sanitize_label(text: str) -> str:
    """Flatten cross-session text to one bounded printable line.

    Labels/names are written by *other* sessions and stored verbatim, so they
    must not carry newlines, control characters, or unbounded length into this
    session's context.
    """
    printable = "".join(ch if ch.isprintable() else " " for ch in text)
    collapsed = " ".join(printable.split())
    if len(collapsed) > MAX_LABEL_CHARS:
        return collapsed[: MAX_LABEL_CHARS - 1].rstrip() + "…"
    return collapsed


def _session_label(session: dict[str, Any]) -> str:
    """Identify a session by claim label or name, else <client>/<short-id>."""
    for key in ("label", "name"):
        value = session.get(key)
        if isinstance(value, str):
            sanitized = _sanitize_label(value)
            if sanitized:
                return sanitized
    client = session.get("client", "")
    session_id = session.get("session_id", "")
    return f"{client}/{session_id[:8]}"


def build_presence_line(document: dict[str, Any], repo_root: str, own_session_id: str) -> str:
    """Return the one-line presence notice, or "" when there's nothing to report."""
    root_path = Path(repo_root)
    others: list[str] = []
    for session in document.get("sessions", []):
        if not isinstance(session, dict):
            continue
        session_id = session.get("session_id")
        cwd = session.get("cwd")
        if session_id == own_session_id:
            continue
        if not isinstance(cwd, str) or not cwd:
            continue
        if not _path_within(Path(cwd), root_path):
            continue
        others.append(_session_label(session))

    note_count = 0
    notes = document.get("notes")
    if isinstance(notes, dict):
        entries = notes.get(repo_root)
        if isinstance(entries, list):
            note_count = len(entries)

    parts: list[str] = []
    if others:
        word = "session" if len(others) == 1 else "sessions"
        parts.append(f"{len(others)} other {word} in this repo ({', '.join(others)})")
    if note_count:
        word = "note" if note_count == 1 else "notes"
        parts.append(f"{note_count} {word} pending — run agents-status")

    return f"agents: {'; '.join(parts)}" if parts else ""


def main() -> None:
    """Main hook entry point."""
    line = ""
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise TypeError("hook input must be a JSON object")

        session_id = payload.get("session_id")
        cwd = payload.get("cwd")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("missing session_id")
        if not isinstance(cwd, str) or not cwd:
            raise ValueError("missing cwd")

        document = _load_status()
        if document is not None:
            repo_root = _repo_root(cwd)
            line = build_presence_line(document, repo_root, session_id)
    except Exception:  # noqa: BLE001 - a hook must never break a prompt.
        line = ""

    if line:
        print(line)
    sys.exit(0)


if __name__ == "__main__":
    main()
