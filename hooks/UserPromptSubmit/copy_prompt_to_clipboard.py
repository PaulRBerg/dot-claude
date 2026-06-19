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

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Absolute path: PATH-independent in the non-interactive hook shell. The pbcopy
# on PATH is just an `exec /usr/bin/pbcopy` shim anyway.
PBCOPY = "/usr/bin/pbcopy"

# Sanitization tunables (module-level for easy adjustment after live pastes).
LONG_LINE_CHARS = 400  # A single line longer than this collapses to "[Pasted]".
MAX_CHARS = 1500  # Whole prompt longer than this keeps a bounded head.
MAX_LINES = 20  # Whole prompt with more lines than this keeps a bounded head.

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
