---
argument-hint: "[path?] [target ...] [--dry-run]"
description: Maintain repo-local skills from task evidence by deleting, merging, or creating skills
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill and run the `maintain` workflow. Follow `references/maintain-skills.md` from that
skill. Use evidence from the current task and keep review and edits inside its repository boundary.
