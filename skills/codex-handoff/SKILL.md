---
argument-hint: '[task]'
compatibility: Requires Claude Code Plan mode, Git, /bin/bash, and an authenticated Codex CLI.
disable-model-invocation: true
metadata:
  install-targets: claude-code
name: codex-handoff
user-invocable: true
description: Delegate an approved Claude Code plan to Codex CLI for implementation.
---

# Codex Handoff

Plan in Claude Code, then hand the approved implementation to one constrained Codex CLI run.

## Contract

- Run only after the user explicitly invokes this skill in Plan mode. If Plan mode is not active, ask the user to switch and stop.
- Claude owns discovery, decisions, and the implementation plan. Do not consult Codex while planning.
- Codex implements the approved plan. It may inspect, edit, and validate, but must not redesign the solution or return another plan.
- Keep Claude's implementation work to orchestration, integrity checks, failure handling, and the conditional polish pass.

Use `$ARGUMENTS` as the task when present; otherwise use the active user request.

## Plan Phase

Produce a decision-complete plan with this section:

```markdown
## Codex Handoff

- Model: `<gpt-5.6-terra|gpt-5.6-sol>`
- Effort: `<medium|high|xhigh|max>`
- Timeout: `<seconds>`
- Implementation brief: `<approved outcome, edits, constraints, and stopping criteria>`
- Completion evidence: `<commands and observable results>`
- Code polish: `<required|not required>` — `<reason>`
```

Select configuration deliberately:

| Work                                     | Model                            | Effort             | Baseline timeout |
| ---------------------------------------- | -------------------------------- | ------------------ | ---------------- |
| Bounded, routine implementation          | `gpt-5.6-terra`                  | `medium` or `high` | 600s             |
| Involved multi-file implementation       | `gpt-5.6-terra` or `gpt-5.6-sol` | `high`             | 1200s            |
| Semantic or cross-cutting implementation | `gpt-5.6-sol`                    | `xhigh`            | 2400s            |
| Exceptional, high-risk implementation    | `gpt-5.6-sol`                    | `max`              | 3600s            |

Never select GPT-5.6 Luna, `low`, or `ultra`. Adjust the timeout when repository evidence shows that required validation needs materially more or less time.

Require `$code-polish` for nonlocal invariants, concurrency or state machines, migrations or parsing, auth or security, retry or error semantics, and public API or data-contract changes. File count alone is not a trigger.

Do not invoke Codex until the user approves the plan and Claude leaves Plan mode.

## Execution Phase

Resolve `scripts/run-codex-handoff.sh` to an absolute path relative to this `SKILL.md`; never search for it in the target repository. Invoke it from anywhere inside the target Git worktree:

```bash
bash <skill-dir>/scripts/run-codex-handoff.sh \
  --model <model> \
  --effort <effort> \
  --timeout-seconds <seconds> <<'CODEX_PROMPT'
<implementation prompt>
CODEX_PROMPT
```

Set the Bash tool timeout slightly above the wrapper timeout. If the host's foreground limit is shorter, run that single Bash call in the background and wait for it; do not create resumable Codex job state.

Build a self-contained, outcome-first prompt containing:

1. The approved implementation brief and completion evidence.
2. Relevant repository constraints and known dirty-work boundaries.
3. This authority boundary: inspect, edit, and validate locally; do not commit, push, deploy, make external writes, or broaden scope.
4. This stopping rule: implement the approved plan exactly; if it is infeasible or requires redesign, return `blocked` with evidence instead of proposing a replacement plan.
5. A requirement to report only files Codex actually touched and every validation command it ran.

The wrapper emits one JSON object matching `references/result.schema.json`. Treat its `changed_files` as the authoritative post-pass scope, then reconcile them with the visible working tree without folding in unrelated concurrent changes.

## Completion

- On `completed`, confirm the reported files exist or were intentionally deleted and that verification evidence matches the approved plan.
- When the plan marked polish as required, invoke `$code-polish` programmatically with exactly `changed_files` and its default simplify-then-review mode. Do not recompute or broaden scope.
- On `blocked`, timeout, or nonzero runner exit, skip polish. Report the blocker, partial edits, and diagnostics; do not silently take over implementation.
- Finish with the selected model, effort, timeout, Codex summary, changed files, verification, polish result when run, and residual risks.
