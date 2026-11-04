import unittest

from app.remote_api_tools import register_remote_api_tools


class FakeTools:
    def action(self, description=""):
        def decorate(fn):
            return fn
        return decorate


class FakeApi:
    def __init__(self):
        self.files = {"home.js": "export async function main(ns) {}"}
        self.calls = []

    async def call(self, method, params):
        self.calls.append((method, params))
        if method == "pushFile":
            self.files[params["filename"]] = params["content"]
            return "OK"
        if method == "getFile":
            return self.files.get(params["filename"], "")
        if method == "calculateRam":
            return 1.6
        if method == "getDefinitionFile":
            return "export interface NS {\n  weaken(host: string): Promise<number>;\n\n  hack(host: string): Promise<number>;\n}"
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
        self.assertEqual([call[0] for call in self.api.calls], ["pushFile", "getFile", "calculateRam"])
        self.assertTrue(all(call[1].get("server", "home") == "home" for call in self.api.calls))

    async def test_docs_returns_only_relevant_official_definition_excerpt(self):
        result = await self.actions["game_netscript_reference"]("weaken")
        self.assertIn("weaken(host: string)", result)
        self.assertNotIn("hack(host: string)", result)
        self.assertIn("getDefinitionFile", [call[0] for call in self.api.calls])

    async def test_invalid_docs_query_is_rejected(self):
        result = await self.actions["game_netscript_reference"]("ns.weaken\ngetSaveFile")
        self.assertIn("ERROR:", result)
        self.assertEqual(self.api.calls, [])


if __name__ == "__main__":
    unittest.main()
