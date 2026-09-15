---
argument-hint: "[description]"
description: Create an issue in openai/codex
---

## Context

- Codex version: !`codex --version 2>/dev/null || echo "unknown"`
- OS: !`~/.agents/skills/yeet/scripts/get-macos-version.sh`
- Terminal: !`echo "$TERM_PROGRAM"`
- Arguments: $ARGUMENTS

## Task

Activate the `yeet` skill to create an issue in `openai/codex` Github repository. Follow the workflow in
`~/.agents/skills/yeet/references/issue-codex-cli.md`.
