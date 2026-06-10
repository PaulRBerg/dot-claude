---
argument-hint: '[description?] [path?] [--root-only] [--minimal] [--full] [--dry-run] [--force]'
description: Generate project-specific CLAUDE.md file with custom context
model: opus
---

## Context

- Current directory: !`pwd`
- Existing context files: !`fd '(CLAUDE|AGENTS)\.md' -t f | sort`
- Git repository: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/md-docs` skill to initialize a CLAUDE.md file. Follow the workflow in `~/.claude/skills/md-docs/references/init-agents.md`.
