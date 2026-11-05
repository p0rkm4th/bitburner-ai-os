import unittest
from unittest.mock import patch

import httpx

from app.remote_api_tools import RemoteApi, register_remote_api_tools


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
        self.actions = register_remote_api_tools(FakeTools(), self.api)

    async def test_read_is_limited_to_simple_script_names_on_home(self):
        result = await self.actions["game_read_script"]("home.js")
        self.assertIn("main(ns)", result)
        self.assertEqual(self.api.calls, [("getFile", {"filename": "home.js", "server": "home"})])
        for invalid in ("../home.js", "foo/bar.js", "home.txt"):
            result = await self.actions["game_read_script"](invalid)
            self.assertIn("ERROR:", result)

    async def test_deploy_reads_back_and_calculates_ram(self):
        code = "export async function main(ns) { await ns.sleep(1); }"
        result = await self.actions["game_deploy_script"]("student.js", code)
        self.assertIn("read-back verified student.js", result)
        self.assertIn("1.6 GB", result)
        self.assertEqual([call[0] for call in self.api.calls], ["getFile", "pushFile", "getFile", "calculateRam"])
        self.assertTrue(all(call[1].get("server", "home") == "home" for call in self.api.calls))

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
        code = "export async function main(ns) { await ns.sleep(1); }"
        self.api.files["student.js"] = code
        result = await self.actions["game_deploy_script"]("student.js", code)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("calculated RAM: 1.6 GB", result)
        self.assertIn("Run it through the visible Terminal", result)
        self.assertEqual([call[0] for call in self.api.calls], ["getFile", "calculateRam"])

    async def test_duplicate_with_only_whitespace_and_doc_comment_changes_is_no_progress(self):
        self.api.files["student.js"] = 'export async function main(ns) { while (true) { await ns.hack("n00dles"); } }'
        variant = '/** @param {NS} ns */\nexport async function main(ns) {\n  while (true) {\n    await ns.hack("n00dles");\n  }\n}'
        result = await self.actions["game_deploy_script"]("student.js", variant)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("no functional code changes", result)
        self.assertEqual([call[0] for call in self.api.calls], ["getFile", "calculateRam"])

    async def test_docs_returns_only_relevant_official_definition_excerpt(self):
        result = await self.actions["game_netscript_reference"]("ns.grow")
        self.assertIn("Exact signature for ns.grow: grow(host?: string, opts?: BasicHGWOptions): Promise<number>;", result)
        self.assertIn("Increase target money", result)
        self.assertNotIn("hack(host: string)", result)
        bare = await self.actions["game_netscript_reference"]("grow")
        self.assertIn("Exact signature for ns.grow: grow(host?: string, opts?: BasicHGWOptions): Promise<number>;", bare)
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
