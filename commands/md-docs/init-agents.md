---
argument-hint: '[description?]'
description: Generate project-specific CLAUDE.md file with custom context
model: opus
---

## Context

- Current directory: !`pwd`
- Existing CLAUDE.md (root): !`test -f CLAUDE.md && echo "exists" || echo "none"`
- Existing CLAUDE.md (.claude): !`test -f .claude/CLAUDE.md && echo "exists" || echo "none"`
- Git repository: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/md-docs` skill to initialize a CLAUDE.md file. Follow the workflow in `~/.claude/skills/md-docs/references/init-agents.md`.
