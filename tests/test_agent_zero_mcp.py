"""Security and dispatch tests for the optional Agent Zero Browser Use bridge."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from pydantic import BaseModel

import app.server as server


class TerminalParams(BaseModel):
    command: str


class AgentZeroMcpTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.old = {
            "enabled": server.mcp_game_tools,
            "browser": server.shared_browser,
            "state": server.status.get("state"),
            "runner": server.runner,
            "run_task": server.agent_run_task,
        }
        server.mcp_game_tools = None
        server.shared_browser = object()
        server.status["state"] = "stopped"
        server.runner = None
        server.agent_run_task = None
        server.mcp_action_state.clear()
        server.mcp_action_lock = __import__("asyncio").Lock()
        self.env = patch.dict(os.environ, {
            "AGENT_ZERO_MCP_ENABLED": "1",
            "AGENT_ZERO_MCP_TOKEN": "test-token",
        })
        self.env.start()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server.app), base_url="http://test"
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        self.env.stop()
        server.mcp_game_tools = self.old["enabled"]
        server.shared_browser = self.old["browser"]
        server.status["state"] = self.old["state"]
        server.runner = self.old["runner"]
        server.agent_run_task = self.old["run_task"]

    def install_fake_tool(self, function):
        action = SimpleNamespace(param_model=TerminalParams, function=function)
        server.mcp_game_tools = SimpleNamespace(
            registry=SimpleNamespace(
                registry=SimpleNamespace(actions={"game_terminal": action})
            )
        )

    async def test_browser_action_is_authenticated_validated_and_uses_shared_session(self):
        function = AsyncMock(return_value="visible terminal output")
        self.install_fake_tool(function)
        response = await self.client.post(
            "/api/agent-zero/tools/game_terminal",
            headers={"Authorization": "Bearer test-token"},
            json={"command": "ls"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": "visible terminal output", "success": True})
        function.assert_awaited_once()
        self.assertIs(function.await_args.kwargs["browser_session"], server.shared_browser)
        self.assertEqual(function.await_args.kwargs["params"].command, "ls")

    async def test_invalid_arguments_keep_actionable_validation_error(self):
        function = AsyncMock(return_value="unused")
        self.install_fake_tool(function)
        response = await self.client.post(
            "/api/agent-zero/tools/game_terminal",
            headers={"Authorization": "Bearer test-token"}, json={},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("command", response.json()["detail"])
        function.assert_not_awaited()

    async def test_unauthorized_and_unadvertised_tools_are_rejected(self):
        response = await self.client.post("/api/agent-zero/tools/game_terminal", json={"command": "ls"})
        self.assertEqual(response.status_code, 401)
        response = await self.client.post(
            "/api/agent-zero/tools/getSaveFile",
            headers={"Authorization": "Bearer test-token"}, json={},
        )
        self.assertEqual(response.status_code, 404)

    async def test_browser_use_owner_and_agent_zero_mode_exclude_each_other(self):
        function = AsyncMock(return_value="unused")
        self.install_fake_tool(function)
        server.status["state"] = "running"
        response = await self.client.post(
            "/api/agent-zero/tools/game_terminal",
            headers={"Authorization": "Bearer test-token"}, json={"command": "ls"},
        )
        self.assertEqual(response.status_code, 409)
        function.assert_not_awaited()

        response = await self.client.post("/api/start", json={"objective": "test"})
        self.assertEqual(response.status_code, 409)

    async def test_disabled_bridge_is_not_discoverable_or_callable(self):
        with patch.dict(os.environ, {"AGENT_ZERO_MCP_ENABLED": "0"}):
            response = await self.client.post(
                "/api/agent-zero/tools/game_terminal",
                headers={"Authorization": "Bearer test-token"}, json={"command": "ls"},
            )
        self.assertEqual(response.status_code, 404)

    def test_browser_mcp_allowlist_matches_registered_game_tools(self):
        with patch.dict(os.environ, {
            "BITBURNER_REMOTE_API_URL": "http://127.0.0.1:3001",
            "BITBURNER_REMOTE_API_TOKEN": "test-token",
        }):
            tools = server.create_game_tools({})
        registered = set(tools.registry.registry.actions)
        self.assertTrue(server.MCP_GAME_ACTIONS <= registered)
        self.assertNotIn("evaluate", server.MCP_GAME_ACTIONS)
        self.assertNotIn("run_bash", server.MCP_GAME_ACTIONS)
        self.assertNotIn("write_file", server.MCP_GAME_ACTIONS)


if __name__ == "__main__":
    unittest.main()
