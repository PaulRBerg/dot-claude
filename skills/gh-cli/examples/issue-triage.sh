#!/usr/bin/env bash
# issue-triage.sh - Bulk Issue Labeling and Assignment
# Usage: ./issue-triage.sh [--repo owner/repo]

set -euo pipefail

# Configuration
REPO=""
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --repo)
      REPO="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Set repo context
if [ -n "$REPO" ]; then
  REPO_FLAG="--repo $REPO"
else
  REPO_FLAG=""
fi

# Function to apply triage rules
triage_issues() {
  echo "🔍 Fetching unlabeled issues..."

  # Get all unlabeled issues
  ISSUES=$(gh issue list $REPO_FLAG --label="" --limit 100 --json number,title,body,author)

  if [ -z "$ISSUES" ] || [ "$ISSUES" = "[]" ]; then
    echo "No unlabeled issues found."
    return
  fi

  echo "Found $(echo "$ISSUES" | jq 'length') unlabeled issues"
  echo ""

  # Process each issue
  echo "$ISSUES" | jq -c '.[]' | while read -r issue; do
    NUMBER=$(echo "$issue" | jq -r '.number')
    TITLE=$(echo "$issue" | jq -r '.title')
    BODY=$(echo "$issue" | jq -r '.body // ""')
    AUTHOR=$(echo "$issue" | jq -r '.author.login')

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Issue #$NUMBER: $TITLE"
    echo "Author: $AUTHOR"

    LABELS=()
    ASSIGNEE=""

    # Auto-label based on keywords
    if echo "$TITLE $BODY" | grep -qi "bug\|error\|crash\|broken"; then
      LABELS+=("bug")
    fi

    if echo "$TITLE $BODY" | grep -qi "feat\|feature\|enhance"; then
      LABELS+=("enhancement")
    fi

    if echo "$TITLE $BODY" | grep -qi "doc\|documentation"; then
      LABELS+=("documentation")
    fi

    if echo "$TITLE $BODY" | grep -qi "security\|vulnerability"; then
      LABELS+=("security")
      LABELS+=("priority: high")
    fi

    if echo "$TITLE $BODY" | grep -qi "performance\|slow\|optimize"; then
      LABELS+=("performance")
    fi

    if echo "$TITLE $BODY" | grep -qi "question\|how to\|help"; then
      LABELS+=("question")
    fi

    # Priority detection
    if echo "$TITLE $BODY" | grep -qi "urgent\|critical\|asap"; then
      LABELS+=("priority: high")
    fi

    # Check if first-time contributor
    CONTRIB_COUNT=$(gh api "/repos/{owner}/{repo}/issues?creator=$AUTHOR&state=all&per_page=100" $REPO_FLAG | jq 'length')
    if [ "$CONTRIB_COUNT" -eq 1 ]; then
      LABELS+=("good first issue")
      echo "👋 First-time contributor!"
    fi

    # Apply labels
    if [ ${#LABELS[@]} -gt 0 ]; then
      LABEL_STR=$(IFS=,; echo "${LABELS[*]}")
      echo "📝 Suggested labels: $LABEL_STR"

      if [ "$DRY_RUN" = false ]; then
        gh issue edit "$NUMBER" $REPO_FLAG --add-label "$LABEL_STR"
        echo "✅ Labels applied"
      else
        echo "🔍 [DRY RUN] Would apply labels: $LABEL_STR"
      fi
    else
      echo "⚠️  No automatic labels identified"
    fi

    echo ""
  done
}

# Function to assign stale issues
assign_stale_issues() {
  echo "🕐 Finding stale issues without assignees..."

  # Issues older than 7 days without assignee
  STALE=$(gh issue list $REPO_FLAG --json number,title,createdAt,assignees --jq '.[] | select(.assignees | length == 0) | select(.createdAt | fromdateiso8601 < (now - 604800)) | .number')

  if [ -z "$STALE" ]; then
    echo "No stale unassigned issues found."
    return
  fi

  echo "Found stale issues: $STALE"

  echo "Enter assignee username (or leave empty to skip):"
  read -r ASSIGNEE

  if [ -n "$ASSIGNEE" ]; then
    for issue_num in $STALE; do
      if [ "$DRY_RUN" = false ]; then
        gh issue edit "$issue_num" $REPO_FLAG --add-assignee "$ASSIGNEE"
        echo "✅ Assigned #$issue_num to $ASSIGNEE"
      else
        echo "🔍 [DRY RUN] Would assign #$issue_num to $ASSIGNEE"
      fi
    done
  fi
}

# Function to close duplicate issues
close_duplicates() {
  echo "🔍 Finding potential duplicates..."

  # This is a simplified approach - in production, use semantic matching
  ISSUES=$(gh issue list $REPO_FLAG --limit 100 --json number,title --state open)

  echo "$ISSUES" | jq -r '.[] | "\(.number)|\(.title)"' | sort -t'|' -k2 | \
    awk -F'|' 'prev==$2 {print prev_num, $1} {prev=$2; prev_num=$1}' | \
    while read -r dup_pair; do
      if [ -n "$dup_pair" ]; then
        echo "Potential duplicates: $dup_pair"
        echo "Review manually and close if needed"
      fi
    done
}

# Main menu
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "GitHub Issue Triage Tool"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1) Auto-label unlabeled issues"
echo "2) Assign stale issues"
echo "3) Find duplicate issues"
echo "4) Run all"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Select option (1-4): " -n 1 -r OPTION
echo ""

case $OPTION in
  1)
    triage_issues
    ;;
  2)
    assign_stale_issues
    ;;
  3)
    close_duplicates
    ;;
  4)
    triage_issues
    echo ""
    assign_stale_issues
    echo ""
    close_duplicates
    ;;
  *)
    echo "Invalid option"
    exit 1
    ;;
esac

echo ""
echo "✅ Triage complete!"
