import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.agent_docs import _docs_root, load_core_guide, register_agent_doc_tools
from app.agent_prompt import BITBURNER_SYSTEM_PROMPT
from app.server import checkpoint_prompt_summary, gameplay_task, summarize_action_results


class FakeTools:
    def action(self, description=""):
        def decorate(fn):
            return fn
        return decorate


class AgentDocumentationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.actions = register_agent_doc_tools(FakeTools())

    def test_compact_guide_is_available_and_within_context_budget(self):
        guide = load_core_guide()
        self.assertLess(len(guide), 6000)
        for fact in ("home` is the player's computer", "Root/admin access", "main(ns)",
                     "game_netscript_reference", "does not prove", "scan-analyze 2",
                     "cat report.txt", "script-only Remote API", "game_progress"):
            self.assertIn(fact, guide)
        self.assertIn("`ns.nuke`", guide)
        self.assertIn("without connecting to that target", guide)
        self.assertIn("root-access error", guide)

    def test_docs_root_supports_flat_container_and_source_package_layouts(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            flat = root / "image"
            (flat / "docs").mkdir(parents=True)
            self.assertEqual(_docs_root(flat / "agent_docs.py"), flat / "docs")
            package = root / "repo" / "app"
            package.mkdir(parents=True)
            (root / "repo" / "docs").mkdir()
            self.assertEqual(_docs_root(package / "agent_docs.py"), root / "repo" / "docs")

    async def test_on_demand_help_returns_only_allowlisted_topics(self):
        servers = await self.actions["game_help"]("servers")
        self.assertIn("Root/admin access and hacking skill are separate requirements", servers)
        self.assertNotIn("money-making script", servers.casefold())
        observation = await self.actions["game_help"]("observe")
        self.assertIn("game_progress", observation)
        self.assertIn("duplicate-observation guard", observation)
        root = await self.actions["game_help"]("root")
        self.assertIn("without connecting to that target", root)
        bad = await self.actions["game_help"]("/etc/passwd")
        self.assertIn("ERROR: Unknown topic", bad)
        self.assertNotIn("/etc/passwd", bad)

    async def test_troubleshooting_selects_relevant_error_notes(self):
        result = await self.actions["game_troubleshoot"]("getFile returned HTTP 500 while Remote API offline")
        self.assertIn("Remote API offline", result)
        self.assertNotIn("generic indexed clicks", result)
        generic = await self.actions["game_troubleshoot"]("unrecognized browser issue")
        self.assertIn("Browser and modal errors", generic)
        command = await self.actions["game_troubleshoot"]("Incorrect usage: scan-analyze depth must be positive numeric")
        self.assertIn("positive numeric", command)
        unknown = await self.actions["game_troubleshoot"]("Command serverinfo not found.")
        self.assertIn("Unknown Terminal command", unknown)

    async def test_removed_function_recovery_uses_observed_live_game_error(self):
        result = await self.actions["game_troubleshoot"](
            "formatNumber: Function removed in 3.0.0; use ns.format.number()")
        self.assertIn("Bitburner v3.0.x", result)
        self.assertIn("game_netscript_reference", result)
        self.assertIn("visible `run` PID confirms", result)

    async def test_ram_troubleshooting_mentions_process_inspection_and_home_file_scope(self):
        result = await self.actions["game_troubleshoot"](
            "Cannot run hack_n00dles.js on home: requires 1.70GB RAM")
        self.assertIn("Use `ps`", result)
        self.assertIn("1.6 GB minimum", result)
        self.assertIn("same APIs", result)
        self.assertIn("positive PID", result)
        self.assertIn("connecting alone", result)
        self.assertIn("does not copy files", result)

    async def test_message_dialog_troubleshooting_preserves_unlock_information(self):
        result = await self.actions["game_troubleshoot"]("Message received from unknown sender dialog")
        self.assertIn("Read its visible body before closing", result)
        self.assertIn("cat filename.msg", result)
        self.assertIn("verify whether it is a new message", result)

    def test_every_session_includes_guide_and_keeps_persistent_game_tab(self):
        task = gameplay_task("Earn money", "checkpoint summary", "https://bitburner-official.github.io/",
                             "https://bitburner-official.github.io/", remote_authoring=True)
        self.assertIn("BITBURNER CORE GUIDE", task)
        self.assertIn("SESSION TASK", task)
        self.assertIn("game_netscript_reference", task)
        self.assertIn("call game_troubleshoot with its exact text", task)
        self.assertIn("A PID confirms startup only", task)
        self.assertIn("Verify actual money/output", task)
        self.assertIn("use game_progress to verify visible money, hacking level, and script income", task)
        self.assertIn("do not poll by repeating game_observe", task)
        self.assertIn("If game_observe says NO_PROGRESS, do not repeat it", task)
        self.assertIn("run that exact filename through game_run_script", task)
        self.assertIn("An earlier Terminal `ls` does not disprove a later verified deployment", task)
        self.assertIn("call game_dismiss_dialog once", task)
        self.assertIn("one game_dismiss_dialog attempt", task)
        self.assertIn("visible root, skill, and port requirements", task)
        self.assertIn("verify any Netscript root-access API against the live reference", task)
        self.assertIn("do not repeat an unchanged observation", task)
        self.assertIn("Do not navigate or reload", task)
        self.assertIn("checkpoint summary", task)

    def test_core_guide_distinguishes_current_server_from_script_arguments(self):
        guide = load_core_guide()
        self.assertIn("on the currently connected", guide)
        self.assertIn("script arguments, not a destination server", guide)

    def test_system_prompt_is_short_and_requires_verified_progress(self):
        self.assertLess(len(BITBURNER_SYSTEM_PROMPT), 2000)
        self.assertIn("one consequential action per step", BITBURNER_SYSTEM_PROMPT)
        self.assertIn("never claim progress without visible evidence", BITBURNER_SYSTEM_PROMPT.casefold())
        self.assertIn("at most one corrected diagnostic attempt", BITBURNER_SYSTEM_PROMPT)
        self.assertIn("no dialog returns `NO_PROGRESS`", BITBURNER_SYSTEM_PROMPT)
        self.assertIn("Do not repeat dismissal", BITBURNER_SYSTEM_PROMPT)
        self.assertIn("expected_host", BITBURNER_SYSTEM_PROMPT)
        self.assertIn("check uncertain Netscript functions with game_netscript_reference", BITBURNER_SYSTEM_PROMPT)
        self.assertIn("if none is listed, author independently", BITBURNER_SYSTEM_PROMPT)

    def test_checkpoint_carries_tool_failures_but_not_long_outputs(self):
        summary = checkpoint_prompt_summary({
            "objective": "test", "tool_results": [{"tool": "game_run_script", "state": "game_error",
                                                      "message": "runtime failure"}],
            "tool_metrics": {"calls": 3, "failed": 1},
        })
        self.assertEqual(summary["tool_results"][0]["message"], "runtime failure")
        self.assertEqual(summary["tool_metrics"]["failed"], 1)

    def test_context_settings_bound_history_and_checkpoint_text(self):
        from app.server import agent_context_settings
        with patch.dict("os.environ", {"MAX_HISTORY_ITEMS": "99", "CHECKPOINT_PROMPT_LIMIT": "9000"}):
            settings = agent_context_settings()
        self.assertEqual(settings["max_history_items"], 8)
        self.assertEqual(settings["checkpoint_prompt_limit"], 3000)
        self.assertTrue(settings["message_compaction"])
        with patch.dict("os.environ", {"MAX_HISTORY_ITEMS": "3"}):
            self.assertEqual(agent_context_settings()["max_history_items"], 6)

    def test_result_summaries_do_not_store_script_contents(self):
        class Result:
            error = None
            extracted_content = "secret code\nRUNTIME ERROR: missing function"
        summary = summarize_action_results([{"game_run_script": {"filename": "x.js"}}], [Result()])
        self.assertEqual(summary[0]["state"], "game_error")
        self.assertNotIn("secret code", summary[0]["message"])

    def test_multiline_runtime_root_error_is_counted(self):
        class Result:
            error = None
            extracted_content = (
                "RUNTIME\n ERROR\n hack: Cannot hack n00dles server because you do not have root access\n"
                "Stack: hack.js:L6@main"
            )
        summary = summarize_action_results([{"game_run_script": {"filename": "hack.js"}}], [Result()])
        self.assertEqual(summary[0]["state"], "game_error")
        self.assertIn("RUNTIME", summary[0]["message"])
        self.assertIn("do not have root access", summary[0]["message"])

    def test_visible_terminal_usage_error_is_counted_as_game_error(self):
        class Result:
            error = None
            extracted_content = "[home /]> scan-analyze n00dles\nIncorrect usage of scan-analyze command"
        summary = summarize_action_results([{"game_terminal": {"command": "scan-analyze n00dles"}}], [Result()])
        self.assertEqual(summary[0]["state"], "game_error")
        self.assertIn("Incorrect usage", summary[0]["message"])

    def test_visible_terminal_unknown_command_is_counted_as_game_error(self):
        class Result:
            error = None
            extracted_content = "[home /]> serverinfo n00dles\nCommand serverinfo not found."
        summary = summarize_action_results([{"game_terminal": {"command": "serverinfo n00dles"}}], [Result()])
        self.assertEqual(summary[0]["state"], "game_error")
        self.assertIn("Command serverinfo not found", summary[0]["message"])


if __name__ == "__main__":
    unittest.main()
