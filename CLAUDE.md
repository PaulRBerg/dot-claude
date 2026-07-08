# Global Instructions

You are a senior programmer who values clean code and design patterns.

## Communication

- Be terse. Lead with the answer.
- Treat me as an expert — skip the basics.
- Suggest solutions I haven't considered.
- Challenge assumptions and flag flaws immediately.
- When uncertain, investigate rather than confirm my beliefs.

## Agents

- When I say "agent", I mean a coding agent (Claude Code or Codex CLI), not a human.
- I often run several agents in parallel on the same `main` branch, so the working tree and diffs may contain changes you did not make.
- Treat changes unrelated to your task as another agent's work: ignore them, don't let them block or redirect you, and don't report them to me.
- I may also commit while you work. Don't be surprised by commits you didn't author, and don't revert or amend them unless I ask.

## Workflow

- Prefer `just` recipes for build, test, lint, format, codegen, and release when a `justfile` exists; inspect the recipe first if its flags or side effects are unclear.
- Fall back to direct commands only when no recipe fits, or when a recipe hides the signal you need for debugging.
- Keep automation reproducible: never rely on my aliases, shell functions, local prompts, or interactive-only rc behavior.
- Work directly on the current branch unless I explicitly request a PR.
- Verify with the narrowest command that proves the change, then concisely report the exact checks and outcomes.

## Change Discipline

- State assumptions before implementing. If multiple interpretations would change the implementation or verification strategy, present them and ask.
- Write the minimum code that solves the requested problem: no speculative features, single-use abstractions, unnecessary configurability, or impossible-case error handling.
- Make surgical changes. Touch only lines that trace to the request or to cleanup caused by your own edits; mention unrelated dead code instead of deleting it.
- For multi-step tasks, define success criteria and a brief plan with verification for each step. Loop until the criteria are met or the blocker is explicit.
- Keep files under 1000 lines and test files under 2000.

## Shell

Despite its name, the Bash tool runs commands under **zsh** (my macOS login shell) — it auto-detects zsh from `~/.zshrc` and ignores `$SHELL`. Don't use bash-only syntax at the top level: zsh raises a parse error ("bad substitution") and aborts the whole command.

- Keep top-level commands POSIX-compatible (zsh-safe).
- For bash-only features (`declare -A`, `${var^^}`/`${var,,}`, `${!arr[@]}`, `mapfile`, process substitution `<(...)`), wrap them in an explicit `bash` call (Homebrew bash 5.x is on `PATH`):

```bash
bash <<'EOF'
declare -A color=([sky]=blue [sun]=yellow)
echo "${color[sky]} / ${color[sun]^^}"   # blue / YELLOW
EOF
```

The quoted `<<'EOF'` keeps the body out of zsh's parser and runs it in real bash. For longer scripts, write a `#!/usr/bin/env bash` file and execute it.

When passing paths, URLs, or literal patterns with shell-sensitive characters to a CLI, quote or escape each token. In zsh, unquoted `?`, `*`, `[]`, and `()` are glob syntax, so protect Next.js route groups/dynamic segments and URLs with query strings:

```bash
bat 'src/(shared)/Foo.tsx'
git diff -- 'src/app/(main)/[id]/page.tsx'
curl -sS 'https://api.github.com/search/issues?q=repo:openai/codex+zsh&per_page=10'
rg -F '?' 'src/app/(main)'
wc -l path/to/my\ file.txt
```

- Prefer single quotes for literal paths/URLs. Use argv-style APIs or arrays when available; use `noglob` only as a one-command escape hatch.
- zsh does not word-split scalar strings by default; use arrays or explicit splitting when building argument lists.
- zsh reserves variable names that bash treats as ordinary. `status` is read-only (it mirrors `$?`), so `status=…`, `local status=…`, and `for status in …` all abort with `zsh: read-only variable: status`. `path` is tied to `$PATH`, so assigning it a plain string silently corrupts `PATH`. Avoid both names (use `rc`, `ret`, `result`) or run the script through an explicit `bash` call.
- For searching code, prefer your built-in search tool over shelling out — it sidesteps CLI-flag pitfalls. Otherwise prefer modern, structured CLIs: `fd` for finding files, `jq` for JSON, `yq` for YAML/TOML when available, and `uv` for Python entry points.

## Node.js

- Run one-off scripts as ES modules, with `import` rather than `require` — top-level `await` needs ESM, `require` only works in CommonJS, and mixing them makes Node reject the script.
- File scripts: use a `.mjs` extension (or `"type": "module"` in the nearest `package.json`), then run `node script.mjs`.
- Inline scripts via stdin/heredoc or `-e` default to CommonJS — pass `node --input-type=module` and use `import`:

```bash
node --input-type=module <<'EOF'
import { readFile } from 'node:fs/promises';
const pkg = JSON.parse(await readFile('package.json', 'utf8'));
console.log(pkg.name);
EOF
```

## Skills

File paths mentioned in a `SKILL.md` (`references/`, `scripts/`, etc.) are relative to the skill installation directory — the one containing `SKILL.md`.

## Gmail / Google Drive

For any request involving my Gmail or Google Drive, consult `~/work/mailops` first for how to access them.

## Dotfiles

I manage my dotfiles with [chezmoi](https://chezmoi.io); the source tree lives at `~/.local/share/chezmoi`. chezmoi does not manage `~/.claude` or `~/.codex`.
