#!/usr/bin/env bash
# workflow-monitor.sh - Watch and Notify on Workflow Completion
# Usage: ./workflow-monitor.sh [run-id] [--notify]

set -euo pipefail

# Configuration
RUN_ID="${1:-}"
NOTIFY=false
CHECK_INTERVAL=30  # seconds

# Parse arguments
for arg in "$@"; do
  case $arg in
    --notify)
      NOTIFY=true
      ;;
    --interval=*)
      CHECK_INTERVAL="${arg#*=}"
      ;;
  esac
done

# Function to send notification (macOS)
send_notification() {
  local title="$1"
  local message="$2"
  local sound="${3:-default}"

  if command -v terminal-notifier &> /dev/null; then
    terminal-notifier -title "$title" -message "$message" -sound "$sound"
  elif command -v osascript &> /dev/null; then
    osascript -e "display notification \"$message\" with title \"$title\""
  else
    echo "🔔 $title: $message"
  fi
}

# Function to get workflow run status
get_run_status() {
  local run_id=$1
  gh run view "$run_id" --json status,conclusion,displayTitle,workflowName --jq '{status, conclusion, title: .displayTitle, workflow: .workflowName}'
}

# Function to watch a single run
watch_run() {
  local run_id=$1

  echo "👀 Watching run #$run_id..."

  # Get initial info
  RUN_INFO=$(get_run_status "$run_id")
  WORKFLOW=$(echo "$RUN_INFO" | jq -r '.workflow')
  TITLE=$(echo "$RUN_INFO" | jq -r '.title')

  echo "Workflow: $WORKFLOW"
  echo "Title: $TITLE"
  echo ""

  # Watch until complete
  while true; do
    STATUS=$(echo "$RUN_INFO" | jq -r '.status')
    CONCLUSION=$(echo "$RUN_INFO" | jq -r '.conclusion')

    if [ "$STATUS" = "completed" ]; then
      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      case $CONCLUSION in
        success)
          echo "✅ Workflow completed successfully!"
          if [ "$NOTIFY" = true ]; then
            send_notification "✅ Workflow Success" "$WORKFLOW: $TITLE" "Glass"
          fi
          ;;
        failure)
          echo "❌ Workflow failed!"
          if [ "$NOTIFY" = true ]; then
            send_notification "❌ Workflow Failed" "$WORKFLOW: $TITLE" "Basso"
          fi

          # Show failed jobs
          echo ""
          echo "Failed jobs:"
          gh run view "$run_id" --json jobs --jq '.jobs[] | select(.conclusion == "failure") | "  - \(.name)"'
          ;;
        cancelled)
          echo "🚫 Workflow was cancelled"
          if [ "$NOTIFY" = true ]; then
            send_notification "🚫 Workflow Cancelled" "$WORKFLOW: $TITLE"
          fi
          ;;
        *)
          echo "⚠️  Workflow completed with status: $CONCLUSION"
          if [ "$NOTIFY" = true ]; then
            send_notification "⚠️ Workflow $CONCLUSION" "$WORKFLOW: $TITLE"
          fi
          ;;
      esac

      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo ""
      echo "View details: gh run view $run_id --web"
      break
    else
      # Show progress
      printf "\r🔄 Status: %s... (checking every %ds)" "$STATUS" "$CHECK_INTERVAL"
      sleep "$CHECK_INTERVAL"
      RUN_INFO=$(get_run_status "$run_id")
    fi
  done
}

# Function to watch latest run for a workflow
watch_latest_workflow() {
  local workflow_name="$1"

  echo "Finding latest run for workflow: $workflow_name"

  LATEST_RUN=$(gh run list --workflow="$workflow_name" --limit 1 --json databaseId --jq '.[0].databaseId')

  if [ -z "$LATEST_RUN" ] || [ "$LATEST_RUN" = "null" ]; then
    echo "❌ No runs found for workflow: $workflow_name"
    exit 1
  fi

  watch_run "$LATEST_RUN"
}

# Function to show active runs and let user select
interactive_select() {
  echo "Active workflow runs:"
  echo ""

  gh run list --limit 20 --json databaseId,displayTitle,status,workflowName,createdAt --jq '.[] | select(.status != "completed")' > /tmp/gh_runs.json

  if [ ! -s /tmp/gh_runs.json ]; then
    echo "No active runs found."
    exit 0
  fi

  # Display runs with numbers
  jq -r 'to_entries | .[] | "\(.key + 1)) [\(.value.workflowName)] \(.value.displayTitle) - \(.value.status)"' /tmp/gh_runs.json

  echo ""
  read -p "Select run number to watch: " -r SELECTION

  RUN_ID=$(jq -r ".[$((SELECTION - 1))].databaseId" /tmp/gh_runs.json)

  if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
    echo "Invalid selection"
    exit 1
  fi

  watch_run "$RUN_ID"
}

# Main logic
if [ -z "$RUN_ID" ]; then
  # No run ID provided - show menu
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Workflow Monitor"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "1) Watch specific run ID"
  echo "2) Watch latest run for workflow"
  echo "3) Select from active runs"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  read -p "Select option (1-3): " -n 1 -r OPTION
  echo ""

  case $OPTION in
    1)
      read -p "Enter run ID: " RUN_ID
      watch_run "$RUN_ID"
      ;;
    2)
      gh workflow list
      echo ""
      read -p "Enter workflow name (or file): " WORKFLOW_NAME
      watch_latest_workflow "$WORKFLOW_NAME"
      ;;
    3)
      interactive_select
      ;;
    *)
      echo "Invalid option"
      exit 1
      ;;
  esac
else
  # Run ID provided as argument
  watch_run "$RUN_ID"
fi
