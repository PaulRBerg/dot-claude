---
argument-hint: "[repository] [description] [--check] [--image <path>]... [--image-release]"
description: Create a GitHub issue with automatic labeling
---

## Context

- OS: !`~/.agents/skills/yeet/scripts/get-macos-version.sh`
- Arguments: $ARGUMENTS

## Task

Activate the `yeet` skill to create a GitHub issue. Follow the workflow in
`~/.agents/skills/yeet/references/create-issue.md`.

When writing issue bodies that include environment information, use the OS value from the Context section above (e.g.,
"macOS Tahoe 26.2"). Do not use raw system output like "Darwin 25.2.0".
