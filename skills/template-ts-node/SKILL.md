---
name: template-ts-node
description: This skill should be used when the user asks to "create a TypeScript project", "set up Node.js project", "scaffold new project", "initialize TypeScript repo", "create a new library", "set up a CLI tool", or mentions setting up a new TypeScript/Node.js codebase.
version: 0.1.0
---

# TypeScript Node.js Project Setup

Scaffold production-ready TypeScript Node.js projects with modern tooling and best practices. Default configuration targets single-repository, non-UI projects (libraries, CLI tools, backend services). Uses Bun for package management and Vitest for testing.

## Quick Reference: Configuration Files

| File               | Purpose                                     |
| ------------------ | ------------------------------------------- |
| `package.json`     | Project metadata, dependencies, and scripts |
| `tsconfig.json`    | TypeScript compiler configuration           |
| `biome.jsonc`      | Linting and formatting rules                |
| `justfile`         | Task automation and project commands        |
| `vitest.config.ts` | Test framework configuration                |
| `.gitignore`       | Version control exclusions                  |
| `.gitattributes`   | Git line-ending and merge behavior          |
| `.husky/`          | Git hooks for pre-commit automation         |
| `bun.lockb`        | Dependency lock file (Bun)                  |

## Setup Workflow

### 1. Initialize Project Structure

Create the project directory and initialize version control.

```bash
mkdir project-name
cd project-name
git init
```

### 2. Copy Configuration Files

Copy all configuration files from `resources/` directory to the project root. These files are pre-configured to extend `@sablier/devkit` and follow established patterns.

**Required files:**

- `package.json` - Adapt name, description, version, and author fields
- `tsconfig.json` - Extends `@sablier/devkit/tsconfig/base.json`
- `biome.jsonc` - Extends `ultracite/core` and `@sablier/devkit/biome/base`
- `justfile` - Imports `@sablier/devkit/just/base.just`
- `vitest.config.ts` - Test configuration
- `.gitignore` - Standard Node.js exclusions
- `.gitattributes` - Line endings and diff behavior

### 3. Install Dependencies

Use Bun to install project dependencies.

```bash
bun install
```

**Core dependencies:**

- `@sablier/devkit` (from GitHub: `github:sablier-labs/devkit`)
- `typescript`
- `vitest` (testing)
- `@biomejs/biome` (linting/formatting)
- `husky` (git hooks)
- `just` (task runner, if not globally installed)

### 4. Initialize Git Hooks

Set up Husky for pre-commit automation.

```bash
bun run prepare
```

This installs git hooks that run linting and formatting checks before commits.

### 5. Create Source Structure

Establish the core source directory and entry point.

```bash
mkdir src
touch src/index.ts
```

Add initial content to `src/index.ts`:

```typescript
// -------------------------------------------------------------------------- //
//                                   EXPORTS                                  //
// -------------------------------------------------------------------------- //

export const VERSION = "0.1.0";
```

### 6. Verify Setup

Run full project checks to ensure configuration is correct.

```bash
just full-check
```

This executes TypeScript compilation, linting, formatting checks, and tests.

## Key Configuration Choices

### Shared Configuration via @sablier/devkit

All configuration files extend the shared devkit to maintain consistency across projects. This approach centralizes common patterns and reduces per-project configuration burden.

**GitHub location:** `github:sablier-labs/devkit`

### TypeScript Configuration

Extend the base TypeScript configuration from devkit. Customize `compilerOptions` only when project-specific requirements demand it.

**Example `tsconfig.json`:**

```json
{
  "extends": "@sablier/devkit/tsconfig/base.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

**Key settings (inherited from devkit):**

- `strict: true` - Maximum type safety
- `esModuleInterop: true` - CommonJS/ESM compatibility
- `skipLibCheck: true` - Faster compilation
- `module: "ESNext"` - Modern module system
- `target: "ES2022"` - Recent language features

### Biome Configuration

Extend both Ultracite core rules and Sablier devkit overrides. This provides opinionated linting and formatting with project-specific adjustments.

**Example `biome.jsonc`:**

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "extends": ["ultracite/core", "@sablier/devkit/biome/base"],
  "formatter": {
    "indentStyle": "space",
    "lineWidth": 120
  }
}
```

**Inherited behaviors:**

- Sorted imports and exports
- Consistent naming conventions
- No unused variables
- Explicit function return types

### Just Task Runner

Import base recipes from devkit and add project-specific tasks as needed. Just provides a modern alternative to npm scripts with better composability.

**Example `justfile`:**

```just
import "@sablier/devkit/just/base.just"

# Project-specific recipe
custom-task:
    echo "Running custom task"
```

**For advanced Just CLI usage** (modules, attributes, inline scripts, conditional execution), consult the `just-cli` skill which provides comprehensive guidance on Just's advanced features.

### Vitest Configuration

Configure test framework with TypeScript support and coverage reporting.

**Example `vitest.config.ts`:**

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
    },
  },
});
```

## Common Just Recipes

Execute these commands from the project root using the `just` command.

### Development

```bash
just dev
```

Start development mode with file watching and auto-reload.

### Build

```bash
just build
```

Compile TypeScript to JavaScript in the `dist/` directory.

### Test

```bash
just test
```

Run all tests with Vitest.

```bash
just test-watch
```

Run tests in watch mode for active development.

### Code Quality

```bash
just full-check
```

Run comprehensive checks: TypeScript compilation, Biome linting, Biome formatting, and tests. Use this before commits and in CI pipelines.

```bash
just full-write
```

Auto-fix all fixable issues: apply Biome formatting and safe linting fixes.

```bash
just biome-check
```

Run only Biome linting and formatting checks without modifying files.

```bash
just biome-write
```

Apply Biome formatting and auto-fixes to all source files.

### Clean

```bash
just clean
```

Remove generated files (`dist/`, `coverage/`, etc.).

## Package.json Scripts

Configure standard npm scripts that delegate to Just recipes or run directly.

**Essential scripts:**

```json
{
  "scripts": {
    "prepare": "husky install",
    "build": "just build",
    "test": "just test",
    "dev": "just dev",
    "lint": "just biome-check",
    "format": "just biome-write",
    "typecheck": "tsc --noEmit"
  }
}
```

**Script purposes:**

- `prepare` - Runs automatically after `npm install` to set up git hooks
- `build` - Compiles production bundle
- `test` - Executes test suite
- `dev` - Starts development server/watcher
- `lint` - Checks code quality without modifications
- `format` - Applies automatic formatting
- `typecheck` - Verifies TypeScript types without emitting files

## Directory Structure

Organize project files following these conventions:

```
project-name/
├── src/
│   ├── index.ts          # Main entry point
│   ├── lib/              # Library code
│   ├── utils/            # Utility functions
│   └── types/            # Type definitions
├── test/
│   └── index.test.ts     # Test files
├── dist/                 # Compiled output (gitignored)
├── coverage/             # Test coverage reports (gitignored)
├── node_modules/         # Dependencies (gitignored)
├── package.json
├── tsconfig.json
├── biome.jsonc
├── justfile
├── vitest.config.ts
├── .gitignore
├── .gitattributes
├── .husky/
│   └── pre-commit
├── bun.lockb
└── README.md
```

## Adapting for Specific Project Types

### CLI Tools

**Add dependencies:**

```bash
bun add commander chalk ora
bun add -d @types/node
```

**Update `package.json`:**

```json
{
  "bin": {
    "cli-name": "./dist/cli.js"
  }
}
```

**Create `src/cli.ts`:**

```typescript
#!/usr/bin/env node

import { Command } from "commander";
import { VERSION } from "./index.js";

const program = new Command();

program
  .name("cli-name")
  .description("CLI description")
  .version(VERSION);

program.parse();
```

### Libraries

**Update `package.json` for library distribution:**

```json
{
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "files": ["dist"]
}
```

**Configure `tsconfig.json` for declaration generation:**

```json
{
  "compilerOptions": {
    "declaration": true,
    "declarationMap": true
  }
}
```

### Backend Services

**Add server dependencies:**

```bash
bun add express
bun add -d @types/express
```

**Create `src/server.ts`:**

```typescript
import express from "express";

const app = express();
const PORT = process.env.PORT || 3000;

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

## Resource Files

Copy these pre-configured files from `resources/` directory to bootstrap new projects:

| File               | Purpose                                                          |
| ------------------ | ---------------------------------------------------------------- |
| `package.json`     | Base package.json with devDependencies (adapt name, description) |
| `tsconfig.json`    | TypeScript configuration extending devkit                        |
| `biome.jsonc`      | Linting and formatting rules                                     |
| `justfile`         | Task automation recipes (build, test, check)                     |
| `vitest.config.ts` | Test framework setup for single repos                            |
| `vitest.shared.ts` | Shared test config for monorepos                                 |
| `.prettierrc.js`   | Prettier config extending devkit                                 |
| `.prettierignore`  | Prettier ignore patterns                                         |
| `.lintstagedrc.js` | Pre-commit hook configuration                                    |
| `.gitignore`       | Standard Node.js exclusions                                      |

**Usage:** Copy files to project root, then adapt `package.json` fields (name, description, author, version).

## Reference Documentation

### For React/Next.js UI Projects

Consult `references/next-ui.md` for guidance on:

- Next.js project structure
- React component patterns
- UI-specific dependencies (Tailwind, Radix, etc.)
- Server and client component architecture
- API routes and middleware

### For Monorepo Workspaces

Consult `references/monorepo.md` for guidance on:

- Workspace configuration with Bun
- Shared package setup
- Cross-package dependencies
- Monorepo-specific scripts
- Turborepo or Nx integration

## Best Practices

### Dependency Management

**Pin major versions** but allow minor and patch updates:

```json
{
  "dependencies": {
    "@sablier/devkit": "github:sablier-labs/devkit",
    "zod": "^3.22.0"
  }
}
```

**Separate dev and production dependencies** clearly:

- Runtime code → `dependencies`
- Build tools, linters, test frameworks → `devDependencies`

### TypeScript Configuration

**Enable strict mode** for maximum type safety. Override specific checks only when absolutely necessary.

**Use path aliases** for cleaner imports:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

### Testing Strategy

**Co-locate tests** with source files or use parallel `test/` directory structure.

**Name test files** with `.test.ts` or `.spec.ts` suffix.

**Write tests first** for complex logic (TDD approach).

**Aim for high coverage** on critical paths, but don't chase 100% arbitrarily.

### Git Workflow

**Commit often** with descriptive messages.

**Use conventional commits** format: `feat:`, `fix:`, `docs:`, `refactor:`, etc.

**Let Husky hooks** catch issues before they reach the repository.

**Tag releases** with semantic versioning: `v1.0.0`, `v1.1.0`, etc.

### Code Organization

**Group by feature** rather than by file type when projects grow beyond simple structure.

**Export from index files** to create clean public APIs:

```typescript
// src/lib/index.ts
export { functionA } from "./moduleA.js";
export { functionB } from "./moduleB.js";
```

**Use barrel exports sparingly** - they can impact tree-shaking.

## Troubleshooting

### TypeScript Errors After Installation

Run type checking explicitly:

```bash
bun run typecheck
```

Check that `@sablier/devkit` installed correctly:

```bash
ls node_modules/@sablier/devkit
```

### Biome Not Finding Configuration

Verify `biome.jsonc` exists in project root:

```bash
ls -la biome.jsonc
```

Check that Biome can parse the configuration:

```bash
bunx biome check --config-path=biome.jsonc
```

### Just Recipes Failing

Confirm Just is installed:

```bash
just --version
```

Verify `justfile` imports are resolvable:

```bash
just --list
```

Check for syntax errors in custom recipes:

```bash
just --dry-run recipe-name
```

### Git Hooks Not Running

Reinstall Husky hooks:

```bash
rm -rf .husky
bun run prepare
```

Verify hook scripts are executable:

```bash
chmod +x .husky/pre-commit
```

## Integration with Existing Tools

### VSCode

**Recommended extensions:**

- Biome (biomejs.biome)
- TypeScript and JavaScript Language Features (built-in)
- Just (skellock.just)

**Workspace settings (`.vscode/settings.json`):**

```json
{
  "editor.defaultFormatter": "biomejs.biome",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "quickfix.biome": "explicit",
    "source.organizeImports.biome": "explicit"
  }
}
```

### GitHub Actions

**Example CI workflow (`.github/workflows/ci.yml`):**

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v1
      - run: bun install
      - run: just full-check
```

### Pre-commit Framework

Integrate with Python's pre-commit framework if needed:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: biome
        name: Biome Check
        entry: just biome-check
        language: system
        pass_filenames: false
```

## Next Steps After Setup

1. **Write initial code** in `src/index.ts`
1. **Add first test** in `test/index.test.ts`
1. **Run `just full-check`** to verify everything works
1. **Create initial commit** with all scaffolding
1. **Set up remote repository** and push
1. **Configure CI/CD** using GitHub Actions or similar
1. **Write README.md** with project-specific documentation
1. **Add LICENSE** file appropriate for your use case

## Related Skills

- **`just-cli`** - Comprehensive Just task runner patterns, modules, and advanced features
- **`typescript`** - TypeScript-specific rules, patterns, and best practices
- **`biome`** - Biome configuration and lint rule customization
- **`node-deps`** - Dependency update strategies with Taze

## Summary

This skill provides a streamlined path to creating production-ready TypeScript Node.js projects. By leveraging shared configuration from `@sablier/devkit` and modern tooling (Bun, Vitest, Biome, Just), new projects achieve consistency and quality from day one. Adapt the base configuration for CLI tools, libraries, or backend services as needed. Consult reference documentation for UI projects or monorepo setups when requirements extend beyond single-repository, non-UI applications.
