"""Small allowlisted gameplay documentation actions for the local agent."""
from pathlib import Path
import re

from browser_use import Tools


def _docs_root(module_file: str | Path = __file__) -> Path:
    """Resolve docs in both the flat image layout and source package layout."""
    module_dir = Path(module_file).resolve().parent
    for candidate in (module_dir / "docs", module_dir.parent / "docs"):
        if candidate.is_dir():
            return candidate
    # Keep the expected deployment location in the error if packaging omitted docs.
    return module_dir / "docs"


DOCS = _docs_root()
CORE_GUIDE = DOCS / "agent-game-guide.md"
MAX_HELP_CHARS = 3800


def load_core_guide() -> str:
    """Read the short guide on every session start, including resumed sessions."""
    text = CORE_GUIDE.read_text(encoding="utf-8").strip()
    if len(text) > 6000:
        raise RuntimeError("The always-loaded Bitburner guide exceeds its 6000 character budget")
    return text


def _sections(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    result: dict[str, list[str]] = {}
    current = "intro"
    result[current] = []
    for line in text.splitlines():
        match = re.match(r"^#{1,2}\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).casefold()
            result[current] = []
        else:
            result[current].append(line)
    return {key: "\n".join(lines).strip() for key, lines in result.items()}


HELP_TOPICS: dict[str, tuple[tuple[str, str], ...]] = {
    "observe": (("agent-tool-guide.md", "Bitburner agent tools"),),
    "tools": (("agent-tool-guide.md", "Bitburner agent tools"),),
    "servers": (("agent-game-guide.md", "Servers and hacking"),),
    "root": (("agent-game-guide.md", "Servers and hacking"),),
    "hacking": (("agent-game-guide.md", "Servers and hacking"),
                ("agent-game-guide.md", "Money, security, and progression")),
    "money": (("agent-game-guide.md", "Money, security, and progression"),),
    "progression": (("agent-game-guide.md", "Money, security, and progression"),),
    "netscript": (("agent-game-guide.md", "Netscript basics"),),
    "ram": (("agent-game-guide.md", "Netscript basics"),),
    "terminal": (("agent-game-guide.md", "File and execution conventions"),
                 ("agent-tool-guide.md", "Bitburner agent tools")),
    "files": (("agent-game-guide.md", "File and execution conventions"),),
    "errors": (("agent-troubleshooting.md", "Deployment and Netscript errors"),
               ("agent-troubleshooting.md", "Browser and modal errors")),
}


TROUBLESHOOT_TOPICS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("remote api", "getfile", "offline"), "Deployment and Netscript errors"),
    (("cannot run", "not enough ram", "process does not start", "available ram", "positive pid"),
     "RAM and active process errors"),
    (("filename", "file not found", "path"), "Deployment and Netscript errors"),
    (("scan-analyze", "incorrect usage", "unknown command"), "Deployment and Netscript errors"),
    (("ram", "calculate", "unknown netscript", "main", "function removed", "undefined"),
     "Deployment and Netscript errors"),
    (("cannot hack", "root", "hostname", "server"), "Deployment and Netscript errors"),
    (("dialog", "popup", "modal", "terminal not visible", "stale", "click", "unchanged"),
     "Browser and modal errors"),
    (("timeout", "context", "malformed", "repeat", "progress", "money"),
     "Observation, progress, and inference limits"),
)


def _render(parts: tuple[tuple[str, str], ...]) -> str:
    output = []
    for filename, heading in parts:
        section = _sections(DOCS / filename).get(heading.casefold())
        if section:
            output.append(f"## {heading}\n{section}")
    return "\n\n".join(output)[:MAX_HELP_CHARS]


def register_agent_doc_tools(tools: Tools) -> dict[str, object]:
    """Expose fixed documentation topics, never an arbitrary filesystem read."""

    @tools.action(description=(
        "Retrieve a short allowlisted Bitburner guide section. Topics: observe, tools, servers, root, "
        "hacking, money, progression, netscript, ram, terminal, files, errors. "
        "Use live game definitions for exact API signatures."
    ))
    async def game_help(topic: str) -> str:
        key = topic.strip().casefold()
        parts = HELP_TOPICS.get(key)
        if not parts:
            return "ERROR: Unknown topic. Allowed topics: " + ", ".join(HELP_TOPICS)
        try:
            return _render(parts)
        except Exception as exc:
            return f"ERROR: Could not load gameplay documentation: {type(exc).__name__}: {exc}"

    @tools.action(description=(
        "Retrieve concise recovery notes for a visible Bitburner, Netscript, Remote API, "
        "browser dialog, timeout, or progress error. Supply the actual error text."
    ))
    async def game_troubleshoot(error: str) -> str:
        query = error.strip().casefold()
        if not query:
            return "ERROR: Supply the visible error text or blocker."
        try:
            parts = []
            if query.startswith("command ") and " not found" in query:
                parts = [("agent-troubleshooting.md", "Deployment and Netscript errors")]
            for terms, heading in TROUBLESHOOT_TOPICS:
                if not parts and any(term in query for term in terms):
                    parts.append(("agent-troubleshooting.md", heading))
                    break
            if not parts:
                parts = [("agent-troubleshooting.md", "Deployment and Netscript errors"),
                         ("agent-troubleshooting.md", "Browser and modal errors"),
                         ("agent-troubleshooting.md", "Observation, progress, and inference limits")]
            return _render(tuple(parts))
        except Exception as exc:
            return f"ERROR: Could not load troubleshooting notes: {type(exc).__name__}: {exc}"

    return {"game_help": game_help, "game_troubleshoot": game_troubleshoot}
