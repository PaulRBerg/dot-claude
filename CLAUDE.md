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
- Commit finished work promptly so it doesn't entangle with other agents' concurrent edits.

## Workflow

- Prefer `just` recipes for build, test, lint, format, codegen, and release when a `justfile` exists; inspect the recipe
  first if its flags or side effects are unclear.
- Fall back to direct commands only when no recipe fits, or when a recipe hides the signal you need for debugging.
- Keep automation reproducible: never rely on my aliases, shell functions, local prompts, or interactive-only rc
  behavior.
- Work directly on the current branch unless I explicitly request a PR.
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
