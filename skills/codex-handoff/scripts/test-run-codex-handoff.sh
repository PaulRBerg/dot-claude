#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
runner="$script_dir/run-codex-handoff.sh"
tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/codex-handoff-test.XXXXXX")"
fake_bin="$tmp_dir/bin"
repo="$tmp_dir/repo with spaces"
repo_root=""
args_file="$tmp_dir/args"
prompt_file="$tmp_dir/prompt"
stdout_file="$tmp_dir/stdout"
stderr_file="$tmp_dir/stderr"

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
  print_flag --ask-for-approval
  exit 0
fi

if [[ "${1:-}" == "exec" && "${2:-}" == "--help" ]]; then
  for flag in --ephemeral --color --cd --model --sandbox --output-schema --output-last-message; do
    print_flag "$flag"
  done
  exit 0
fi

: >"$FAKE_ARGS_FILE"
for arg in "$@"; do
  printf '%s\n' "$arg" >>"$FAKE_ARGS_FILE"
done
cat >"$FAKE_PROMPT_FILE"

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

assert_arg --ask-for-approval
assert_arg never
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
assert_arg --sandbox
assert_arg workspace-write
assert_arg --output-schema
assert_arg --output-last-message
assert_arg -
grep -Fxq -- '--search' "$args_file" && fail "runner enabled search"
grep -Fxq -- '--ignore-user-config' "$args_file" && fail "runner ignored user config"
[[ "$(cat "$prompt_file")" == 'approved implementation' ]] || fail "prompt was not forwarded exactly"

ask_line="$(grep -nFx -- '--ask-for-approval' "$args_file" | cut -d: -f1)"
exec_line="$(grep -nFx -- 'exec' "$args_file" | cut -d: -f1)"
[[ $ask_line -lt $exec_line ]] || fail "--ask-for-approval must precede exec"

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
  expect_failure 69 'lacks --ask-for-approval' env PATH="$fake_path" FAKE_HELP_MISSING=--ask-for-approval \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5
  expect_failure 69 'lacks required flag: --output-schema' env PATH="$fake_path" FAKE_HELP_MISSING=--output-schema \
    "$runner" --model gpt-5.6-sol --effort high --timeout-seconds 5
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

echo "codex-handoff runner tests passed"
