#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run-codex-handoff.sh --model MODEL --effort EFFORT --timeout-seconds SECONDS

Read an approved implementation prompt from stdin and run one ephemeral Codex
implementation session in the current Git worktree.

Allowed models: gpt-5.6-sol, gpt-5.6-terra
Allowed efforts: medium, high, xhigh, max
EOF
}

model=""
effort=""
timeout_seconds=""

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
[[ "$top_help" == *"--ask-for-approval"* ]] || { echo "ERROR: codex lacks --ask-for-approval" >&2; exit 69; }

for required_flag in --ephemeral --color --cd --model --sandbox --output-schema --output-last-message; do
  if [[ "$exec_help" != *"$required_flag"* ]]; then
    echo "ERROR: codex exec lacks required flag: $required_flag" >&2
    exit 69
  fi
done

prompt_file="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.prompt.XXXXXX")"
stdout_file="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.stdout.XXXXXX")"
stderr_file="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.stderr.XXXXXX")"
result_file="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.result.XXXXXX")"
timeout_marker="$(mktemp "${TMPDIR:-/tmp}/codex-handoff.timeout.XXXXXX")"
rm -f "$timeout_marker"

codex_pid=""

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

"$codex_bin" --ask-for-approval never exec \
  --ephemeral \
  --color never \
  -C "$repo_root" \
  -m "$model" \
  -c "model_reasoning_effort=\"$effort\"" \
  --sandbox workspace-write \
  --output-schema "$schema_file" \
  --output-last-message "$result_file" \
  - \
  <"$prompt_file" >"$stdout_file" 2>"$stderr_file" &
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

if [[ -f "$timeout_marker" ]]; then
  echo "ERROR: Codex timed out after ${timeout_seconds}s" >&2
  [[ ! -s "$stderr_file" ]] || tail -n 200 "$stderr_file" >&2
  exit 124
fi

if [[ $codex_rc -ne 0 ]]; then
  echo "ERROR: Codex exited with status $codex_rc" >&2
  if [[ -s "$stdout_file" ]]; then
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
  echo "ERROR: Codex completed without a structured result" >&2
  [[ ! -s "$stderr_file" ]] || tail -n 200 "$stderr_file" >&2
  exit 70
fi

cat "$result_file"
