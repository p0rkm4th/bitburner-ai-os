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

    def test_checkpoint_restores_ram_rejection_diagnostic_gate(self):
        result = server.checkpoint_ram_rejection({
            "latest_visible_state": "Cannot run simple_hack.js (t=1) on home. This script requires 1.70GB of RAM.",
            "errors": [],
        })
        self.assertEqual(result, {
            "filename": "simple_hack.js", "host": "home", "required_ram": "1.70", "diagnosed": False,
        })
        self.assertIsNone(server.checkpoint_ram_rejection({"latest_visible_state": "no RAM error"}))

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
        self.assertEqual(server.status["state"], "active")
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
        self.assertEqual(server.runtime_session_number(None), 0)
        self.assertEqual(server.runtime_session_number("3"), 3)

    async def test_continuation_stays_on_existing_game_and_summarizes_checkpoint(self):
        task = server.browser_task("Continue playing", "", "https://bitburner-official.github.io/",
                                   "https://bitburner-official.github.io/")
        self.assertIn("already open", task)
        self.assertIn("Do not navigate or reload", task)
        self.assertNotIn("Open https://", task)
        self.assertNotIn("https://", task)
        self.assertIn("Open https://", server.browser_task("Continue", "", "about:blank",
                                                            "https://bitburner-official.github.io/"))
        summary = server.checkpoint_prompt_summary({"result": "x" * 10000,
            "latest_visible_state": "v" * 3000, "next_intended_action": "next"})
        self.assertNotIn("result", summary)
        self.assertLessEqual(len(summary["latest_visible_state"]), 1400)

    def test_restricted_agent_disables_browser_use_auto_navigation(self):
        tools = server.create_game_tools()
        self.assertNotIn("navigate", tools.registry.registry.actions)
        llm = server.ChatOllama(model="qwen3.6:35b", host="http://127.0.0.1:11434")
        task = "Open https://example.com"
        with self.assertRaises(KeyError) as raised:
            server.Agent(task=task, llm=llm, tools=tools)
        self.assertEqual(raised.exception.args, ("navigate",))

        agent = server.Agent(task=task, llm=llm, tools=tools, directly_open_url=False)
        self.assertIsNone(agent.initial_actions)

    async def test_gameplay_registry_removes_stale_index_actions(self):
        with patch.object(server, "remote_api_from_env", return_value=object()):
            tools = server.create_game_tools()
        actions = tools.registry.registry.actions
        for blocked in ("navigate", "go_back", "evaluate", "run_bash", "run_python", "write_file",
                        "click", "input", "send_keys", "select_dropdown", "find_elements", "scroll"):
            self.assertNotIn(blocked, actions)
        for game_action in ("game_observe", "game_progress", "game_dismiss_dialog", "game_open_tab", "game_terminal",
                            "game_run_script", "game_help", "game_troubleshoot", "game_read_script",
                            "game_deploy_script", "game_netscript_reference"):
            self.assertIn(game_action, actions)
        self.assertNotIn("game_open_editor", actions)
        self.assertNotIn("game_edit_script", actions)
        expected = {
            "game_observe": set(),
            "game_progress": {"baseline_money", "baseline_hacking_level"},
            "game_dismiss_dialog": set(),
            "game_open_tab": {"tab"},
            "game_terminal": {"command"},
            "game_run_script": {"filename", "args"},
            "game_help": {"topic"},
            "game_troubleshoot": {"error"},
            "game_read_script": {"filename"},
            "game_deploy_script": {"filename", "content"},
            "game_netscript_reference": {"symbol"},
        }
        for name, fields in expected.items():
            schema = tools.registry.registry.actions[name].param_model.model_json_schema()
            self.assertEqual(set(schema["properties"]), fields)
            self.assertNotIn("browser_session", schema["properties"])

    async def test_remote_api_configuration_removes_browser_editor_tools(self):
        with patch.object(server, "remote_api_from_env", return_value=object()):
            tools = server.create_game_tools()
        actions = tools.registry.registry.actions
        self.assertNotIn("game_open_editor", actions)
        self.assertNotIn("game_edit_script", actions)
        self.assertNotIn("input", actions)
        for name in ("game_read_script", "game_deploy_script", "game_netscript_reference",
                     "game_run_script", "game_terminal", "game_open_tab", "game_observe"):
            self.assertIn(name, actions)

    async def test_remote_api_checkpoint_discards_stale_editor_instructions(self):
        checkpoint = {
            "objective": "Use game_edit_script to repair home.js",
            "subobjective": "Open the Script Editor",
            "accomplishments": ["Remote API Online", "Monaco editor opened"],
            "latest_visible_state": "Stale Script Editor snapshot",
            "scripts_and_observed_results": ["home.js editor input mismatch"],
            "errors": ["game_edit_script failed", "No script execution verified"],
            "next_intended_action": "Open the editor and retry game_edit_script",
        }
        with patch.dict(os.environ, {"BITBURNER_REMOTE_API_URL": "http://localhost:3001",
                                     "BITBURNER_REMOTE_API_TOKEN": "test"}):
            summary = server.checkpoint_prompt_summary(checkpoint)
        rendered = json.dumps(summary)
        for stale in ("game_edit_script", "Monaco", "Script Editor", "editor input"):
            self.assertNotIn(stale.casefold(), rendered.casefold())
        self.assertIn("game_deploy_script", summary["next_intended_action"])
        self.assertIn("Remote API Online", summary["accomplishments"])

    async def test_identical_failed_action_is_bounded_and_new_action_resets(self):
        signature = "same-action-and-visible-error"
        self.assertEqual(server.failed_action_repeat_count("", 0, signature), 1)
        self.assertEqual(server.failed_action_repeat_count(signature, 1, signature), 2)
        self.assertEqual(server.failed_action_repeat_count(signature, 2, "different-action"), 1)
        self.assertEqual(server.failed_action_repeat_count(signature, 2, ""), 0)

    async def test_empty_model_response_failures_have_a_repeatable_signature(self):
        failure = [{"tool": "unmapped", "state": "failed", "message": "LLM call timed out"}]
        first = server.failed_result_signature([], "[12] Offline dialog", failure)
        repeated = server.failed_result_signature([], "[99] Offline dialog", failure)
        changed_error = server.failed_result_signature([], "[99] Offline dialog",
                                                        [{**failure[0], "message": "Malformed JSON"}])
        changed_ui = server.failed_result_signature([], "Terminal ready", failure)
        self.assertEqual(first, repeated)
        self.assertNotEqual(repeated, changed_error)
        self.assertNotEqual(repeated, changed_ui)
        self.assertEqual(server.failed_result_signature([], "Terminal ready", []), "")

    async def test_terminal_ram_error_and_duplicate_deploy_are_counted_as_game_errors(self):
        from types import SimpleNamespace
        terminal = server.summarize_action_results(
            [{"game_terminal": {"command": "run home.js"}}],
            [SimpleNamespace(error=None, extracted_content=(
                "VISIBLE GAME ERROR (verbatim):\nCannot run home.js on home. "
                "This script requires 81.60GB of RAM."))],
        )
        duplicate = server.summarize_action_results(
            [{"game_deploy_script": {"filename": "home.js"}}],
            [SimpleNamespace(error=None, extracted_content="NO_PROGRESS: home.js already exists")],
        )
        self.assertEqual(terminal[0]["state"], "game_error")
        self.assertIn("81.60GB of RAM", terminal[0]["message"])
        self.assertEqual(duplicate[0]["state"], "game_error")

    async def test_slow_local_inference_timeouts_remain_bounded(self):
        with patch.dict(os.environ, {"LLM_TIMEOUT": "170", "STEP_TIMEOUT": "190"}):
            self.assertEqual(server.inference_timeout_settings(), {"llm_timeout": 170, "step_timeout": 190})
        with patch.dict(os.environ, {"LLM_TIMEOUT": "999", "STEP_TIMEOUT": "999"}):
            self.assertEqual(server.inference_timeout_settings(), {"llm_timeout": 180, "step_timeout": 240})

    async def test_bitnode_completion_requires_positive_report_and_visible_confirmation(self):
        self.assertTrue(server.bitnode1_completion_confirmed(
            "BITNODE_1_COMPLETE", "Congratulations, BitNode 1 completed."))
        self.assertFalse(server.bitnode1_completion_confirmed(
            "BITNODE_1_COMPLETE: NOT YET VERIFIED", "BitNode 1 completed"))
        self.assertFalse(server.bitnode1_completion_confirmed(
            "BITNODE_1_COMPLETE", "BitNode 1 progress"))

    async def test_progress_signature_ignores_volatile_element_ids(self):
        a = server.progress_signature("[13] Terminal [14] Money $10", '{"index": 13, "click": true}')
        b = server.progress_signature("[94] Terminal [95] Money $10", '{"index": 94, "click": true}')
        c = server.progress_signature("[94] Terminal [95] Money $11", '{"index": 94, "click": true}')
        self.assertEqual(a, b)
        self.assertNotEqual(b, c)

    async def test_stagnation_streak_survives_sessions_and_ignores_action_cycles(self):
        old = {"latest_visible_state": "[1] Terminal $10", "action": "click", "action_count": 2,
               "no_progress_sessions": 1, "recent_actions": ["a", "b", "a"]}
        current = {"latest_visible_state": "[99] Terminal $10", "action": "click", "action_count": 3}
        self.assertEqual(server.stagnation_count(old, current), 2)
        self.assertEqual(len(current["recent_actions"]), 4)
        changed = {"latest_visible_state": "Terminal $11", "action": "type", "action_count": 4}
        self.assertEqual(server.stagnation_count(current, changed), 0)

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
