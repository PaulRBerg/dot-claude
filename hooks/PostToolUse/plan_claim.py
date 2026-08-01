#!/usr/bin/env python3
"""Claim a plan's title as the session's task label on ExitPlanMode.

Registered with the ``ExitPlanMode`` matcher, this PostToolUse hook resolves
the just-approved plan's H1 and hands it to ``agent_session_status.py claim``
(see https://github.com/PaulRBerg/dot-codex) so peers running
``agents-status`` see the plan's title as this session's label between plan
approval and its first edit.

Plan text is preferred straight from the payload (``tool_input.plan`` — Claude
Code passes the full plan markdown, frontmatter included once
``add_plan_frontmatter.py`` stamps it). Failing that, ``~/.claude/plans/*.md``
is scanned for frontmatter whose ``session_id`` matches; the most recently
modified match wins.

Silent on success and on any failure — a hook must never break the tool
chain. Always exits 0.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

AGENT_STATUS_SCRIPT = (
    Path.home() / ".codex" / "hooks" / "AgentSessionStatus" / "agent_session_status.py"
)
PLANS_DIR = Path.home() / ".claude" / "plans"
CLAIM_TIMEOUT_SECONDS = 5.0
MAX_LABEL_CHARS = 80

# Matches the frontmatter line add_plan_frontmatter.py writes, e.g.
# session_id: "acd212d8-147c-493e-afaf-46942ebf4378"
FRONTMATTER_SESSION_ID_RE = re.compile(r'^session_id:\s*"([^"]*)"\s*$', re.MULTILINE)
H1_RE = re.compile(r"^#[ \t]+(.+?)[ \t]*$", re.MULTILINE)


def _strip_frontmatter(text: str) -> str:
    """Return text with a leading YAML frontmatter block removed, if present."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + len("\n---") :]


def _frontmatter_session_id(text: str) -> str | None:
    """Return the frontmatter session_id, or None if absent/malformed."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    match = FRONTMATTER_SESSION_ID_RE.search(text[:end])
    return match.group(1) if match else None


def _extract_h1(text: str) -> str | None:
    """Return the first H1 heading after any frontmatter, truncated to ~80 chars."""
    match = H1_RE.search(_strip_frontmatter(text))
    if not match:
        return None
    title = match.group(1).strip()
    if not title:
        return None
    return title[:MAX_LABEL_CHARS].rstrip()


def _plan_text_from_payload(data: dict[str, Any]) -> str | None:
    """Return inline plan markdown from the payload, when the hook carries one."""
    for container_key in ("tool_input", "tool_response"):
        container = data.get(container_key)
        if not isinstance(container, dict):
            continue
        for key in ("plan", "content"):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None


def _plan_text_from_disk(session_id: str) -> str | None:
    """Scan ~/.claude/plans/*.md for frontmatter matching session_id.

    Returns the text of the most recently modified match, or None.
    """
    if not PLANS_DIR.is_dir():
        return None

    best: tuple[float, str] | None = None
    for path in PLANS_DIR.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if _frontmatter_session_id(text) != session_id:
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if best is None or mtime > best[0]:
            best = (mtime, text)

    return best[1] if best is not None else None


def main() -> None:
    """Main hook entry point."""
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            sys.exit(0)

        if data.get("tool_name") != "ExitPlanMode":
            sys.exit(0)

        session_id = data.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            sys.exit(0)

        text = _plan_text_from_payload(data) or _plan_text_from_disk(session_id)
        if text is None:
            sys.exit(0)

        title = _extract_h1(text)
        if not title:
            sys.exit(0)

        subprocess.run(
            [
                str(AGENT_STATUS_SCRIPT),
                "claim",
                "--client",
                "claude",
                "--session",
                session_id,
                title,
            ],
            capture_output=True,
            timeout=CLAIM_TIMEOUT_SECONDS,
        )
    except Exception:  # noqa: BLE001 - a hook must never break the tool chain.
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
