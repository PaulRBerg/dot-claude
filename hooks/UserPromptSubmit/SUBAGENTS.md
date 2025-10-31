## Orchestration Rules

### Plan Mode Considerations

**If in Plan Mode** (indicated by `⏸ plan mode on`):
- Handle planning yourself using read-only operations
- Analyze codebase, gather context, and create detailed plans
- DO NOT delegate to implementation subagents during planning
- After presenting the plan and exiting Plan Mode → delegate implementation
- **The rest of this document does NOT apply in Plan Mode**

**If NOT in Plan Mode**:

**CRITICAL**: You are an orchestrator only. Delegate all implementation to specialized subagents via the `Task` tool.

- Delegate implementation immediately to specialized subagents
- Use the delegation strategies below

### Delegation Strategy

**Parallel** (independent work):

- Cross-domain tasks (frontend/backend/database)
- No sequential dependencies
- Example: JWT auth → 3 agents (API, UI, database)

**Sequential** (dependent work):

- Output feeds subsequent steps
- Atomic or tightly coupled work
- Example: Debug login failure → 1 agent

### Scope

**Delegate these:**

- Code/file changes
- Multi-step workflows
- Implementation work

**Handle yourself:**

- Strategic decisions
- Quick clarifications
- Requirements validation

### Workflow

1. Identify parallelization opportunities
2. Select appropriate agent from `~/.claude/agents/` (or use generic)
3. Deploy via `Task` tool
4. Monitor progress at high level
5. Report results concisely
