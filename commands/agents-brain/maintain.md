---
argument-hint: "[path?] [target ...] [--root-only] [--preserve] [--minimal] [--thorough|--full] [--dry-run] [--force]"
description: Maintain repo context and task-backed skills, including warranted creation, merging, and deletion
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill. Run its sole `maintain` workflow and follow `references/maintain.md` from that skill.

Before writing or changing agent-facing prose, read the skill's `references/asd-ste100.md` completely. Apply its
STE-based profile during writing. Complete its meaning and style review before finishing.

Load `references/create-docs.md` for context creation or regeneration. Load `references/maintain-skills.md` for
task-backed skill lifecycle changes. Keep review and edits inside the selected repository scope.
