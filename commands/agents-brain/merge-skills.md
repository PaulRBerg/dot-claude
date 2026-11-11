---
argument-hint: "<survivor> <absorbed> [absorbed ...] [--dry-run]"
description: Merge overlapping repo-owned skills into one surviving skill
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill. Run its `maintain` workflow and apply the Merge lifecycle change in
`references/maintain-skills.md`.

This invocation authorizes the merge of the named repo-owned skills. Keep the first name as the survivor unless the
request names a new skill. For a new name, follow `references/create-skill.md` for the new identity. Apply the Merge
evidence bar. If the skills do not serve the same trigger or a tightly coupled workflow, make no writes and report the
evidence.

Read `references/writing-great-skills.md` before restructuring the survivor. Read `references/asd-ste100.md` completely
before writing agent-facing prose, and apply its review. In the report, map every previously supported outcome to its
place in the survivor.
