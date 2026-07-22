#!/bin/bash
# Watch one Codex handoff wave and emit machine-readable JSONL records.

set -euo pipefail

exec python3 - "$@" <<'PY'
from __future__ import annotations

import json
import math
import signal
import sys
import time
from pathlib import Path


def fail(message: str, code: int = 64) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def emit(record: dict) -> None:
    print(json.dumps(record, separators=(",", ":"), sort_keys=True), flush=True)


agents: list[dict] = []
digest_seconds = 300.0
poll_seconds = 1.0
arguments = sys.argv[1:]
index = 0
while index < len(arguments):
    argument = arguments[index]
    if argument == "--agent":
        if index + 3 >= len(arguments):
            fail("--agent requires ID BUDGET_SECONDS PROGRESS_FILE")
        agent_id, raw_budget, raw_path = arguments[index + 1 : index + 4]
        try:
            budget = float(raw_budget)
        except ValueError:
            fail(f"invalid budget for {agent_id}: {raw_budget}")
        if not agent_id or budget <= 0:
            fail("agent ID must be non-empty and budget must be positive")
        agents.append(
            {
                "id": agent_id,
                "budget": budget,
                "path": Path(raw_path),
                "offset": 0,
                "partial": "",
                "events": 0,
                "lastActivity": None,
                "settled": False,
                "sentinel": None,
            }
        )
        index += 4
    elif argument in {"--digest-seconds", "--poll-seconds"}:
        if index + 1 >= len(arguments):
            fail(f"{argument} requires a value")
        try:
            value = float(arguments[index + 1])
        except ValueError:
            fail(f"invalid value for {argument}: {arguments[index + 1]}")
        if value <= 0:
            fail(f"{argument} must be positive")
        if argument == "--digest-seconds":
            digest_seconds = value
        else:
            poll_seconds = value
        index += 2
    else:
        fail(f"unknown argument: {argument}")

if not agents:
    fail("at least one --agent triple is required")
ids = [agent["id"] for agent in agents]
if len(ids) != len(set(ids)):
    fail("agent IDs must be unique")
paths = [str(agent["path"].resolve()) for agent in agents]
if len(paths) != len(set(paths)):
    fail("progress files must be unique")

started = time.monotonic()


def elapsed() -> int:
    return math.floor(time.monotonic() - started)


def settlement() -> None:
    settled = sum(agent["settled"] for agent in agents)
    total = len(agents)
    filled = min(10, math.floor(10 * settled / total + 0.5))
    percentage = math.floor(100 * settled / total + 0.5)
    emit(
        {
            "type": "watcher.settlement",
            "elapsedSeconds": elapsed(),
            "settled": settled,
            "total": total,
            "settledPercentage": percentage,
            "bar": "█" * filled + "░" * (10 - filled),
        }
    )


def cancel(_signum, _frame) -> None:
    emit({"type": "watcher.cancelled", "elapsedSeconds": elapsed(), "settled": sum(agent["settled"] for agent in agents), "total": len(agents)})
    raise SystemExit(143)


signal.signal(signal.SIGTERM, cancel)
signal.signal(signal.SIGINT, cancel)


def process_line(agent: dict, line: str) -> None:
    if not line.strip():
        return
    try:
        event = json.loads(line)
    except json.JSONDecodeError as exc:
        emit({"type": "watcher.failed", "agentId": agent["id"], "reason": "malformed-progress", "line": line, "elapsedSeconds": elapsed()})
        fail(f"{agent['id']} progress contains malformed JSON: {exc}", 65)
    if not isinstance(event, dict):
        fail(f"{agent['id']} progress event must be an object", 65)
    event_type = event.get("type")
    if event_type in {"handoff.completed", "handoff.failed"}:
        if agent["settled"]:
            fail(f"{agent['id']} progress contains multiple sentinels", 65)
        agent["settled"] = True
        agent["sentinel"] = event
        emit(
            {
                "type": "watcher.sentinel",
                "agentId": agent["id"],
                "status": "completed" if event_type == "handoff.completed" else "failed",
                "reason": event.get("reason"),
                "elapsedSeconds": elapsed(),
                "budgetSeconds": agent["budget"],
                "eventCount": agent["events"],
                "sentinel": event,
            }
        )
        settlement()
        return
    agent["events"] += 1
    item = event.get("item") if isinstance(event.get("item"), dict) else {}
    if item.get("type") in {"command_execution", "file_change"}:
        agent["lastActivity"] = {
            "type": item["type"],
            "command": item.get("command"),
            "status": item.get("status"),
        }


def read_new(agent: dict) -> None:
    path = agent["path"]
    if not path.exists():
        return
    try:
        with path.open("r", encoding="utf-8") as handle:
            handle.seek(agent["offset"])
            chunk = handle.read()
            agent["offset"] = handle.tell()
    except OSError as exc:
        fail(f"cannot read {path}: {exc}", 66)
    text = agent["partial"] + chunk
    lines = text.split("\n")
    agent["partial"] = lines.pop()
    for line in lines:
        process_line(agent, line)


next_digest = started + digest_seconds
while not all(agent["settled"] for agent in agents):
    for agent in agents:
        read_new(agent)
    now = time.monotonic()
    if now >= next_digest and not all(agent["settled"] for agent in agents):
        for agent in agents:
            if agent["settled"]:
                continue
            emit(
                {
                    "type": "watcher.digest",
                    "agentId": agent["id"],
                    "elapsedSeconds": elapsed(),
                    "budgetSeconds": agent["budget"],
                    "eventCount": agent["events"],
                    "lastActivity": agent["lastActivity"],
                    "noRecentActivity": agent["lastActivity"] is None,
                    "progressFileExists": agent["path"].exists(),
                }
            )
        while next_digest <= now:
            next_digest += digest_seconds
    if not all(agent["settled"] for agent in agents):
        time.sleep(poll_seconds)

raise SystemExit(1 if any(agent["sentinel"].get("type") == "handoff.failed" for agent in agents) else 0)
PY
