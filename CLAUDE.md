# Global Instructions

Prefer simple, conventional, readable designs. Introduce abstractions or patterns only when they reduce overall
complexity.

## Communication

- Lead with the conclusion. Include the evidence needed for the decision, material caveats, and next action. Trim
  introductions, repetition, and optional background first.
- Treat me as an expert — skip the basics.
- Surface materially better alternatives or flaws, but do not expand implementation scope without authorization.
- Challenge assumptions and flag flaws immediately.
- When facts are discoverable, investigate rather than confirm my beliefs. Otherwise state what is unknown and take the
  smallest safe next step.

## Authority

- For answers, reviews, diagnosis, and plans: inspect and report; do not change files unless requested.
- For changes, builds, and fixes: make in-scope local changes and run relevant non-destructive validation.
- Require confirmation for external writes, destructive actions, credential/permission changes, purchases, or material
  scope expansion.

## Agents

- When I say "agent", I mean a coding agent (Claude Code or Codex CLI), not a human.
- I usually run multiple agents in parallel in the same working tree on `main` — no PRs, no separate worktrees. Treat
  the working tree, index, and remote as shared mutable state that can change at any point while you work.
- Treat changes unrelated to your task as another agent's work: ignore them, don't let them block or redirect you, and
  don't report them to me.
- I may also commit and push while you work. Don't be surprised by commits you didn't author, and don't revert or amend
  them unless I ask.
- Stage and commit only files you edited this session. Never run tree-wide git commands that sweep other agents'
  uncommitted work: `git add -A`, `git commit -a`, `git stash`, `git checkout .` / `git restore .`, `git reset --hard`,
  `git clean`.
- Stay on the current branch. Don't switch, rebase, merge, or pull without asking — those assume a clean tree, and
  autostash variants would stash other agents' work.
- On a git `index.lock` error, another agent is mid-operation: wait a moment and retry; never delete the lock file.
- If an edit fails because a file changed after you read it, re-read and reapply on the new content — the file may now
  contain another agent's work. Never force-overwrite a whole file to win the race.
- Attribute failures before debugging them: if a repo-wide check fails only in files you didn't touch, it's likely
  another agent's in-flight work — confirm your own files pass and move on.
- Run formatters, linters, and codegen scoped to the files you changed, not repo-wide.
- Commit proactively and as quickly as possible: the moment a coherent unit of work passes validation, commit it without
  waiting for the task to fully finish. Many small commits are good — never batch them into one big commit at the end.
  Uncommitted work is what blocks other agents from starting conflicting tasks, so the working tree should return to
  clean as fast as you can get it there.

### Conflict detection before starting

Before starting any task — in standard mode and plan mode alike — check the repo state with `git status`. Dirty
uncommitted changes are likely another agent's in-flight work: reason through whether your task would collide with it
(same files or modules, overlapping refactors, shared codegen outputs). Use the `/agents-introspection` skill to see
which AI agent sessions are currently active in this repo and what they are working on. The goal is smarter
parallelization of agents on the same `main` branch.

- No overlap with your task → proceed normally (per the bullet above: ignore unrelated changes).
- Potential conflict → keep analyzing and planning the task (reading is always safe), but do not edit any files yet.
  Wait for the other agent(s) to finish, signaled by the conflicting changes being committed.
- While waiting, poll the repo state (e.g., `git status --porcelain` on the conflicting paths): every 2 minutes for the
  first 10 minutes, then every 5 minutes, up to 1 hour of total waiting.
- The moment the conflicting work is committed, start implementing immediately — do not ask for approval.
- If still blocked after 1 hour, give up on waiting: present your finished plan and tell me I can run it once the
  conflicting agent workloads are done.
- In plan mode, still write the plan, but include a "Wait out conflicting agents" section that applies the polling
  schedule above before the first edit.

## Workflow

- Prefer `just` recipes for build, test, lint, format, codegen, and release when a `justfile` exists; inspect the recipe
  first if its flags or side effects are unclear.
- Fall back to direct commands only when no recipe fits, or when a recipe hides the signal you need for debugging.
- Keep automation reproducible: never rely on my aliases, shell functions, local prompts, or interactive-only rc
  behavior.
- Work directly on the current branch unless I explicitly request a PR.
- In plans, do not restate standing instructions or facts from `AGENTS.md` or `CLAUDE.md`; include only task-specific
  constraints, decisions, and risks.
- Verify with the narrowest command that proves the change, then concisely report the exact checks and outcomes.
- I keep personal todos in `TODO.md` files across projects. These are private notes, not task specs: don't read or
  reference them unless I explicitly point you at one.

## Change Discipline

- Before implementing, state material assumptions. Ask only when an unresolved choice changes scope, safety,
  implementation, or verification.
- Write the minimum code that solves the requested problem: no speculative features, single-use abstractions,
  unnecessary configurability, or impossible-case error handling.
- Make surgical changes. Touch only lines that trace to the request or to cleanup caused by your own edits; mention
  unrelated dead code instead of deleting it.
- For multi-step work, state a brief plan and validation target. Continue until the success criteria are met or the
  blocker is explicit.
- Keep files under 1000 lines and test files under 2000.

## Shell

The Bash tool runs commands under **zsh** (my macOS login shell), ignoring `$SHELL`. Do not use bash-only syntax at the
top level.

- Keep top-level commands POSIX-compatible (zsh-safe).
- For bash-only features (`declare -A`, `${var^^}`/`${var,,}`, `${!arr[@]}`, `mapfile`, process substitution `<(...)`),
  wrap them in an explicit `bash` call (Homebrew bash 5.x is on `PATH`):

```bash
bash <<'EOF'
declare -A color=([sky]=blue [sun]=yellow)
echo "${color[sky]} / ${color[sun]^^}"   # blue / YELLOW
EOF
```

- Quote literal paths, URLs, and patterns with single quotes. In zsh, unquoted `?`, `*`, `[]`, and `()` are glob syntax.
- Use argv-style APIs or arrays when available; use `noglob` only as a one-command escape hatch. zsh does not word-split
  scalar strings by default.
- Avoid `status` and `path` as variable names: `status` is read-only and `path` is tied to `$PATH`. Use `rc`, `ret`, or
  `result`.
- For code search use `rg`; otherwise prefer `fd`, `jq`, `yq`, and `uv` where appropriate.

## Gmail / Google Drive

Use the installed `mailops` CLI to access Gmail and Google Drive from any directory: `mailops login <alias>` and
`mailops <alias> gmail …`. Consult `~/work/mailops` for account aliases and detailed workflows.

## Dotfiles

I manage my dotfiles with chezmoi; the source tree lives at `~/.local/share/chezmoi`.
