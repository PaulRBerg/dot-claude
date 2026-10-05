---
argument-hint: "[path?] [target ...] [--root-only] [--preserve] [--minimal] [--thorough|--full] [--dry-run] [--force]"
description: Maintain repo context and task-backed skills, including warranted creation, merging, and deletion
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill and run its sole `maintain` workflow. Follow `references/maintain.md` from that skill,
loading `references/create-docs.md` for context creation or regeneration and `references/maintain-skills.md` for
task-backed skill lifecycle changes. Keep review and edits inside the selected repository scope.
