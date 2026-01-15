---
argument-hint: '[description]'
description: Create an issue in openai/codex
model: opus
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Codex version: !`codex --version 2>/dev/null || echo "unknown"`
- Platform: !`uname -mprs`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/oss` skill to create an issue in `openai/codex` Github repository. Follow the workflow in `~/.claude/skills/oss/references/issues-codex-cli.md`.
