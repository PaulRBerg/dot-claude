---
argument-hint: "[task]"
compatibility: Requires Claude Code Plan mode and Agent-tool subagents with Haiku, Sonnet, and Opus model access.
disable-model-invocation: true
metadata:
  install-targets: claude-code
name: claude-handoff
user-invocable: true
description:
  Orchestrate read-only Explore research subagents during planning and one to five Haiku, Sonnet, or Opus subagents to
  implement the approved plan.
---

# Claude Handoff

If these instructions are already present in the conversation from a slash or dollar invocation, follow them directly;
do not invoke this skill again through a skill tool.

Follow the Contract below, then use Claude Code's in-session Agent workflow to research during planning and implement
the approved plan.

## Contract

- Run only after the user explicitly invokes this skill in Plan mode. If Plan mode is not active, ask the user to switch
  and stop.
- Claude owns decisions, the final implementation plan, and agent orchestration. For complex tasks, delegate
  investigation to read-only research subagents before writing the plan.
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

When triggered, assign up to three agents stable IDs `R1` through `R3` and launch them immediately during Plan mode
through the Agent tool with `subagent_type: "Explore"`. The read-only Explore toolset makes this launch legitimate
during Plan mode. Launch all selected agents in parallel as Agent calls in one message, post
`🔎 Research started — <n> agents`, then rely on native subagent progress rendering; do not build dashboards.

Give each research agent a self-contained prompt containing the open questions to answer, its exact investigation scope,
the read-only boundary, and a thoroughness hint: `medium` for bounded surveys or `very thorough` for multi-subsystem
sweeps. Require findings, evidence, open questions, and blockers; explicitly prohibit returning a plan or design.

Use the default Explore agent for bounded surveys. Set the Agent tool's `model` override to `opus` only for genuinely
hard synthesis, consistent with the implementation model-escalation rules below. Agent count and repository size alone
do not justify escalation.

When the research wave settles, read every result and fold its findings and evidence into the implementation plan.
Surface open questions or blockers through `AskUserQuestion` only when they change scope or approach. Do not reconcile
the working tree: research agents change nothing. Flag any research result reporting edits as a contract violation.

## Plan Phase

Produce a decision-complete plan with this section:

```markdown
## Claude Handoff

- Research: `<none | R1..Rn — key findings used>`
- Strategy: `<sequential|parallel|hybrid>`
- Agents: `<1-5>` — `<why this is the smallest effective count>`
- Validation owner: `<agent-id|claude>` — `<aggregate checks it runs once>`

| Agent | Wave | Depends on | Scope              | Model                   | Implementation brief                                   | Completion evidence                 |
| ----- | ---- | ---------- | ------------------ | ----------------------- | ------------------------------------------------------ | ----------------------------------- |
| `A1`  | `1`  | `none`     | `<files/behavior>` | `<haiku\|sonnet\|opus>` | `<outcome, edits, constraints, and stopping criteria>` | `<commands and observable results>` |

- Code polish: `<required|not required>` — `<reason>`
```

Choose the execution shape from repository evidence and the approved work:

- Use sequential agents when one agent depends on another, their write scopes overlap, or a later agent owns integration
  or aggregate validation.
- Use parallel agents only for independent work with explicitly disjoint write scopes. Agents may inspect shared
  context, but must not write outside their assigned scope.
- Use hybrid execution for dependency-ordered waves: run independent agents within a wave in parallel, reconcile the
  entire wave, then start its dependents.

A wave finishes with its slowest agent. Keep the Opus agents' scope minimal and move deferrable validation to the
validation owner.

If parallel work does not collectively prove the overall plan, reserve a later sequential agent for integration and
aggregate validation.

Assign aggregate validation to exactly one owner per handoff: package-wide or repo-wide checks (full test suites,
whole-package typecheck or lint, catalog-wide checks) run once — by the integration agent when one exists, otherwise by
Claude during post-wave reconciliation. Every other agent's completion evidence must be the narrowest checks that prove
its own edits: file-scoped lint, format, or typecheck plus targeted tests for the files it touched. Duplicate aggregate
runs across a wave's agents are wasted wall-clock time, not extra assurance.

Select each agent's model from this table:

| Work                                                                               | Model    |
| ---------------------------------------------------------------------------------- | -------- |
| Strictly mechanical, low-risk brief with exact instructions and cheap verification | `haiku`  |
| Bounded implementation with a clear shape                                          | `sonnet` |
| Multi-file implementation that follows established repository patterns             | `sonnet` |
| Semantic or cross-cutting implementation, or subtle invariants                     | `opus`   |
| High-risk implementation, or a brief needing judgment under ambiguity              | `opus`   |

Select only `haiku`, `sonnet`, or `opus`. Default to `sonnet`; use `haiku` only for the strictly mechanical tier, and
use `opus` when semantic risk or ambiguity demands it. File count, agent count, and wave width alone are not model
triggers. The `$code-polish` triggers below are risk signals that force `opus`, never `haiku`.

Every agent runs through the `general-purpose` subagent type; the Agent tool exposes no per-agent effort or timeout
controls, so per-agent model choice and scope decomposition are the only levers for balancing a wave.

Require `$code-polish` for nonlocal invariants, concurrency or state machines, migrations or parsing, auth or security,
retry or error semantics, and public API or data-contract changes. File count alone is not a trigger.

Do not spawn implementation subagents until the user approves the plan and Claude leaves Plan mode. The read-only
research phase above is the only pre-approval exception.

## Execution Phase

### Launch

Before launching subagents, do not hold a path-scoped session claim over any path in a subagent's write scope. Record
orchestrator intent with a pathless label only; the subagents' work is covered by the orchestrating session's presence.

Launch each agent with the Agent tool: `subagent_type: "general-purpose"`, `model: "<agent-model>"` taken verbatim from
that agent's approved manifest row, and a description like `A1/3: <scope> (<model>)`. Start every agent in a parallel
wave in the same message as parallel tool calls; start sequential agents only after reconciling their dependencies.
Claude Code renders subagent progress natively — do not build bespoke progress dashboards, polling loops, or status
tables around the calls. After launch, post one compact
`🚀 Handoff started — <agent count> agents · <strategy> · <wave count> waves · <n> opus / <n> sonnet / <n> haiku` line;
then rely on native progress.

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
5. A delegation-context statement naming the orchestrating session by label and/or session-ID prefix. State that its
   claim or presence authorizes the assigned scope rather than conflicts with it; sibling subagents in the same handoff
   have disjoint scopes and are also not conflicts; and only an unrelated session's claim on the subagent's exact
   assigned files justifies reporting `blocked`.
6. This stopping rule: implement the approved plan exactly; if it is infeasible or requires redesign, report blocked
   with evidence instead of proposing a replacement plan.
7. A requirement to end its final message with exactly these named fields: `status` (`completed` or `blocked`),
   `summary`, `changed files` listing only files it actually touched, `verification` listing every command with its
   outcome, `residual risks`, and `blockers`.

### Collect

When an agent returns, read the required result fields and treat `changed files` as its authoritative post-pass scope.
Confirm the reported files exist or were intentionally deleted, stay within the agent's scope, and carry verification
evidence matching its assignment. After every wave, reconcile all results with the plan manifest and the visible working
tree without folding in unrelated concurrent changes. When Claude is the validation owner, run the assigned aggregate
checks once during this reconciliation. Attribute aggregate-check failures before treating them as blockers: a failure
confined to files outside every agent's scope is unrelated concurrent work — confirm the handoff's own files still pass
and continue. Unexpected out-of-scope edits, overlap between agents in the same parallel wave, or an aggregate-check
failure attributable to the handoff's changes are blockers; do not start their dependents or polish, and do not silently
take over implementation.

## Completion

- On `status: blocked`, treat the result as a plan problem. Let already-started independent agents finish, gate its
  dependents, report the evidence, and let the user decide; never silently take over implementation or relaunch the
  agent on a larger model. Pass relevant completed results to dependent agents.
- Treat an Agent tool call error or a final message without all required result fields as an infrastructure failure.
  Inspect the agent's write scope for partial edits with `git status` and `git diff`, then continue that same named
  agent once through SendMessage with a short verify-and-continue message naming the partially edited files. Its prior
  context is preserved. This is a retry of the same agent, not a new agent against the five-agent limit. A second
  infrastructure failure for that agent is a blocker. Never relaunch it on a larger model.
- After every required agent completes, deduplicate the union of reported changed files and confirm the combined
  verification evidence proves the approved plan.
- When the plan marked polish as required, invoke `$code-polish` once with exactly that union and its default
  simplify-then-review mode. Skip polish if any required agent failed; do not recompute or broaden scope.
- If the approved work changes one or more Git repositories on this machine other than the repository where the handoff
  began, automatically invoke `$commit` from each additional repository after its work, validation, and any required
  polish are complete. Scope each invocation to the files changed there, do not ask for separate confirmation, and do
  not commit incomplete, blocked, unexpected, or out-of-scope changes. Push only when the user explicitly requested it.
- Finish with `### 🏁 Claude handoff — <completed or blocked>`, the strategy and agent count, and a compact per-agent
  result table carrying each agent's model. Follow with `### 📦 Changed` as a file tree, `### 🧪 Verification`,
  `### 🧹 Polish` when run, automatic cross-repository commit hashes when any, and an always-present
  `### ⚠️ Risks / blockers`; write `none` when empty. Use `⛔ blocked` as the result for failed required work. Keep
  paths, commands, hashes, and subagent-return fields exact and undecorated.
