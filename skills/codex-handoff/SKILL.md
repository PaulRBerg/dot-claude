---
argument-hint: "[task]"
compatibility: Requires Claude Code Plan mode, Git, /bin/bash, and an authenticated Codex CLI with dangerous bypass support. Claude Code >= 2.1.98 recommended for live progress via the Monitor tool.
disable-model-invocation: true
metadata:
  install-targets: claude-code
name: codex-handoff
user-invocable: true
description: Orchestrate one to five Codex CLI agents to implement an approved Claude Code plan.
---

# Codex Handoff

Plan in Claude Code, then hand the approved implementation to one to five Codex CLI agents in the sequence the task
requires. The runner uses `--dangerously-bypass-approvals-and-sandbox`, so agents can write anywhere the host user can,
including outside the worktree.

## Contract

- Run only after the user explicitly invokes this skill in Plan mode. If Plan mode is not active, ask the user to switch
  and stop.
- Claude owns discovery, decisions, the implementation plan, and agent orchestration. Do not consult Codex while
  planning.
- Each Codex agent implements its assigned part of the approved plan. It may inspect, edit, and validate, but must not
  redesign the solution or return another plan.
- Use the smallest effective team. One agent remains valid; use additional agents only when decomposition materially
  improves latency, correctness, or verification. Never exceed five agents total across the handoff.
- Keep Claude's implementation work to orchestration, integrity checks, failure handling, and the conditional polish
  pass.

Use `$ARGUMENTS` as the task when present; otherwise use the active user request.

## Plan Phase

Produce a decision-complete plan with this section:

```markdown
## Codex Handoff

- Strategy: `<sequential|parallel|hybrid>`
- Agents: `<1-5>` — `<why this is the smallest effective count>`

| Agent | Wave | Depends on | Scope              | Model                          | Effort                       | Timeout             | Implementation brief                                   | Completion evidence                 |
| ----- | ---- | ---------- | ------------------ | ------------------------------ | ---------------------------- | ------------------- | ------------------------------------------------------ | ----------------------------------- |
| `A1`  | `1`  | `none`     | `<files/behavior>` | `<gpt-5.6-terra\|gpt-5.6-sol>` | `<medium\|high\|xhigh\|max>` | `<minutes> minutes` | `<outcome, edits, constraints, and stopping criteria>` | `<commands and observable results>` |

- Code polish: `<required|not required>` — `<reason>`
```

Choose the execution shape from repository evidence and the approved work:

- Use sequential agents when one agent depends on another, their write scopes overlap, or a later agent owns integration
  or aggregate validation.
- Use parallel agents only for independent work with explicitly disjoint write scopes. Agents may inspect shared
  context, but must not write outside their assigned scope.
- Use hybrid execution for dependency-ordered waves: run independent agents within a wave in parallel, reconcile the
  entire wave, then start its dependents.

The five-agent limit applies to the entire handoff, not each wave. Assign every agent a stable ID, exact dependencies,
an implementation scope, and its own configuration and stopping criteria. If parallel work does not collectively prove
the overall plan, reserve a later sequential agent for integration and aggregate validation.

Select configuration deliberately:

| Work                                     | Model                            | Effort             | Baseline timeout |
| ---------------------------------------- | -------------------------------- | ------------------ | ---------------- |
| Bounded, routine implementation          | `gpt-5.6-terra`                  | `medium` or `high` | 10 minutes       |
| Involved multi-file implementation       | `gpt-5.6-terra` or `gpt-5.6-sol` | `high`             | 20 minutes       |
| Semantic or cross-cutting implementation | `gpt-5.6-sol`                    | `xhigh`            | 40 minutes       |
| Exceptional, high-risk implementation    | `gpt-5.6-sol`                    | `max`              | 60 minutes       |

Never select GPT-5.6 Luna, `low`, or `ultra`. Adjust the timeout when repository evidence shows that required validation
needs materially more or less time.

Require `$code-polish` for nonlocal invariants, concurrency or state machines, migrations or parsing, auth or security,
retry or error semantics, and public API or data-contract changes. File count alone is not a trigger.

Do not invoke Codex until the user approves the plan and Claude leaves Plan mode.

## Execution Phase

Resolve `scripts/run-codex-handoff.sh` to an absolute path relative to this `SKILL.md`; never search for it in the
target repository. Each invocation is one ephemeral Codex agent.

### Launch

The runner deliberately disables Codex approvals and sandboxing. Use it only when the user has accepted that agents can
read, modify, or delete any files accessible to the host account.

For every agent, create a per-agent progress path such as `"${TMPDIR:-/tmp}/codex-handoff.<agent-id>.progress.jsonl"`,
convert its approved whole-minute timeout to seconds only at the wrapper boundary, then start the runner from anywhere
inside the target Git worktree as a background Bash task (`run_in_background: true`) with a description like
`Codex A1/3: <scope> (<model>, <effort>, ≤<minutes>m)`:

```bash
bash <skill-dir>/scripts/run-codex-handoff.sh \
  --model <agent-model> \
  --effort <agent-effort> \
  --timeout-seconds <agent-minutes-times-60> \
  --progress-file <agent-progress-file> <<'CODEX_PROMPT'
<agent implementation prompt>
CODEX_PROMPT
```

Do not set a Bash tool timeout; the wrapper's `--timeout-seconds` is the sole timeout authority and the wrapper always
terminates itself. Start sequential agents only after reconciling their dependencies. Start every agent in a parallel
wave in the same turn. After launching a wave, post the 🚀 kickoff block (see Status Reporting).

Build a self-contained, outcome-first prompt for each agent containing:

1. The approved overall outcome plus that agent's implementation brief, dependencies, and completion evidence.
2. Its exact write scope, relevant repository constraints, known dirty-work boundaries, and any prerequisite agent
   results.
3. This authority boundary: inspect, edit within the assigned scope, and validate locally; do not commit, push, deploy,
   make external writes, or broaden scope.
4. This stopping rule: implement the approved plan exactly; if it is infeasible or requires redesign, return `blocked`
   with evidence instead of proposing a replacement plan.
5. A requirement to report only files Codex actually touched and every validation command it ran.

### Watch

Each progress file streams Codex JSONL events and ends with exactly one wrapper sentinel — `handoff.completed` or
`handoff.failed` with reason `timeout`, `error`, or `cancelled` (vocabulary, filters, and a ready-made watch loop:
`references/progress-events.md`). The sentinel, not process state, is the completion signal.

Arm ONE Monitor per wave that tails every progress file in the wave and emits each sentinel immediately plus a per-agent
digest roughly every 300 seconds (elapsed vs budget, event count, last `command_execution` or `file_change` activity),
exiting once all sentinels are seen. Set the Monitor `timeout_ms` above the wave's largest agent timeout. On each
digest, post one short ⏳ wave-status block. If the Monitor tool is unavailable in the host, poll each progress file for
its sentinel with short foreground Bash checks instead.

### Collect

When an agent's sentinel arrives, read that background task's output file (use the Read tool, not deprecated
TaskOutput): stdout is one JSON object matching `references/result.schema.json`; stderr carries a
`codex-handoff: elapsed=<seconds>s` line and, on failure, the agent's last recorded activity. Treat each agent's
`changed_files` as its authoritative post-pass scope. After every wave, reconcile all results with the manifest and the
visible working tree without folding in unrelated concurrent changes. Unexpected out-of-scope edits or overlap between
agents in the same parallel wave are blockers; do not start their dependents or polish.

## Status Reporting

Use this legend consistently: 🚀 kickoff · ⏳ running · ✅ completed · ⛔ blocked · ⏱️ timed out · 💥 runner error · 🧹
polish · 🏁 final report. Keep every update to one short block — no walls of text.

Kickoff, once per wave: the wave's manifest rows (agent, scope, model, effort, timeout), one `tail -f <progress-file>`
line per agent for real-time watching in another pane, and a note that `/tasks` lists and stops running agents.

Wave status, on each digest or completion:

```markdown
### ⏳ Wave 1/2 — 15m elapsed

| Agent | Status     | Activity                   |
| ----- | ---------- | -------------------------- |
| A1    | ⏳ 15m/20m | ran `cargo test`           |
| A2    | ✅ 8m      | done — 3 files, tests pass |
```

## Completion

- On `completed`, confirm the reported files exist or were intentionally deleted, stay within the agent's scope, and
  carry verification evidence matching its assignment. Pass relevant results to dependent agents.
- On `blocked`, timeout, or nonzero runner exit, let already-started independent agents finish, but do not start agents
  that depend on the failure. Continue only work proven independent. Do not silently take over implementation.
- After every required agent completes, deduplicate the union of reported `changed_files` and confirm the combined
  verification evidence proves the approved plan.
- When the plan marked polish as required, invoke `$code-polish` once with exactly that union and its default
  simplify-then-review mode. Skip polish if any required agent failed; do not recompute or broaden scope.
- Finish with a 🏁 report: the strategy, agent count, and per agent — model, effort, timeout budget vs actual elapsed
  (from `elapsed=`/the sentinel), output tokens when available, status, and summary — plus the combined changed files
  and verification, the polish result when run, blockers, and residual risks.
