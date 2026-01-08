---
argument-hint: '[--dry-run]'
description: Update CLAUDE.md and AGENTS.md files to match actual codebase
model: opus
---

## Context

- Context files: !`fd '(CLAUDE|AGENTS)\.md' -t f | sort`
- Working directory: !`pwd`
- Arguments: $ARGUMENTS

## Task

Activate the `md-docs` skill to update context files. Follow the workflow in `references/update-agents.md`.
