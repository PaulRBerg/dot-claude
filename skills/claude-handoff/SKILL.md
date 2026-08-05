---
argument-hint: "[task]"
compatibility: Requires Claude Code Plan mode and Agent-tool subagents with Sonnet model access.
disable-model-invocation: true
metadata:
  install-targets: claude-code
name: claude-handoff
user-invocable: true
description:
  Orchestrate read-only Explore research subagents during planning and one to eight Sonnet subagents to implement the
  approved plan.
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
  when decomposition materially improves latency, correctness, or verification. Never exceed eight implementation agents
  across the handoff.
- Size every implementation brief before finalizing the team: estimate its wall-clock agent time, and split any brief
  likely to exceed roughly 25-30 minutes into parallel disjoint scopes or dependency waves, adding an integration agent
  when needed, instead of one monolithic agent. Steering, follow-up, and interrupt churn on an oversized agent costs
  more than decomposition.
- Use at most three research agents with stable IDs `R1` through `R3`. Count them separately from the eight
  implementation agents.
- Keep Claude's implementation work to orchestration, integrity checks, failure handling, and the conditional polish
  pass.
- Treat the approved outcome, not the initial agent manifest or its write scopes, as the authorization boundary. When
  implementation reveals a related in-repository fix or evidence change required to achieve that outcome, Claude is
  fully authorized to extend the handoff and launch follow-on implementation agents for the newly discovered scope
  without asking the user again. The subagent that discovered the need must still stop at its assigned scope and return
  evidence; Claude owns the scope expansion, repository coordination, and delegation.

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

Use the default Explore agent and do not override its model — research gathers evidence, the parent synthesizes.

When the research wave settles, read every result and fold its findings and evidence into the implementation plan.
Surface open questions or blockers through `AskUserQuestion` only when they change scope or approach. Do not reconcile
the working tree: research agents change nothing. Flag any research result reporting edits as a contract violation.

## Plan Phase

Produce a decision-complete plan with this section:

```markdown
## Claude Handoff

- Research: `<none | R1..Rn — key findings used>`
- Strategy: `<sequential|parallel|hybrid>`
- Agents: `<1-8>` — `<why this is the smallest effective count>`
- Validation owner: `<agent-id|claude>` — `<aggregate checks it runs once>`

| Agent | Wave | Depends on | Scope              | Model    | Implementation brief                                   | Completion evidence                 |
| ----- | ---- | ---------- | ------------------ | -------- | ------------------------------------------------------ | ----------------------------------- |
| `A1`  | `1`  | `none`     | `<files/behavior>` | `sonnet` | `<outcome, edits, constraints, and stopping criteria>` | `<commands and observable results>` |

- Code polish: `<required|not required>` — `<reason>`
```

Choose the execution shape from repository evidence and the approved work:

- Use sequential agents when one agent depends on another, their write scopes overlap, or a later agent owns integration
  or aggregate validation.
- Use parallel agents only for independent work with explicitly disjoint write scopes. Agents may inspect shared
  context, but must not write outside their assigned scope.
- Use hybrid execution for dependency-ordered waves: run independent agents within a wave in parallel, reconcile the
  entire wave, then start its dependents.

A wave finishes with its slowest agent; move deferrable validation to the validation owner.

If parallel work does not collectively prove the overall plan, reserve a later sequential agent for integration and
aggregate validation.

Assign aggregate validation to exactly one owner per handoff: package-wide or repo-wide checks (full test suites,
whole-package typecheck or lint, catalog-wide checks) run once — by the integration agent when one exists, otherwise by
Claude during post-wave reconciliation. Every other agent's completion evidence must be the narrowest checks that prove
its own edits: file-scoped lint, format, or typecheck plus targeted tests for the files it touched. Duplicate aggregate
runs across a wave's agents are wasted wall-clock time, not extra assurance.

Every agent runs on `sonnet`; per-agent model escalation is not part of this skill. Do not set a per-agent effort level:
the Agent tool exposes no such control, so subagents inherit the session's effort.

Every agent runs through the `general-purpose` subagent type; scope decomposition is the only lever for balancing a
wave.

Require `$code-polish` for nonlocal invariants, concurrency or state machines, migrations or parsing, auth or security,
retry or error semantics, and public API or data-contract changes. File count alone is not a trigger.

Do not spawn implementation subagents until the user approves the plan and Claude leaves Plan mode. The read-only
research phase above is the only pre-approval exception.

## Execution Phase

### Launch

Before launching subagents, do not hold a path-scoped session claim over any path in a subagent's write scope. Record
orchestrator intent with a pathless label only; the subagents' work is covered by the orchestrating session's presence.

Launch each agent with the Agent tool: `subagent_type: "general-purpose"`, `model: "sonnet"` for every agent, and a
description like `A1 — <scope>`. Start every agent in a parallel wave in the same message as parallel tool calls; start
sequential agents only after reconciling their dependencies. Claude Code renders subagent progress natively — do not
build bespoke progress dashboards, polling loops, or status tables around the calls. After launch, post one compact
`🚀 Handoff started — <agent count> agents · <strategy> · <wave count> waves` line; then rely on native progress.

Subagents receive none of the planning conversation. Build a self-contained, outcome-first prompt for each agent
containing:

1. The approved overall outcome plus that agent's implementation brief, dependencies, and completion evidence.
2. Its exact write scope, relevant repository constraints, known dirty-work boundaries (other agents or sessions may be
   editing the same tree), and any prerequisite agent results.
3. Its validation assignment: the scoped checks it must run, and — for every agent other than the validation owner — the
   aggregate checks it must not run because the validation owner runs them once after the wave.
4. A soft time budget matching its manifest sizing, with the instruction to report blocked with partial evidence rather
   than grinding past it.
5. This authority boundary: inspect, edit within the assigned scope, and validate locally; do not commit, push, deploy,
   make external writes, or broaden scope — even when repository or host instructions favor committing finished work
   promptly. Committing stays with the orchestrator after reconciliation.
6. A delegation-context statement naming the orchestrating session by label and/or session-ID prefix. State that its
   claim or presence authorizes the assigned scope rather than conflicts with it; sibling subagents in the same handoff
   have disjoint scopes and are also not conflicts; and only an unrelated session's claim on the subagent's exact
   assigned files justifies reporting `blocked`.
7. This stopping rule: implement the approved plan exactly; if it is infeasible or requires redesign, report blocked
   with evidence instead of proposing a replacement plan.
8. A requirement to end its final message with exactly these named fields: `status` (`completed` or `blocked`),
   `summary`, `changed files` listing only files it actually touched, `verification` listing every command with its
   outcome, `residual risks`, and `blockers`.

### Collect

When an agent returns, read the required result fields and treat `changed files` as its authoritative post-pass scope.
Confirm the reported files exist or were intentionally deleted, stay within the agent's scope, and carry verification
evidence matching its assignment. After every wave, reconcile all results with the current manifest and the visible
working tree without folding in unrelated concurrent changes. Do not add agents or change models, scopes, or validation
ownership merely because a worker is slow or quiet. Do revise the manifest and launch a narrowly scoped follow-on agent
when completed work discovers an unplanned prerequisite covered by the approved outcome. Preserve stable IDs, dependency
order, the eight-agent handoff limit, and one aggregate-validation owner; include follow-on agents in the final counts
and report. When Claude is the validation owner, run the assigned aggregate checks once during this reconciliation.
Attribute aggregate-check failures before treating them as blockers: a failure confined to files outside every agent's
scope is unrelated concurrent work — confirm the handoff's own files still pass and continue. Unexpected out-of-scope
edits, overlap between agents in the same parallel wave, or an aggregate-check failure attributable to the handoff's
changes are blockers; do not start their dependents or polish, and do not silently take over implementation.

## Skill Evolution Review

After every required implementation agent has completed successfully and the overall complex task is verified, Claude
reviews the user's completed task for skill-evolution opportunities. Do not run or report this review for a blocked,
failed, or partial handoff. Claude makes the judgment itself; research and implementation agents never make the
user-facing recommendation.

Recommend skill work only when the completed task exposes a stable, reusable workflow credibly likely to recur. Task
size or difficulty alone does not establish recurrence; reject one-off work, rare contingencies, incidental cleanup, and
patterns whose future value is speculative.

- For a new skill, state whether it belongs in the repository where the work was done because its reuse is
  project-specific or globally in `~/projects/agent-skills` because it is useful across projects.
- For a revision, name every exact existing skill and briefly state why each needs to change.

When a proposal clears this bar, append at most one compact suggestion of no more than two short sentences to Claude's
existing completion report without otherwise changing its format. State the reusable need and the proposed create or
revise target, then offer `$task-handoff` as the next action for capturing a decision-complete implementation handoff.
Leave design choices, file-level changes, acceptance details, and other low-level material to that future handoff.

Never invoke `$task-handoff`, create a handoff, create a skill, or revise a skill automatically during this review. When
no proposal clears the recurrence bar, remain silent: add no placeholder section and do not report that no skill
opportunity was found.

## Completion

- When `status: blocked` identifies a related in-repository fix or evidence change outside the subagent's scope that is
  necessary for the approved outcome, treat it as follow-on work rather than a request for fresh authorization. Let
  already-started independent agents finish, gate dependents, extend the manifest with the smallest sufficient scope,
  satisfy repository coordination for that scope, and launch a new or reused implementation agent. Repeat this process
  until the approved outcome is complete or a genuine authorization boundary is reached.
- Ask the user only when continuation would change the approved outcome, require a material redesign or unrelated work,
  or cross an existing confirmation boundary such as destructive action, purchase, deployment, or external write. Never
  silently take over implementation or relaunch solely on a different model. Pass relevant completed results to
  dependent agents.
- Treat an Agent tool call error or a final message without all required result fields as an infrastructure failure.
  Inspect the agent's write scope for partial edits with `git status` and `git diff`, then continue that same named
  agent once through SendMessage with a short verify-and-continue message naming the partially edited files. Its prior
  context is preserved. This is a retry of the same agent, not a new agent against the eight-agent limit. A second
  infrastructure failure for that agent is a blocker. Never relaunch it.
- After every required agent completes, deduplicate the union of reported changed files and confirm the combined
  verification evidence proves the approved plan.
- When the plan marked polish as required, invoke `$code-polish` once with exactly that union and its default
  simplify-then-review mode. Skip polish if any required agent failed; do not recompute or broaden scope.
- If the approved work changes one or more Git repositories on this machine other than the repository where the handoff
  began, automatically invoke `$commit` from each additional repository after its work, validation, and any required
  polish are complete. `$commit` owns semantic message composition; its `ai-commit` backend owns deterministic
  transaction, commit, and push mechanics. Scope each invocation to the files changed there, do not ask for separate
  confirmation, and do not commit incomplete, blocked, unexpected, or out-of-scope changes. Push only when the user
  explicitly requested it.
- Finish with `### 🏁 Claude handoff — <completed or blocked>`, the strategy and agent count, and a compact per-agent
  result table. Follow with `### 📦 Changed` as a file tree, `### 🧪 Verification`, `### 🧹 Polish` when run, automatic
  cross-repository commit hashes when any, and an always-present `### ⚠️ Risks / blockers`; write `none` when empty. Use
  `⛔ blocked` as the result for failed required work. Keep paths, commands, hashes, and subagent-return fields exact
  and undecorated.
