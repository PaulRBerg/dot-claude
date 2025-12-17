# Monorepo Setup

Configure TypeScript monorepos with workspaces, shared tooling, and cross-package imports.

## Workspace Configuration

Set up the root `package.json` with workspace declarations and shared development dependencies.

```json
{
  "name": "monorepo-root",
  "private": true,
  "workspaces": ["packages/*"],
  "devDependencies": {
    "@biomejs/biome": "^2.3.8",
    "vitest": "^4.0.15",
    "typescript": "^5.9.3",
    "husky": "^9.1.7",
    "lint-staged": "^16.2.7"
  },
  "scripts": {
    "prepare": "husky install"
  }
}
```

Install shared tooling at the root. Individual packages declare their own runtime and development dependencies.

## Directory Structure

Organize the monorepo with clear separation between packages and shared configuration.

```
monorepo/
├── packages/
│   ├── pkg-a/
│   │   ├── src/
│   │   │   └── index.ts      # Barrel export
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── vitest.config.ts
│   └── pkg-b/
│       ├── src/
│       │   └── index.ts
│       ├── package.json
│       ├── tsconfig.json
│       └── vitest.config.ts
├── tests/
│   └── setup.ts              # Shared test setup
├── package.json              # Root workspace config
├── tsconfig.json             # Root TypeScript config
├── biome.jsonc               # Root Biome config
├── vitest.config.ts          # Multi-project aggregator
├── vitest.shared.ts          # Shared Vitest config
├── justfile                  # Root recipes with modules
└── .husky/
    └── pre-commit
```

Place shared configuration at the root. Each package maintains its own source code and package-specific configuration.

## TypeScript Configuration

### Root Configuration

Create a root `tsconfig.json` with path aliases for cross-package imports.

```json
{
  "extends": "./node_modules/@sablier/devkit/tsconfig/base.json",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@pkg-a": ["./packages/pkg-a/src/index.ts"],
      "@pkg-a/*": ["./packages/pkg-a/src/*"],
      "@pkg-b": ["./packages/pkg-b/src/index.ts"],
      "@pkg-b/*": ["./packages/pkg-b/src/*"]
    }
  },
  "references": [
    { "path": "./packages/pkg-a" },
    { "path": "./packages/pkg-b" }
  ]
}
```

Use project references for faster incremental builds. Map package names to barrel exports for clean imports.

### Package Configuration

Each package extends the root configuration and defines its own compilation settings.

```json
{
  "extends": "../../tsconfig.json",
  "compilerOptions": {
    "composite": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

Enable `composite` for project references. Specify `outDir` and `rootDir` for build outputs.

## Vitest Multi-Project Setup

### Root Workspace Configuration

Define a Vitest workspace that aggregates all package test configurations.

```typescript
import { defineWorkspace } from "vitest/config";

export default defineWorkspace([
  "./packages/pkg-a/vitest.config.ts",
  "./packages/pkg-b/vitest.config.ts",
]);
```

Run all tests from the root with `vitest`. Vitest automatically discovers and runs tests across all projects.

### Shared Test Configuration

Extract common test configuration to `vitest.shared.ts`.

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    setupFiles: ["./tests/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      exclude: ["**/node_modules/**", "**/dist/**", "**/*.test.ts"],
    },
  },
});
```

Import and merge this configuration in package-specific configs.

### Package Test Configuration

Each package merges shared configuration with package-specific settings.

```typescript
import { defineConfig, mergeConfig } from "vitest/config";
import sharedConfig from "../../vitest.shared";

export default mergeConfig(
  sharedConfig,
  defineConfig({
    test: {
      include: ["src/**/*.test.ts"],
      name: "pkg-a",
    },
  })
);
```

Use `mergeConfig` to combine shared and package settings. Name each project for clear test output.

## Just Modules

### Root Justfile

Import shared recipes and define package modules.

```just
import "./node_modules/@sablier/devkit/just/base.just"

# Import package modules
mod pkg-a "packages/pkg-a"
mod pkg-b "packages/pkg-b"

# Aggregate checks across all packages
[group("checks")]
full-check:
    just pkg-a::check
    just pkg-b::check

# Run all tests
[group("test")]
test-all:
    na vitest run

# Build all packages
[group("build")]
build-all:
    just pkg-a::build
    just pkg-b::build

# Clean all packages
[group("clean")]
clean-all:
    just pkg-a::clean
    just pkg-b::clean
    rm -rf node_modules
```

Use module imports to organize package-specific recipes. Define aggregate commands that run across all packages.

### Package Justfile

Each package defines its own recipes, importing shared base recipes.

```just
import "../../node_modules/@sablier/devkit/just/base.just"

# Run package-specific checks
[group("checks")]
check:
    na biome check ./src
    na tsc --noEmit

# Build package
[group("build")]
build:
    na tsc --build

# Clean build artifacts
[group("clean")]
clean:
    rm -rf dist
    rm -rf node_modules

# Run package tests
[group("test")]
test:
    na vitest run
```

Invoke package recipes from the root with `just pkg-a::check` or from within the package with `just check`.

## Cross-Package Imports

### Package Configuration

Declare internal dependencies in each package's `package.json`.

```json
{
  "name": "@scope/pkg-b",
  "version": "1.0.0",
  "dependencies": {
    "@scope/pkg-a": "workspace:*"
  }
}
```

Use `workspace:*` protocol for internal dependencies. npm/pnpm/yarn will link packages during installation.

### Barrel File Enforcement

Enforce barrel imports with Biome's restricted imports rule.

```jsonc
{
  "linter": {
    "rules": {
      "suspicious": {
        "noRestrictedImports": {
          "level": "error",
          "options": {
            "paths": {
              "@scope/pkg-a/src": "Import from @scope/pkg-a (barrel) instead",
              "@scope/pkg-a/src/*": "Import from @scope/pkg-a (barrel) instead",
              "@scope/pkg-b/src": "Import from @scope/pkg-b (barrel) instead",
              "@scope/pkg-b/src/*": "Import from @scope/pkg-b (barrel) instead"
            }
          }
        }
      }
    }
  }
}
```

Block direct imports into `src/` directories. Force consumers to use the barrel export at `@scope/pkg-a`.

### Barrel Exports

Each package exposes a public API through `src/index.ts`.

```typescript
// packages/pkg-a/src/index.ts
export { functionA } from "./functionA.js";
export { ClassA } from "./ClassA.js";
export type { TypeA } from "./types.js";
```

Import from other packages using the barrel.

```typescript
// packages/pkg-b/src/example.ts
import { functionA, type TypeA } from "@scope/pkg-a";
```

Barrel exports provide encapsulation and prevent coupling to internal file structure.

## Biome Configuration

### Root Configuration

Define shared linting and formatting rules at the root.

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  },
  "files": {
    "ignore": ["**/node_modules/**", "**/dist/**", "**/.vite/**"]
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "lineWidth": 100
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "double",
      "semicolons": "always"
    }
  },
  "organizeImports": {
    "enabled": true
  }
}
```

Packages inherit root configuration automatically. Override specific rules in package-level `biome.jsonc` files when needed.

## Git Hooks

### Husky Setup

Install husky during workspace installation.

```bash
npx husky install
npx husky add .husky/pre-commit "npx lint-staged"
```

### Lint-Staged Configuration

Configure lint-staged in root `package.json` to run checks on staged files.

```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": [
      "biome check --write --no-errors-on-unmatched --files-ignore-unknown=true"
    ],
    "*.{json,jsonc}": [
      "biome format --write"
    ]
  }
}
```

Lint-staged automatically detects workspace structure and runs checks on files across all packages.

## Build Orchestration

### TypeScript Project References

Build all packages with a single command.

```bash
npm run build -ws
```

TypeScript compiles packages in dependency order using project references.

### Incremental Builds

Use `--build` flag for incremental compilation.

```bash
npx tsc --build
```

TypeScript skips unchanged packages, speeding up development iteration.

### Watch Mode

Run TypeScript in watch mode across all packages.

```bash
npx tsc --build --watch
```

Automatically recompile packages when source files change.

## Package Publishing

### Versioning Strategy

Use conventional commits and changesets for version management.

```bash
npx changeset add
npx changeset version
npx changeset publish
```

Changesets automatically determine semantic versions based on changes.

### Publishing Configuration

Configure publishing in each package's `package.json`.

```json
{
  "name": "@scope/pkg-a",
  "version": "1.0.0",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js"
    }
  },
  "files": ["dist"],
  "publishConfig": {
    "access": "public"
  }
}
```

Include only distribution files in published packages. Specify entry points with `exports` field.

## Troubleshooting

### Module Resolution

If TypeScript cannot resolve cross-package imports, verify path aliases in root `tsconfig.json` match package names and barrel exports.

### Test Discovery

If Vitest fails to discover tests in a package, check that the package config is included in the root `vitest.config.ts` workspace array.

### Build Failures

If builds fail with circular dependency errors, ensure package dependencies are acyclic and use project references correctly.

### Biome Errors

If Biome reports import restriction errors, verify barrel exports exist in `src/index.ts` and imports use the package name, not file paths.
