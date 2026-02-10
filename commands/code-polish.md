---
description: Simplify then review recently changed code
---

## Task

Run these two agents **sequentially**:

1. **code-simplifier** — Simplify and refine recently modified code for clarity, consistency, and maintainability while preserving all functionality.
2. **code-reviewer** — Review the recently modified code (including the simplifications) for quality, security, and maintainability.

By default, both agents should focus on files changed since the last commit. However, if the user provides a specific path or a commit, the agents should focus on that instead.
