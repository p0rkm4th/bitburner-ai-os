import unittest
from unittest.mock import patch

import httpx

from app.remote_api_tools import (RemoteApi, deployment_guard_checkpoint,
                                  register_remote_api_tools, restore_deployment_guard)


class FakeTools:
    def action(self, description=""):
        def decorate(fn):
            return fn
        return decorate


class FakeApi:
    def __init__(self):
        self.files = {"home.js": "export async function main(ns) {}"}
        self.calls = []
        self.failure = None
        self.missing_file_error = False

    async def call(self, method, params):
        self.calls.append((method, params))
        if self.failure and method == self.failure[0]:
            raise RuntimeError(self.failure[1])
        if (method == "getFile" and self.missing_file_error
                and params["filename"] not in self.files):
            raise RuntimeError("getFile returned HTTP 500: Bitburner API error")
        if method == "pushFile":
            self.files[params["filename"]] = params["content"]
            return "OK"
        if method == "getFile":
            return self.files.get(params["filename"], "")
        if method == "calculateRam":
            return 1.6
        if method == "getDefinitionFile":
            return ("export interface NS {\n"
                    "  /** Reduce target security.\n   * Returns the reduction.\n   */\n"
                    "  weaken(host: string, opts?: BasicHGWOptions): Promise<number>;\n\n"
                    "  /** Increase target money.\n   * Returns the growth multiplier.\n   */\n"
                    "  grow(host?: string, opts?: BasicHGWOptions): Promise<number>;\n\n"
                    "  hack(host: string): Promise<number>;\n}")
        raise AssertionError(f"unexpected method {method}")


class RemoteApiToolTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api = FakeApi()
        self.action_state = {}
        self.actions = register_remote_api_tools(FakeTools(), self.api, action_state=self.action_state)

    async def test_read_is_limited_to_simple_script_names_on_home(self):
        result = await self.actions["game_read_script"]("home.js")
        self.assertIn("main(ns)", result)
        self.assertEqual(self.api.calls, [("getFile", {"filename": "home.js", "server": "home"})])
        for invalid in ("../home.js", "foo/bar.js", "home.txt"):
            result = await self.actions["game_read_script"](invalid)
            self.assertIn("ERROR:", result)

    async def test_read_reports_missing_script_as_actionable_not_found(self):
        self.api.missing_file_error = True
        result = await self.actions["game_read_script"]("student.js")
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("No existing script named student.js was found on home", result)
        self.assertIn("Do not repeat this read", result)
        self.assertIn("`ls`", result)
        self.assertIn("game_deploy_script", result)
        self.assertEqual(self.api.calls, [("getFile", {"filename": "student.js", "server": "home"})])

    async def test_pending_deployment_blocks_reads_and_reference_until_visible_run(self):
        self.action_state.update(deployments_without_run=1, last_deployed_filename="hack.js")
        read = await self.actions["game_read_script"]("hack.js")
        reference = await self.actions["game_netscript_reference"]("ns.hack")
        for result in (read, reference):
            self.assertTrue(result.startswith("NO_PROGRESS:"))
            self.assertIn("game_run_script('hack.js'", result)
        self.assertEqual(self.api.calls, [])

    async def test_read_preserves_non_missing_remote_api_errors(self):
        self.api.failure = ("getFile", "Remote API is not connected")
        result = await self.actions["game_read_script"]("student.js")
        self.assertIn("Remote API is not connected", result)

    async def test_deploy_reads_back_and_calculates_ram(self):
        self.action_state["last_terminal_command"] = "run student.js"
        code = "export async function main(ns) { await ns.sleep(1); }"
        result = await self.actions["game_deploy_script"]("student.js", code)
        self.assertIn("read-back verified student.js", result)
        self.assertIn("1.6 GB", result)
        self.assertEqual([call[0] for call in self.api.calls], ["getFile", "pushFile", "getFile", "calculateRam"])
        self.assertTrue(all(call[1].get("server", "home") == "home" for call in self.api.calls))
        self.assertNotIn("last_terminal_command", self.action_state)

    async def test_pending_run_guard_survives_session_checkpoint(self):
        first = "export async function main(ns) { await ns.sleep(1); }"
        revised = "export async function main(ns) { await ns.sleep(2); }"
        self.assertIn("read-back verified", await self.actions["game_deploy_script"]("student.js", first))
        checkpoint = {"deployment_guard": deployment_guard_checkpoint(self.action_state)}
        restored_state = {}
        restore_deployment_guard(checkpoint, restored_state)
        restored_actions = register_remote_api_tools(FakeTools(), self.api, action_state=restored_state)
        calls_before_rejected_write = len(self.api.calls)
        blocked = await restored_actions["game_deploy_script"]("student.js", revised)
        self.assertTrue(blocked.startswith("NO_PROGRESS:"))
        self.assertIn("game_run_script('student.js')", blocked)
        self.assertEqual(len(self.api.calls), calls_before_rejected_write)

    async def test_deploy_creates_file_when_bridge_reports_missing_file_as_api_error(self):
        self.api.missing_file_error = True
        code = "export async function main(ns) { await ns.hack('n00dles'); }"
        result = await self.actions["game_deploy_script"]("new.js", code)
        self.assertIn("Deployed and read-back verified new.js", result)
        self.assertEqual([call[0] for call in self.api.calls],
                         ["getFile", "pushFile", "getFile", "calculateRam"])
        self.assertEqual(self.api.files["new.js"], code)

    async def test_deploy_does_not_write_after_other_read_error(self):
        self.api.failure = ("getFile", "Remote API is not connected")
        result = await self.actions["game_deploy_script"]("new.js", "export async function main(ns) {}")
        self.assertIn("Remote API is not connected", result)
        self.assertEqual([call[0] for call in self.api.calls], ["getFile"])

    async def test_duplicate_deployment_is_reported_as_no_progress_without_rewriting(self):
        self.action_state["last_terminal_command"] = "run student.js"
        code = "export async function main(ns) { await ns.sleep(1); }"
        self.api.files["student.js"] = code
        result = await self.actions["game_deploy_script"]("student.js", code)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("calculated RAM: 1.6 GB", result)
        self.assertIn("Run it through the visible Terminal", result)
        self.assertEqual([call[0] for call in self.api.calls], ["getFile", "calculateRam"])
        self.assertEqual(self.action_state["last_terminal_command"], "run student.js")

    async def test_duplicate_with_only_whitespace_and_doc_comment_changes_is_no_progress(self):
        self.api.files["student.js"] = 'export async function main(ns) { while (true) { await ns.hack("n00dles"); } }'
        variant = '/** @param {NS} ns */\nexport async function main(ns) {\n  while (true) {\n    await ns.hack("n00dles");\n  }\n}'
        result = await self.actions["game_deploy_script"]("student.js", variant)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("no functional code changes", result)
        self.assertEqual([call[0] for call in self.api.calls], ["getFile", "calculateRam"])

    async def test_ram_rejected_script_cannot_be_redeployed_before_process_diagnosis(self):
        self.action_state["ram_rejection"] = {
            "filename": "student.js", "host": "home", "required_ram": "1.70", "diagnosed": False,
        }
        result = await self.actions["game_deploy_script"](
            "student.js", "export async function main(ns) { await ns.grow('n00dles'); }"
        )
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("Inspect running processes with `ps`", result)
        self.assertIn("no file write was made", result)
        self.assertEqual(self.api.calls, [])

    async def test_recovered_ram_rejection_reports_unknown_host_without_writing(self):
        self.action_state["ram_rejection"] = {
            "filename": "student.js", "host": "unknown", "required_ram": "unknown", "diagnosed": False,
        }
        result = await self.actions["game_deploy_script"](
            "student.js", "export async function main(ns) { await ns.grow('n00dles'); }"
        )
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("host and exact requirement were not preserved", result)
        self.assertIn("no file write was made", result)
        self.assertEqual(self.api.calls, [])

    async def test_ram_rejected_script_may_be_revised_after_diagnosis(self):
        self.action_state["ram_rejection"] = {
            "filename": "student.js", "host": "home", "required_ram": "1.70", "diagnosed": True,
        }
        code = "export async function main(ns) { await ns.grow('n00dles'); }"
        result = await self.actions["game_deploy_script"]("student.js", code)
        self.assertIn("Deployed and read-back verified student.js", result)
        self.assertNotIn("ram_rejection", self.action_state)

    async def test_docs_returns_only_relevant_official_definition_excerpt(self):
        result = await self.actions["game_netscript_reference"]("ns.grow")
        self.assertIn("Exact signature for ns.grow: grow(host?: string, opts?: BasicHGWOptions): Promise<number>;", result)
        self.assertIn("Increase target money", result)
        self.assertNotIn("hack(host: string)", result)
        bare = await self.actions["game_netscript_reference"]("grow")
        self.assertIn("Exact signature for ns.grow: grow(host?: string, opts?: BasicHGWOptions): Promise<number>;", bare)
        with_args = await self.actions["game_netscript_reference"]("ns.grow(host, opts)")
        self.assertIn("Exact signature for ns.grow: grow(host?: string, opts?: BasicHGWOptions): Promise<number>;", with_args)
        self.assertIn("getDefinitionFile", [call[0] for call in self.api.calls])

    async def test_docs_lookup_failure_keeps_bridge_error(self):
        self.api.failure = ("getDefinitionFile", "definition request timed out")
        result = await self.actions["game_netscript_reference"]("ns.grow")
        self.assertIn("definition request timed out", result)

    async def test_deployment_failure_keeps_ram_error(self):
        self.api.failure = ("calculateRam", "Unknown Netscript function ns.fakeCall")
        result = await self.actions["game_deploy_script"]("student.js", "export function main(ns) {}")
        self.assertIn("Unknown Netscript function ns.fakeCall", result)

    async def test_http_error_body_is_preserved_for_model_debugging(self):
        async def respond(request):
            return httpx.Response(500, json={"success": False, "error": "Bitburner is not connected"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        with patch("app.remote_api_tools.httpx.AsyncClient", return_value=client):
            with self.assertRaisesRegex(RuntimeError, "Bitburner is not connected"):
                await RemoteApi("http://bridge", "token").call("getDefinitionFile", {})

    async def test_invalid_docs_query_is_rejected(self):
        result = await self.actions["game_netscript_reference"]("ns.weaken\ngetSaveFile")
        self.assertIn("ERROR:", result)
        self.assertEqual(self.api.calls, [])


if __name__ == "__main__":
    unittest.main()
