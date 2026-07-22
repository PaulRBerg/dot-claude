# Progress Stream Reference

When `run-codex-handoff.sh` is invoked with `--progress-file PATH`, the file is a live JSONL stream: every line Codex
emits under `codex exec --json`, followed by exactly one wrapper-authored sentinel line on exit. Tail it for real-time
watching; grep it for digests and post-mortems. Pass `--result-file PATH` separately to keep the final structured result
in an artifact and leave background-task stdout empty.

## Codex events

One JSON object per line, each with a top-level `type`
([non-interactive mode docs](https://developers.openai.com/codex/noninteractive)):

| Event                                              | Meaning                                                  |
| -------------------------------------------------- | -------------------------------------------------------- |
| `thread.started`, `turn.started`                   | Session/turn lifecycle                                   |
| `turn.completed`                                   | Turn finished; carries `usage` with `output_tokens` etc. |
| `turn.failed`                                      | Turn failed; carries error details                       |
| `item.started` / `item.updated` / `item.completed` | Work items; `item.type` identifies the activity          |

Item types: `agent_message` (assistant text), `reasoning`, `command_execution` (has `command` and `status`),
`file_change`, `mcp_tool_call`, `web_search`, plus plan updates. Example:

```json
{ "type": "item.completed", "item": { "id": "item_3", "type": "agent_message", "text": "Repo contains docs and sdk." } }
```

### Intentional visibility gap

The app-server protocol documents separate `model/safetyBuffering/updated` and `model/rerouted` notifications
([turn events](https://learn.chatgpt.com/docs/app-server#turn-events)), but they are not part of the documented
`codex exec --json` event set and Codex CLI 0.144.3 does not forward them to this stream. Do not invent equivalent JSONL
events or infer a safety check from silence. A quiet period may be ordinary work or transient buffering, and an
independent server-side policy reroute may leave the responding model unknowable.

In status digests, say `no recent activity` and keep watching until the wrapper sentinel or approved timeout. Do not
cancel, retry, extend, downgrade to a suggested faster model, or relaunch because the stream is quiet; preserve normal
timeout and failure handling.

## Wrapper sentinel

The wrapper appends exactly one terminal line per run; its presence — not process state — is the completion signal:

| Sentinel                                                                | Emitted when                                                 |
| ----------------------------------------------------------------------- | ------------------------------------------------------------ |
| `{"type":"handoff.completed","elapsed_seconds":N,"output_tokens":M}`    | Success (`output_tokens` best-effort, omitted if unparsable) |
| `{"type":"handoff.failed","reason":"timeout","elapsed_seconds":N}`      | Wrapper timeout hit                                          |
| `{"type":"handoff.failed","reason":"error","rc":R,"elapsed_seconds":N}` | Codex nonzero exit or missing result                         |
| `{"type":"handoff.failed","reason":"cancelled","elapsed_seconds":N}`    | Wrapper received INT/TERM                                    |

The result JSON itself is in the path passed to `--result-file`, not in this progress file. Without `--result-file`, the
wrapper writes the result to stdout for backward compatibility.

## Wave watcher

Use one bundled watcher per wave. Pass repeated agent ID, budget-seconds, and progress-file triples:

```sh
bash scripts/watch-codex-wave.sh \
  --agent A1 1200 /tmp/A1.progress.jsonl \
  --agent A2 2400 /tmp/A2.progress.jsonl
```

Its stdout is machine-readable JSONL. `watcher.digest` reports elapsed/budget, event count, last relevant activity, and
delayed-file state. `watcher.sentinel` preserves the wrapper sentinel and reason. `watcher.settlement` supplies exact
settled counts, percentage, and ten-cell bar. A completed wave exits `0`; any failed agent sentinel settles normally and
makes the watcher exit `1` after all agents settle. Malformed progress is an invariant failure, not an agent result.
