---
argument-hint: '[description]'
description: Create an issue in anthropics/claude-code
model: opus
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Claude Code version: !`claude --version 2>/dev/null || echo "unknown"`
- OS: !`~/.agents/skills/oss/scripts/get-macos-version.sh`
- Terminal: !`echo "$TERM_PROGRAM"`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/oss` skill to create an issue in `anthropics/claude-code` Github repository. Follow the workflow in `~/.claude/skills/oss/references/issue-claude-code.md`.
