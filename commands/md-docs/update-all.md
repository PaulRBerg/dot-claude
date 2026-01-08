---
argument-hint: '[--preserve] [--minimal] [--thorough] [--dry-run]'
description: Update README.md and AI context files (CLAUDE.md, AGENTS.md)
model: opus
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- GitHub remote: !`git remote get-url origin 2>/dev/null || echo "no remote"`
- Existing README: !`test -f README.md && echo "exists" || echo "none"`
- Context files: !`fd '(CLAUDE|AGENTS)\.md' -t f | sort`
- Arguments: $ARGUMENTS

## Task

Activate the `md-docs` skill to update project documentation. Perform both workflows:

1. **README.md** - Follow `references/update-readme.md`
1. **Context files** - Follow `references/update-agents.md`

Update README first, then context files. If `--dry-run` is passed, report proposed changes without writing.
