# Bad Code Review Anti-Patterns

Avoid these patterns in code reviews.

______________________________________________________________________

## Anti-Pattern 1: Fabricated Line Numbers

❌ **Bad**:

> There's a bug at `src/utils.ts:847` where the array isn't checked.

When you haven't verified the line number exists, this creates confusion and erodes trust.

✅ **Good**:

> In the `processItems` function in `src/utils.ts`, the array isn't null-checked before iteration.

______________________________________________________________________

## Anti-Pattern 2: Vague Findings

❌ **Bad**:

> The code has some issues with error handling.

No specific location, no explanation of impact, no fix suggested.

✅ **Good**:

> **Missing Error Handling** — `src/api/handler.ts`, `fetchUser` function
>
> The async call lacks try-catch, causing unhandled rejections that crash the process.
>
> **Fix**: Wrap in try-catch and return appropriate error response.

______________________________________________________________________

## Anti-Pattern 3: Opinion Without Evidence

❌ **Bad**:

> This function is too long and should be refactored.

No specific issues identified, just general discomfort.

✅ **Good**:

> This function handles three distinct responsibilities (validation, transformation, persistence). Consider extracting `validateInput()` and `persistRecord()` to improve testability and reduce cognitive load.

______________________________________________________________________

## Anti-Pattern 4: Nitpicking Without Severity

❌ **Bad**:

> - Use const instead of let
> - Add semicolon
> - Rename variable x
> - Missing space after comma
> - CRITICAL: SQL injection vulnerability

Mixing lint issues with security vulnerabilities buries critical findings.

✅ **Good**: Group by severity, address critical issues first. Let linters handle style.

______________________________________________________________________

## Anti-Pattern 5: Missing Context Acknowledgment

❌ **Bad**:

> This implementation is wrong because [assumption about requirements].

Making assumptions about intent without asking.

✅ **Good**:

> I'm assuming this endpoint is public-facing. If it's internal-only, the authentication check may not be necessary. Could you clarify the access requirements?

______________________________________________________________________

## Anti-Pattern 6: Vague Naming Feedback

❌ **Bad**:

> Variable names could be better.

No specifics about which names, where they are, or what they should be.

✅ **Good**:

> **Naming Clarity** — `src/api/orders.ts:23`
>
> Variable `x` in `processOrder` doesn't reveal intent. Consider `orderTotal` or `discountedPrice` based on what it represents.
