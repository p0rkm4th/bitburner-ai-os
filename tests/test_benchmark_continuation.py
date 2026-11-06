import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "prepare-benchmark-continuation.py"
SPEC = importlib.util.spec_from_file_location("prepare_benchmark_continuation", MODULE_PATH)
continuation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(continuation)


class BenchmarkContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "profile").mkdir()
        (self.source / "profile" / "Cookies").write_text("isolated test profile")
        (self.source / "checkpoints").mkdir()
        self.objective = self.root / "objective.md"
        self.objective.write_text("independent test objective\n")
        digest = hashlib.sha256(self.objective.read_bytes()).hexdigest()
        for name, value in {
            "latest.json": {"state": "active", "objective": self.objective.read_text(), "session": 2, "steps": 11},
            "runtime.json": {"state": "active", "objective": self.objective.read_text()},
            "objective.json": {"objective": self.objective.read_text()},
        }.items():
            (self.source / "checkpoints" / name).write_text(json.dumps(value))
        (self.source / "logs").mkdir()
        (self.source / "logs" / "trial-config.json").write_text(json.dumps({
            "trial_id": "source-run", "objective_sha256": digest,
            "model": {"model_tag": "qwen3.6:35b", "digest": "abc123"},
            "think_setting": "false", "context_size": 16384,
            "temperature": 0.2, "seed": 7,
        }))
        self.destination = self.root / "next"
        self.model = {"model_tag": "qwen3.6:35b", "digest": "abc123"}

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self):
        return continuation.prepare(self.source, self.destination, self.objective,
                                    self.model, "false", 16384, 0.2, 7)

    def test_copies_only_profile_and_checkpoint_for_matching_interrupted_run(self):
        info = self.prepare()
        self.assertEqual(info["source_trial_id"], "source-run")
        self.assertEqual(info["source_steps"], 11)
        self.assertEqual((self.destination / "profile" / "Cookies").read_text(), "isolated test profile")
        self.assertTrue((self.destination / "checkpoints" / "latest.json").exists())
        self.assertFalse((self.destination / "logs").exists())

    def test_rejects_terminal_checkpoint(self):
        (self.source / "checkpoints" / "runtime.json").write_text(json.dumps({"state": "completed"}))
        with self.assertRaisesRegex(ValueError, "active checkpoint"):
            self.prepare()
        self.assertFalse(self.destination.exists())

    def test_rejects_model_or_inference_setting_mismatch(self):
        self.model["digest"] = "different"
        with self.assertRaisesRegex(ValueError, "model_digest"):
            self.prepare()
        self.assertFalse(self.destination.exists())

    def test_rejects_changed_objective(self):
        self.objective.write_text("different objective")
        with self.assertRaisesRegex(ValueError, "objective"):
            self.prepare()
        self.assertFalse(self.destination.exists())

    def test_never_overwrites_existing_destination(self):
        self.destination.mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
