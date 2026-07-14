#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run-codex-handoff.sh --model MODEL --effort EFFORT --timeout-seconds SECONDS [--progress-file PATH] [--result-file PATH]

Read an approved implementation prompt from stdin and run one ephemeral Codex
implementation session in the current Git worktree.

With --progress-file, Codex runs with --json and streams JSONL events to PATH;
the wrapper appends one terminal {"type":"handoff.completed"|"handoff.failed"}
sentinel line and leaves the file in place for inspection.

With --result-file, the structured result is written to PATH and stdout stays
empty so background-task interfaces do not display raw JSON.

Allowed models: gpt-5.6-sol, gpt-5.6-terra
Allowed efforts: medium, high, xhigh, max
EOF
}

model=""
effort=""
timeout_seconds=""
progress_file=""
result_output_file=""

while [[ $# -gt 0 ]]; do
  case "$1" in
  --model)
    [[ $# -ge 2 ]] || { echo "ERROR: --model requires a value" >&2; exit 64; }
    model="$2"
    shift 2
    ;;
  --model=*)
    model="${1#*=}"
    shift
    ;;
  --effort)
    [[ $# -ge 2 ]] || { echo "ERROR: --effort requires a value" >&2; exit 64; }
    effort="$2"
    shift 2
    ;;
  --effort=*)
    effort="${1#*=}"
    shift
    ;;
  --timeout-seconds)
    [[ $# -ge 2 ]] || { echo "ERROR: --timeout-seconds requires a value" >&2; exit 64; }
    timeout_seconds="$2"
    shift 2
    ;;
  --timeout-seconds=*)
    timeout_seconds="${1#*=}"
    shift
    ;;
  --progress-file)
    [[ $# -ge 2 ]] || { echo "ERROR: --progress-file requires a value" >&2; exit 64; }
    progress_file="$2"
    shift 2
    ;;
  --progress-file=*)
    progress_file="${1#*=}"
    shift
    ;;
  --result-file)
    [[ $# -ge 2 ]] || { echo "ERROR: --result-file requires a value" >&2; exit 64; }
    result_output_file="$2"
    shift 2
    ;;
  --result-file=*)
    result_output_file="${1#*=}"
    shift
    ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    echo "ERROR: unknown argument: $1" >&2
    usage >&2
    exit 64
    ;;
  esac
done

case "$model" in
gpt-5.6-sol | gpt-5.6-terra) ;;
*)
  echo "ERROR: --model must be gpt-5.6-sol or gpt-5.6-terra" >&2
  exit 64
  ;;
esac

case "$effort" in
medium | high | xhigh | max) ;;
*)
  echo "ERROR: --effort must be medium, high, xhigh, or max" >&2
  exit 64
  ;;
esac

if [[ ! "$timeout_seconds" =~ ^[1-9][0-9]*$ ]]; then
  echo "ERROR: --timeout-seconds must be a positive integer" >&2
  exit 64
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
schema_file="$script_dir/../references/result.schema.json"
[[ -f "$schema_file" ]] || { echo "ERROR: missing result schema: $schema_file" >&2; exit 66; }

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$repo_root" ]] || { echo "ERROR: run from inside a Git worktree" >&2; exit 66; }

codex_bin="$(command -v codex || true)"
[[ -n "$codex_bin" ]] || { echo "ERROR: codex not found in PATH" >&2; exit 69; }

if ! "$codex_bin" login status >/dev/null 2>&1; then
  echo "ERROR: Codex CLI is not authenticated; run 'codex login'" >&2
  exit 69
fi

top_help="$("$codex_bin" --help 2>/dev/null || true)"
exec_help="$("$codex_bin" exec --help 2>/dev/null || true)"
[[ "$top_help" == *"--dangerously-bypass-approvals-and-sandbox"* ]] || {
  echo "ERROR: codex lacks --dangerously-bypass-approvals-and-sandbox" >&2
  exit 69
}

required_flags="--ephemeral --color --cd --model --output-schema --output-last-message"
if [[ -n "$progress_file" ]]; then
  required_flags="$required_flags --json"
fi
for required_flag in $required_flags; do
  if [[ "$exec_help" != *"$required_flag"* ]]; then
    echo "ERROR: codex exec lacks required flag: $required_flag" >&2
    exit 69
  fi
done

if [[ -n "$progress_file" ]]; then
  if ! : >"$progress_file" 2>/dev/null; then
    echo "ERROR: cannot create progress file: $progress_file" >&2
    exit 66
  fi
fi

if [[ -n "$result_output_file" ]]; then
  if [[ "$result_output_file" == "$progress_file" ]]; then
    echo "ERROR: --result-file and --progress-file must be different paths" >&2
    exit 64
  fi
  if ! : >"$result_output_file" 2>/dev/null; then
    echo "ERROR: cannot create result file: $result_output_file" >&2
    exit 66
  fi
fi

prompt_file="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.prompt.XXXXXX")"
stdout_file="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.stdout.XXXXXX")"
stderr_file="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.stderr.XXXXXX")"
result_file="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.result.XXXXXX")"
timeout_marker="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.timeout.XXXXXX")"
rm -f "$timeout_marker"

codex_pid=""
started_at=""
sentinel_done=0

# Append exactly one terminal sentinel line to the progress file so watchers
# never have to rely on process state to detect completion.
emit_sentinel() {
  if [[ -z "$progress_file" || $sentinel_done -eq 1 ]]; then
    return 0
  fi
  sentinel_done=1
  printf '%s\n' "$1" >>"$progress_file" 2>/dev/null || true
}

elapsed_now() {
  if [[ -n "$started_at" ]]; then
    printf '%s' $((SECONDS - started_at))
  else
    printf '0'
  fi
}

report_elapsed() {
  echo "codex-handoff: elapsed=$(elapsed_now)s" >&2
}

# Surface what Codex was doing when it died: final messages and failures from
# the JSONL stream are the only forensics available after a kill.
report_last_activity() {
  if [[ -n "$progress_file" && -s "$progress_file" ]]; then
    echo "--- Codex last activity (from progress file) ---" >&2
    grep -E '"type":"(turn\.failed|error|agent_message)"' "$progress_file" 2>/dev/null | tail -n 5 >&2 || true
  fi
}

cleanup() {
  if [[ -n "$codex_pid" ]] && kill -0 "$codex_pid" >/dev/null 2>&1; then
    kill -TERM "$codex_pid" >/dev/null 2>&1 || true
    wait "$codex_pid" >/dev/null 2>&1 || true
  fi
  rm -f "$prompt_file" "$stdout_file" "$stderr_file" "$result_file" "$timeout_marker"
}

forward_signal() {
  signal="$1"
  if [[ -n "$codex_pid" ]]; then
    kill "-$signal" "$codex_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "$started_at" ]]; then
    emit_sentinel "{\"type\":\"handoff.failed\",\"reason\":\"cancelled\",\"elapsed_seconds\":$(elapsed_now)}"
    report_elapsed
  fi
  case "$signal" in
  INT) exit 130 ;;
  TERM) exit 143 ;;
  esac
}

trap cleanup EXIT
trap 'forward_signal INT' INT
trap 'forward_signal TERM' TERM

cat >"$prompt_file"
if [[ ! -s "$prompt_file" ]]; then
  echo "ERROR: empty prompt; provide the approved implementation brief on stdin" >&2
  exit 64
fi

codex_args=(--dangerously-bypass-approvals-and-sandbox exec
  --ephemeral
  --color never
  -C "$repo_root"
  -m "$model"
  -c "model_reasoning_effort=\"$effort\""
  --output-schema "$schema_file"
  --output-last-message "$result_file")
codex_stdout="$stdout_file"
if [[ -n "$progress_file" ]]; then
  codex_args+=(--json)
  codex_stdout="$progress_file"
fi
codex_args+=(-)

"$codex_bin" "${codex_args[@]}" \
  <"$prompt_file" >"$codex_stdout" 2>"$stderr_file" &
codex_pid=$!

started_at=$SECONDS
timed_out=0
while kill -0 "$codex_pid" >/dev/null 2>&1; do
  if ((SECONDS - started_at >= timeout_seconds)); then
    timed_out=1
    : >"$timeout_marker"
    kill -TERM "$codex_pid" >/dev/null 2>&1 || true
    break
  fi
  sleep 0.2
done

if [[ $timed_out -eq 1 ]]; then
  grace_started_at=$SECONDS
  while kill -0 "$codex_pid" >/dev/null 2>&1 && ((SECONDS - grace_started_at < 5)); do
    sleep 0.2
  done
  kill -KILL "$codex_pid" >/dev/null 2>&1 || true
fi

set +e
wait "$codex_pid"
codex_rc=$?
set -e
codex_pid=""

elapsed=$(elapsed_now)

if [[ -f "$timeout_marker" ]]; then
  emit_sentinel "{\"type\":\"handoff.failed\",\"reason\":\"timeout\",\"elapsed_seconds\":$elapsed}"
  report_elapsed
  echo "ERROR: Codex timed out after ${timeout_seconds}s" >&2
  report_last_activity
  [[ ! -s "$stderr_file" ]] || tail -n 200 "$stderr_file" >&2
  exit 124
fi

if [[ $codex_rc -ne 0 ]]; then
  emit_sentinel "{\"type\":\"handoff.failed\",\"reason\":\"error\",\"rc\":$codex_rc,\"elapsed_seconds\":$elapsed}"
  report_elapsed
  echo "ERROR: Codex exited with status $codex_rc" >&2
  report_last_activity
  if [[ -z "$progress_file" && -s "$stdout_file" ]]; then
    echo "--- Codex stdout (last 200 lines) ---" >&2
    tail -n 200 "$stdout_file" >&2
  fi
  if [[ -s "$stderr_file" ]]; then
    echo "--- Codex stderr (last 200 lines) ---" >&2
    tail -n 200 "$stderr_file" >&2
  fi
  exit "$codex_rc"
fi

if [[ ! -s "$result_file" ]]; then
  emit_sentinel "{\"type\":\"handoff.failed\",\"reason\":\"error\",\"rc\":70,\"elapsed_seconds\":$elapsed}"
  report_elapsed
  echo "ERROR: Codex completed without a structured result" >&2
  report_last_activity
  [[ ! -s "$stderr_file" ]] || tail -n 200 "$stderr_file" >&2
  exit 70
fi

if [[ -n "$result_output_file" ]]; then
  if ! cp "$result_file" "$result_output_file"; then
    emit_sentinel "{\"type\":\"handoff.failed\",\"reason\":\"error\",\"rc\":74,\"elapsed_seconds\":$elapsed}"
    report_elapsed
    echo "ERROR: cannot write result file: $result_output_file" >&2
    exit 74
  fi
else
  cat "$result_file"
  # Codex writes the result without a trailing newline; add one so the JSON
  # stays on its own line when stdout and stderr share a terminal.
  [[ -z "$(tail -c 1 "$result_file")" ]] || echo
fi

output_tokens=""
if [[ -n "$progress_file" ]]; then
  output_tokens="$(grep -o '"output_tokens":[0-9]*' "$progress_file" 2>/dev/null |
    cut -d: -f2 | awk '{ sum += $1 } END { if (NR > 0) print sum }' || true)"
fi
if [[ -n "$output_tokens" ]]; then
  emit_sentinel "{\"type\":\"handoff.completed\",\"elapsed_seconds\":$elapsed,\"output_tokens\":$output_tokens}"
else
  emit_sentinel "{\"type\":\"handoff.completed\",\"elapsed_seconds\":$elapsed}"
fi
report_elapsed
