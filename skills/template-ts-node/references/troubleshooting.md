# Troubleshooting

## TypeScript Errors After Installation

Run type checking explicitly:

```bash
bun run typecheck
```

Check that `@sablier/devkit` installed correctly:

```bash
ls node_modules/@sablier/devkit
```

## Biome Not Finding Configuration

Verify `biome.jsonc` exists in project root:

```bash
ls -la biome.jsonc
```

Check that Biome can parse the configuration:

```bash
bunx biome check --config-path=biome.jsonc
```

## Just Recipes Failing

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

## Git Hooks Not Running

Reinstall Husky hooks:

```bash
rm -rf .husky
bun run prepare
```

Verify hook scripts are executable:

```bash
chmod +x .husky/pre-commit
```
