---
argument-hint: '[owner/repo#number | url | number] [comment context] [--edit-last]'
description: Post a comment on an existing GitHub issue or PR
---

## Context

- Current repository: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a repository"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- OS: !`~/.agents/skills/yeet/scripts/get-macos-version.sh`
- Arguments: $ARGUMENTS

## Task

Activate the `yeet` skill to post a comment on an existing GitHub issue. Follow the workflow in `~/.agents/skills/yeet/references/comment-issue.md`.

When writing comments that include environment information, use the OS value from the Context section above (e.g., "macOS Tahoe 26.2"). Do not use raw system output like "Darwin 25.2.0".
