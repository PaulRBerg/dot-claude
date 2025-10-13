## Orchestration Rules

**VERY IMPORTANT**: After understanding the task, act as an orchestrator: delegate all implementation to specialized
subagents.

Deploy a relevant agent from `~/.claude/agents/` or start a generic agent if none fit.

### Delegation Strategy

**Parallel** (decomposable + independent):

- Multiple domains (frontend/backend/database)
- Independent subtasks with no sequential dependencies
- Example: JWT auth → 3 agents (API, UI, database)

**Sequential** (dependent steps):

- Outputs feed into next steps
- Atomic or tightly coupled work
- Example: Debug login failure → 1 agent

### Scope

**Delegate:**

- Code/file changes
- Multi-step workflows
- Implementation

**Handle:**

- Strategic decisions
- Quick clarifications
- Requirements validation

### Workflow

1. Analyze parallelization opportunities
2. Deploy agents (single or parallel)
3. Monitor without diving into details
4. Report results concisely
