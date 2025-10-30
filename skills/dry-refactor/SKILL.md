---
name: dry-refactor
description:
  Expert code refactoring to eliminate duplication using DRY principles. Use when code has repetition, similar patterns,
  duplicate logic, or when extracting common functionality into reusable abstractions.
---

# DRY Refactoring

Apply these principles and techniques when refactoring code to eliminate duplication and improve maintainability through
the Don't Repeat Yourself (DRY) principle.

## General Principles

- Be terse
- Anticipate needs—suggest solutions the user hasn't considered
- Treat the user as an expert
- Be precise and exhaustive
- Lead with the answer; add explanations only as needed
- Embrace new tools and contrarian ideas, not just best practices
- Refactor incrementally with tests

## DRY Refactoring Process

Follow this systematic approach to safely eliminate duplication:

### 1. Identify Duplication

Look for these patterns:

- **Exact copies** - Identical or near-identical code blocks
- **Similar patterns** - Code with the same structure but different values/names
- **Parallel hierarchies** - Similar class/module structures across domains
- **Copy-paste indicators** - Similar variable names like `data1`, `data2`, or `handleUserClick`, `handleAdminClick`

### 2. Analyze Context

Before refactoring, evaluate:

- **Coupling** - Will the abstraction create unwanted dependencies?
- **Cohesion** - Do the duplicated pieces truly belong together?
- **Frequency** - How often is this pattern repeated? (Rule of Three applies)
- **Volatility** - Do the duplicated pieces change together or independently?

### 3. Choose Refactoring Technique

Select the appropriate technique based on the duplication type (see Refactoring Techniques below).

### 4. Extract and Test

- Extract in small, verifiable steps
- Run tests after each extraction
- Verify behavior preservation
- Consider introducing the abstraction gradually (strangler pattern)

## Refactoring Techniques

### Extract Function/Method

When the same logic appears in multiple places.

**Before:**

```typescript
// Duplicated in multiple components
const userName = user.firstName + " " + user.lastName;
const emailSubject = "Hello, " + userName;
```

**After:**

```typescript
function getFullName(user: User): string {
  return `${user.firstName} ${user.lastName}`;
}

const userName = getFullName(user);
const emailSubject = `Hello, ${userName}`;
```

### Extract Variable/Constant

When the same value or expression is computed multiple times.

**Before:**

```typescript
if (user.age >= 18 && user.age < 65) {
  /* ... */
}
if (user.age >= 18 && user.age < 65) {
  /* ... */
}
```

**After:**

```typescript
const isWorkingAge = user.age >= 18 && user.age < 65;
if (isWorkingAge) {
  /* ... */
}
if (isWorkingAge) {
  /* ... */
}
```

### Parameterize Duplicated Code

When code differs only in values.

**Before:**

```typescript
function validateEmail(email: string): boolean {
  /* ... */
}
function validatePhone(phone: string): boolean {
  /* ... */
}
function validateZip(zip: string): boolean {
  /* ... */
}
```

**After:**

```typescript
function validateField(value: string, pattern: RegExp): boolean {
  /* ... */
}

const validateEmail = (email: string) => validateField(email, EMAIL_REGEX);
const validatePhone = (phone: string) => validateField(phone, PHONE_REGEX);
```

### Extract Class/Module

When related functions and data are scattered or duplicated.

**Before:**

```typescript
// Scattered across multiple files
function calculateUserDiscount(user: User, amount: number) {
  /* ... */
}
function getUserLoyaltyPoints(user: User) {
  /* ... */
}
function updateUserRewards(user: User) {
  /* ... */
}
```

**After:**

```typescript
class UserRewards {
  calculateDiscount(user: User, amount: number) {
    /* ... */
  }
  getLoyaltyPoints(user: User) {
    /* ... */
  }
  updateRewards(user: User) {
    /* ... */
  }
}
```

### Replace Conditional with Polymorphism

When the same switch/if-else appears multiple times.

**Before:**

```typescript
function processPayment(type: string, amount: number) {
  if (type === "credit") {
    /* ... */
  } else if (type === "debit") {
    /* ... */
  } else if (type === "crypto") {
    /* ... */
  }
}
```

**After:**

```typescript
type PaymentProcessor = {
  process(amount: number): void;
};

class CreditProcessor implements PaymentProcessor {
  /* ... */
}
class DebitProcessor implements PaymentProcessor {
  /* ... */
}
class CryptoProcessor implements PaymentProcessor {
  /* ... */
}
```

### Introduce Strategy Pattern

When algorithm selection logic is duplicated.

**Before:**

```typescript
// Duplicated in multiple places
if (sortType === "date") {
  items.sort(byDate);
} else if (sortType === "name") {
  items.sort(byName);
} else {
  items.sort(byPriority);
}
```

**After:**

```typescript
const sortStrategies = {
  date: byDate,
  name: byName,
  priority: byPriority,
};

const sortFn = sortStrategies[sortType] ?? byPriority;
items.sort(sortFn);
```

### Pull Up Method

When subclasses have identical methods.

**Before:**

```typescript
class AdminUser {
  getDisplayName() {
    return `${this.firstName} ${this.lastName}`;
  }
}

class RegularUser {
  getDisplayName() {
    return `${this.firstName} ${this.lastName}`;
  }
}
```

**After:**

```typescript
class BaseUser {
  getDisplayName() {
    return `${this.firstName} ${this.lastName}`;
  }
}

class AdminUser extends BaseUser {}
class RegularUser extends BaseUser {}
```

## Detection Heuristics

### Rule of Three

Wait until code appears **3+ times** before abstracting. Two occurrences might be coincidental; three suggests a
pattern.

### Similarity Indicators

- Variable names like `data1`, `data2`, `data3`
- Function names like `handleUserClick`, `handleAdminClick`
- Near-identical code with only constants changed
- Similar error handling across multiple functions

### Structural Duplication

- Multiple classes/modules with parallel structures
- Repeated validation logic
- Similar API endpoint handlers
- Duplicate test setup code

### Code Smells

- Long methods doing multiple similar things
- Large switch statements appearing in multiple places
- Repeated null checks or type guards
- Duplicate string literals or magic numbers

## When NOT to DRY

Refactoring inappropriately creates worse problems than duplication. Avoid DRY when:

### Coincidental Similarity

Code that looks similar but serves different domains or business logic.

**Example:**

```typescript
// Both calculate "discount" but have different business rules
function calculateEmployeeDiscount(amount: number) {
  return amount * 0.2; // 20% employee discount
}

function calculateSeasonalDiscount(amount: number) {
  return amount * 0.2; // 20% seasonal sale
}
```

These should remain separate—they may diverge as business rules evolve.

### Premature Abstraction

Don't abstract until patterns are clear. Early abstraction often guesses wrong.

### Single-Use Code

If code appears only once or twice and is unlikely to grow, leave it concrete.

### Testing Code

Test clarity often trumps DRY. Duplicating test setup for readability is acceptable.

**Example:**

```typescript
// Acceptable duplication in tests
it("handles admin user", () => {
  const user = { role: "admin", permissions: ["read", "write"] };
  // test...
});

it("handles regular user", () => {
  const user = { role: "user", permissions: ["read"] };
  // test...
});
```

### Over-Engineering

Avoid creating abstractions for every 2-3 line similarity. Balance DRY against readability and simplicity.

## Language-Specific Considerations

### TypeScript/JavaScript

- **Hooks** - Extract custom hooks for repeated React logic
- **Higher-order functions** - Use `map`, `filter`, `reduce` to eliminate loops
- **Composition** - Compose small functions rather than large utilities
- **Utility types** - Use TypeScript utility types (`Pick`, `Omit`, etc.) to DRY up type definitions

**Example:**

```typescript
// Custom hook extraction
function useFormValidation(initialValues: FormValues) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  // validation logic...
  return { values, errors, handleChange };
}
```

### Python

- **Decorators** - Extract cross-cutting concerns (logging, timing, auth)
- **Context managers** - DRY up setup/teardown patterns
- **Generators** - Replace repeated iteration logic
- **Dataclasses** - Eliminate boilerplate in data structures

**Example:**

```python
# Decorator for repeated auth checks
def require_admin(func):
    def wrapper(user, *args, **kwargs):
        if not user.is_admin:
            raise PermissionError()
        return func(user, *args, **kwargs)
    return wrapper
```

### General Patterns

- **Configuration over code** - Use data structures to eliminate conditional logic
- **Template Method** - Define algorithm skeleton in base, vary steps in subclasses
- **Dependency Injection** - Parameterize dependencies rather than hardcoding
- **Builder Pattern** - Eliminate constructor duplication for complex objects

## Best Practices

1. **Refactor after green tests** - Ensure tests pass before refactoring
2. **One refactoring at a time** - Don't mix behavior changes with refactoring
3. **Commit frequently** - Small, reversible commits during refactoring
4. **Name clearly** - Abstraction names should reveal intent, not implementation
5. **Document why** - Explain the pattern being abstracted, especially for complex cases
6. **Consider performance** - Ensure abstractions don't introduce performance penalties
7. **Review with team** - Abstractions affect everyone; ensure they're intuitive
