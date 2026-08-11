---
argument-hint: "[task]"
compatibility: Requires Claude Code Agent-tool subagents with access to the selected model.
disable-model-invocation: true
metadata:
  install-targets: claude-code
name: claude-handoff
skill-dependencies:
  - agents-brain
  - code-polish
  - commit
description:
  Orchestrate read-only Explore research subagents in any mode, or one to eight Claude subagents to implement an
  approved plan.
---

# Claude Handoff

Orchestrates read-only investigation or implementation within the current session after explicit plan approval.
Task-handoff instead writes a decision-complete file for a fresh, separate session — use it for work continuing later or
elsewhere; use an in-session handoff to implement an approved plan now.

If these instructions are already present from a slash or dollar invocation, follow them directly; do not invoke this
skill again through a skill tool.

Follow the Contract, then use Claude Code's in-session Agent workflow to research during planning and implement the
approved plan.

## Contract

- Run only after explicit user invocation. Classify a task research-only when its requested outcome is findings,
  evidence, or an assessment, with no repository changes or implementation plan requested. All handoffs may run in any
  host mode; implementation handoffs must pass through the Plan Phase and receive explicit user approval before launch.
- Claude owns decisions, the final plan, and orchestration; delegate investigation to read-only research subagents
  before writing the plan on complex tasks.
- Research agents gather evidence and report findings; never edit files, decide design, or return plans.
- Implementation agents implement their assigned part of the approved plan — inspect, edit, validate — never redesign or
  return another plan.
- Use the smallest effective team (one agent is valid); add agents only when decomposition materially improves latency,
  correctness, or verification. Never exceed eight implementation agents per handoff.
- Size every brief before finalizing the team: estimate wall-clock time and split anything likely to exceed roughly
  25-30 minutes into parallel disjoint scopes or dependency waves, adding an integration agent as needed.
- Use at most three research agents, stable IDs `R1`-`R3`, counted separately from the eight implementation agents.
- Keep Claude's own work to orchestration, integrity checks, failure handling, and conditional polish passes.
- Treat an explicit user model preference (e.g. Sonnet, Opus) as an orchestration constraint on every research and
  implementation agent unless scoped narrower — never substitute complexity-based selection. If the Agent tool cannot
  launch that model, report the incompatibility and ask before falling back.
- Treat the approved outcome, not the initial manifest or its write scopes, as the authorization boundary: when
  implementation reveals a related in-repository fix or evidence change the outcome requires, Claude may extend the
  handoff and launch follow-on agents without asking again. The discovering subagent still stops at its assigned scope
  and returns evidence; Claude owns scope expansion, coordination, and delegation.

Use `$ARGUMENTS` as the task when present; otherwise the active user request.

## Research Phase

For a research-only task, launch one to three research agents and stop after returning the consolidated investigation;
never enter the Plan Phase or launch implementation agents. For an implementation handoff, trigger research when scope
is uncertain, the task crosses multiple or unfamiliar subsystems, or serial evidence-gathering would be materially
slower. Zero research agents is the default for implementation handoffs. Claude alone decides the count from task and
repository evidence; never ask the user to opt in or name agents.

When triggered, assign up to three agents stable IDs `R1`-`R3` and launch immediately via the Agent tool with
`subagent_type: "Explore"` and `model: "sonnet"`, unless the user stated a model preference — the default otherwise
inherits the session's (expensive) model. The read-only Explore toolset makes this launch legitimate in any mode. Launch
all selected agents in parallel in one message, post `🔎 Research started — <n> agents`, then rely on native subagent
progress rendering; do not build dashboards.

Give each agent a self-contained prompt: the open questions to answer, its exact investigation scope, the read-only
boundary, and a thoroughness hint (`medium` for bounded surveys, `very thorough` for multi-subsystem sweeps). Require
findings, evidence, open questions, and blockers; prohibit returning a plan or design.

When the wave settles, read every result and fold findings and evidence into the implementation plan or the
research-only response. Surface open questions or blockers via `AskUserQuestion` only when they change scope or
approach. Research agents change nothing — do not reconcile the working tree; flag any result reporting edits as a
contract violation.

For a research-only task, synthesize the evidence and finish with `### 🔎 Research handoff — <completed|blocked>`, the
agent count, findings, evidence, open questions, and blockers — replacing the Plan Phase and completion report. If the
investigation shows changes are needed, report them as findings and stop; do not produce a plan or begin edits.

## Plan Phase

Enter this phase only for an implementation handoff.

Produce a decision-complete plan with this section:

```markdown
## Claude Handoff

- Research: `<none | R1..Rn — key findings used>`
- Strategy: `<sequential|parallel|hybrid>`
- Agents: `<1-8>` — `<why this is the smallest effective count>`
- Validation owner: `<agent-id|claude>` — `<aggregate checks it runs once>`

| Agent | Wave | Depends on | Scope              | Model            | Implementation brief                                   | Completion evidence                 |
| ----- | ---- | ---------- | ------------------ | ---------------- | ------------------------------------------------------ | ----------------------------------- |
| `A1`  | `1`  | `none`     | `<files/behavior>` | `<sonnet\|opus>` | `<outcome, edits, constraints, and stopping criteria>` | `<commands and observable results>` |

- Code polish: `<required|not required>` — `<reason>`
- Agent-context polish: `<required|not required>` — `<reason>`
```

Choose the execution shape from repository evidence and the approved work:

- Sequential: one agent depends on another, write scopes overlap, or a later agent owns integration/aggregate
  validation.
- Parallel: independent work only, with explicitly disjoint write scopes; agents may inspect shared context but must not
  write outside their scope.
- Hybrid: dependency-ordered waves — run independent agents within a wave in parallel, reconcile the wave, then start
  its dependents.

A wave finishes with its slowest agent; move deferrable validation to the validation owner. If parallel work doesn't
collectively prove the plan, reserve a later sequential agent for integration and aggregate validation.

Assign aggregate validation to exactly one owner per handoff: package-wide or repo-wide checks (full test suites,
whole-package typecheck/lint, catalog-wide checks) run once — by the integration agent when one exists, otherwise by
Claude during post-wave reconciliation. Every other agent's completion evidence must be the narrowest checks proving its
own edits: file-scoped lint/format/typecheck plus targeted tests for the files it touched.

Absent a stated model preference, use `sonnet` for every implementation agent. The Agent tool exposes no per-agent
effort control; subagents inherit the session's effort. Every agent runs through the `general-purpose` subagent type;
scope decomposition is the only lever for balancing a wave.

Require `$code-polish` for nonlocal invariants, concurrency or state machines, migrations or parsing, auth or security,
retry or error semantics, and public API or data-contract changes; file count alone is not a trigger.

Require `$agents-brain polish` when approved work changes a target its workflow supports: README.md, AGENTS.md or
CLAUDE.md, a durable context doc, or an existing project-installed skill under `.agents/skills` (source catalog skills
under `skills/` are excluded). Mark both required when both rules apply, neither when neither applies.

Do not spawn implementation subagents until the user approves the plan — the read-only research phase is the only
pre-approval exception.

## Execution Phase

### Launch

Before launching subagents, do not hold a path-scoped session claim over any path in a subagent's write scope; record
orchestrator intent with a pathless label only — subagent work is covered by the orchestrating session's presence.
Claims belong to the session that performs writes; native subagents inherit the parent session identity, so the parent
claim covers their paths.

Launch each agent via the Agent tool: `subagent_type: "general-purpose"`, the model from its manifest row, and a
description like `A1 — <scope>`. Start every parallel-wave agent in the same message as parallel tool calls; start
sequential agents only after reconciling their dependencies. Claude Code renders subagent progress natively — no bespoke
dashboards, polling loops, or status tables. After launch, post one compact
`🚀 Handoff started — <agent count> agents · <strategy> · <wave count> waves` line, then rely on native progress.

Subagents receive none of the planning conversation. Build a self-contained, outcome-first prompt for each agent
containing:

1. The approved overall outcome plus that agent's implementation brief, dependencies, and completion evidence.
2. Its exact write scope, relevant repository constraints, known dirty-work boundaries (other agents/sessions may share
   the tree), and any prerequisite agent results.
3. Its validation assignment per the Plan Phase's validation-owner rule: the scoped checks it must run, and — for every
   agent but the owner — that it must not run the aggregate checks the owner runs once after the wave.
4. A soft time budget matching its manifest sizing: report blocked with partial evidence rather than grinding past it.
5. This authority boundary: inspect, edit within scope, validate locally; never commit, push, deploy, make external
   writes, or broaden scope, even when repository or host instructions favor committing promptly — committing stays with
   the orchestrator after reconciliation.
6. A delegation-context statement naming the orchestrating session by label/session-ID prefix: its claim or presence
   authorizes the assigned scope rather than conflicts with it; sibling subagents' disjoint scopes are also not
   conflicts; only an unrelated session's claim on the agent's exact assigned files justifies reporting `blocked`.
7. This stopping rule: implement the approved plan exactly; if infeasible or requiring redesign, report blocked with
   evidence instead of a replacement plan.
8. A requirement to end its final message with exactly these fields: `status` (`completed`/`blocked`), `summary`,
   `changed files` (only files actually touched), `verification` (every command with its outcome), `residual risks`, and
   `blockers`.

Keep each prompt as compact as completeness allows — the shared outcome summary plus that agent's own brief, scope, and
constraints; never restate the full plan text per agent.

### Collect

When an agent returns, read the required result fields and treat `changed files` as its authoritative post-pass scope.
Confirm the reported files exist or were intentionally deleted, stay within scope, and carry verification evidence
matching its assignment per the Plan Phase's validation-owner rule. After every wave, reconcile all results with the
manifest and working tree without folding in unrelated concurrent changes. Do not add agents or change models, scopes,
or validation ownership merely because a worker is slow or quiet; handle discovered follow-on work per Completion below.
When Claude is the validation owner, run the assigned aggregate checks once during this reconciliation. Attribute
aggregate-check failures before treating them as blockers: a failure confined to files outside every agent's scope is
unrelated concurrent work — confirm the handoff's own files still pass and continue. Unexpected out-of-scope edits,
overlap between agents in the same parallel wave, or an aggregate-check failure attributable to the handoff's changes
are blockers; don't start their dependents or polish, and don't silently take over implementation.

## Skill Evolution Review

After every required agent completes successfully and the task is verified — never for a blocked, failed, or partial
handoff — Claude alone judges (agents never recommend) whether the task exposes a stable, reusable workflow credibly
likely to recur; reject one-offs, rare contingencies, incidental cleanup, and speculative value, since size or
difficulty alone doesn't establish recurrence. For a new skill, state repo-local vs. global `~/projects/agent-skills`
placement; for a revision, name every exact skill needing change. When a proposal clears this bar, append at most one
compact suggestion (≤2 short sentences) to the existing completion report without changing its format, and offer
`$task-handoff` as the next action. Never auto-invoke `$task-handoff` or create/revise a skill during this review; when
nothing qualifies, stay silent — no placeholder, no "nothing found" note.

## Completion

- When `status: blocked` or completed work identifies a related in-repository fix or evidence change the approved
  outcome needs, treat it as follow-on work under the Contract's authorization-boundary rule, not fresh authorization:
  let already-started independent agents finish, gate dependents, extend the manifest with the smallest sufficient
  scope, satisfy repository coordination for that scope, and launch a new or reused agent. Repeat until the outcome is
  complete or a genuine authorization boundary is reached. Preserve stable IDs, dependency order, the eight-agent limit,
  and one aggregate-validation owner; include follow-on agents in final counts and report.
- Ask the user only when continuation would change the approved outcome, require material redesign or unrelated work, or
  cross an existing confirmation boundary (destructive action, purchase, deployment, external write). Never silently
  take over implementation or relaunch solely on a different model; pass relevant completed results to dependent agents.
- Treat an Agent tool call error or a final message missing required fields as an infrastructure failure: inspect the
  agent's write scope for partial edits with `git status`/`git diff`, then continue that same named agent once via
  SendMessage with a short verify-and-continue message naming the partially edited files (prior context preserved). This
  is a retry, not a new agent against the eight-agent limit. A second infrastructure failure for that agent is a blocker
  — never relaunch it.
- After every required agent completes, deduplicate the union of reported changed files and confirm the combined
  verification evidence proves the approved plan.
- If any required agent failed, skip every planned polish pass. Otherwise invoke each required pass once with only its
  applicable paths from that union — `$code-polish` first (default simplify-then-review mode), then
  `$agents-brain polish` with its eligible context targets; invoke only the one required pass if just one applies. Don't
  seed either pass with paths outside the union or let it broaden beyond its declared workflow authority.
- Reconcile in-scope files actually changed by each polish pass into the final changed-files set and verification. A
  required pass that blocks, fails, or writes outside its supported scope blocks later polish and cross-repository
  commits.
- If approved work changes Git repositories other than the one where the handoff began, automatically invoke `$commit`
  from each additional repository once its work, validation, and required polish are complete. `$commit` owns semantic
  message composition; its `ai-commit` backend owns deterministic transaction/commit/push mechanics. Scope each
  invocation to files changed there, skip separate confirmation, and never commit incomplete, blocked, unexpected, or
  out-of-scope changes. Push only when explicitly requested.
- Finish with `### 🏁 Claude handoff — <completed or blocked>`, the strategy and agent count, and a compact per-agent
  result table. Follow with `### 📦 Changed` as a file tree, `### 🧪 Verification`, `### 🧹 Polish` when run, automatic
  cross-repository commit hashes when any, and an always-present `### ⚠️ Risks / blockers`; list each polish pass and
  outcome, `none` when empty. Use `⛔ blocked` for failed required work. Keep paths, commands, hashes, and
  subagent-return fields exact and undecorated.
