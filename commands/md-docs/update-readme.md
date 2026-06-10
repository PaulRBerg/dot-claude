---
argument-hint: '[path?] [--root-only] [--preserve] [--minimal] [--thorough] [--dry-run]'
description: Update README.md based on current codebase structure
model: opus
---

## Context

- Current directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Existing READMEs: !`fd '^README\.md$' -t f | sort`
- GitHub remote: !`git remote get-url origin 2>/dev/null || echo "no remote"`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/md-docs` skill to update README.md. Follow the workflow in `~/.claude/skills/md-docs/references/update-readme.md`.
