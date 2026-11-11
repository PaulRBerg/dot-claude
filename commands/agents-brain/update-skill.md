---
argument-hint: "<skill-name> [change request] [--dry-run]"
description: Update an existing repo-owned skill from a change request or repository drift
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill. Run its `maintain` workflow with the first argument as the only `target`. Follow
`references/maintain.md` and apply its Skill Decisions. Select no README.md, AGENTS.md, or context-doc targets.

Treat the remaining text as the requested change. Without a change request, fix factual drift only. A change request
authorizes edits to the skill's SKILL.md and bundled files beyond factual corrections. For a source-catalog skill,
change frontmatter, `agents/openai.yaml`, or the bundled-file set only through the repository's catalog lifecycle. When
the repository has no such lifecycle, report those changes as recommendations.

When the change creates or rewrites skill instructions, read the prompting guides as SKILL.md requires and use
`references/writing-great-skills.md`. Read `references/asd-ste100.md` completely before writing agent-facing prose, and
apply its review.

If the guard rail excludes the skill, make no writes and report the source catalog that owns it.
