---
argument-hint: "<skill-name> [skill-name ...] [--dry-run]"
description: Delete repo-owned skills and preserve their still-useful guidance
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill. Run its `maintain` workflow and apply the Delete lifecycle change in
`references/maintain-skills.md`.

This invocation authorizes deletion of the named repo-owned skills. It replaces the Delete evidence bar. Before you
delete a skill, inspect it completely and find its inbound references. Move still-useful unique guidance to a surviving
skill or context file. If a supported caller still needs unique behavior that has no replacement, do not delete that
skill. Report the caller and the missing replacement.

Read `references/asd-ste100.md` completely before writing agent-facing prose, and apply its review.
