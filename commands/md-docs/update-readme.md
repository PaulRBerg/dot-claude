---
argument-hint: '[--preserve] [--minimal] [--thorough]'
description: Update README.md based on current codebase structure
model: opus
---

## Context

- Current directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Existing README: !`test -f README.md && echo "exists" || echo "none"`
- GitHub remote: !`git remote get-url origin 2>/dev/null || echo "no remote"`
- Arguments: $ARGUMENTS

## Task

Activate the `md-docs` skill to update README.md. Follow the workflow in `references/update-readme.md`.
