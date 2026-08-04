from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("watch-codex-wave.sh")


class WatchCodexWaveTests(unittest.TestCase):
    def test_multiple_agents_digest_delayed_creation_and_exact_settlement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "a.progress.jsonl"
            second = root / "b.progress.jsonl"

            def write_progress() -> None:
                time.sleep(0.08)
                first.write_text(
                    '{"type":"item.completed","item":{"type":"command_execution","command":"just test","status":"completed"}}\n'
                    '{"type":"handoff.completed","elapsed_seconds":1}\n'
                )
                time.sleep(0.08)
                second.write_text(
                    '{"type":"item.completed","item":{"type":"file_change","status":"completed"}}\n'
                    '{"type":"handoff.failed","reason":"timeout","elapsed_seconds":2}\n'
                )

            thread = threading.Thread(target=write_progress)
            thread.start()
            result = subprocess.run(
                ["bash", str(SCRIPT), "--agent", "A1", "10", str(first), "--agent", "A2", "20", str(second),
                 "--digest-seconds", "0.04", "--poll-seconds", "0.01"],
                text=True,
                capture_output=True,
                timeout=5,
            )
            thread.join()
            self.assertEqual(result.returncode, 1, result.stderr)
            records = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertTrue(any(record["type"] == "watcher.digest" and record["noRecentActivity"] for record in records))
            sentinels = [record for record in records if record["type"] == "watcher.sentinel"]
            self.assertEqual([record["agentId"] for record in sentinels], ["A1", "A2"])
            self.assertEqual(sentinels[1]["reason"], "timeout")
            settlements = [record for record in records if record["type"] == "watcher.settlement"]
            self.assertEqual(settlements[0]["settledPercentage"], 50)
            self.assertEqual(settlements[0]["bar"], "█████░░░░░")
            self.assertEqual(settlements[-1]["settledPercentage"], 100)
            self.assertEqual(settlements[-1]["bar"], "██████████")

    def test_error_and_cancellation_sentinels_settle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for reason in ("error", "cancelled"):
                progress = root / f"{reason}.jsonl"
                progress.write_text(json.dumps({"type": "handoff.failed", "reason": reason}) + "\n")
                result = subprocess.run(
                    ["bash", str(SCRIPT), "--agent", reason, "2", str(progress), "--poll-seconds", "0.01"],
                    text=True,
                    capture_output=True,
                    timeout=2,
                )
                self.assertEqual(result.returncode, 1)
                records = [json.loads(line) for line in result.stdout.splitlines()]
                self.assertEqual(records[0]["reason"], reason)
                self.assertEqual(records[-1]["settled"], 1)

    def test_no_sentinel_backstop_settles_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "missing.progress.jsonl"
            result = subprocess.run(
                ["bash", str(SCRIPT), "--agent", "A1", "0.03", str(progress),
                 "--no-sentinel-grace-seconds", "0.02", "--poll-seconds", "0.01"],
                text=True,
                capture_output=True,
                timeout=2,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            records = [json.loads(line) for line in result.stdout.splitlines()]
            sentinel = next(record for record in records if record["type"] == "watcher.sentinel")
            self.assertEqual(sentinel["status"], "failed")
            self.assertEqual(sentinel["reason"], "no-sentinel")
            self.assertEqual(sentinel["sentinel"], {"type": "handoff.failed", "reason": "no-sentinel"})
            self.assertEqual(records[-1]["type"], "watcher.settlement")
            self.assertEqual(records[-1]["settled"], 1)

    def test_late_sentinel_after_backstop_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stalled = root / "stalled.progress.jsonl"
            healthy = root / "healthy.progress.jsonl"
            stalled.write_text("")
            healthy.write_text("")

            def write_progress() -> None:
                time.sleep(0.15)
                with stalled.open("a") as handle:
                    handle.write('{"type":"handoff.completed","elapsed_seconds":1}\n')
                time.sleep(0.15)
                with healthy.open("a") as handle:
                    handle.write('{"type":"handoff.completed","elapsed_seconds":2}\n')

            thread = threading.Thread(target=write_progress)
            thread.start()
            result = subprocess.run(
                ["bash", str(SCRIPT), "--agent", "A1", "0.03", str(stalled), "--agent", "A2", "2", str(healthy),
                 "--no-sentinel-grace-seconds", "0.02", "--poll-seconds", "0.01"],
                text=True,
                capture_output=True,
                timeout=5,
            )
            thread.join()
            self.assertEqual(result.returncode, 1, result.stderr)
            records = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertFalse(any(record["type"] == "watcher.failed" for record in records))
            sentinels = [record for record in records if record["type"] == "watcher.sentinel"]
            self.assertEqual([record["agentId"] for record in sentinels], ["A1", "A2"])
            self.assertEqual(sentinels[0]["reason"], "no-sentinel")
            self.assertEqual(sentinels[1]["status"], "completed")
            self.assertEqual(records[-1]["settled"], 2)

    def test_message_and_reasoning_completions_are_activity(self) -> None:
        for item_type in ("agent_message", "reasoning"):
            with self.subTest(item_type=item_type), tempfile.TemporaryDirectory() as directory:
                progress = Path(directory) / f"{item_type}.progress.jsonl"
                progress.write_text(json.dumps({"type": "item.completed", "item": {"type": item_type}}) + "\n")

                def finish() -> None:
                    time.sleep(0.08)
                    with progress.open("a") as handle:
                        handle.write('{"type":"handoff.completed"}\n')

                thread = threading.Thread(target=finish)
                thread.start()
                result = subprocess.run(
                    ["bash", str(SCRIPT), "--agent", "A1", "2", str(progress),
                     "--digest-seconds", "0.02", "--poll-seconds", "0.01"],
                    text=True,
                    capture_output=True,
                    timeout=2,
                )
                thread.join()
                self.assertEqual(result.returncode, 0, result.stderr)
                records = [json.loads(line) for line in result.stdout.splitlines()]
                digest = next(record for record in records if record["type"] == "watcher.digest")
                self.assertFalse(digest["noRecentActivity"])
                self.assertEqual(digest["lastActivity"], {"type": item_type})

    def test_invariant_exits_emit_watcher_failed(self) -> None:
        cases = {
            "malformed-progress": "{\n",
            "non-object-progress": "[]\n",
            "duplicate-sentinel": '{"type":"handoff.completed"}\n{"type":"handoff.failed"}\n',
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unreadable = root / "unreadable"
            unreadable.mkdir()
            for reason, content in cases.items():
                with self.subTest(reason=reason):
                    progress = root / f"{reason}.jsonl"
                    progress.write_text(content)
                    result = subprocess.run(
                        ["bash", str(SCRIPT), "--agent", "A1", "2", str(progress), "--poll-seconds", "0.01"],
                        text=True,
                        capture_output=True,
                        timeout=2,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    records = [json.loads(line) for line in result.stdout.splitlines()]
                    failure = next(record for record in records if record["type"] == "watcher.failed")
                    self.assertEqual(failure["agentId"], "A1")
                    self.assertEqual(failure["reason"], reason)
                    self.assertIn("elapsedSeconds", failure)

            result = subprocess.run(
                ["bash", str(SCRIPT), "--agent", "A1", "2", str(unreadable), "--poll-seconds", "0.01"],
                text=True,
                capture_output=True,
                timeout=2,
            )
            self.assertNotEqual(result.returncode, 0)
            records = [json.loads(line) for line in result.stdout.splitlines()]
            failure = next(record for record in records if record["type"] == "watcher.failed")
            self.assertEqual(failure["agentId"], "A1")
            self.assertEqual(failure["reason"], "unreadable-progress")
            self.assertIn("elapsedSeconds", failure)


if __name__ == "__main__":
    unittest.main()
