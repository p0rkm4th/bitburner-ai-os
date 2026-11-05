import json
import tempfile
import unittest
from pathlib import Path

from app.server import MeasuredOllamaClient


class FakeResponse:
    model = "qwen3.8:27b"
    prompt_eval_count = 123
    eval_count = 45
    total_duration = 1_200_000_000
    load_duration = 200_000_000
    prompt_eval_duration = 300_000_000
    eval_duration = 600_000_000
    done_reason = "stop"


class FakeClient:
    async def chat(self, **kwargs):
        return FakeResponse()


class BenchmarkMetricsTests(unittest.IsolatedAsyncioTestCase):
    async def test_metrics_capture_counts_without_prompt_or_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metrics.jsonl"
            client = MeasuredOllamaClient(FakeClient(), str(path))
            await client.chat(model="qwen3.8:27b", messages=[{"content": "private prompt"}])
            row = json.loads(path.read_text())
            self.assertEqual(row["prompt_eval_count"], 123)
            self.assertEqual(row["eval_count"], 45)
            self.assertEqual(row["model"], "qwen3.8:27b")
            self.assertNotIn("private prompt", json.dumps(row))
            self.assertNotIn("messages", row)

    async def test_inference_failure_is_recorded_and_propagated(self):
        class FailedClient:
            async def chat(self, **kwargs):
                raise TimeoutError("inference timed out")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metrics.jsonl"
            client = MeasuredOllamaClient(FailedClient(), str(path))
            with self.assertRaisesRegex(TimeoutError, "inference timed out"):
                await client.chat(model="devstral-small-2")
            self.assertIn("inference timed out", path.read_text())


if __name__ == "__main__":
    unittest.main()
