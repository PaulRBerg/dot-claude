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


if __name__ == "__main__":
    unittest.main()
