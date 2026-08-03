---
argument-hint: "[path?] [--root-only] [--minimal] [--thorough|--full] [--dry-run] [--force]"
description: Create missing README.md and AGENTS.md context files
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Existing READMEs: !`fd '^README\.md$' -t f | sort`
- Existing context files: !`fd '(CLAUDE|AGENTS)\.md' -t f -t l | sort`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-context-management` skill and run the `create` workflow. Follow `references/create-docs.md` from
that skill.
