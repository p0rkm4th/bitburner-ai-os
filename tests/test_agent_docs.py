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
                     "cat report.txt", "script-only Remote API"):
            self.assertIn(fact, guide)

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

    def test_every_session_includes_guide_and_keeps_persistent_game_tab(self):
        task = gameplay_task("Earn money", "checkpoint summary", "https://bitburner-official.github.io/",
                             "https://bitburner-official.github.io/", remote_authoring=True)
        self.assertIn("BITBURNER CORE GUIDE", task)
        self.assertIn("SESSION TASK", task)
        self.assertIn("game_netscript_reference", task)
        self.assertIn("Do not navigate or reload", task)
        self.assertIn("checkpoint summary", task)

    def test_system_prompt_is_short_and_requires_verified_progress(self):
        self.assertLess(len(BITBURNER_SYSTEM_PROMPT), 2000)
        self.assertIn("one consequential action per step", BITBURNER_SYSTEM_PROMPT)
        self.assertIn("never claim progress without visible evidence", BITBURNER_SYSTEM_PROMPT.casefold())
        self.assertIn("at most one corrected diagnostic attempt", BITBURNER_SYSTEM_PROMPT)

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
