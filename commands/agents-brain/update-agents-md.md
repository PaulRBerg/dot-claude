---
argument-hint: "[path?] [--preserve] [--minimal] [--thorough|--full] [--dry-run] [--force]"
description: Update AGENTS.md files and their CLAUDE.md companions without touching other context
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill. Run its `maintain` workflow and follow `references/maintain.md` from that skill.

Select only AGENTS.md files and their sibling CLAUDE.md entries in the selected scope. Apply the Context Economy Audit,
AGENTS.md Decisions, and CLAUDE.md Decisions. Do not edit README.md files, skills, or context docs. Report drift found
in them as recommendations.

Read `references/create-docs.md` only for `--force` regeneration or a warranted missing nested AGENTS.md. Read
`references/asd-ste100.md` completely before writing agent-facing prose, and apply its review.
