---
argument-hint: "[task]"
compatibility: Requires Claude Code Plan mode and Agent-tool subagents with Sonnet model access.
disable-model-invocation: true
metadata:
  install-targets: claude-code
name: claude-handoff
user-invocable: true
description: Orchestrate one to five Sonnet subagents to implement an approved Claude Code plan.
---

# Claude Handoff

Plan in Claude Code with the session's planning model, then hand the approved implementation to one to five Sonnet
subagents in the sequence the task requires. Subagents run in-session through the Agent tool with the host session's
permissions, so they can write anywhere the session can. Use this skill to reserve the expensive planning model for
thinking, orchestration, and verification while cheaper Sonnet agents do the implementation.

## Contract

- Run only after the user explicitly invokes this skill in Plan mode. If Plan mode is not active, ask the user to switch
  and stop.
- Claude owns discovery, decisions, the implementation plan, and agent orchestration. Do not consult subagents while
  planning.
- Each subagent implements its assigned part of the approved plan. It may inspect, edit, and validate, but must not
  redesign the solution or return another plan.
- Use the smallest effective team. One agent remains valid; use additional agents only when decomposition materially
  improves latency, correctness, or verification. Never exceed five agents total across the handoff.
- Keep Claude's implementation work to orchestration, integrity checks, failure handling, and the conditional polish
  pass.

Use `$ARGUMENTS` as the task when present; otherwise use the active user request.

## Plan Phase

Produce a decision-complete plan with this section:

```markdown
## Claude Handoff

- Strategy: `<sequential|parallel|hybrid>`
- Agents: `<1-5>` — `<why this is the smallest effective count>`
- Validation owner: `<agent-id|claude>` — `<aggregate checks it runs once>`

| Agent | Wave | Depends on | Scope              | Implementation brief                                   | Completion evidence                 |
| ----- | ---- | ---------- | ------------------ | ------------------------------------------------------ | ----------------------------------- |
| `A1`  | `1`  | `none`     | `<files/behavior>` | `<outcome, edits, constraints, and stopping criteria>` | `<commands and observable results>` |

- Code polish: `<required|not required>` — `<reason>`
```

Choose the execution shape from repository evidence and the approved work:

- Use sequential agents when one agent depends on another, their write scopes overlap, or a later agent owns integration
  or aggregate validation.
- Use parallel agents only for independent work with explicitly disjoint write scopes. Agents may inspect shared
  context, but must not write outside their assigned scope.
- Use hybrid execution for dependency-ordered waves: run independent agents within a wave in parallel, reconcile the
  entire wave, then start its dependents.

A wave finishes with its slowest agent. Keep every agent's scope focused and move deferrable validation to the
validation owner.

The five-agent limit applies to the entire handoff, not each wave. Assign every agent a stable ID, exact dependencies,
an implementation scope, and its own stopping criteria. If parallel work does not collectively prove the overall plan,
reserve a later sequential agent for integration and aggregate validation.

Assign aggregate validation to exactly one owner per handoff: package-wide or repo-wide checks (full test suites,
whole-package typecheck or lint, catalog-wide checks) run once — by the integration agent when one exists, otherwise by
Claude during post-wave reconciliation. Every other agent's completion evidence must be the narrowest checks that prove
its own edits: file-scoped lint, format, or typecheck plus targeted tests for the files it touched. Duplicate aggregate
runs across a wave's agents are wasted wall-clock time, not extra assurance.

Every agent runs on the latest Sonnet model through the `general-purpose` subagent type; the Agent tool exposes no
per-agent effort or timeout controls, so balance a wave by decomposing scope, not by tuning configuration.

Require `$code-polish` for nonlocal invariants, concurrency or state machines, migrations or parsing, auth or security,
retry or error semantics, and public API or data-contract changes. File count alone is not a trigger.

Do not spawn subagents until the user approves the plan and Claude leaves Plan mode.

## Execution Phase

### Launch

Launch each agent with the Agent tool: `subagent_type: "general-purpose"`, `model: "sonnet"`, and a description like
`A1/3: <scope>`. Start every agent in a parallel wave in the same message as parallel tool calls; start sequential
agents only after reconciling their dependencies. Claude Code renders subagent progress natively — do not build bespoke
progress dashboards, polling loops, or status tables around the calls.

Subagents receive none of the planning conversation. Build a self-contained, outcome-first prompt for each agent
containing:

1. The approved overall outcome plus that agent's implementation brief, dependencies, and completion evidence.
2. Its exact write scope, relevant repository constraints, known dirty-work boundaries (other agents or sessions may be
   editing the same tree), and any prerequisite agent results.
3. Its validation assignment: the scoped checks it must run, and — for every agent other than the validation owner — the
   aggregate checks it must not run because the validation owner runs them once after the wave.
4. This authority boundary: inspect, edit within the assigned scope, and validate locally; do not commit, push, deploy,
   make external writes, or broaden scope — even when repository or host instructions favor committing finished work
   promptly. Committing stays with the orchestrator after reconciliation.
5. This stopping rule: implement the approved plan exactly; if it is infeasible or requires redesign, report blocked
   with evidence instead of proposing a replacement plan.
6. A reporting requirement: return only the files it actually touched, every validation command it ran with outcomes,
   and any residual risks or blockers.

### Collect

When an agent returns, treat its reported changed files as its authoritative post-pass scope. After every wave,
reconcile all results with the plan manifest and the visible working tree without folding in unrelated concurrent
changes. When Claude is the validation owner, run the assigned aggregate checks once during this reconciliation.
Attribute aggregate-check failures before treating them as blockers: a failure confined to files outside every agent's
scope is unrelated concurrent work — confirm the handoff's own files still pass and continue. Unexpected out-of-scope
edits, overlap between agents in the same parallel wave, or an aggregate-check failure attributable to the handoff's
changes are blockers; do not start their dependents or polish, and do not silently take over implementation.

## Completion

- On success, confirm the reported files exist or were intentionally deleted, stay within the agent's scope, and carry
  verification evidence matching its assignment. Pass relevant results to dependent agents.
- On a blocked or failed agent, let already-started independent agents finish, but do not start agents that depend on
  the failure. Continue only work proven independent. Do not silently take over implementation.
- After every required agent completes, deduplicate the union of reported changed files and confirm the combined
  verification evidence proves the approved plan.
- When the plan marked polish as required, invoke `$code-polish` once with exactly that union and its default
  simplify-then-review mode. Skip polish if any required agent failed; do not recompute or broaden scope.
- If the approved work changes one or more Git repositories on this machine other than the repository where the handoff
  began, automatically invoke `$commit` from each additional repository after its work, validation, and any required
  polish are complete. Scope each invocation to the files changed there, do not ask for separate confirmation, and do
  not commit incomplete, blocked, unexpected, or out-of-scope changes. Push only when the user explicitly requested it.
- Finish with a concise prose summary: strategy and agent count, each agent's status with a one-line summary, the
  combined changed files, the verification evidence, the polish result when run, any automatic cross-repository commit
  hashes, and remaining risks or blockers.
