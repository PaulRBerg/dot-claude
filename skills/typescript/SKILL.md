---
name: typescript
description: This skill should be used when the user asks to "configure TypeScript", "fix type errors", "use dayjs", "add type definitions", "set up React with TypeScript", mentions ".ts" or ".tsx" files, or asks about TypeScript best practices or TypeScript-specific tooling.
---

# TypeScript Skill

## Rules

Note that these are not hard-and-fast rules. If there's a good reason not to apply a rule, don't apply it.

### Alphabetical Order

Maintain alphabetical order for better readability and consistency:

- **Function parameters** - Order by parameter name
- **Object literal fields** - Sort by key name
- **Type definitions** - Arrange fields alphabetically
- **Class properties** - Order by property name

**Example (type definitions):**

```typescript
// bad
type User = {
  name: string;
  age: number;
  email: string;
};

// good
type User = {
  age: number;
  email: string;
  name: string;
};
```

### Biome

Use BiomeJS for linting and formatting JavaScript and TypeScript code. Look for a `biome.jsonc` file and, if it's not present, create it.

Exception: project already uses ESLint and Prettier.

### dayjs for date and time calculations

Use the `dayjs` library for date calculations. Avoid using the native JavaScript Date object.

**Example:**

```typescript
import dayjs from "dayjs";

const now = dayjs();
const tomorrow = now.add(1, "day");
```

### No `any` type

Never use the `any` type.

### Never return a value in `forEach` callbacks

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

### Use `Number.isNaN` instead of `isNaN`

**Example:**

```typescript
const x = Number.isNaN(y); // good
const x = isNaN(y); // bad
```

### Comment Dividers

Use centered comment dividers for major section breaks:

**Format (80 chars total):**

```typescript
// -------------------------------------------------------------------------- //
//                                   TITLE                                    //
// -------------------------------------------------------------------------- //
```

**Rules:**

- Total width: 80 characters
- Title: UPPERCASE, centered with spaces
- Border line: dashes `-` filling the space between `// ` and ` //`

**When to use:**

- Major logical sections (imports, types, constants, main logic, exports)
- Separating distinct feature areas
- NOT for every function or small grouping

**Example:**

```typescript
// -------------------------------------------------------------------------- //
//                                   IMPORTS                                  //
// -------------------------------------------------------------------------- //

import { Effect } from "effect";

// -------------------------------------------------------------------------- //
//                                    TYPES                                   //
// -------------------------------------------------------------------------- //

type Config = {
  name: string;
};
```
