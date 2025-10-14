---
description: Validate CLAUDE.md and AGENTS.md files against actual codebase
---

## Context

- Context files: !`fd '(CLAUDE|AGENTS)\.md' -t f | sort`
- Working directory: !`pwd`

## Your Task

Audit all context/documentation files for accuracy against the actual codebase.

### STEP 1: For each context file

Read the file and extract **verifiable claims**:

- File paths mentioned
- Directory structures described
- Commands referenced (build tools, scripts, package managers)
- Rules about what to edit/not edit
- Workflow descriptions
- Testing patterns
- Dependencies and integrations

### STEP 2: Verify each claim

Check against actual codebase:

**File/Directory claims:**
- Use `ls`, `fd`, or `tree` to verify paths exist
- Check directory structures match descriptions

**Command claims:**
- Verify commands exist in `justfile`, `package.json`, `Makefile`, or scripts
- Check command syntax is correct
- Validate available scripts/tasks match documentation

**Code structure claims:**
- Read actual files to verify patterns described
- Check that relationships mentioned are accurate
- Verify import/export patterns match documentation

**Workflow claims:**
- Verify build/deploy workflows match descriptions
- Check that process flows are accurate
- Validate dependencies and execution order

### STEP 3: Report findings

For EACH discrepancy found, report:

```
❌ {file}: {specific issue}
   Claimed: {what the doc says}
   Actual: {what exists in code}
```

If ALL files are accurate:

```
✓ All context files validated successfully
```

## Validation Checklist

For each file, verify:

- [ ] Referenced file paths exist
- [ ] Referenced directories exist
- [ ] Commands are correct (check all task runners)
- [ ] Described structures match reality
- [ ] Rules (edit X, don't edit Y) are accurate
- [ ] Cross-references between docs are consistent
- [ ] Examples match actual patterns in code
- [ ] Version numbers and dependencies are current

## Notes

- Be thorough but concise
- Focus on factual claims, not stylistic opinions
- Check both presence (file exists) and accuracy (content matches claim)
- Validate commands are runnable and syntax is correct
- Adapt verification approach to project type (web, CLI, library, etc.)
