---
argument-hint: "[task]"
compatibility:
  Requires Claude Code Plan mode, Git, /bin/bash, Python 3, and an authenticated Codex CLI with dangerous bypass
  support. Claude Code >= 2.1.98 recommended for live progress via the Monitor tool.
disable-model-invocation: true
metadata:
  install-targets: claude-code
name: codex-handoff
user-invocable: true
description:
  Orchestrate read-only Codex research agents during planning and one to five Codex CLI agents to implement the approved
  plan.
---

# Codex Handoff

If these instructions are already present in the conversation from a slash or dollar invocation, follow them directly;
do not invoke this skill again through a skill tool.

Follow the Contract below, then use the Codex CLI workflow to research during planning and implement the approved plan.

## Contract

- Run only after the user explicitly invokes this skill in Plan mode. If Plan mode is not active, ask the user to switch
  and stop.
- Claude owns decisions, the final implementation plan, and agent orchestration. For complex tasks, delegate
  investigation to read-only Codex research agents before writing the plan.
- Research agents gather evidence and report findings. They never edit files, make design decisions, or return plans of
  their own.
- Each implementation agent implements its assigned part of the approved plan. It may inspect, edit, and validate, but
  must not redesign the solution or return another plan.
- Use the smallest effective implementation team. One implementation agent remains valid; use additional agents only
  when decomposition materially improves latency, correctness, or verification. Never exceed five implementation agents
  across the handoff.
- Use at most three research agents with stable IDs `R1` through `R3`. Count them separately from the five
  implementation agents.
- Keep Claude's implementation work to orchestration, integrity checks, failure handling, and the conditional polish
  pass.

Use `$ARGUMENTS` as the task when present; otherwise use the active user request.

## Research Phase

Trigger research when scope is uncertain, the task crosses multiple or unfamiliar subsystems, or the plan depends on
evidence that would be materially slower for Claude to gather serially. Zero research agents remains the default. Claude
alone decides from the task and repository evidence whether research runs; never ask the user to opt in or name agents.
Either launch the research wave immediately or proceed straight to planning.

When triggered, assign up to three agents stable IDs `R1` through `R3` and launch them immediately during Plan mode.
Resolve `scripts/run-codex-handoff.sh` relative to this `SKILL.md`, use the Execution Phase launch template with
`--read-only`, and give every agent separate `<agent-id>.progress.jsonl`, `<agent-id>.result.json`, and
`<agent-id>.stderr.log` artifacts. Start all selected agents as background Bash tasks (`run_in_background: true`) in the
same turn, then watch the wave through the same `watch-codex-wave.sh` and Monitor flow used for implementation. The
runner's enforced read-only sandbox makes this launch legitimate during Plan mode.

Apply implementation prompt checklist items 2, 4, 6, and 7 to each self-contained research prompt, adapting write scope
and edit authority to a read-only investigation scope. Require the agent to answer the open questions, report `status`,
`findings`, `open_questions`, `evidence`, and `blockers` per `references/research-result.schema.json`, and never return
a plan or design.

Select research configuration from the same tiers used for implementation:

| Investigation                          | Model           | Effort             | Baseline timeout |
| -------------------------------------- | --------------- | ------------------ | ---------------- |
| Bounded, routine survey                | `gpt-5.6-luna`  | `medium`           | 10 minutes       |
| Involved survey across unfamiliar code | `gpt-5.6-terra` | `medium` or `high` | 15 minutes       |
| Deep, cross-cutting investigation      | `gpt-5.6-sol`   | `xhigh`            | 20 minutes       |

Use Luna or Terra for bounded surveys and Sol at `xhigh` for deep cross-cutting investigation. Never select `low` or
`ultra`. Research should normally use shorter budgets than implementation; keep the baseline between 10 and 20 minutes
unless repository evidence requires otherwise.

When the research wave settles, read every result artifact and fold its findings and evidence into the implementation
plan. Surface `open_questions` or `blockers` through `AskUserQuestion` only when they change scope or approach. Do not
reconcile the working tree: research agents change nothing. Flag any research result reporting edits as a contract
violation.

## Plan Phase

Produce a decision-complete plan with this section:

```markdown
## Codex Handoff

- Research: `<none | R1..Rn — key findings used>`
- Strategy: `<sequential|parallel|hybrid>`
- Agents: `<1-5>` — `<why this is the smallest effective count>`
- Validation owner: `<agent-id|claude>` — `<aggregate checks it runs once>`

| Agent | Wave | Depends on | Scope              | Model                                        | Effort                       | Timeout             | Implementation brief                                   | Completion evidence                 |
| ----- | ---- | ---------- | ------------------ | -------------------------------------------- | ---------------------------- | ------------------- | ------------------------------------------------------ | ----------------------------------- |
| `A1`  | `1`  | `none`     | `<files/behavior>` | `<gpt-5.6-luna\|gpt-5.6-terra\|gpt-5.6-sol>` | `<medium\|high\|xhigh\|max>` | `<minutes> minutes` | `<outcome, edits, constraints, and stopping criteria>` | `<commands and observable results>` |

- Code polish: `<required|not required>` — `<reason>`
```

Choose the execution shape from repository evidence and the approved work:

- Use sequential agents when one agent depends on another, their write scopes overlap, or a later agent owns integration
  or aggregate validation.
- Use parallel agents only for independent work with explicitly disjoint write scopes. Agents may inspect shared
  context, but must not write outside their assigned scope.
- Use hybrid execution for dependency-ordered waves: run independent agents within a wave in parallel, reconcile the
  entire wave, then start its dependents.

A wave finishes with its slowest agent. Keep the highest-tier agent's scope minimal and move deferrable validation to
the validation owner.

If parallel work does not collectively prove the overall plan, reserve a later sequential agent for integration and
aggregate validation.

Assign aggregate validation to exactly one owner per handoff: package-wide or repo-wide checks (full test suites,
whole-package typecheck or lint, catalog-wide checks) run once — by the integration agent when one exists, otherwise by
Claude during post-wave reconciliation. Every other agent's completion evidence must be the narrowest checks that prove
its own edits: file-scoped lint, format, or typecheck plus targeted tests for the files it touched. Duplicate aggregate
runs across a wave's agents are wasted wall-clock time, not extra assurance.

Select configuration deliberately:

| Work                                     | Model           | Effort             | Baseline timeout |
| ---------------------------------------- | --------------- | ------------------ | ---------------- |
| Bounded, routine implementation          | `gpt-5.6-luna`  | `medium`           | 10 minutes       |
| Everyday or involved implementation      | `gpt-5.6-terra` | `medium` or `high` | 20 minutes       |
| Semantic or cross-cutting implementation | `gpt-5.6-sol`   | `xhigh`            | 40 minutes       |
| Exceptional, high-risk implementation    | `gpt-5.6-sol`   | `max`              | 60 minutes       |

Never select `low` or `ultra`. Adjust the timeout when repository evidence shows that required validation needs
materially more or less time. The timeout is a kill-switch, not pacing: Codex never sees it and an early finish costs
nothing, so never tighten it hoping for speed — size it only to bound how long a hung agent can block its wave.

Require `$code-polish` for nonlocal invariants, concurrency or state machines, migrations or parsing, auth or security,
retry or error semantics, and public API or data-contract changes. File count alone is not a trigger.

Do not invoke implementation agents until the user approves the plan and Claude leaves Plan mode. The read-only research
phase above is the only pre-approval exception.

## Execution Phase

Resolve `scripts/run-codex-handoff.sh` to an absolute path relative to this `SKILL.md`; never search for it in the
target repository. Each invocation is one Codex agent.

### Launch

These instructions launch implementation agents. Without `--read-only`, the runner deliberately disables Codex approvals
and sandboxing. Use that mode only when the user has accepted that agents can read, modify, or delete any files
accessible to the host account. The runner pins every Codex process to the `default` service tier, overriding any
inherited fast or priority selection without changing the host's persisted Codex configuration.

Before launching agents, do not hold a path-scoped session claim over any path in an agent's write scope. Record
orchestrator intent with a pathless label only; the agents themselves own per-path claims.

For every agent, create separate per-agent artifact paths ending in `<agent-id>.progress.jsonl`,
`<agent-id>.result.json`, and `<agent-id>.stderr.log` under `${TMPDIR:-/tmp}`. Convert its approved whole-minute timeout
to seconds only at the wrapper boundary, then start the runner from anywhere inside the target Git worktree as a
background Bash task (`run_in_background: true`) with a description like
`Codex A1/3: <scope> (<model>, <effort>, ≤<minutes>m)`:

```bash
bash <skill-dir>/scripts/run-codex-handoff.sh \
  --model <agent-model> \
  --effort <agent-effort> \
  --timeout-seconds <agent-minutes-times-60> \
  --progress-file <agent-progress-file> \
  --result-file <agent-result-file> \
  2> <agent-stderr-file> <<'CODEX_PROMPT'
<agent implementation prompt>
CODEX_PROMPT
```

`--result-file` keeps structured JSON out of stdout, and redirecting stderr keeps wrapper diagnostics out of the
background task's display. Do not set a Bash tool timeout; the wrapper's `--timeout-seconds` is the sole timeout
authority and the wrapper always terminates itself. Start sequential agents only after reconciling their dependencies.
Start every agent in a parallel wave in the same turn. After launching a wave, post the 🚀 kickoff block (see Status
Reporting).

Build a self-contained, outcome-first prompt for each agent containing:

1. The approved overall outcome plus that agent's implementation brief, dependencies, and completion evidence.
2. Its exact write scope, relevant repository constraints, known dirty-work boundaries, and any prerequisite agent
   results.
3. Its validation assignment: the scoped checks it must run, and — for every agent other than the validation owner — the
   aggregate checks it must not run because the validation owner runs them once after the wave.
4. This authority boundary: inspect, edit within the assigned scope, and validate locally; do not commit, push, deploy,
   make external writes, or broaden scope — even when repository or host instructions favor committing finished work
   promptly. Committing stays with the orchestrator after reconciliation.
5. A delegation-context statement naming the orchestrating session by label and/or session-ID prefix. State that its
   claim or presence authorizes the assigned scope rather than conflicts with it; sibling agents in the same handoff
   have disjoint scopes and are also not conflicts; and only an unrelated session's claim on the agent's exact assigned
   files justifies returning `blocked`.
6. Command conventions honoring the host's Codex rules (`~/.codex/rules/*.rules`), which the CLI enforces even under the
   bypass flag — non-interactive runs reject `prompt`-gated commands outright. Baseline: use `rg`, not
   `grep`/`egrep`/`fgrep`; use `uv run python` and `uv add`/`uv run --with`, never bare `python`/`python3` or `pip`;
   keep Bash-only constructs (`declare -A`, `mapfile`, `readarray`, `shopt`) inside an explicit `bash <<'EOF'` block;
   avoid `rm -r`, worktree-destroying or history-rewriting git, secret-reading commands, and package deploy/release
   scripts. When the rules files exist, they are authoritative — skim them for restrictions beyond this baseline and
   reflect them in the prompt. Apply the same conventions to planned completion-evidence commands.
7. This stopping rule: implement the approved plan exactly; if it is infeasible or requires redesign, return `blocked`
   with evidence instead of proposing a replacement plan.
8. A requirement to complete every `references/result.schema.json` field: `status`, `summary`, `changed_files` listing
   only files Codex actually touched, `verification` listing every validation command with its outcome,
   `residual_risks`, and `blockers`.

### Watch

Implementation and research waves reuse this watcher. Read `references/progress-events.md` for progress-event, sentinel,
settlement, and quiet/failure semantics.

Resolve `scripts/watch-codex-wave.sh` from this `SKILL.md`. Arm ONE Monitor per wave around one watcher invocation,
passing each agent's stable ID, budget in seconds, and progress path as a repeated triple:

```sh
bash <skill-dir>/scripts/watch-codex-wave.sh \
  --agent A1 <budget-seconds> <A1.progress.jsonl> \
  --agent A2 <budget-seconds> <A2.progress.jsonl>
```

The watcher tolerates delayed file creation and emits stable JSONL `watcher.digest`, `watcher.sentinel`, and
`watcher.settlement` records. It owns elapsed time, event counts, last command/file activity, settled percentage, and
the ten-cell bar. Set the Monitor `timeout_ms` above the wave's largest budget plus the 120-second no-sentinel grace. On
each watcher digest or settlement, post one short wave-status block using those exact facts. If Monitor is unavailable,
run the same watcher in a foreground command; do not recreate its loop or arithmetic.

The watcher settles an agent as failed with reason `no-sentinel` once elapsed exceeds its budget plus 120 seconds of
grace; handle that settlement like any failed sentinel. Silence is never evidence of safety buffering or model
rerouting. Keep watching until the wrapper sentinel or approved timeout; never cancel, retry, extend, or downgrade
because of silence. Report `no recent activity` during quiet periods.

### Collect

When an implementation agent's sentinel arrives, read its result artifact and its stderr artifact for the
`codex-handoff: elapsed=<seconds>s` line or failure forensics. The `--output-schema` request shapes the result artifact;
the wrapper does not validate it. Treat a result that does not parse against `references/result.schema.json` as a
failure. Research waves reuse this collection flow with `references/research-result.schema.json`, then feed their
findings into the plan without working-tree reconciliation. Do not read or print the background task output;
artifact-mode stdout is intentionally empty.

Treat each implementation agent's `changed_files` as its authoritative post-pass scope. After every implementation wave,
reconcile all results with the manifest and the visible working tree without folding in unrelated concurrent changes.
When Claude is the validation owner, run the assigned aggregate checks once during this reconciliation. Attribute
aggregate-check failures before treating them as blockers: a failure confined to files outside every implementation
agent's scope is unrelated concurrent work — confirm the handoff's own files still pass and continue. Unexpected
out-of-scope edits, overlap between agents in the same parallel wave, or an aggregate-check failure attributable to the
handoff's changes are blockers; do not start their dependents or polish, and do not silently take over implementation.

## Status Reporting

These wave dashboards and the Completion report are mandatory user-facing output. Host-rendered `Background command`,
`Task Output`, and `Monitor event` banners are transport notifications, not status reports, and their chrome cannot be
restyled by this skill. Do not echo their task IDs, raw JSON, sentinels, or monitor payloads. Keep task output empty
through the artifact paths above, then immediately follow each relevant host event with the appropriate wave dashboard
below.

Use this legend consistently: 🔎 research · 🚀 kickoff · ⏳ running · ✅ completed · ⛔ blocked · ⏱️ timed out · 💥
runner error · 🧹 polish · 🏁 final report. Keep every update to one compact block and render the tables; do not replace
them with prose.

Prefix every wave-scoped kickoff, digest, and completion update with the watcher's exact 10-cell bar, percentage, and
settled counts. Progress means sentinel settlement, including failed sentinels; never infer it from elapsed time, event
count, or activity. Keep failures visible through the existing status emoji and agent row.

Kickoff, once per wave:

```markdown
### 🚀 Wave 1/2 [░░░░░░░░░░] 0% (0/3 settled) — 3 agents launched

| Agent | Scope               | Model · effort        | Budget | State       |
| ----- | ------------------- | --------------------- | ------ | ----------- |
| A1    | `internal/pricing`  | `gpt-5.6-sol` · high  | ≤30m   | 🚀 launched |
| A2    | `internal/backfill` | `gpt-5.6-sol` · high  | ≤30m   | 🚀 launched |
| A3    | `internal/evidence` | `gpt-5.6-sol` · xhigh | ≤40m   | 🚀 launched |
```

Research waves reuse these dashboards with investigation scopes in place of implementation scopes. Use 🔎 in every
research-wave heading, for example `### 🔎 Research wave 1/1 [██████████] 100% (2/2 settled) — 2 agents completed`;
retain the row-level status icons.

The kickoff table already contains the wave's manifest rows; do not repeat them.

Wave status, on each digest or completion:

```markdown
### ⏳ Wave 1/2 [███░░░░░░░] 33% (1/3 settled) — 15m elapsed

| Agent | Status     | Activity                   |
| ----- | ---------- | -------------------------- |
| A1    | ⏳ 15m/20m | ran `cargo test`           |
| A2    | ✅ 8m      | done — 3 files, tests pass |
| A3    | ⏳ 15m/20m | no recent activity         |
```

At full settlement, use the final watcher settlement record. A wave that settled with failures still reaches 100%; its
heading and agent rows must show the failure rather than imply success.

## Completion

- On `completed`, confirm the reported files exist or were intentionally deleted, stay within the agent's scope, and
  carry verification evidence matching its assignment. Pass relevant results to dependent agents.
- Treat a returned `status: blocked` as a plan problem. Let already-started independent agents finish, gate its
  dependents, report the evidence, and let the user decide; never silently take over implementation. Treat timeouts,
  nonzero runner exits, and watcher `no-sentinel` settlements as failed settlements, and continue only work proven
  independent.
- Triage a `handoff.failed` sentinel with reason `error` before treating it as a plan failure. When the stderr artifact
  evidences a transport, stream, or API death (`stream disconnected`, `Transport error`, `network error`,
  `error decoding response body`) and the forensics show no Codex-reported task failure, inspect the agent's write scope
  for partial edits with `git status` and `git diff`. Extract the session ID from the progress file's `thread.started`
  event, then relaunch that agent once through the runner's `--resume <session-id>` with a fresh budget and a short
  verify-and-continue prompt naming the partially edited files. Fall back to one fresh relaunch only when no session ID
  is recoverable. This is a retry of the same agent, not a new agent against the five-agent limit. A second
  infrastructure failure for that agent is a blocker. Returned `blocked` results and timeouts are never infrastructure
  failures.
- After every required agent completes, deduplicate the union of reported `changed_files` and confirm the combined
  verification evidence proves the approved plan.
- When the plan marked polish as required, invoke `$code-polish` once with exactly that union and its default
  simplify-then-review mode. Skip polish if any required agent failed; do not recompute or broaden scope.
- If the approved work changes one or more Git repositories on this machine other than the repository where the handoff
  began, automatically invoke `$commit` from each additional repository after its work, validation, and any required
  polish are complete. Scope each invocation to the files changed there, do not ask for separate confirmation, and do
  not commit incomplete, blocked, unexpected, or out-of-scope changes. Push only when the user explicitly requested it.
- Finish with the rendered 🏁 report below. Include the strategy, agent count, and per agent — requested model, effort,
  timeout budget vs actual elapsed (from `elapsed=`/the sentinel), output tokens when available, status, and summary —
  for a resumed retry, report the resumed sentinel's `output_tokens` minus the prior run's as that attempt's usage —
  plus the combined changed files and verification, the polish result when run, any automatic cross-repository commit
  hashes, blockers, and residual risks. Omit inapplicable subsections; write `none` for an applicable empty value. Never
  expose the result JSON.

````markdown
### 🏁 Codex handoff [██████████] 100% (3/3 settled) — completed

`parallel` · `3 agents` · `1 wave`

| Agent | Result       | Model · effort        | Budget → actual | Tokens | Summary                |
| ----- | ------------ | --------------------- | --------------- | ------ | ---------------------- |
| A1    | ✅ completed | `gpt-5.6-sol` · high  | 30m → 11m 42s   | 8,421  | Fixed price inversion  |
| A2    | ✅ completed | `gpt-5.6-sol` · high  | 30m → 18m 05s   | 12,804 | Added backfill library |
| A3    | ✅ completed | `gpt-5.6-sol` · xhigh | 40m → 22m 19s   | 15,117 | Added evidence checks  |

**📦 Changed**

```text
├── internal/pricing/invert.go
├── internal/backfill/backfill.go
└── internal/evidence/check.go
```

**🧪 Verification**

```text
├── ✅ go test ./internal/pricing/...
├── ✅ go test ./internal/backfill/...
└── ✅ go test ./internal/evidence/...
```

**🧹 Polish** — not required

**⚠️ Risks / blockers** — none
````
