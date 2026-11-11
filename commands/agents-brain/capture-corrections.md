---
argument-hint: "[path?] [--dry-run]"
description: Record durable user corrections from this session as rules in repo context or skills
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill. Run only the correction-capture step of its Maintain Workflow. Do not run broader
discovery or a context audit.

Scan this session for user corrections, such as a restated instruction, "do not do X", "always do Y", or a reverted
choice. Record each durable correction as one rule in the nearest in-scope steering file, such as AGENTS.md, or in the
owning repo-owned skill. Use the AGENTS.md Decisions in `references/maintain.md` for placement and wording. Merge a rule
into an equivalent existing rule instead of adding a duplicate.

When the owner of a correction is outside the repository, such as a global skill or global instructions, make no write
there. Report the owner and the proposed rule. For each correction that is not durable, state the reason: one-off,
already stated, or a project-specific exception.

Read `references/asd-ste100.md` completely before writing agent-facing prose, and apply its review.
