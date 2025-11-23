#!/usr/bin/env bash
# auto-pr-create.sh - Automated Pull Request Creation
# Usage: ./auto-pr-create.sh [branch-name] [--draft]

set -euo pipefail

# Configuration
DEFAULT_BASE="main"
DRAFT_FLAG=""
BRANCH_NAME="${1:-}"

# Parse arguments
for arg in "$@"; do
  case $arg in
    --draft)
      DRAFT_FLAG="--draft"
      shift
      ;;
  esac
done

# Function to generate branch name from ticket/issue
generate_branch_name() {
  echo "Enter issue/ticket number (or leave empty):"
  read -r ISSUE_NUM

  echo "Brief description (kebab-case):"
  read -r DESCRIPTION

  if [ -n "$ISSUE_NUM" ]; then
    echo "issue-${ISSUE_NUM}-${DESCRIPTION}"
  else
    echo "${DESCRIPTION}"
  fi
}

# Get or generate branch name
if [ -z "$BRANCH_NAME" ]; then
  BRANCH_NAME=$(generate_branch_name)
fi

# Determine PR labels based on branch name
determine_labels() {
  local branch=$1
  local labels=()

  case "$branch" in
    *bug*|*fix*)
      labels+=("bug")
      ;;
    *feat*|*feature*)
      labels+=("enhancement")
      ;;
    *docs*|*documentation*)
      labels+=("documentation")
      ;;
    *test*)
      labels+=("tests")
      ;;
    *refactor*)
      labels+=("refactoring")
      ;;
  esac

  # Join labels with comma
  IFS=','
  echo "${labels[*]}"
}

# Check if on correct branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$BRANCH_NAME" ]; then
  echo "Creating and switching to branch: $BRANCH_NAME"
  git checkout -b "$BRANCH_NAME"
else
  echo "Already on branch: $BRANCH_NAME"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
  echo "⚠️  You have uncommitted changes. Commit them first."
  exit 1
fi

# Push branch to remote
echo "Pushing branch to remote..."
git push -u origin "$BRANCH_NAME"

# Determine labels
LABELS=$(determine_labels "$BRANCH_NAME")

# Create PR with smart defaults
echo "Creating pull request..."
PR_ARGS=(
  "--base" "$DEFAULT_BASE"
  "--head" "$BRANCH_NAME"
  "--fill"  # Auto-fill from commits
)

# Add draft flag if specified
if [ -n "$DRAFT_FLAG" ]; then
  PR_ARGS+=("$DRAFT_FLAG")
fi

# Add labels if any
if [ -n "$LABELS" ]; then
  PR_ARGS+=("--label" "$LABELS")
fi

# Create PR and capture URL
PR_URL=$(gh pr create "${PR_ARGS[@]}")

echo "✅ Pull request created: $PR_URL"

# Optionally open in browser
read -p "Open PR in browser? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  gh pr view --web
fi
