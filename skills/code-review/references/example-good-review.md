# Good Code Review Example

This example demonstrates effective code review output following skill guidelines.

______________________________________________________________________

## Context Questions

Before diving into findings, clarify scope:

- Is this a performance-critical path?
- What's the expected load for this endpoint?

______________________________________________________________________

## Findings

### 🚨 CRITICAL

**SQL Injection in User Query** — `src/api/users.ts:45`

```typescript
const query = `SELECT * FROM users WHERE id = ${userId}`;
```

User-controlled `userId` directly interpolated into SQL string enables arbitrary query execution.

**Fix**: Use parameterized queries:

```typescript
const query = 'SELECT * FROM users WHERE id = $1';
const result = await db.query(query, [userId]);
```

______________________________________________________________________

### ⚠️ HIGH

**Missing Error Handling** — `src/api/users.ts:52-58`

```typescript
const user = await db.query(query, [userId]);
return user.rows[0]; // Throws if rows is undefined
```

Query failure or empty result causes unhandled exception.

**Fix**: Add null check and error handling:

```typescript
const result = await db.query(query, [userId]);
if (!result.rows?.[0]) {
  throw new NotFoundError(`User ${userId} not found`);
}
return result.rows[0];
```

______________________________________________________________________

### 💡 MEDIUM

**N+1 Query Pattern** — `src/api/users.ts:67-72`

Loop fetches related records individually instead of batching.

**Fix**: Use `WHERE id IN (...)` with collected IDs.

______________________________________________________________________

**Generic Function Name** — `src/api/users.ts:80`

```typescript
async function process(data: OrderInput) { ... }
```

Function name `process` doesn't describe the action. Requires reading the implementation to understand behavior.

**Fix**: Use a verb phrase describing the action:

```typescript
async function validateAndSubmitOrder(order: OrderInput) { ... }
```

______________________________________________________________________

### ℹ️ LOW

**Naming Clarity** — `src/api/users.ts:30`

Variable `d` could be more descriptive. Consider `userData` or `userRecord`.

______________________________________________________________________

**Boolean Variable Name** — `src/api/users.ts:42`

```typescript
const flag = user.status === 'active';
```

Boolean `flag` doesn't convey what condition it represents.

**Fix**: Use a name that reads as a yes/no question:

```typescript
const isActive = user.status === 'active';
```

______________________________________________________________________

## Positive Observations

- Good use of TypeScript strict mode
- Input validation present at API boundary
- Consistent error response format

______________________________________________________________________

## Deployment Notes

- SQL injection fix requires immediate deployment
- Monitor error rates after error handling changes
- Consider database query logging during rollout
