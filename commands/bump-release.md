---
argument-hint: [--beta] [--dry-run]
description: Rolls out a new release by updating changelog, bumping version, committing, and tagging
---

# Bump Release

Support for both regular and beta releases.

## Parameters

- `--beta`: Create a beta release with `-beta.X` suffix
- `--dry-run`: Preview the release without making any changes (no file modifications, commits, or tags)

## Steps

1. Update the `CHANGELOG.md` file with all changes since the last version release (**skip this step for beta releases**).
2. Bump the version in `package.json`:
   - **Regular release**: Follow semantic versioning (e.g., 1.2.3)
   - **Beta release**: Add `-beta.X` suffix (e.g., 1.2.3-beta.1)
3. Commit the changes with a message like "docs: release <version>"
4. Create a new git tag by running `git tag -a v<version> -m "<version>"`

**Note**: When `--dry-run` flag is provided, display what would be done without making any actual changes to files, creating commits, or tags.

## Tasks

## Process

1. **Check for flags** - Determine if this is a beta release (`--beta` parameter) and/or dry-run (`--dry-run` parameter)
2. **Review git history** - Examine commits since the last tagged release
3. **Follow format** - Use [Common Changelog](https://common-changelog.org/) specification
4. **Check version** - Get current version from `package.json`
5. **Bump version** - If unchanged since last release, increment per Semantic Versioning rules:
   - **For regular releases**:
     - **PATCH** (x.x.X) - Bug fixes, documentation updates
     - **MINOR** (x.X.x) - New features, backward-compatible changes
     - **MAJOR** (X.x.x) - Breaking changes
   - **For beta releases** (`--beta` flag):
     - If current version has no beta suffix: Add `-beta.1` to the version
     - If current version already has beta suffix: Increment beta number (e.g., `-beta.1` → `-beta.2`)
     - If moving from beta to release: Remove beta suffix and use the base version

## Beta Release Logic

When `--beta` flag is provided in the $ARGUMENTS

1. **Parse current version** from `package.json`
2. **Determine beta version**:
   - If current version is `1.2.3`: Create `1.2.4-beta.1` (increment patch + beta.1)
   - If current version is `1.2.3-beta.1`: Create `1.2.3-beta.2` (increment beta number)
   - If current version is `1.2.3-beta.5`: Create `1.2.3-beta.6` (increment beta number)
3. **Skip CHANGELOG.md update** - Beta releases don't update the changelog
4. **Commit and tag** with beta version (e.g., `v1.2.4-beta.1`)

## Output

For regular releases only, in the `CHANGELOG.md` file, generate changelog entries categorizing changes in this order:

- **Changed** - Changes in existing functionality
- **Added** - New functionality
- **Removed** - Removed functionality
- **Fixed** - Bug fixes

## Inclusion Criteria

For regular releases only (changelog generation is skipped for beta releases):

- **Production changes only** - Exclude test changes, CI/CD workflows, and development tooling
- **Reference pull requests** - Link to PRs when available for context
- **Net changes only** - Skip commits that revert changes made after the last release
- **Only dependencies and peerDependencies changes** - Exclude changes to devDependencies

## Examples

### Regular Release

```bash
# Create a regular patch/minor/major release
/bump-release

# Preview what a regular release would do
/bump-release --dry-run
```

### Beta Release

```bash
# Create a beta release with -beta.X suffix
/bump-release --beta

# Preview what a beta release would do
/bump-release --beta --dry-run
```

## Version Examples

| Current Version | Release Type | New Version     |
| --------------- | ------------ | --------------- |
| `1.2.3`         | Regular      | `1.2.4` (patch) |
| `1.2.3`         | Beta         | `1.2.4-beta.1`  |
| `1.2.3-beta.1`  | Beta         | `1.2.3-beta.2`  |
| `1.2.3-beta.5`  | Regular      | `1.2.3`         |
