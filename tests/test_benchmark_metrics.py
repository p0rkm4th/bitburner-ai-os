import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.server import MeasuredChatOllama, MeasuredOllamaClient, get_model, ollama_think_options


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
    def __init__(self):
        self.last_kwargs = None

    async def chat(self, **kwargs):
        self.last_kwargs = kwargs
        return FakeResponse()


class BenchmarkMetricsTests(unittest.IsolatedAsyncioTestCase):
    async def test_metrics_capture_counts_without_prompt_or_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metrics.jsonl"
            underlying = FakeClient()
            client = MeasuredOllamaClient(underlying, str(path))
            await client.chat(model="qwen3.8:27b", messages=[{"content": "private prompt"}], think=False)
            row = json.loads(path.read_text())
            self.assertIs(underlying.last_kwargs["think"], False)
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


class OllamaThinkOptionTests(unittest.TestCase):
    def test_pinned_chatollama_extracts_think_as_top_level_parameter(self):
        model = MeasuredChatOllama(
            model="qwen3.6:35b",
            host="http://127.0.0.1:11434",
            ollama_options={"num_ctx": 16384, "think": False},
        )
        options, top_level = model._split_chat_options()
        self.assertEqual(options, {"num_ctx": 16384})
        self.assertEqual(top_level, {"think": False})

    def test_unset_and_empty_preserve_ollama_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ollama_think_options(), {})
        with patch.dict(os.environ, {"OLLAMA_THINK": "  "}, clear=True):
            self.assertEqual(ollama_think_options(), {})

    def test_explicit_false_is_passed_as_boolean(self):
        with patch.dict(os.environ, {"OLLAMA_THINK": "false"}, clear=True):
            self.assertEqual(ollama_think_options(), {"think": False})

    def test_explicit_true_is_passed_as_boolean(self):
        with patch.dict(os.environ, {"OLLAMA_THINK": "TRUE"}, clear=True):
            self.assertEqual(ollama_think_options(), {"think": True})

    def test_invalid_value_is_rejected(self):
        with patch.dict(os.environ, {"OLLAMA_THINK": "off"}, clear=True):
            with self.assertRaisesRegex(ValueError, "OLLAMA_THINK"):
                ollama_think_options()

    @patch("app.server.MeasuredChatOllama")
    def test_benchmark_model_receives_explicit_think_override(self, measured):
        env = {
            "OLLAMA_BASE_URL": "http://ollama:11434/",
            "OLLAMA_MODEL": "qwen3.6:35b",
            "OLLAMA_METRICS_PATH": "/tmp/metrics.jsonl",
            "OLLAMA_THINK": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            get_model()
        self.assertEqual(measured.call_args.kwargs["ollama_options"], {
            "num_ctx": 16384,
            "temperature": 0.2,
            "seed": 7,
            "keep_alive": "30m",
            "think": False,
        })

    @patch("app.server.MeasuredChatOllama")
    def test_benchmark_model_preserves_default_options_when_think_is_unset(self, measured):
        env = {
            "OLLAMA_BASE_URL": "http://ollama:11434",
            "OLLAMA_MODEL": "qwen3.6:35b",
            "OLLAMA_METRICS_PATH": "/tmp/metrics.jsonl",
        }
        with patch.dict(os.environ, env, clear=True):
            get_model()
        self.assertEqual(measured.call_args.kwargs["ollama_options"], {
            "num_ctx": 16384,
            "temperature": 0.2,
            "seed": 7,
            "keep_alive": "30m",
        })

    @patch("app.server.ChatOllama")
    def test_production_model_receives_explicit_bounded_context_and_parameters(self, chat_model):
        env = {"OLLAMA_BASE_URL": "http://ollama:11434", "OLLAMA_MODEL": "qwen3.6:35b"}
        with patch.dict(os.environ, env, clear=True):
            get_model()
        self.assertEqual(chat_model.call_args.kwargs["ollama_options"], {
            "num_ctx": 16384,
            "temperature": 0.2,
            "seed": 7,
            "keep_alive": "30m",
        })

    @patch("app.server.ChatOllama")
    def test_production_model_receives_think_override_with_other_options(self, chat_model):
        env = {"OLLAMA_BASE_URL": "http://ollama:11434", "OLLAMA_MODEL": "qwen3.6:35b",
               "OLLAMA_THINK": "false", "OLLAMA_NUM_CTX": "16384", "OLLAMA_TEMPERATURE": "0.0",
               "OLLAMA_SEED": "42", "OLLAMA_KEEP_ALIVE": "5m"}
        with patch.dict(os.environ, env, clear=True):
            get_model()
        self.assertEqual(chat_model.call_args.kwargs["ollama_options"], {
            "num_ctx": 16384,
            "temperature": 0.0,
            "seed": 42,
            "keep_alive": "5m",
            "think": False,
        })


if __name__ == "__main__":
    unittest.main()
