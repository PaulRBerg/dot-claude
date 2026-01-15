---
argument-hint: '[description]'
description: Create an issue in anthropics/claude-code
model: opus
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Claude Code version: !`claude --version 2>/dev/null || echo "unknown"`
- OS: !`~/.claude/helpers/get_macos_version.sh`
- Terminal: !`echo "${TERM_PROGRAM:-${TERMINAL_EMULATOR:-unknown}}"`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/oss` skill to create an issue in `anthropics/claude-code` Github repository. Follow the workflow in `~/.claude/skills/oss/references/issues-claude-code.md`.
