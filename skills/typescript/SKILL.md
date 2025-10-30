---
name: typescript
description: Expert TypeScript engineering practices and patterns. Use when working with .ts or .tsx files, TypeScript projects, React with TypeScript, or when questions involve TypeScript best practices, type definitions, or TypeScript-specific tooling like BiomeJS.
---

# TypeScript Engineer

Apply these TypeScript engineering practices when working with TypeScript and React TypeScript projects.

## General Principles

- Be terse
- Anticipate needs—suggest solutions the user hasn't considered
- Treat the user as an expert
- Be precise and exhaustive
- Lead with the answer; add explanations only as needed
- Embrace new tools and contrarian ideas, not just best practices
- Speculate freely, but clearly label speculation

## TypeScript Rules

Note that these are not hard-and-fast rules. If there's a good reason not to apply a rule, don't apply it.

### Alphabetical Order

Maintain alphabetical order for better readability and consistency:

- **Function parameters** - Order by parameter name
- **Object literal fields** - Sort by key name
- **Type definitions** - Arrange fields alphabetically
- **Class properties** - Order by property name

#### Exceptions

##### Nesting depth

Group by nesting depth before alphabetical sorting.

**Example:**

```json
{
  "id": "12345", // depth 0 - comes first alphabetically
  "name": "Sample Item", // depth 0 - comes second alphabetically
  "details": {
    // depth 1 - comes last despite "d" < "i"
    "description": "...",
    "status": "active"
  }
}
```

### BiomeJS

Use BiomeJS for linting and formatting JavaScript and TypeScript code. Look for a `biome.jsonc` file and, if it's not present, create it.

Exception: project already uses ESLint and Prettier.

### Dayjs for date and time calculations

Use the `dayjs` library for date calculations. Avoid using the native JavaScript Date object.

**Example:**

```typescript
import dayjs from "dayjs";

const now = dayjs();
const tomorrow = now.add(1, "day");
```

### Lodash utilities

- Use `_.toNumber` instead of `Number.parseInt()`
- Use `_.isNan` instead of `Number.isNaN()`

### No `any` type

Never use the `any` type.

### No double negation (`!!`)

Do not use the double negation (`!!`) operator. Instead, use the `Boolean` constructor.

**Example:**

```typescript
const x = !!y; // bad
const x = Boolean(y); // good
```

### No return value in `forEach` callbacks

Never return a value from a `forEach` callback.

**Example:**

```typescript
[].forEach(() => {
  return 1; // bad
});

[].forEach(() => {
  // good
});
```

**Another example:**

```typescript
[].forEach((item) => console.log(item)); // bad

[].forEach((item) => {
  console.log(item); // good
});
```

### Prefer TypeScript over JavaScript

Use TypeScript for all new code.

### Prefer `type` instead of `interface`

Use `type` instead of `interface` for declaring types.

### Typechecking

If a `justfile` is available, run `just tsc-check`. Otherwise, run `na tsc --noEmit`.

### Use `Number.isNaN` instead of `isNaN`

**Example:**

```typescript
const x = Number.isNaN(y); // good
const x = isNaN(y); // bad
```

## TypeScript React Rules

### Hooks

Use React hooks to manage state and side effects.

Use the context7 MCP to fetch the latest documentation for React.

### Cursor Pointer

When adding a clickable component, apply the `cursor-pointer` Tailwind class to the element.
