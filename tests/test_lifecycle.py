"""Focused lifecycle and durability tests; run inside the deployment image."""
import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("STATE_DIR", tempfile.mkdtemp(prefix="bitburner-tests-"))
import app.server as server


class FakeAgent:
    def __init__(self):
        self.stopped = asyncio.Event()
        self.paused = False

    def stop(self):
        self.stopped.set()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        server.stop_requested = False
        server.pause_event.set()
        server.status.update(state="running", objective="test", session=1, error="")

    async def test_stop_awaits_actual_agent_run_and_supervisor(self):
        old_agent, old_child, old_runner = server.agent, server.agent_run_task, server.runner
        fake = FakeAgent()
        server.agent = fake
        async def run():
            await fake.stopped.wait()
        server.agent_run_task = asyncio.create_task(run())
        async def supervisor():
            await asyncio.Event().wait()
        server.runner = asyncio.create_task(supervisor())
        await server.stop()
        self.assertTrue(server.agent_run_task is None or server.agent_run_task.done())
        self.assertTrue(server.runner is None or server.runner.done())
        self.assertEqual(server.status["state"], "operator_stopped")
        server.agent, server.agent_run_task, server.runner = old_agent, old_child, old_runner

    async def test_new_start_waits_for_previous_agent_run_to_terminate(self):
        old_agent, old_child, old_runner = server.agent, server.agent_run_task, server.runner
        blocker = asyncio.Event()
        server.agent = FakeAgent()
        server.agent_run_task = asyncio.create_task(blocker.wait())
        server.runner = None
        with self.assertRaises(server.HTTPException) as raised:
            await server.start(server.StartRequest(objective="another run"))
        self.assertEqual(raised.exception.status_code, 409)
        blocker.set()
        await server.agent_run_task
        server.agent, server.agent_run_task, server.runner = old_agent, old_child, old_runner

    async def test_pause_suspends_watchdog_and_resume(self):
        old_agent, old_runner = server.agent, server.runner
        fake = FakeAgent()
        server.agent = fake
        server.runner = None
        await server.pause()
        self.assertTrue(fake.paused)
        self.assertFalse(server.watchdog_expired("paused", 9999, 60))
        objective = server.STATE / "checkpoints" / "objective.json"
        objective.write_text(json.dumps({"objective": "test"}))
        await server.resume()
        self.assertFalse(fake.paused)
        self.assertTrue(server.pause_event.is_set())
        if server.runner and not server.runner.done():
            server.runner.cancel()
            await asyncio.gather(server.runner, return_exceptions=True)
        server.agent, server.runner = old_agent, old_runner

    async def test_resume_after_interruption_but_not_terminal_states(self):
        self.assertTrue(server.startup_resume_allowed("1", "active", True))
        for state in ("operator_stopped", "failed", "exhausted", "completed", "paused"):
            self.assertFalse(server.startup_resume_allowed("1", state, True), state)
        self.assertFalse(server.startup_resume_allowed("0", "active", True))

    async def test_interrupted_active_runtime_resumes_saved_objective(self):
        objective_path = server.STATE / "checkpoints" / "objective.json"
        objective_path.write_text(json.dumps({"objective": "continue from checkpoint"}))
        server.save_runtime("active", objective="continue from checkpoint", session=4)
        runtime = json.loads((server.STATE / "checkpoints" / "runtime.json").read_text())
        self.assertEqual(runtime["session"], 4)
        self.assertTrue(server.startup_resume_allowed("1", runtime["state"], objective_path.exists()))

    async def test_failed_atomic_checkpoint_keeps_previous_valid_file(self):
        path = server.STATE / "checkpoints" / "latest.json"
        previous = {"objective": "previous", "steps": 2}
        path.write_text(json.dumps(previous))
        with patch.object(server.os, "replace", side_effect=OSError("simulated disk error")):
            with self.assertRaises(OSError):
                server.save_checkpoint({"objective": "new", "steps": 3})
        self.assertEqual(json.loads(path.read_text()), previous)
        self.assertFalse(path.with_name(path.name + f".{os.getpid()}.tmp").exists())


if __name__ == "__main__":
    unittest.main()
