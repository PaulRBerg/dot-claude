---
name: dry-refactor
description:
  Expert code refactoring to eliminate duplication using DRY principles. Use when code has repetition, similar patterns,
  duplicate logic, or when extracting common functionality into reusable abstractions.
---

# DRY Refactoring

## Process

1. **Identify** - Exact copies, similar patterns, parallel hierarchies, naming patterns (`data1`/`data2`, `handleXClick`)
2. **Analyze** - Coupling, cohesion, frequency (Rule of Three: wait for 3+ occurrences), volatility
3. **Refactor** - Choose technique below, extract incrementally, test after each step

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

**Code Smells**: Numbered variables (`data1`, `data2`), parallel function names (`handleXClick`), near-identical code differing only in constants, repeated validation/error handling, parallel class structures, large switches in multiple places, repeated null checks, magic numbers

**Rule of Three**: Wait for 3+ occurrences before abstracting

## When NOT to DRY

- **Coincidental similarity** - Different domains/business rules that happen to look alike (will diverge)
- **Premature abstraction** - Pattern isn't clear yet; early abstraction often guesses wrong
- **Single use** - Appears 1-2 times, unlikely to grow
- **Test clarity** - Readable test setup beats DRY
- **Over-engineering** - Don't abstract every 2-3 line similarity

## Patterns

- **Configuration over code** - Data structures eliminate conditionals
- **Template Method** - Base defines skeleton, subclasses vary steps
- **Dependency Injection** - Parameterize dependencies
- **Builder** - Complex object construction

## Best Practices

- Refactor after green tests
- One refactoring at a time
- Commit frequently
- Name for intent not implementation
- Consider performance
- Review abstractions with team
