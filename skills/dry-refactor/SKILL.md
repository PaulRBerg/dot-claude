---
name: dry-refactor
description: This skill should be used when the user asks to "refactor duplicate code", "apply DRY principles", "eliminate code repetition", "extract common functionality", or mentions code duplication, similar patterns, repeated logic, or reusable abstractions.
---

# DRY Refactoring

## Process

1. **Identify** - Exact copies, similar patterns, parallel hierarchies, naming patterns (`data1`/`data2`, `handleXClick`)
1. **Analyze** - Coupling, cohesion, frequency (Rule of Three: wait for 3+ occurrences), volatility
1. **Refactor** - Choose technique below, extract incrementally, test after each step

## Techniques

**Extract Function** - Same logic in multiple places

```ts
getFullName(user: User) => `${user.firstName} ${user.lastName}`
```

**Extract Variable** - Repeated expression

```ts
const isWorkingAge = user.age >= 18 && user.age < 65;
```

**Parameterize** - Code differs only in values

```ts
validateField(value: string, pattern: RegExp)
// Use: validateField(email, EMAIL_REGEX)
```

**Extract Class** - Related functions scattered

```ts
class UserRewards {
  calculateDiscount(user, amount) { }
  getLoyaltyPoints(user) { }
}
```

**Polymorphism** - Repeated switch/if-else

```ts
interface PaymentProcessor { process(amount: number): void }
class CreditProcessor implements PaymentProcessor { }
```

**Strategy Pattern** - Duplicated algorithm selection

```ts
const strategies = { date: byDate, name: byName };
items.sort(strategies[sortType] ?? byPriority);
```

**Pull Up Method** - Identical methods in subclasses

```ts
class BaseUser { getDisplayName() { } }
class AdminUser extends BaseUser { }
```

## Detection

**Code Smells**: Look for numbered variables (`data1`, `data2`), parallel function names (`handleXClick`), near-identical code differing only in constants, repeated validation/error handling, parallel class structures, large switches in multiple places, repeated null checks, magic numbers

**Rule of Three**: Wait for 3+ occurrences before abstracting

## When NOT to DRY

- **Coincidental similarity** - Avoid abstracting different domains/business rules that happen to look alike (will diverge)
- **Premature abstraction** - Wait until pattern is clear; early abstraction often guesses wrong
- **Single use** - Skip abstraction when code appears 1-2 times and is unlikely to grow
- **Test clarity** - Prefer readable test setup over DRY
- **Over-engineering** - Avoid abstracting every 2-3 line similarity

## Patterns

- **Configuration over code** - Use data structures to eliminate conditionals
- **Template Method** - Define skeleton in base, vary steps in subclasses
- **Dependency Injection** - Parameterize dependencies to reduce coupling
- **Builder** - Construct complex objects incrementally

## Best Practices

- Refactor only after tests pass (green)
- Apply one refactoring at a time
- Commit changes frequently
- Name abstractions for intent, not implementation
- Consider performance impact of abstractions
- Review abstractions with team before finalizing
