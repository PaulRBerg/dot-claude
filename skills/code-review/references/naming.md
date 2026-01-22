# Naming Conventions Reference

## Function Naming

Functions should use verb phrases describing the action performed.

**Patterns:**

- Actions: `createUser`, `validateInput`, `fetchOrders`, `calculateTotal`
- Transformations: `parseJSON`, `formatDate`, `convertToCSV`
- Boolean-returning: `isValid`, `hasPermission`, `canEdit`, `shouldRetry`

**Anti-patterns:**

- Generic names: `process`, `handle`, `do`, `run`, `execute` without specificity
- Noun-only: `user()` instead of `getUser()` or `createUser()`
- Misleading verbs: `getUser` that creates a user if not found

**Severity:**

- MEDIUM: Generic names requiring comments to understand (`process`, `handle`)
- LOW: Minor clarity improvements where intent is still discernible

## Variable Naming

Variables should reveal intent without requiring comments.

**Patterns:**

- Descriptive: `userCount` over `n`, `orderTotal` over `sum`
- Boolean: `isActive`, `hasChildren`, `canDelete`, `shouldRefresh`
- Collections: Plural nouns (`users`, `orders`) or suffixed (`userList`, `orderMap`)
- Temporary/scope-limited: Short names acceptable in small scopes (loop index `i`, lambda param `x`)

**Anti-patterns:**

- Single letters outside small scopes: `d`, `x`, `temp` in function bodies
- Abbreviations: `usrCnt` instead of `userCount`, `addr` instead of `address`
- Type prefixes (Hungarian notation): `strName`, `intCount`, `arrItems`
- Generic names: `data`, `info`, `item`, `thing`, `stuff`
- Misleading names: `userList` that's actually a Map, `count` that holds a boolean

**Severity:**

- MEDIUM: Misleading names, abbreviations requiring domain knowledge
- LOW: Minor clarity improvements, slightly verbose alternatives available

## File Naming

File names should follow project conventions and reflect contents.

**Patterns by ecosystem:**

- TypeScript/JavaScript: `camelCase.ts`, `PascalCase.tsx` (components), `kebab-case.ts` (Node.js)
- Python: `snake_case.py`
- React components: Match component name (`UserProfile.tsx` exports `UserProfile`)
- Tests: `*.test.ts`, `*.spec.ts`, `test_*.py`
- Config: Lowercase with dots (`tsconfig.json`, `eslint.config.js`)

**Anti-patterns:**

- Inconsistent casing within project
- Generic names: `utils.ts`, `helpers.ts`, `misc.ts` (accumulate unrelated code)
- Mismatched component/file names
- Numbered files: `utils2.ts`, `handler_v2.py`

**Severity:**

- MEDIUM: Inconsistent with project conventions, mismatched exports
- LOW: Minor convention deviations, slightly more descriptive alternatives

## Class and Component Naming

Classes and components should use noun phrases describing the entity.

**Patterns:**

- Entities: `User`, `Order`, `PaymentProcessor`
- Components: `UserProfile`, `OrderList`, `NavigationMenu`
- Services: `AuthService`, `PaymentGateway`, `EmailSender`
- Abstract/Base: `BaseRepository`, `AbstractHandler`

**Anti-patterns:**

- Verbs as class names: `Validate`, `Process`, `Handle`
- Overly generic: `Manager`, `Handler`, `Processor`, `Helper` without specificity
- Redundant suffixes: `UserClass`, `OrderObject`

**Severity:**

- MEDIUM: Generic names requiring documentation, misleading names
- LOW: Minor improvements to specificity

## Constant Naming

Constants should use UPPER_SNAKE_CASE and describe purpose, not value.

**Patterns:**

- `MAX_RETRY_COUNT` over `THREE`
- `DEFAULT_TIMEOUT_MS` over `FIVE_THOUSAND`
- `API_BASE_URL` over `URL_STRING`

**Anti-patterns:**

- Value-describing names: `FIVE`, `HUNDRED`, `COMMA`
- Lowercase constants: `maxRetries` for immutable config
- Magic numbers/strings without extraction

**Severity:**

- MEDIUM: Magic numbers in critical logic (timeouts, limits, thresholds)
- LOW: Magic numbers in non-critical paths, minor naming improvements

## Language-Specific Conventions

### TypeScript/JavaScript

- Interfaces: `IUser` (legacy) or `User` (modern, preferred)
- Type aliases: PascalCase (`UserResponse`, `OrderStatus`)
- Enums: PascalCase names, UPPER_SNAKE_CASE or PascalCase members
- Private fields: `#privateField` (native) or `_privateField` (convention)

### Python

- Classes: PascalCase (`UserService`)
- Functions/variables: snake_case (`get_user`, `user_count`)
- Constants: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- Private: `_private`, `__mangled`
- Dunder methods: `__init__`, `__str__`

### React

- Components: PascalCase (`UserProfile`)
- Hooks: `use` prefix (`useAuth`, `useFetch`)
- Event handlers: `handle` prefix (`handleClick`, `handleSubmit`)
- Render helpers: `render` prefix (`renderItem`, `renderHeader`)

## Common Anti-Patterns Summary

| Anti-Pattern    | Example                | Better Alternative          |
| --------------- | ---------------------- | --------------------------- |
| Single letter   | `d`, `x`, `t`          | `data`, `user`, `timestamp` |
| Abbreviation    | `usr`, `cnt`, `addr`   | `user`, `count`, `address`  |
| Generic verb    | `process()`            | `validateOrder()`           |
| Type prefix     | `strName`, `arrUsers`  | `name`, `users`             |
| Value name      | `FIVE`, `COMMA`        | `MAX_RETRIES`, `DELIMITER`  |
| Misleading      | `userList` (is Map)    | `userMap`, `usersById`      |
| Negated boolean | `notFound`, `disabled` | `found`, `isEnabled`        |
