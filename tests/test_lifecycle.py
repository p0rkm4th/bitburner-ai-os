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

    def test_visible_money_parser_handles_suffixes_without_hidden_state(self):
        self.assertEqual(server.visible_money_amount("Money\n$1.262k"), 1262)
        self.assertEqual(server.visible_money_amount("Money $2.5m"), 2_500_000)
        self.assertIsNone(server.visible_money_amount("No balance shown"))

    def test_money_success_requires_confirmed_script_and_visible_gain(self):
        objective = "Create and run a script that earns money"
        state = {"initial_visible_money": 1500}
        self.assertIn("run", server.money_completion_block(objective, True, state, "Money $1.5k"))
        state.update(confirmed_script_run="earn.js", money_at_script_run=1500)
        self.assertIn("has not increased", server.money_completion_block(objective, True, state, "Money $1.5k"))
        self.assertIsNone(server.money_completion_block(objective, True, state, "Money $1.6k"))

    def test_verified_money_progress_outcome_is_objective_scoped(self):
        evidence = {"confirmed_script_run": "hack.js", "money_at_script_run": 1262}
        self.assertTrue(server.money_progress_verified(
            "Create a script that earns money", evidence,
            "Money $1.551k\nhack: Successfully hacked 'n00dles' for $288.750"))
        self.assertFalse(server.money_progress_verified(
            "Complete BitNode 1", evidence,
            "Money $1.551k\nhack: Successfully hacked 'n00dles' for $288.750"))
        self.assertFalse(server.money_progress_verified(
            "Create a script that earns money", {},
            "Money $1.551k\nhack: Successfully hacked 'n00dles' for $288.750"))
        self.assertFalse(server.money_progress_verified(
            "Create a script that earns money", evidence,
            "Money $1.262k\nhack: Successfully hacked 'n00dles' for $288.750"))
        self.assertFalse(server.money_progress_verified(
            "Create a script that earns money", evidence, "Money $1.551k"))

    def test_session_start_balance_wins_over_post_run_balance(self):
        # `money_at_script_run` may be sampled after a fast script has already
        # earned money; compare with the earliest visible session balance.
        evidence = {"confirmed_script_run": "hack.js", "initial_visible_money": 1262,
                    "money_at_script_run": 1551}
        visible = "Money $1.551k\nhack: Successfully hacked 'n00dles' for $288.750"
        self.assertTrue(server.money_progress_verified(
            "Create a script that earns money", evidence, visible))
        self.assertIsNone(server.money_completion_block(
            "Create a script that earns money", True, evidence, visible))

    def test_progress_report_missing_outcome_is_durable_in_runtime(self):
        server.save_runtime("failed", objective="earn money",
                            outcome="progress_verified_report_missing")
        runtime = json.loads((server.STATE / "checkpoints" / "runtime.json").read_text())
        self.assertEqual(runtime["state"], "failed")
        self.assertEqual(runtime["outcome"], "progress_verified_report_missing")

    def test_money_gate_allows_explicit_incomplete_report_and_non_money_objectives(self):
        self.assertIsNone(server.money_completion_block(
            "Create a money-making script", False, {}, "Money $0"))
        self.assertIsNone(server.money_completion_block(
            "Inspect the visible hacking level", True, {}, "Money $0"))

    async def test_registered_done_action_rejects_unverified_money_success(self):
        tools = server.create_game_tools({})
        state = {"initial_visible_money": 1262}
        server.register_completion_guard(tools, "Create and run a script that earns money", state)
        action = tools.registry.registry.actions["done"]
        self.assertIn("increased visible game balance", action.description)
        with patch.object(server, "visible_snapshot", return_value="Money $1.262k"):
            result = await action.function(
                params=server.DoneAction(text="I wrote it but did not run it", success=True),
                browser_session=object(), file_system=object(),
            )
        self.assertFalse(result.is_done)
        self.assertFalse(result.success)
        self.assertIn("No visible successful Netscript run", result.extracted_content)

    async def test_registered_done_action_accepts_visible_money_gain_after_script_run(self):
        tools = server.create_game_tools({})
        state = {"initial_visible_money": 1262, "confirmed_script_run": "earn.js",
                 "money_at_script_run": 1262}
        server.register_completion_guard(tools, "Create and run a script that earns money", state)
        action = tools.registry.registry.actions["done"]
        with patch.object(server, "visible_snapshot", return_value="Money $1.3k"):
            result = await action.function(
                params=server.DoneAction(text="The script ran and balance increased", success=True),
                browser_session=object(), file_system=object(),
            )
        self.assertTrue(result.is_done)
        self.assertTrue(result.success)

    def test_checkpoint_restores_ram_rejection_diagnostic_gate(self):
        result = server.checkpoint_ram_rejection({
            "latest_visible_state": "Cannot run simple_hack.js (t=1) on home. This script requires 1.70GB of RAM.",
            "errors": [],
        })
        self.assertEqual(result, {
            "filename": "simple_hack.js", "host": "home", "required_ram": "1.70", "diagnosed": False,
        })
        self.assertIsNone(server.checkpoint_ram_rejection({"latest_visible_state": "no RAM error"}))

    def test_checkpoint_keeps_ram_rejection_after_visible_state_changes(self):
        result = server.checkpoint_ram_rejection({
            "latest_visible_state": "Offline earnings dialog",
            "ram_rejection": {
                "filename": "simple_hack.js", "host": "home", "required_ram": "1.70", "diagnosed": True,
            },
        })
        self.assertEqual(result, {
            "filename": "simple_hack.js", "host": "home", "required_ram": "1.70", "diagnosed": False,
        })

    def test_checkpoint_recovers_generic_ram_error_with_unverified_host(self):
        result = server.checkpoint_ram_rejection({
            "latest_visible_state": "Offline earnings dialog",
            "errors": ["The command failed because of RAM limits."],
            "subobjective": "Inspect simple_hack.js using cat simple_hack.js.",
        })
        self.assertEqual(result, {
            "filename": "simple_hack.js", "host": "unknown", "required_ram": "unknown", "diagnosed": False,
        })

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

    def test_gameplay_task_finishes_immediately_after_verified_success(self):
        task = server.gameplay_task(
            "Earn money with a Netscript", "", "https://bitburner-official.github.io/",
            "https://bitburner-official.github.io/", remote_authoring=True)
        self.assertIn("call done(success=True) immediately", task)
        self.assertIn("without killing the script", task)
        self.assertIn("taking another observation", task)

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
            "game_run_script": {"filename", "args", "expected_host"},
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

    async def test_checkpoint_continuation_prioritizes_pending_visible_script_run(self):
        summary = server.checkpoint_prompt_summary({
            "objective": "Earn money with an original Netscript",
            "next_intended_action": "Rewrite the verified script again",
            "deployment_guard": {
                "deployments_without_run": 1,
                "last_deployed_filename": "student.js",
            },
        })
        self.assertIn("Run the latest verified student.js", summary["next_intended_action"])
        self.assertEqual(summary["deployment_guard"], {
            "deployments_without_run": 1,
            "last_deployed_filename": "student.js",
        })

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

    async def test_pending_deployment_refusal_ignores_changed_script_content(self):
        visible = "[home /]> connect home"
        failure = [{"tool": "game_deploy_script", "state": "game_error",
                    "message": "NO_PROGRESS: 1 scripts have already been deployed and read-back verified without a visible execution. Run the latest verified file with game_run_script('hack.js')."}]
        first_action = [{"game_deploy_script": {"filename": "hack.js", "content": "export async function main(ns) {}"}}]
        changed_action = [{"game_deploy_script": {"filename": "hack.js", "content": "export async function main(ns) { await ns.hack('n00dles'); }"}}]
        first = server.failed_result_signature(first_action, visible, failure)
        second = server.failed_result_signature(changed_action, visible, failure)
        self.assertEqual(first, second)
        self.assertEqual(first, server.failed_result_signature(changed_action,
            "[home /]> connect home\n$1.4m\nHacking: 17", failure))
        self.assertEqual(server.failed_action_repeat_count(first, 1, second), 2)
        diagnostic = [{"game_terminal": {"command": "ps"}}]
        changed_action = [{"game_terminal": {"command": "run hack.js"}}]
        self.assertNotEqual(first, server.failed_result_signature(
            diagnostic, visible,
            [{"tool": "game_terminal", "state": "game_error", "message": "Command failed"}],
        ))
        self.assertNotEqual(first, server.failed_result_signature(
            changed_action, visible,
            [{"tool": "game_terminal", "state": "game_error", "message": "Command failed"}],
        ))

    async def test_successful_recovery_action_resets_pending_deploy_failure_streak(self):
        blocked = {"tool": "game_deploy_script", "state": "game_error",
                   "message": "NO_PROGRESS: 1 scripts already deployed without a visible execution"}
        first = server.failure_signature_for_tool_results(
            [{"game_deploy_script": {"filename": "hack.js", "content": "one"}}],
            "Terminal", [blocked])
        self.assertEqual(server.failed_action_repeat_count("", 0, first), 1)

        recovery_response = [blocked, {"tool": "game_terminal", "state": "returned",
                                       "message": "Tool returned a visible result"}]
        reset = server.failure_signature_for_tool_results(
            [{"game_deploy_script": {"filename": "hack.js", "content": "two"}},
             {"game_terminal": {"command": "ps"}}], "Terminal", recovery_response)
        self.assertEqual(reset, "")
        self.assertEqual(server.failed_action_repeat_count(first, 1, reset), 0)

        passive_observation = server.failure_signature_for_tool_results(
            [{"game_deploy_script": {"filename": "hack.js", "content": "two"}},
             {"game_observe": {}}], "Terminal", [blocked,
                 {"tool": "game_observe", "state": "returned", "message": "Same visible state"}])
        self.assertEqual(passive_observation, first)

        ordinary_error = {"tool": "game_run_script", "state": "game_error",
                          "message": "Visible script runtime error: invalid target"}
        mixed_ordinary_error = server.failure_signature_for_tool_results(
            [{"game_run_script": {"filename": "hack.js"}},
             {"game_terminal": {"command": "ps"}}], "Terminal",
            [ordinary_error, {"tool": "game_terminal", "state": "returned",
                              "message": "Tool returned a visible result"}])
        self.assertTrue(mixed_ordinary_error)
        self.assertEqual(mixed_ordinary_error, server.failed_result_signature(
            [{"game_run_script": {"filename": "hack.js"}},
             {"game_terminal": {"command": "ps"}}], "Terminal", [ordinary_error]))

    async def test_non_pending_deployment_no_progress_stays_argument_sensitive(self):
        failure = [{"tool": "game_deploy_script", "state": "game_error",
                    "message": "NO_PROGRESS: script already exists; no write was made"}]
        first = server.failed_result_signature(
            [{"game_deploy_script": {"filename": "a.js", "content": "one"}}], "Terminal", failure)
        second = server.failed_result_signature(
            [{"game_deploy_script": {"filename": "a.js", "content": "two"}}], "Terminal", failure)
        self.assertNotEqual(first, second)

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

    async def test_delayed_visible_runtime_error_is_counted_once(self):
        message = "Visible Netscript runtime error: missing root access"
        returned = [{"tool": "game_run_script", "state": "returned", "message": "PID 1"}]
        captured = [{"tool": "game_run_script", "state": "game_error", "message": "runtime error"}]
        self.assertTrue(server.should_count_visible_runtime_error(message, [], returned))
        self.assertFalse(server.should_count_visible_runtime_error(message, [message], returned))
        self.assertFalse(server.should_count_visible_runtime_error(message, [], captured))

    async def test_slow_local_inference_timeouts_remain_bounded(self):
        with patch.dict(os.environ, {"LLM_TIMEOUT": "170", "STEP_TIMEOUT": "190"}):
            self.assertEqual(server.inference_timeout_settings(), {"llm_timeout": 170, "step_timeout": 190})
        with patch.dict(os.environ, {"LLM_TIMEOUT": "999", "STEP_TIMEOUT": "999"}):
            self.assertEqual(server.inference_timeout_settings(), {"llm_timeout": 180, "step_timeout": 240})

    def test_ollama_http_timeout_uses_benchmark_request_budget(self):
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://127.0.0.1:11434",
                                     "OLLAMA_MODEL": "local-test", "OLLAMA_TIMEOUT": "180",
                                     "OLLAMA_METRICS_PATH": ""}, clear=True):
            model = server.get_model()
        self.assertEqual(model.timeout, 180)

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
