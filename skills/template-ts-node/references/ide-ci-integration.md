# IDE and CI Integration

## VSCode

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

## GitHub Actions

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

## Pre-commit Framework

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
