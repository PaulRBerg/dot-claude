#!/usr/bin/env bash
# release-automation.sh - Complete Release Workflow Automation
# Usage: ./release-automation.sh <version> [--draft] [--prerelease]

set -euo pipefail

# Configuration
VERSION="${1:-}"
DRAFT_FLAG=""
PRERELEASE_FLAG=""
BUILD_DIR="dist"

# Parse arguments
shift || true
for arg in "$@"; do
  case $arg in
    --draft)
      DRAFT_FLAG="--draft"
      ;;
    --prerelease)
      PRERELEASE_FLAG="--prerelease"
      ;;
    --build-dir=*)
      BUILD_DIR="${arg#*=}"
      ;;
  esac
done

# Validate version provided
if [ -z "$VERSION" ]; then
  echo "❌ Error: Version required"
  echo "Usage: $0 <version> [--draft] [--prerelease]"
  echo "Example: $0 1.2.0"
  exit 1
fi

# Normalize version (add 'v' prefix if not present)
if [[ ! $VERSION =~ ^v ]]; then
  VERSION="v$VERSION"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Release Automation: $VERSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Pre-flight checks
echo "1️⃣  Running pre-flight checks..."

# Check we're on main/master
CURRENT_BRANCH=$(git branch --show-current)
if [[ ! $CURRENT_BRANCH =~ ^(main|master)$ ]]; then
  echo "⚠️  Warning: You're on branch '$CURRENT_BRANCH', not main/master"
  read -p "Continue anyway? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
  echo "❌ Error: You have uncommitted changes"
  git status --short
  exit 1
fi

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
  echo "❌ Error: Tag $VERSION already exists"
  exit 1
fi

# Pull latest changes
echo "Pulling latest changes..."
git pull origin "$CURRENT_BRANCH"

echo "✅ Pre-flight checks passed"
echo ""

# Step 2: Run tests (if test command exists)
echo "2️⃣  Running tests..."

if [ -f "package.json" ] && jq -e '.scripts.test' package.json >/dev/null 2>&1; then
  npm test
elif [ -f "Makefile" ] && grep -q "^test:" Makefile; then
  make test
elif [ -f "pytest.ini" ] || [ -f "setup.py" ]; then
  pytest
else
  echo "⚠️  No test command found, skipping..."
fi

echo "✅ Tests passed"
echo ""

# Step 3: Build project (if build command exists)
echo "3️⃣  Building project..."

if [ -f "package.json" ] && jq -e '.scripts.build' package.json >/dev/null 2>&1; then
  npm run build
elif [ -f "Makefile" ] && grep -q "^build:" Makefile; then
  make build
else
  echo "⚠️  No build command found, skipping..."
fi

echo "✅ Build complete"
echo ""

# Step 4: Update version in files
echo "4️⃣  Updating version in project files..."

VERSION_NUM="${VERSION#v}"  # Remove 'v' prefix

if [ -f "package.json" ]; then
  jq ".version = \"$VERSION_NUM\"" package.json > package.json.tmp
  mv package.json.tmp package.json
  echo "Updated package.json"
fi

if [ -f "pyproject.toml" ]; then
  sed -i.bak "s/^version = .*/version = \"$VERSION_NUM\"/" pyproject.toml
  rm -f pyproject.toml.bak
  echo "Updated pyproject.toml"
fi

# Commit version bump if files were modified
if ! git diff-index --quiet HEAD --; then
  git add -A
  git commit -m "chore: bump version to $VERSION"
  git push origin "$CURRENT_BRANCH"
  echo "✅ Version bump committed"
fi

echo ""

# Step 5: Create git tag
echo "5️⃣  Creating git tag..."

git tag -a "$VERSION" -m "Release $VERSION"
git push origin "$VERSION"

echo "✅ Tag created and pushed"
echo ""

# Step 6: Generate release notes
echo "6️⃣  Generating release notes..."

# Get commits since last tag
LAST_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
  RELEASE_NOTES=$(git log "$LAST_TAG..HEAD" --pretty=format:"- %s (%h)" --reverse)
else
  RELEASE_NOTES=$(git log --pretty=format:"- %s (%h)" --reverse)
fi

# Save to temporary file
NOTES_FILE=$(mktemp)
cat > "$NOTES_FILE" <<EOF
## What's Changed

$RELEASE_NOTES

## Installation

```bash
# Install via package manager
npm install package@$VERSION_NUM

# Or download from releases
gh release download $VERSION
```

---

**Full Changelog**: https://github.com/$(gh repo view --json nameWithOwner -q '.nameWithOwner')/compare/${LAST_TAG}...${VERSION}
EOF

echo "✅ Release notes generated"
echo ""

# Step 7: Create GitHub release
echo "7️⃣  Creating GitHub release..."

RELEASE_ARGS=(
  "$VERSION"
  "--title" "$VERSION"
  "--notes-file" "$NOTES_FILE"
)

# Add draft/prerelease flags
if [ -n "$DRAFT_FLAG" ]; then
  RELEASE_ARGS+=("$DRAFT_FLAG")
fi

if [ -n "$PRERELEASE_FLAG" ]; then
  RELEASE_ARGS+=("$PRERELEASE_FLAG")
fi

# Create release
RELEASE_URL=$(gh release create "${RELEASE_ARGS[@]}")

echo "✅ Release created: $RELEASE_URL"
echo ""

# Step 8: Upload artifacts (if build directory exists)
if [ -d "$BUILD_DIR" ] && [ -n "$(ls -A "$BUILD_DIR")" ]; then
  echo "8️⃣  Uploading build artifacts..."

  gh release upload "$VERSION" "$BUILD_DIR"/*

  echo "✅ Artifacts uploaded"
else
  echo "8️⃣  No build artifacts found in $BUILD_DIR, skipping upload..."
fi

echo ""

# Cleanup
rm -f "$NOTES_FILE"

# Final summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Release $VERSION Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Summary:"
echo "  • Tag: $VERSION"
echo "  • Branch: $CURRENT_BRANCH"
echo "  • URL: $RELEASE_URL"
echo ""
echo "Next steps:"
echo "  • Announce the release"
echo "  • Update documentation if needed"
echo "  • Monitor for issues"
echo ""

# Optionally open release in browser
read -p "Open release in browser? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  gh release view "$VERSION" --web
fi
