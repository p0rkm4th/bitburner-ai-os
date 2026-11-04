"""Narrow Bitburner MCP bridge tools for authored scripts and official type docs.

The tools call the audited bridge's REST facade. They never expose arbitrary
Remote API method names, server names, save access, game state, or file deletion.
"""
import os
import re

import httpx
from browser_use import Tools


FILENAME = re.compile(r"^[A-Za-z0-9_.-]+\.js$")
IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]{0,79}$")
ALLOWED_METHODS = {"getFile", "pushFile", "calculateRam", "getDefinitionFile"}


class RemoteApi:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    async def call(self, method: str, params: dict) -> object:
        if method not in ALLOWED_METHODS:
            raise ValueError("Remote API method is not allowed")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/api/remote/{method}", json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            response.raise_for_status()
            payload = response.json()
        if not payload.get("success"):
            raise RuntimeError(str(payload.get("error", "Remote API request failed")))
        return payload.get("result")


def _safe_filename(filename: str) -> str:
    if not FILENAME.fullmatch(filename) or filename in {".", ".."}:
        raise ValueError("Use a simple .js filename without directories")
    return filename


def register_remote_api_tools(tools: Tools, api: RemoteApi) -> dict[str, object]:
    """Attach only four constrained operations to the existing Browser Use agent."""

    @tools.action(description=(
        "Read one existing .js Netscript file through Bitburner's official Remote API. "
        "Target is fixed to home. This does not inspect saves or other game state."
    ))
    async def game_read_script(filename: str) -> str:
        try:
            filename = _safe_filename(filename)
            content = await api.call("getFile", {"filename": filename, "server": "home"})
            if not isinstance(content, str):
                raise RuntimeError("The game did not return script text")
            return content[:30000]
        except Exception as exc:
            return f"ERROR: Could not read {filename}: {type(exc).__name__}: {exc}"

    @tools.action(description=(
        "Write model-authored Netscript into one .js file on home using Bitburner's "
        "official Remote API, then read it back and calculate its in-game RAM cost. "
        "The model must author and debug the code; use the visible game UI to execute it."
    ))
    async def game_deploy_script(filename: str, content: str) -> str:
        try:
            filename = _safe_filename(filename)
            if not content.strip() or len(content) > 30000:
                raise ValueError("Script content must be 1 to 30,000 characters")
            result = await api.call("pushFile", {
                "filename": filename, "content": content, "server": "home"
            })
            actual = await api.call("getFile", {"filename": filename, "server": "home"})
            if result != "OK" or actual != content:
                raise RuntimeError("The game did not confirm a matching script write")
            ram = await api.call("calculateRam", {"filename": filename, "server": "home"})
            return f"Deployed and read-back verified {filename}; calculated RAM: {ram} GB. Run it through game_run_script."
        except Exception as exc:
            return f"ERROR: Could not deploy {filename}: {type(exc).__name__}: {exc}"

    @tools.action(description=(
        "Read a small excerpt for one Netscript symbol from the official type definitions "
        "served by this Bitburner version. This is documentation only; it does not inspect game state."
    ))
    async def game_netscript_reference(symbol: str) -> str:
        try:
            if not IDENTIFIER.fullmatch(symbol):
                raise ValueError("Query one Netscript identifier, such as weaken or getHackingLevel")
            definition = await api.call("getDefinitionFile", {})
            if not isinstance(definition, str):
                raise RuntimeError("The game did not return its Netscript definitions")
            lines = definition.splitlines()
            hits = [i for i, line in enumerate(lines) if re.search(rf"\b{re.escape(symbol)}\b", line)]
            if not hits:
                return f"No match for {symbol} in this game's Netscript definitions."
            excerpts = [lines[i] for i in hits[:8]]
            return "Official in-game Netscript type definition lines:\n" + "\n".join(excerpts)[:5000]
        except Exception as exc:
            return f"ERROR: Could not read Netscript reference: {type(exc).__name__}: {exc}"

    return {
        "game_read_script": game_read_script,
        "game_deploy_script": game_deploy_script,
        "game_netscript_reference": game_netscript_reference,
    }


def remote_api_from_env() -> RemoteApi | None:
    base_url = os.getenv("BITBURNER_REMOTE_API_URL", "").strip()
    token = os.getenv("BITBURNER_REMOTE_API_TOKEN", "").strip()
    if bool(base_url) != bool(token):
        raise RuntimeError("Set both BITBURNER_REMOTE_API_URL and BITBURNER_REMOTE_API_TOKEN")
    return RemoteApi(base_url, token) if base_url else None
