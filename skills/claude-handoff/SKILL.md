---
argument-hint: "[task]"
compatibility: Requires Claude Code Agent-tool subagents with access to the selected model.
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

This skill orchestrates read-only investigation or implementation within the current session after explicit plan
approval. Task-handoff writes a decision-complete file for a fresh, separate session. Use task-handoff for work
continuing later or elsewhere. Use an in-session handoff to implement an approved plan now.

If a slash or dollar invocation already supplied these instructions, follow them directly. In that case, do not invoke
this skill again through a skill tool.

Follow the Contract, then use Claude Code's in-session Agent workflow to research during planning and implement the
approved plan.

## Contract

- Run only after explicit user invocation. Classify a task research-only when its requested outcome is findings,
  evidence, or an assessment, with no repository changes or implementation plan requested. All handoffs may run in any
  host mode. Implementation handoffs must pass through the Plan Phase and receive explicit user approval before launch.
- Reuse an already approved plan when the outcome and material constraints are unchanged. Explicit user instructions
  take precedence over skill defaults. Ask again only for an unresolved decision or action outside that authorization.
- Claude owns decisions, the final plan, and orchestration. Delegate investigation to read-only research subagents only
  when task and repository evidence make it useful before planning.
- Research agents gather evidence and report findings. They never edit files, decide design, or return plans.
- Implementation agents inspect, edit, and validate their assigned part of the approved plan. They never redesign or
  return another plan.
- Use the smallest effective team. One agent is valid. Add agents only when decomposition materially improves latency,
  correctness, or verification. Never exceed eight implementation agents per handoff.
- Before finalizing the team, estimate each brief's wall-clock time. Split anything likely to exceed roughly 25-30
  minutes into parallel disjoint scopes or dependency waves. Add an integration agent as needed.
- Use at most three research agents, stable IDs `R1`-`R3`, counted separately from the eight implementation agents.
- Keep Claude's own work to orchestration, integrity checks, failure handling, and conditional polish passes.
- Let Claude Code choose foreground or background delivery. Only a direct terminal result or error, or a later
  completion or failure notification, settles an agent. A launch acknowledgement, native task row, quiet period, or
  surfaced permission prompt does not settle an agent. Reconcile a wave only after every required terminal outcome
  arrives.
- Treat an explicit user model preference (e.g. Sonnet, Opus) as an orchestration constraint on every research and
  implementation agent unless scoped narrower. Within that scope, never substitute the usual Sonnet/Opus selection. If
  the Agent tool cannot launch that model, report the incompatibility and ask before falling back.
- Treat the approved outcome as the authorization boundary, rather than the initial manifest or its write scopes. When
  implementation reveals a related in-repository fix or evidence change the outcome requires, Claude may extend the
  handoff. Claude may launch follow-on agents for that required work without asking again. The discovering subagent
  still stops at its assigned scope and returns evidence. Claude owns scope expansion, coordination, and delegation.
- Size verification to the requested outcome. Never add validation machinery (gates, manifests, checkpoints, hash pins,
  journals, receipts) unless the approved plan explicitly calls for it. An explicit user request to hurry or wrap up
  overrides optional repeat checks and required polish passes. In that case, commit the validated work and report what
  was skipped or left unverified.

When present, use `$ARGUMENTS` as the task. Otherwise, use the active user request. A task naming another skill follows
Companion Skills.

## Companion Skills

A task that names another skill alongside this handoff — for example,
`run $fresh-eyes-sweep and delegate the implementation` — is a composition. The companion skill defines the work. This
handoff owns delegation mechanics.

- Load the companion skill and run its discovery, judgment, and planning phases in Claude. Route read-only discovery
  through this skill's research agents when materially faster. Then incorporate the companion's method, findings, and
  constraints into the handoff plan. A companion missing from the skill list may be installed but hidden by
  `disable-model-invocation: true`. Read `~/.claude/skills/<name>/SKILL.md` directly before concluding it is absent.
- When the companion's discovery is itself the bulk of the work — an audit or sweep over a whole repository or large
  file set — Claude maps and divides the scope instead of reading it inline. After plan approval, each implementation
  agent audits and fixes its own slice under the companion's rules, inlined in its brief.
- This contract overrides the companion's overlapping plan approval, agent limits and stable IDs, single validation
  owner, and result fields. It also overrides failure classification, commit ownership, and completion reporting. These
  overrides apply even when the companion prescribes its own subagent, validation, or commit mechanics. Its
  user-decision gates still bind. This skill's plan approval satisfies coincident gates. A plan-only companion
  implements only when the combined invocation requested implementation and the user approved the plan.
- Agents cannot load skills. Never brief one to "use skill X" by name. Inline the specific companion instructions,
  conventions, or excerpts it needs.
- A companion requirement to run `$code-polish` or `$agents-brain maintain` marks that pass required in the Plan Phase.
  The pass still runs once, per Completion. Companion commit instructions never add commits.
- Satisfy both contracts at Completion: produce the companion's required report artifacts (ledgers, tables, verdicts)
  alongside the completion report.

## Research Phase

For a research-only task, launch one to three research agents and stop after returning the consolidated investigation.
For that task, never enter the Plan Phase or launch implementation agents. For an implementation handoff, trigger
research when scope is uncertain, the task crosses multiple or unfamiliar subsystems, or serial evidence-gathering would
be materially slower. Zero research agents is the default for implementation handoffs. Claude alone decides the count
from task and repository evidence. Never ask the user to opt in or name agents.

When research is triggered, assign up to three agents stable IDs `R1`-`R3`. Launch them immediately via the Agent tool
with `subagent_type: "Explore"` and an explicit model, unless the user stated a model preference. Absent that
preference, use `sonnet` for bounded surveys and `opus` for involved sweeps across unfamiliar or multiple subsystems.
Omitting `model` inherits the session's model. The read-only Explore toolset makes this launch legitimate in any mode.

Launch all selected agents in parallel in one message. Post `🔎 Research started — <n> agents`. Then rely on native
subagent progress rendering. Do not build dashboards.

Give each agent a self-contained prompt with the open questions, exact investigation scope, every task-relevant
repository constraint, and read-only boundary. Include a thoroughness hint (`medium` for bounded surveys,
`very thorough` for multi-subsystem sweeps). Explore does not load project `CLAUDE.md`. Never assume those constraints
arrive implicitly. Require findings, evidence, open questions, and blockers. Prohibit returning a plan or design.

When the wave settles, read every result and incorporate findings and evidence into the implementation plan or the
research-only response. Surface open questions or blockers via `AskUserQuestion` only when they change scope or
approach. Research agents change nothing. Do not reconcile the working tree. Flag any result reporting edits as a
contract violation.

Explore agents are one-shot and return no reusable agent ID. Never apply the implementation continuation rule to them.
Treat missing required evidence as an open question or blocker in the consolidated result.

For a research-only task, synthesize the evidence and finish with `### 🔎 Research handoff — <completed|blocked>`, the
agent count, findings, evidence, open questions, and blockers — replacing the Plan Phase and completion report. If the
investigation shows changes are needed, report them as findings and stop. In that case, do not produce a plan or begin
edits.

## Plan Phase

Enter this phase only for an implementation handoff.

When research — delegated or Claude's own — contradicts a fact the user stated explicitly (quantities, which items,
which accounts), ask via `AskUserQuestion` before writing the plan. In that case, never widen the plan's default scope
to fit the research.

Produce a decision-complete plan with this section:

```markdown
## Claude Handoff

- Research: `<none | R1..Rn — key findings used>`
- Companion skills: `<none | $x — phases Claude runs / what is folded into briefs>`
- Strategy: `<sequential|parallel|hybrid>`
- Agents: `<1-8>` — `<why this is the smallest effective count>`
- Validation owner: `<agent-id|claude>` — `<aggregate checks it runs once>`

| Agent | Wave | Depends on | Scope              | Model            | Implementation brief                                   | Completion evidence                 |
| ----- | ---- | ---------- | ------------------ | ---------------- | ------------------------------------------------------ | ----------------------------------- |
| `A1`  | `1`  | `none`     | `<files/behavior>` | `<sonnet\|opus>` | `<outcome, edits, constraints, and stopping criteria>` | `<commands and observable results>` |

- Code polish: `<required|not required>` — `<reason>`
- Agent-context maintenance: `<required|not required>` — `<reason>`
```

While finalizing the plan, record the union of every manifest write scope with
`ai-coord draft --name <plan-slug> '<label>' '<path>'...`, using `--recursive` only for directory scopes. Derive
`<plan-slug>` from the plan's short identity (for example `debarrel-lib`): lowercase it, replace characters outside
`[A-Za-z0-9._-]` with `-`, and truncate to 40 characters. For two or more Git roots, use
`ai-coord bundle draft --name <plan-slug> '<label>' '<absolute-path>'...`. In the plan's "Wait out conflicting agents"
section, write the exact promote command `ai-coord start --draft <plan-slug>` (or
`ai-coord bundle start --draft <plan-slug>`) and retain the explicit `ai-coord start '<label>' '<path>'...` fallback (or
`ai-coord bundle start '<label>' '<absolute-path>'...`) over the same union.

A fresh implementation session must receive these commands in the plan itself, without reconstructing scopes from prose.
Use the fallback only when promotion reports `no draft named ...`. Named drafts grant no authority and expire after
seven days.

Choose the execution shape from repository evidence and the approved work:

- Sequential: one agent depends on another, write scopes overlap, or a later agent owns integration/aggregate
  validation.
- Parallel: independent work only, with explicitly disjoint write scopes. Agents may inspect shared context but must not
  write outside their scope.
- Hybrid: dependency-ordered waves — run independent agents within a wave in parallel, reconcile the wave, then start
  its dependents.

A wave finishes with its slowest agent. Move deferrable validation to the validation owner. If parallel work does not
collectively prove the plan, reserve a later sequential agent for integration and aggregate validation.

Assign aggregate validation to exactly one owner per handoff. Package-wide or repo-wide checks (full test suites,
whole-package typecheck/lint, catalog-wide checks) run once. The integration agent runs them when one exists. Otherwise,
Claude runs them during post-wave reconciliation. For every other agent, require the narrowest checks proving its own
edits as completion evidence. These are file-scoped lint/format/typecheck plus targeted tests for the files it touched.

Absent a stated model preference, select each implementation agent's model from its work:

| Work                                                                                                          | Model    |
| ------------------------------------------------------------------------------------------------------------- | -------- |
| Bounded, routine, or everyday implementation                                                                  | `sonnet` |
| Semantic, cross-cutting, or hardest implementation: interacting invariants or difficult algorithmic reasoning | `opus`   |

The `sonnet` and `opus` aliases resolve to Sonnet 5.5 and Opus 5.5 on the Anthropic API. The Agent tool exposes no
per-call effort control. Subagents inherit the session's effort. Every agent runs through the `general-purpose` subagent
type. Model choice and scope decomposition balance a wave.

Require `$code-polish` for nonlocal invariants, concurrency or state machines, migrations or parsing, auth or security,
retry or error semantics, and public API or data-contract changes. File count alone is not a trigger.

Require `$agents-brain maintain` when approved work changes a target its maintenance workflow supports: README.md,
AGENTS.md or CLAUDE.md, a durable context doc, an existing project-installed skill under `.agents/skills`, or an
existing git-tracked source-catalog skill under `skills/` where factual context corrections are prose-only. Installed
copies under managed agent-config roots remain excluded. When both trigger rules apply, mark both passes required. When
neither applies, mark neither required.

Do not spawn implementation subagents until the user approves the plan. The read-only research phase is the only
pre-approval exception.

## Execution Phase

### Launch

Before launching implementation subagents, promote the plan's named draft using its recorded command to acquire a
parent-owned claim covering the union of every manifest write scope. Use the recorded explicit start fallback only when
promotion reports `no draft named ...`. Name exact files individually and use `--recursive` for directory scopes.
Require `READY` before launch.

When promotion or start queues or blocks, never end the turn to pause. In that case, run `ai-coord wait` with Bash
`run_in_background: true` so its return wakes the session. It also returns on non-readiness wake events (message,
unknown coverage, work release, 300-second default timeout). On each wake, handle `MESSAGE` events through
`ai-coord inbox`. Re-submit the recorded promote or start command and diagnose stale blockers on each wake.

Native subagents inherit the parent session identity, so that claim authorizes their assigned writes. The parent owns
all coordination lifecycle commands and holds coverage through reconciliation, required polish, and commits. Subagents
never run lifecycle commands. The delegate guard cannot enforce this rule. A Claude subagent inherits the parent's
session identity and is indistinguishable from it. Thus, its lifecycle command would act on the parent's claim.

Every brief must forbid lifecycle commands. Subagents must never run them.

Launch each agent via the Agent tool: `subagent_type: "general-purpose"`, the model from its manifest row, and a
description like `A1 — <scope>`. Start every parallel-wave agent in the same message as parallel tool calls. Start
sequential agents only after reconciling their dependencies. Claude Code renders subagent progress natively. Do not
create bespoke dashboards, polling loops, or status tables.

After launch, post one compact `🚀 Handoff started — <agent count> agents · <strategy> · <wave count> waves` line. Then
rely on native progress. Record the agent ID returned with each completed implementation result for any allowed
continuation.

Subagents receive none of the planning conversation. Build a self-contained, outcome-first prompt for each agent
containing:

1. The approved overall outcome plus that agent's implementation brief, dependencies, and completion evidence.
2. Its exact write scope, relevant repository constraints, known dirty-work boundaries (other agents/sessions may share
   the tree), and any prerequisite agent results.
3. Its validation assignment per the Plan Phase's validation-owner rule: the scoped checks it must run. For every agent
   but the owner, state that it must not run the aggregate checks the owner runs once after the wave. Never brief new
   validation machinery the approved plan does not call for.
4. A pacing estimate matching its manifest sizing and any user- or adapter-imposed hard runtime limit. A soft estimate
   alone is not a stop condition. When blocked, report partial evidence and the concrete blocker or exhausted hard
   limit.
5. This authority boundary: inspect, edit within scope, and validate locally. Never commit, push, deploy, make external
   writes, or broaden scope, even when repository or host instructions favor committing promptly — committing stays with
   the orchestrator after reconciliation.
6. A delegation-context statement naming the orchestrating session by label/session-ID prefix: its claim or presence
   authorizes the assigned scope rather than conflicts with it. Sibling subagents' disjoint scopes are also not
   conflicts. Only an unrelated session's claim on the agent's exact assigned files justifies reporting `blocked`.
7. This stopping rule: implement the approved plan exactly. If infeasible or requiring redesign, report blocked with
   evidence instead of a replacement plan. End only with the final result or a genuine blocker. Never end with a
   progress summary that announces the next step, an offer to continue, a milestone report, or decisions that block
   nothing.
8. A requirement to end its final message with exactly these fields: `status` (`completed`/`blocked`), `summary`,
   `changed files` (only files actually touched), `verification` (every command with its outcome), `residual risks`, and
   `blockers`.

Keep each prompt as compact as completeness allows. Include the shared outcome summary plus that agent's own brief,
scope, and constraints. Never restate the full plan text per agent.

### Collect

When an agent returns, read the required result fields and treat `changed files` as its authoritative post-pass scope.
Confirm the reported files exist or were intentionally deleted. Confirm they stay within scope. Confirm their
verification evidence matches the assignment per the Plan Phase's validation-owner rule. After every wave, reconcile all
results with the manifest and working tree without including unrelated concurrent changes. Do not add agents or change
models, scopes, or validation ownership merely because a worker is slow or quiet.

Handle discovered follow-on work per Completion below. When Claude is the validation owner, run the assigned aggregate
checks once during this reconciliation. Attribute aggregate-check failures before treating them as blockers. First rule
out effects of the handoff's changes, formatters, hooks, and generators, including failures in downstream files outside
its write scopes. Continue past a failure only when evidence establishes that it is unrelated and the handoff's own
checks still pass.

Unexpected out-of-scope edits, overlap between agents in the same parallel wave, or an aggregate-check failure
attributable to the handoff's changes are blockers. For these blockers, do not start their dependents or polish. Do not
silently take over implementation.

## Skill Evolution Review

Keep verified repairs to skills used during the handoff separate from the optional review below. When user or repository
instructions already authorize repairs, the parent owns their completion. Subagents report evidence without expanding
their write scopes. One verified occurrence is enough, and a blocked main task does not prevent independent repairs.
Complete the handoff's required work or establish its blocker, then finish independent repairs before the final report
under the applicable maintenance policy. Plan Mode still prohibits edits.

After every required agent completes successfully and the task is verified, Claude alone judges whether the task exposes
a stable, reusable workflow credibly likely to recur. Agents never recommend skill-evolution changes in this review.
Never conduct this review for a blocked, failed, or partial handoff. Reject one-offs, rare contingencies, incidental
cleanup, and speculative value. Size or difficulty alone does not establish recurrence.

For a new skill, state repo-local vs. global `~/projects/agent-skills` placement. For a revision, name every exact skill
needing change. When a proposal clears this bar, append at most one compact suggestion (≤2 short sentences) to the
existing completion report. For that proposal, keep the report's format unchanged and offer `$task-handoff` as the next
action. Never auto-invoke `$task-handoff` or create/revise a skill during this review. When nothing qualifies, stay
silent — no placeholder, no "nothing found" note.

## Completion

- When `status: blocked` or completed work identifies a related in-repository fix or evidence change the approved
  outcome needs, treat it as follow-on work under the Contract's authorization-boundary rule, not fresh authorization.
  For that work, let already-started independent agents finish and gate dependents. Extend the manifest with the
  smallest sufficient scope. Satisfy repository coordination for that scope. Then launch a new or reused agent. Repeat
  until the outcome is complete or a genuine authorization boundary is reached.

  Preserve stable IDs, dependency order, the eight-agent limit, and one aggregate-validation owner. Include follow-on
  agents in final counts and report.

- Before the completion report, fix remaining same-pattern sites the approved outcome covers this way. Never list those
  sites as optional or out-of-scope items.
- Ask the user only when continuation would change the approved outcome, require material redesign or unrelated work, or
  cross an existing confirmation boundary (destructive action, purchase, deployment, external write). Never silently
  take over implementation or relaunch solely on a different model. Pass relevant completed results to dependent agents.
- Treat an Agent tool call error or a final message missing required fields as an infrastructure failure. This includes
  a progress report that stops with work still open. For that failure, inspect the agent's write scope for partial edits
  with `git status`/`git diff`. Then continue that same agent once via `SendMessage` addressed to its returned agent ID.
  Send a short verify-and-continue message naming the partially edited files, with prior context preserved. This is a
  retry, not a new agent against the eight-agent limit.

  If no ID was returned, or the continuation fails, that agent is blocked. Never relaunch it except under the following
  stall exception. The exception applies after a harness stall (e.g. `Agent stalled: no progress for 600s`) whose write
  scope `git status`/`git diff` shows untouched. In that case, relaunch it exactly once, fresh, with the same brief,
  outside the eight-agent limit.

- After every required agent completes, deduplicate the union of reported changed files and confirm the combined
  verification evidence proves the approved plan.
- If any required agent failed, or the user explicitly asked to hurry or wrap up, skip every planned polish pass and
  report the skip. Otherwise invoke each required pass once with only its applicable paths from that union:
  `$code-polish` first (default simplify-then-review mode), then `$agents-brain maintain` with its eligible context
  targets. If just one applies, invoke only that required pass. Do not seed either pass with paths outside the union or
  let it broaden beyond its declared workflow authority.
- Reconcile in-scope files actually changed by each polish pass into the final changed-files set and verification. A
  required pass that blocks, fails, or writes outside its supported scope blocks later polish and cross-repository
  commits.
- If approved work changes Git repositories other than the one where the handoff began, automatically invoke `$commit`
  from each additional repository once its work, validation, and required polish are complete, scoped to files changed
  there. For those commits, skip separate confirmation. Never commit incomplete, blocked, unexpected, or out-of-scope
  changes. Push when the request or standing user instructions authorize it.
- When the handoff pushed commits and the repository defines CI workflows, such as `.github/workflows`, watch the pushed
  head's runs before the completion report (`gh run list --commit <sha>`, then `gh run watch <run-id>`, in the
  background when the host supports it). Fix failures attributable to the handoff as follow-on work and report the CI
  outcome. When changed code behaves differently by platform and local checks covered only one, name the unverified
  platforms as a risk.
- Finish with `### 🏁 Claude handoff — <completed or blocked>`, the strategy and agent count, and a compact per-agent
  result table. Follow with `### 📦 Changed` as a file tree, `### 🧪 Verification`, `### 🧹 Polish` when run, automatic
  cross-repository commit hashes when any, and `### Issues and caveats` when present. List each polish pass and outcome,
  `none` for other applicable empty values. Use `⛔ blocked` for failed required work. Keep paths, commands, hashes, and
  subagent-return fields exact and undecorated.
- Group issues and caveats as `Resolved` (verified fixes with evidence) and `Open` (remaining problems, limitations, or
  unverified assumptions, with impact and next step). Omit empty groups and the whole section when empty. Report each
  item once. Put neutral context and agreed decisions under changes or scope. Reserve `blocker` for something preventing
  required work and `risk` for a specific potential adverse outcome. A workaround leaves an item open when the
  underlying issue still affects the result.
