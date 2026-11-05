"""Narrow Bitburner MCP bridge tools for authored scripts and official type docs.

The tools call the audited bridge's REST facade. They never expose arbitrary
Remote API method names, server names, save access, game state, or file deletion.
"""
import os
import re

import httpx
from browser_use import Tools


FILENAME = re.compile(r"^[A-Za-z0-9_.-]+\.js$")
IDENTIFIER = re.compile(r"^(?:ns\.)?([A-Za-z_$][A-Za-z0-9_$]{0,79})$")
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
            try:
                payload = response.json()
            except ValueError:
                payload = {"error": response.text[:1200]}
        if response.is_error:
            detail = payload.get("error") or payload.get("message") or response.text
            raise RuntimeError(f"{method} returned HTTP {response.status_code}: {str(detail)[:1200]}")
        if not payload.get("success"):
            detail = payload.get("error") or payload.get("message") or "Remote API request failed"
            raise RuntimeError(f"{method} failed: {str(detail)[:1200]}")
        return payload.get("result")


def _safe_filename(filename: str) -> str:
    if not FILENAME.fullmatch(filename) or filename in {".", ".."}:
        raise ValueError("Use a simple .js filename without directories")
    return filename


def _same_script_ignoring_formatting_and_doc_comments(left: str, right: str) -> bool:
    """Catch cosmetic re-authoring loops without treating code changes as duplicates."""
    def normalize(source: str) -> str:
        source = re.sub(r"/\*\*.*?\*/", "", source, flags=re.DOTALL)
        return re.sub(r"\s+", "", source)

    return normalize(left) == normalize(right)


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
            try:
                existing = await api.call("getFile", {"filename": filename, "server": "home"})
            except RuntimeError as exc:
                # The audited bridge maps Bitburner's missing-file response to
                # HTTP 500 with this generic API message. Existing files remain
                # readable; allow a constrained push to establish a new file,
                # then require the usual exact read-back before reporting it.
                # Any other read error still stops before a write.
                if str(exc) != "getFile returned HTTP 500: Bitburner API error":
                    raise
                existing = None
            if isinstance(existing, str) and _same_script_ignoring_formatting_and_doc_comments(existing, content):
                ram = await api.call("calculateRam", {"filename": filename, "server": "home"})
                return (f"NO_PROGRESS: {filename} already exists on home with equivalent code; "
                        f"read-back verified with no functional code changes, calculated RAM: {ram} GB, "
                        "and no write was made. "
                        "Do not redeploy identical contents. Run it through the visible Terminal or "
                        "diagnose the actual execution error.")
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
            requested = symbol.strip()
            match = IDENTIFIER.fullmatch(requested)
            if not match:
                raise ValueError("Query one Netscript identifier, such as ns.grow, grow, or getHackingLevel")
            name = match.group(1)
            definition = await api.call("getDefinitionFile", {})
            if not isinstance(definition, str):
                raise RuntimeError("The game did not return its Netscript definitions")
            lines = definition.splitlines()
            signature = re.compile(rf"^\s*{re.escape(name)}\s*\(.*\)\s*:")
            index = next((i for i, line in enumerate(lines) if signature.search(line)), None)
            if index is None:
                return f"No exact Netscript function signature found for {name} in this game's definitions."

            start = index
            for candidate in range(index - 1, max(-1, index - 50), -1):
                if lines[candidate].strip().startswith("/**"):
                    start = candidate
                    break
            doc_lines = lines[start:index]
            # Keep both the short description and parameter/return details. Some
            # Netscript docblocks are long enough to push their signature out of
            # a naive prefix truncation, so always put the exact signature first.
            excerpt = list(doc_lines[:10]) + list(doc_lines[-5:])
            excerpt = list(dict.fromkeys(line for line in excerpt if line.strip()))
            return (f"Exact signature for ns.{name}: {lines[index].strip()}\n"
                    "Official documentation excerpt:\n" + "\n".join(excerpt))[:2500]
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
