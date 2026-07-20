#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
runner="$script_dir/run-codex-handoff.sh"
schema="$script_dir/../references/result.schema.json"
tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/codex-handoff-test.XXXXXX")"
fake_bin="$tmp_dir/bin"
repo="$tmp_dir/repo with spaces"
repo_root=""
args_file="$tmp_dir/args"
prompt_file="$tmp_dir/prompt"
stdout_file="$tmp_dir/stdout"
stderr_file="$tmp_dir/stderr"
result_artifact="$tmp_dir/result.json"

cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_file_contains() {
  needle="$1"
  file="$2"
  grep -Fq -- "$needle" "$file" || fail "expected '$needle' in $file"
}

assert_arg() {
  needle="$1"
  grep -Fxq -- "$needle" "$args_file" || fail "missing argument: $needle"
}

grep -Fq -- '"uniqueItems"' "$schema" && fail "result schema uses unsupported uniqueItems"

expect_failure() {
  expected_rc="$1"
  expected_text="$2"
  shift 2

  set +e
  printf '%s\n' 'approved implementation' | "$@" >"$stdout_file" 2>"$stderr_file"
  actual_rc=$?
  set -e

  [[ $actual_rc -eq $expected_rc ]] || fail "expected exit $expected_rc, got $actual_rc"
  assert_file_contains "$expected_text" "$stderr_file"
}

mkdir -p "$fake_bin" "$repo"
git -C "$repo" init -q
repo_root="$(git -C "$repo" rev-parse --show-toplevel)"

cat >"$fake_bin/codex" <<'FAKE_CODEX'
#!/usr/bin/env bash
set -euo pipefail

print_flag() {
  flag="$1"
  [[ "${FAKE_HELP_MISSING:-}" == "$flag" ]] || printf '%s\n' "$flag"
}

if [[ "${1:-}" == "login" && "${2:-}" == "status" ]]; then
  [[ "${FAKE_AUTH_FAIL:-0}" != "1" ]] || exit 1
  echo "Logged in"
  exit 0
fi

if [[ "${1:-}" == "--help" ]]; then
  print_flag --dangerously-bypass-approvals-and-sandbox
  exit 0
fi

if [[ "${1:-}" == "exec" && "${2:-}" == "--help" ]]; then
  for flag in --ephemeral --color --cd --model --output-schema --output-last-message --json; do
    print_flag "$flag"
  done
  exit 0
fi

: >"$FAKE_ARGS_FILE"
for arg in "$@"; do
  printf '%s\n' "$arg" >>"$FAKE_ARGS_FILE"
done
cat >"$FAKE_PROMPT_FILE"

emit_json=0
for arg in "$@"; do
  if [[ "$arg" == "--json" ]]; then
    emit_json=1
  fi
done
if [[ $emit_json -eq 1 ]]; then
  cat <<'EVENTS'
{"type":"thread.started","thread_id":"thread_1"}
{"type":"turn.started"}
{"type":"item.completed","item":{"id":"item_1","type":"command_execution","command":"echo hi","status":"completed"}}
{"type":"item.completed","item":{"id":"item_2","type":"agent_message","text":"implementation done"}}
{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":50,"output_tokens":42}}
EVENTS
fi

if [[ -n "${FAKE_SLEEP:-}" ]]; then
  sleep "$FAKE_SLEEP"
fi

if [[ -n "${FAKE_EXIT:-}" ]]; then
  echo "simulated codex failure" >&2
  exit "$FAKE_EXIT"
fi

if [[ "${FAKE_NO_RESULT:-0}" == "1" ]]; then
  exit 0
fi

result_file=""
while [[ $# -gt 0 ]]; do
  if [[ "$1" == "--output-last-message" ]]; then
    result_file="$2"
    break
  fi
  shift
done

[[ -n "$result_file" ]] || { echo "missing result file" >&2; exit 2; }
if [[ -n "${FAKE_RESULT:-}" ]]; then
  printf '%s\n' "$FAKE_RESULT" >"$result_file"
else
  cat >"$result_file" <<'RESULT'
{"status":"completed","summary":"done","changed_files":[],"verification":[],"residual_risks":[],"blockers":[]}
RESULT
fi
FAKE_CODEX
chmod +x "$fake_bin/codex"

export FAKE_ARGS_FILE="$args_file"
export FAKE_PROMPT_FILE="$prompt_file"
fake_path="$fake_bin:$PATH"
expected_result='{"status":"completed","summary":"done","changed_files":[],"verification":[],"residual_risks":[],"blockers":[]}'

for model in gpt-5.6-sol gpt-5.6-terra; do
  for effort in medium high xhigh max; do
    actual_result="$(
      cd "$repo"
      printf '%s\n' 'approved implementation' | PATH="$fake_path" "$runner" \
        --model "$model" \
        --effort "$effort" \
        --timeout-seconds 5
    )"
    [[ "$actual_result" == "$expected_result" ]] || fail "unexpected result for $model/$effort"
  done
done

assert_arg --dangerously-bypass-approvals-and-sandbox
assert_arg exec
assert_arg --ephemeral
assert_arg --color
assert_arg never
assert_arg -C
assert_arg "$repo_root"
assert_arg -m
assert_arg gpt-5.6-terra
assert_arg -c
assert_arg 'model_reasoning_effort="max"'
assert_arg 'service_tier="default"'
assert_arg --output-schema
assert_arg --output-last-message
assert_arg -
grep -Fxq -- '--ask-for-approval' "$args_file" && fail "runner configured a separate approval policy"
grep -Fxq -- '--sandbox' "$args_file" && fail "runner configured a sandbox alongside dangerous bypass"
grep -Fxq -- '--search' "$args_file" && fail "runner enabled search"
grep -Fxq -- '--ignore-user-config' "$args_file" && fail "runner ignored user config"
grep -Fxq -- '--json' "$args_file" && fail "runner passed --json without --progress-file"
[[ "$(cat "$prompt_file")" == 'approved implementation' ]] || fail "prompt was not forwarded exactly"

# Artifact mode keeps raw result JSON out of background-task output.
(
  cd "$repo"
  printf '%s\n' 'approved implementation' | PATH="$fake_path" "$runner" \
    --model gpt-5.6-sol --effort high --timeout-seconds 5 \
    --result-file "$result_artifact"
) >"$stdout_file" 2>"$stderr_file"
[[ ! -s "$stdout_file" ]] || fail "artifact mode must keep stdout empty"
[[ "$(cat "$result_artifact")" == "$expected_result" ]] || fail "artifact mode wrote an unexpected result"
assert_file_contains 'codex-handoff: elapsed=' "$stderr_file"

bypass_line="$(grep -nFx -- '--dangerously-bypass-approvals-and-sandbox' "$args_file" | cut -d: -f1)"
exec_line="$(grep -nFx -- 'exec' "$args_file" | cut -d: -f1)"
[[ $bypass_line -lt $exec_line ]] || fail "--dangerously-bypass-approvals-and-sandbox must precede exec"

(
  cd "$repo"
  expect_failure 64 'must be gpt-5.6-sol or gpt-5.6-terra' env PATH="$fake_path" \
    "$runner" --model gpt-5.6-luna --effort high --timeout-seconds 5
  expect_failure 64 'must be medium, high, xhigh, or max' env PATH="$fake_path" \
    "$runner" --model gpt-5.6-sol --effort low --timeout-seconds 5
  expect_failure 64 'must be medium, high, xhigh, or max' env PATH="$fake_path" \
    "$runner" --model gpt-5.6-sol --effort ultra --timeout-seconds 5
  expect_failure 64 'must be a positive integer' env PATH="$fake_path" \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 0
  expect_failure 69 'not authenticated' env PATH="$fake_path" FAKE_AUTH_FAIL=1 \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5
  expect_failure 69 'lacks --dangerously-bypass-approvals-and-sandbox' env PATH="$fake_path" \
    FAKE_HELP_MISSING=--dangerously-bypass-approvals-and-sandbox \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5
  expect_failure 69 'lacks required flag: --output-schema' env PATH="$fake_path" FAKE_HELP_MISSING=--output-schema \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5
  expect_failure 64 'must be different paths' env PATH="$fake_path" \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5 \
    --progress-file "$tmp_dir/same-output" --result-file "$tmp_dir/same-output"
  expect_failure 66 'cannot create result file' env PATH="$fake_path" \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5 \
    --result-file "$tmp_dir/missing-result-dir/result.json"
  expect_failure 17 'simulated codex failure' env PATH="$fake_path" FAKE_EXIT=17 \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5
  expect_failure 70 'without a structured result' env PATH="$fake_path" FAKE_NO_RESULT=1 \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5
  expect_failure 124 'timed out after 1s' env PATH="$fake_path" FAKE_SLEEP=3 \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 1
)

set +e
(
  cd "$repo"
  PATH="$fake_path" "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5 </dev/null
) >"$stdout_file" 2>"$stderr_file"
empty_rc=$?
set -e
[[ $empty_rc -eq 64 ]] || fail "empty prompt should exit 64"
assert_file_contains 'empty prompt' "$stderr_file"

mkdir -p "$tmp_dir/non-git"
set +e
(
  cd "$tmp_dir/non-git"
  printf '%s\n' 'approved implementation' | PATH="$fake_path" "$runner" \
    --model gpt-5.6-sol --effort high --timeout-seconds 5
) >"$stdout_file" 2>"$stderr_file"
non_git_rc=$?
set -e
[[ $non_git_rc -eq 66 ]] || fail "non-Git directory should exit 66"
assert_file_contains 'inside a Git worktree' "$stderr_file"

set +e
(
  cd "$repo"
  printf '%s\n' 'approved implementation' | PATH="/usr/bin:/bin" "$runner" \
    --model gpt-5.6-sol --effort high --timeout-seconds 5
) >"$stdout_file" 2>"$stderr_file"
missing_codex_rc=$?
set -e
[[ $missing_codex_rc -eq 69 ]] || fail "missing codex should exit 69"
assert_file_contains 'codex not found' "$stderr_file"

# Progress plus artifact mode streams events, appends one sentinel, and keeps stdout empty.
success_progress="$tmp_dir/success.progress.jsonl"
(
  cd "$repo"
  printf '%s\n' 'approved implementation' | PATH="$fake_path" "$runner" \
    --model gpt-5.6-terra --effort high --timeout-seconds 5 \
    --progress-file "$success_progress" --result-file "$result_artifact"
) >"$stdout_file" 2>"$stderr_file"
[[ ! -s "$stdout_file" ]] || fail "progress plus artifact mode must keep stdout empty"
[[ "$(cat "$result_artifact")" == "$expected_result" ]] || fail "progress plus artifact mode lost the result"
assert_arg --json
assert_file_contains '"type":"thread.started"' "$success_progress"
assert_file_contains '"type":"turn.completed"' "$success_progress"
assert_file_contains 'codex-handoff: elapsed=' "$stderr_file"
sentinel_line="$(grep '"type":"handoff.completed"' "$success_progress")"
case "$sentinel_line" in
*'"elapsed_seconds":'*'"output_tokens":42'*) ;;
*) fail "sentinel missing elapsed_seconds/output_tokens: $sentinel_line" ;;
esac
sentinel_count="$(grep -c '"type":"handoff\.' "$success_progress")"
[[ "$sentinel_count" == "1" ]] || fail "expected exactly one sentinel, got $sentinel_count"

# Progress mode: every failure path appends exactly one handoff.failed sentinel.
error_progress="$tmp_dir/error.progress.jsonl"
timeout_progress="$tmp_dir/timeout.progress.jsonl"
noresult_progress="$tmp_dir/noresult.progress.jsonl"
(
  cd "$repo"
  expect_failure 17 'simulated codex failure' env PATH="$fake_path" FAKE_EXIT=17 \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5 --progress-file "$error_progress"
  assert_file_contains '--- Codex last activity' "$stderr_file"
  assert_file_contains 'implementation done' "$stderr_file"
  assert_file_contains 'codex-handoff: elapsed=' "$stderr_file"
  grep -Fq -- '--- Codex stdout' "$stderr_file" && fail "progress mode should not tail codex stdout"
  expect_failure 124 'timed out after 1s' env PATH="$fake_path" FAKE_SLEEP=3 \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 1 --progress-file "$timeout_progress"
  expect_failure 70 'without a structured result' env PATH="$fake_path" FAKE_NO_RESULT=1 \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5 --progress-file "$noresult_progress"
)
assert_file_contains '"type":"handoff.failed","reason":"error","rc":17' "$error_progress"
assert_file_contains '"type":"handoff.failed","reason":"timeout"' "$timeout_progress"
assert_file_contains '"type":"handoff.failed","reason":"error","rc":70' "$noresult_progress"
for progress in "$error_progress" "$timeout_progress" "$noresult_progress"; do
  sentinel_count="$(grep -c '"type":"handoff\.' "$progress")"
  [[ "$sentinel_count" == "1" ]] || fail "expected exactly one sentinel in $progress, got $sentinel_count"
done

# --json support is required only when --progress-file is requested.
(
  cd "$repo"
  json_gate_result="$(printf '%s\n' 'approved implementation' | PATH="$fake_path" FAKE_HELP_MISSING=--json \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5)"
  [[ "$json_gate_result" == "$expected_result" ]] || fail "missing --json help must not fail without --progress-file"
  expect_failure 69 'lacks required flag: --json' env PATH="$fake_path" FAKE_HELP_MISSING=--json \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5 \
    --progress-file "$tmp_dir/gate.progress.jsonl"
  expect_failure 66 'cannot create progress file' env PATH="$fake_path" \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5 \
    --progress-file "$tmp_dir/missing-dir/progress.jsonl"
)

# Cancellation (TERM, e.g. the user stopping the background task) still writes a sentinel.
cancel_progress="$tmp_dir/cancel.progress.jsonl"
(
  cd "$repo"
  printf '%s\n' 'approved implementation' | PATH="$fake_path" FAKE_SLEEP=10 \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 30 \
    --progress-file "$cancel_progress" >"$stdout_file" 2>"$stderr_file" &
  runner_pid=$!
  sleep 1
  kill -TERM "$runner_pid"
  set +e
  wait "$runner_pid"
  cancel_rc=$?
  set -e
  [[ $cancel_rc -eq 143 ]] || fail "expected exit 143 on TERM, got $cancel_rc"
)
assert_file_contains '"type":"handoff.failed","reason":"cancelled"' "$cancel_progress"
sentinel_count="$(grep -c '"type":"handoff\.' "$cancel_progress")"
[[ "$sentinel_count" == "1" ]] || fail "expected exactly one sentinel after cancel, got $sentinel_count"

echo "codex-handoff runner tests passed"
