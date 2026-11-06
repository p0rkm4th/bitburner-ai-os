"""Small local control plane for the persistent Bitburner browser agent."""
import asyncio
import gzip
import hashlib
import html
import json
import logging
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Optional

import httpx
from browser_use import Agent, BrowserProfile, BrowserSession, ChatOllama, Tools
from browser_use.agent.views import ActionResult
from browser_use.filesystem.file_system import FileSystem
from browser_use.tools.views import DoneAction
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
try:  # Package import for tests, flat import for the deployment image.
    from .agent_docs import load_core_guide, register_agent_doc_tools
    from .agent_prompt import BITBURNER_SYSTEM_PROMPT
    from .game_tools import _modal, find_visible_tab_node, register_game_tools, visible_runtime_error
    from .remote_api_tools import (deployment_guard_checkpoint, pending_script_run, pending_script_run_message,
                                   register_remote_api_tools,
                                   remote_api_from_env, restore_deployment_guard)
except ImportError:
    from agent_docs import load_core_guide, register_agent_doc_tools
    from agent_prompt import BITBURNER_SYSTEM_PROMPT
    from game_tools import _modal, find_visible_tab_node, register_game_tools, visible_runtime_error
    from remote_api_tools import (deployment_guard_checkpoint, pending_script_run, pending_script_run_message,
                                  register_remote_api_tools,
                                  remote_api_from_env, restore_deployment_guard)

STATE = Path(os.getenv("STATE_DIR", "/state"))
for name in ("profile", "checkpoints", "logs", "screenshots", "saves", "backups"):
    (STATE / name).mkdir(parents=True, exist_ok=True)
SAVE_DOWNLOADS = STATE / "saves"
SAVE_BACKUPS = STATE / "backups"
NATIVE_SAVE_NAME = re.compile(r"^bitburnerSave_\d+_BN\d+x\d+\.json\.gz$")
ARCHIVE_NAME = re.compile(r"^native-save-\d{8}T\d{6}Z-[0-9a-f]{12}\.json\.gz$")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bitburner-agent")
app = FastAPI(title="Bitburner AI OS", docs_url=None, redoc_url=None)
gate = asyncio.Lock()
runner: Optional[asyncio.Task] = None
agent_run_task: Optional[asyncio.Task] = None
backup_worker: Optional[asyncio.Task] = None
agent: Optional[Agent] = None
shared_browser: Optional[BrowserSession] = None
started_at = None
events: list[dict] = []
status = {"state": "stopped", "objective": "", "model": os.getenv("OLLAMA_MODEL", "unset"),
          "node": os.getenv("INFERENCE_NODE", "unconfigured"), "error": "", "steps": 0}
stop_requested = False
pause_event = asyncio.Event()
pause_event.set()
existing_events = STATE / "logs" / "actions.jsonl"
if existing_events.exists():
    try:
        events = [json.loads(line) for line in existing_events.read_text().splitlines()[-30:]]
    except Exception:
        log.exception("Could not load recent action events")


def record(kind: str, message: str) -> None:
    item = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kind": kind, "message": str(message)[:1200]}
    events.append(item)
    del events[:-300]
    log_path = STATE / "logs" / "actions.jsonl"
    if log_path.exists() and log_path.stat().st_size > 1_000_000:
        for generation in (2, 1):
            src = log_path.with_suffix(f".jsonl.{generation}") if generation > 1 else log_path.with_suffix(".jsonl")
            dst = log_path.with_suffix(f".jsonl.{generation + 1}")
            if src.exists():
                shutil.move(src, dst)
        if log_path.exists():
            shutil.move(log_path, log_path.with_suffix(".jsonl.1"))
    with log_path.open("a") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def save_checkpoint(checkpoint: dict) -> None:
    path = STATE / "checkpoints" / "latest.json"
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def save_runtime(state: str, **extra) -> None:
    path = STATE / "checkpoints" / "runtime.json"
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    data = {"state": state, "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **extra}
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


async def visible_snapshot(browser: Optional[BrowserSession]) -> str:
    if browser is None:
        return ""
    try:
        summary = await browser.get_browser_state_summary(include_screenshot=False)
        return summary.dom_state.llm_representation()[:5000]
    except Exception as exc:
        return f"Visible UI unavailable: {type(exc).__name__}"


def visible_script_evidence(text: str) -> list[str]:
    """Keep only script names/results actually present in rendered UI text."""
    markers = (".js", "script", "running", "income", "error", "RAM")
    lines = [line.strip()[:300] for line in text.splitlines()
             if any(marker.casefold() in line.casefold() for marker in markers)]
    return lines[-12:]


def startup_resume_allowed(auto_resume: str, runtime_state: Optional[str], objective_exists: bool) -> bool:
    return auto_resume == "1" and objective_exists and runtime_state not in {
        "operator_stopped", "failed", "exhausted", "completed", "paused"
    }


def watchdog_expired(state: str, idle_seconds: float, idle_limit: float) -> bool:
    return state != "paused" and idle_seconds >= idle_limit


VISIBLE_MONEY = re.compile(r"\bMoney\b[^$]{0,60}\$\s*([\d,.]+)\s*([kmbt]?)", re.IGNORECASE)
MONEY_SUFFIXES = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000, "t": 1_000_000_000_000}


def visible_money_amount(visible: str) -> Optional[float]:
    match = VISIBLE_MONEY.search(visible)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "")) * MONEY_SUFFIXES[match.group(2).casefold()]
    except (ValueError, KeyError):
        return None


def money_completion_block(objective: str, success: bool, action_state: dict,
                           visible: str) -> Optional[str]:
    """Require observable execution and increased in-game money before a success claim."""
    if not success or not re.search(r"\b(money|income|earnings|profit)\b", objective, re.IGNORECASE):
        return None
    if not action_state.get("confirmed_script_run"):
        return "No visible successful Netscript run has been confirmed. Use the visible game terminal to run your authored script and inspect its result before claiming success."
    baseline = action_state.get("money_at_script_run")
    if baseline is None:
        baseline = action_state.get("initial_visible_money")
    current = visible_money_amount(visible)
    if baseline is None or current is None:
        return "Visible money could not be compared with the session baseline. Use game_progress to observe the current balance and verify the result before claiming success."
    if current <= baseline:
        return (f"The game-visible balance has not increased from the session baseline (${baseline:,.0f}; current ${current:,.0f}). "
                "Inspect the script output and game_progress, debug using the returned evidence, and retry within the session budget.")
    return None


def money_progress_verified(objective: str, action_state: dict, visible: str) -> bool:
    """Recognize visible progress for money objectives without completing the task."""
    if not re.search(r"\b(money|income|earnings|profit)\b", objective, re.IGNORECASE):
        return False
    if not action_state.get("confirmed_script_run"):
        return False
    baseline = action_state.get("money_at_script_run")
    if baseline is None:
        baseline = action_state.get("initial_visible_money")
    current = visible_money_amount(visible)
    reward = re.search(
        r"(?:successfully hacked .+? for|\b(?:earned|reward|profit|income)\b[^$\n]{0,50})\s*\$\s*([\d,]+(?:\.\d+)?)",
        visible, re.IGNORECASE,
    )
    positive_reward = bool(reward and float(reward.group(1).replace(",", "")) > 0)
    return (positive_reward and baseline is not None and current is not None and
            current > baseline)


def register_completion_guard(tools: Tools, objective: str, action_state: dict) -> None:
    """Replace Browser Use's unconditional `done` with a visible-evidence gate."""
    default_done = tools.registry.registry.actions["done"].function

    @tools.action(
        description=("Finish the task only after checking the user's objective. For money or income objectives, "
                     "success requires a visibly confirmed script run and an increased visible game balance. "
                     "A read-back-verified deployment must be visibly run before ending, even when reporting failure."),
        param_model=DoneAction,
    )
    async def done(params: DoneAction, browser_session: BrowserSession,
                   file_system: FileSystem) -> ActionResult | str:
        pending = pending_script_run_message(action_state)
        if pending:
            return ActionResult(is_done=False, success=False,
                                extracted_content="Cannot finish before the deployed script is run: " + pending)
        visible_now = await visible_snapshot(browser_session)
        if action_state.get("initial_visible_money") is None:
            action_state["initial_visible_money"] = visible_money_amount(visible_now)
        block = money_completion_block(objective, params.success, action_state, visible_now)
        if block:
            return ActionResult(is_done=False, success=False,
                                extracted_content="Success not accepted: " + block)
        result = await default_done(params=params, file_system=file_system)
        if (params.success and getattr(result, "is_done", False) and
                getattr(result, "success", False)):
            action_state["accepted_done"] = True
            action_state["done_report"] = params.text[:1200]
        return result


def runtime_session_number(value) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def highest_recorded_session(state_dir: Optional[Path] = None, current: Any = 0) -> int:
    """Return the highest session number in runtime/checkpoint data without trusting either alone."""
    root = state_dir or STATE
    highest = runtime_session_number(current)
    for path in (root / "checkpoints" / "runtime.json", root / "checkpoints" / "latest.json"):
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError, TypeError):
            continue
        if isinstance(data, dict):
            highest = max(highest, runtime_session_number(data.get("session")))
    return highest


def browser_task(objective: str, progress: str, current_url: str, game_url: str) -> str:
    """Avoid reloading the persistent game tab when continuing an existing session."""
    if current_url.rstrip("/") == game_url.rstrip("/"):
        # Browser Use treats any URL in a task as an initial navigation request.
        # Do not include the URL at all while already on the game page.
        prefix = "Bitburner is already open in the persistent browser tab. Do not navigate or reload it."
    else:
        prefix = f"Open {game_url} using ordinary visible browser controls."
    return f"{prefix} {objective}{progress}"


def gameplay_task(objective: str, progress: str, current_url: str, game_url: str,
                  *, remote_authoring: bool, pending_script: Optional[str] = None,
                  ram_diagnosis_required: bool = False) -> str:
    """Build the same compact, guide-backed instruction on every resumed session."""
    task = browser_task(objective, progress, current_url, game_url)
    task += (" Once the requested success evidence is visible and verified, call done(success=True) immediately; "
             "do not add cleanup or extra observations after the evidence is sufficient. For a money/income objective, "
             "a visible positive script reward together with a game_progress balance above the recorded baseline is "
             "sufficient: report the script, reward, and before/after balance in done, without killing the script or "
             "taking another observation.")
    if remote_authoring:
        task += (" Use game_read_script/game_deploy_script for model-authored script work, "
                 "game_netscript_reference for exact live APIs, game_open_tab for visible game pages, game_terminal/game_run_script "
                 "for visible execution, and game_observe/game_progress for verification. After each script run, inspect the visible result; "
                 "after game_deploy_script confirms read-back and RAM, run that exact filename through game_run_script before rewriting or "
                 "deploying it again. An earlier Terminal `ls` does not disprove a later verified deployment. "
                 "A PID confirms startup only. After a script starts, use game_progress to verify visible money, hacking level, and script income; "
                 "do not attribute aggregate Active Scripts production to your script unless its visible row or output confirms that script. "
                 "do not poll by repeating game_observe. If game_observe says NO_PROGRESS, do not repeat it; use game_progress or take a different "
                 "useful action, and finish once the objective has visible evidence. If a runtime error appears, call game_troubleshoot with its exact text, check the named API "
                 "against the current live reference, revise your own script, and retry within the step budget. Verify actual money/output "
                 "before claiming success. For missing root access, inspect the target's visible root, skill, and port requirements; "
                 "verify any Netscript root-access API against the live reference before revising your script. If a dialog remains after "
                 "one game_dismiss_dialog attempt, do not call it again for an unchanged dialog; report the visible blocker. If the tool reports a "
                 "dialog transition, inspect the newly revealed dialog text and diagnose that new state before acting. If the first observation shows a "
                 "dialog, read it and call game_dismiss_dialog once; do not repeat an unchanged observation.")
    if remote_authoring and pending_script:
        task += (f" PRIORITY RESUME STEP: {pending_script} is already deployed and must be executed before any other Terminal "
                 "command. Your first game action must be game_run_script with this exact filename and expected_host='home'. "
                 "This checkpoint requirement takes precedence over any general task instruction to list files or inspect scripts. "
                 "If execution returns a visible error, use that exact error to choose the next diagnostic; do not redeploy first.")
    elif remote_authoring and ram_diagnosis_required:
        task += (" PRIORITY RECOVERY STEP: a visible script RAM rejection is unresolved. Before authoring or deploying any "
                 "file, inspect visible running processes with game_terminal('ps') or open the visible Active Scripts page, "
                 "then base the next action on that evidence.")
    return ("BITBURNER CORE GUIDE (compact, version-aware orientation; use live game state and definitions where version-specific):\n"
            + load_core_guide() + "\n\nSESSION TASK:\n" + task)


def checkpoint_last_action_failed(checkpoint: dict) -> bool:
    """A failed last tool action invalidates its model-suggested continuation."""
    results = checkpoint.get("tool_results", []) or []
    return any(isinstance(item, dict) and item.get("state") in ("failed", "game_error")
               for item in results)


def checkpoint_prompt_summary(checkpoint: dict) -> dict:
    """Pass only compact, useful progress context to the next model session."""
    remote_authoring = bool(os.getenv("BITBURNER_REMOTE_API_URL") and
                            os.getenv("BITBURNER_REMOTE_API_TOKEN"))

    def obsolete_editor_text(value: object) -> bool:
        text = str(value).casefold()
        return any(marker in text for marker in (
            "game_open_editor", "game_edit_script", "monaco", "editor input",
            "script editor", "visible editor", "open the editor",
        ))

    def clean_items(values) -> list[str]:
        items = [str(x)[:350] for x in values[-4:]]
        if remote_authoring:
            items = [item for item in items if not obsolete_editor_text(item)]
        return items

    objective = str(checkpoint.get("objective", ""))[:500]
    subobjective = str(checkpoint.get("subobjective", ""))[:500]
    latest_visible = str(checkpoint.get("latest_visible_state", ""))[-1400:]
    next_action = str(checkpoint.get("next_intended_action", ""))[:500]
    tool_results = checkpoint.get("tool_results", [])[-4:]
    previous_step_failed = checkpoint_last_action_failed(checkpoint)
    scripts = checkpoint.get("scripts_and_observed_results", [])[-6:]
    stored_action_state = {}
    restore_deployment_guard(checkpoint, stored_action_state)
    deployment_guard = deployment_guard_checkpoint(stored_action_state)
    if remote_authoring:
        if obsolete_editor_text(objective) or obsolete_editor_text(subobjective):
            objective = "Use the current task objective; previous editor-based guidance is obsolete."
            subobjective = "Read scripts and author them with the official Remote API; execute and observe through the visible game UI."
        if obsolete_editor_text(latest_visible):
            latest_visible = "Prior UI snapshot is stale. Use game_observe for the current visible state."
        if obsolete_editor_text(next_action):
            next_action = "Prior editor action is obsolete. Use game_read_script, consult official definitions, then author and deploy with game_deploy_script."
        scripts = [item for item in scripts if not obsolete_editor_text(item)]
    if deployment_guard:
        filename = deployment_guard["last_deployed_filename"]
        next_action = (f"Run the latest verified {filename} through game_run_script and inspect the visible result "
                       "before attempting another deployment.")
    if previous_step_failed:
        if deployment_guard:
            filename = deployment_guard["last_deployed_filename"]
            subobjective = (f"A verified deployment of {filename} is still pending execution. Re-observe the current UI, "
                            "then complete that execution before changing or redeploying the script.")
            next_action = (f"Use game_run_script({filename!r}, expected_host=\"home\"). If Terminal is hidden, "
                           "open it through the visible game interaction; if its prompt shows another host, connect home, "
                           "verify the prompt, then run the pending file. Inspect the actual output/error afterward.")
        else:
            subobjective = "The prior step failed; treat its subobjective and next action as historical suggestions. Observe the current game and choose a different evidence-based action from the recorded error."
            next_action = "Re-observe current visible state, diagnose the latest tool error, and do not repeat the action it rejected."
    return {
        "session": checkpoint.get("session"), "steps": checkpoint.get("steps"),
        "objective": objective,
        "subobjective": subobjective,
        "accomplishments": clean_items(checkpoint.get("accomplishments", [])),
        "latest_visible_state": latest_visible,
        "scripts_and_observed_results": scripts,
        "errors": clean_items(checkpoint.get("errors", [])),
        "tool_results": tool_results,
        "tool_metrics": checkpoint.get("tool_metrics", {}),
        "deployment_guard": deployment_guard,
        "next_intended_action": next_action,
    }


RAM_REJECTION_PATTERN = re.compile(
    r"Cannot run\s+([A-Za-z0-9_.-]+\.js)\s+\(t=\d+\)\s+on\s+([A-Za-z0-9_.-]+)\.\s+This script requires\s+([\d.]+)\s*GB of RAM",
    re.IGNORECASE,
)


def checkpoint_ram_rejection(checkpoint: Optional[dict]) -> Optional[dict]:
    """Restore a visible RAM rejection as a diagnostic gate after session restart."""
    if not checkpoint:
        return None
    stored = checkpoint.get("ram_rejection")
    if isinstance(stored, dict) and stored.get("filename") and stored.get("host"):
        return {"filename": str(stored["filename"]).casefold(), "host": str(stored["host"]),
                "required_ram": str(stored.get("required_ram", "unknown")), "diagnosed": False}
    candidates = [checkpoint.get("latest_visible_state", ""), *checkpoint.get("scripts_and_observed_results", []),
                  *checkpoint.get("errors", []), checkpoint.get("subobjective", ""),
                  checkpoint.get("next_intended_action", "")]
    for candidate in reversed(candidates):
        match = RAM_REJECTION_PATTERN.search(str(candidate))
        if match:
            return {"filename": match.group(1).casefold(), "host": match.group(2),
                    "required_ram": match.group(3), "diagnosed": False}
    generic_ram_failure = any(
        re.search(r"command failed because of RAM limits|script failed because of RAM limits", str(item), re.I)
        for item in checkpoint.get("errors", [])
    )
    if generic_ram_failure:
        for candidate in (checkpoint.get("next_intended_action", ""), checkpoint.get("subobjective", "")):
            filename = re.search(r"([A-Za-z0-9_.-]+\.js)", str(candidate), re.I)
            if filename:
                return {"filename": filename.group(1).casefold(), "host": "unknown",
                        "required_ram": "unknown", "diagnosed": False}
    return None


def create_game_tools(action_state: Optional[dict] = None) -> Tools:
    """Limit the player to in-game interactions; app startup owns initial navigation."""
    action_state = action_state if action_state is not None else {}
    tools = Tools(exclude_actions=["evaluate", "write_file", "replace_file", "read_file", "upload_file",
                                  "search", "search_page", "save_as_pdf", "run_python", "run_bash",
                                  "navigate", "go_back", "click", "input", "select_dropdown",
                                  "dropdown_options", "find_elements", "find_text", "scroll", "switch",
                                  "close", "send_keys", "extract"])
    remote_api = remote_api_from_env()
    register_game_tools(tools, include_editor=remote_api is None, action_state=action_state)
    register_agent_doc_tools(tools)
    if remote_api is not None:
        # Remote API is the reliable authoring path; generic text entry can
        # otherwise send the model back into fragile editor/terminal typing.
        tools.registry.registry.actions.pop("input", None)
        register_remote_api_tools(tools, remote_api, action_state=action_state)
    return tools


def inference_timeout_settings() -> dict[str, int]:
    """Keep large visual model calls bounded while allowing a slower local response."""
    llm_timeout = max(60, min(180, int(os.getenv("LLM_TIMEOUT", "150"))))
    step_timeout = max(llm_timeout + 15, min(240, int(os.getenv("STEP_TIMEOUT", "180"))))
    return {"llm_timeout": llm_timeout, "step_timeout": step_timeout}


def agent_context_settings() -> dict[str, int | bool]:
    """Keep short action histories so visual traces do not consume the local context window."""
    # Browser Use validates this setting as None or strictly greater than 5.
    history = max(6, min(8, int(os.getenv("MAX_HISTORY_ITEMS", "6"))))
    checkpoint_limit = max(800, min(3000, int(os.getenv("CHECKPOINT_PROMPT_LIMIT", "1400"))))
    return {"max_history_items": history, "checkpoint_prompt_limit": checkpoint_limit,
            "message_compaction": True}


def bitnode1_completion_confirmed(report: str, visible: str) -> bool:
    report_lines = [line.casefold() for line in report.splitlines()]
    positive_marker = any("bitnode_1_complete" in line and
                          not any(term in line for term in ("not yet", "not verified", "incomplete", "not complete"))
                          for line in report_lines)
    ui = re.sub(r"[-_\s]+", " ", visible.casefold())
    visible_confirmation = bool(re.search(r"bitnode 1.{0,100}(completed|complete|destroyed|finished)", ui) or
                                re.search(r"(completed|complete|destroyed|finished).{0,100}bitnode 1", ui))
    return positive_marker and visible_confirmation


def scoped_goal_completion_confirmed(objective: str, checkpoint: dict) -> bool:
    """Accept a guarded `done` for bounded goals, but require BitNode evidence for long-term goals."""
    requires_bitnode = bool(re.search(r"\bbit\s*node\s*1\b", objective, re.IGNORECASE))
    return bool(checkpoint.get("accepted_done")) and not requires_bitnode


def progress_signature(visible: str, action: str) -> str:
    """Compare rendered content and actions without volatile browser element IDs."""
    visible = re.sub(r"\[\d+\]", "[]", visible)
    visible = re.sub(r"offline for \d+ seconds", "offline for # seconds", visible, flags=re.IGNORECASE)
    action = re.sub(r'("index"\s*:\s*)\d+', r"\1#", action)
    return hashlib.sha256((visible + "\n" + action).encode()).hexdigest()


def stagnation_count(previous: dict, current: dict) -> int:
    """Persist a session-level stagnation streak, discounting UI churn and repeated action patterns."""
    old_state = re.sub(r"\[\d+\]", "[]", str(previous.get("latest_visible_state", "")))
    new_state = re.sub(r"\[\d+\]", "[]", str(current.get("latest_visible_state", "")))
    old_state = re.sub(r"offline for \d+ seconds", "offline for # seconds", old_state, flags=re.I)
    new_state = re.sub(r"offline for \d+ seconds", "offline for # seconds", new_state, flags=re.I)
    action = re.sub(r'("index"\s*:\s*)\d+', r"\1#", str(current.get("action", "")))
    old_action = re.sub(r'("index"\s*:\s*)\d+', r"\1#", str(previous.get("action", "")))
    action_history = list(previous.get("recent_actions", []))[-3:]
    action_history.append(hashlib.sha256(action.encode()).hexdigest()[:16])
    action_history = action_history[-4:]
    # Only visible gameplay change or successful action evidence resets the streak.
    changed = bool(old_state and new_state and old_state != new_state)
    repeated_cycle = len(action_history) == 4 and len(set(action_history)) <= 2
    completed = int(current.get("action_count", 0)) > 0 and action != old_action and not repeated_cycle
    if changed or (completed and not repeated_cycle):
        count = 0
    else:
        count = int(previous.get("no_progress_sessions", 0)) + 1
    current["recent_actions"] = action_history
    current["no_progress_sessions"] = count
    return count


def summarize_action_results(actions: list[dict], results: list[object]) -> list[dict[str, str]]:
    """Normalize Browser Use tool replies without retaining authored code or long output."""
    summaries = []
    for index, action in enumerate(actions):
        name = next(iter(action), "unknown") if isinstance(action, dict) else "unknown"
        result = results[index] if index < len(results) else None
        error = str(getattr(result, "error", "") or "").strip()
        content = str(getattr(result, "extracted_content", "") or "").strip()
        if error:
            state, message = "failed", error
        elif content.startswith("NO_PROGRESS:"):
            state, message = "game_error", content.splitlines()[0]
        elif content.startswith("ERROR:"):
            state, message = "failed", content.splitlines()[0]
        elif name == "game_run_script" and re.search(
                r"runtime\s+error|script crashed|does not have a main function|requires .*? RAM|not enough RAM|"
                r"does not have root access|cannot hack .*? yet|requires root access", content, re.I):
            message = visible_runtime_error(content) or next(
                (line.strip() for line in content.splitlines()
                 if re.search(r"script crashed|does not have a main function|requires .*? RAM|not enough RAM|"
                              r"does not have root access|cannot hack .*? yet|requires root access", line, re.I)),
                "Visible script runtime error",
            )
            state = "game_error"
        elif name == "game_terminal" and re.search(
                r"(?im)^\s*(?:visible game error|incorrect usage\b|runtime error\b|error:|unknown command\b|command .+ not found\b|cannot run .*requires .*? RAM|not enough RAM|.*(?:does not have root access|cannot hack this server yet).*)", content):
            state = "game_error"
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            message = next((lines[index + 1] if line.casefold().startswith("visible game error") and index + 1 < len(lines)
                            else line for index, line in enumerate(lines)
                            if re.search(r"(?i)^\s*(?:visible game error|incorrect usage\b|runtime error\b|error:|unknown command\b|command .+ not found\b|cannot run .*requires .*? RAM|not enough RAM|.*(?:does not have root access|cannot hack this server yet).*)", line)),
                           "Visible Terminal command error")
        else:
            state, message = "returned", "Tool returned a visible result"
        summaries.append({"tool": name, "state": state, "message": message[:320]})
    # Preserve framework errors even if a malformed response has fewer action records.
    for result in results[len(actions):]:
        error = str(getattr(result, "error", "") or getattr(result, "extracted_content", "") or "").strip()
        if error:
            summaries.append({"tool": "unmapped", "state": "failed", "message": error[:320]})
    return summaries[-8:]


def should_count_visible_runtime_error(message: str, existing_errors: list[str],
                                      tool_results: list[dict[str, str]]) -> bool:
    """Count a delayed visible runtime error once when its run tool result missed it."""
    if not message or message in existing_errors:
        return False
    return not any(item.get("state") == "game_error" and
                   item.get("tool") in ("game_run_script", "game_terminal")
                   for item in tool_results)


def failed_action_repeat_count(previous_signature: str, previous_count: int,
                               current_signature: str) -> int:
    """Count consecutive identical failed action/state signatures; empty means reset."""
    if not current_signature:
        return 0
    return previous_count + 1 if current_signature == previous_signature else 1


def failed_result_signature(actions: list[dict], visible: str, failures: list[dict]) -> str:
    """Identify consecutive identical failed tool or structured-model responses."""
    if not failures:
        return ""
    state = re.sub(r"\[\d+\]", "[]", visible)
    pending_deployment = any(
        item.get("tool") == "game_deploy_script" and
        item.get("state") == "game_error" and
        str(item.get("message", "")).startswith("NO_PROGRESS:") and
        "without a visible execution" in str(item.get("message", ""))
        for item in failures
    )
    if pending_deployment:
        # Changing proposed source cannot unblock a verified file awaiting a
        # visible run. Visible money/HUD churn also cannot unblock it. Give one
        # recovery step, then stop repeated redeploys.
        action_json = json.dumps(["game_deploy_script:pending_run_required"])
        failure_text = "game_deploy_script:NO_PROGRESS:pending_run_required"
        state = ""
    else:
        blocked_ram_redeploy = None
        for item in failures:
            if item.get("tool") != "game_deploy_script":
                continue
            match = re.search(
                r"last visible run of ([A-Za-z0-9_.-]+\.js) on ([A-Za-z0-9_.-]+) failed because it required ([\d.]+) GB of RAM",
                str(item.get("message", "")), re.IGNORECASE)
            if match:
                blocked_ram_redeploy = tuple(part.casefold() for part in match.groups())
                break
        if blocked_ram_redeploy:
            filename, host, required_ram = blocked_ram_redeploy
            # Source edits cannot resolve a host RAM rejection. Treat every
            # changed-content retry as the same failed action until the model
            # takes a successful diagnostic step.
            action_json = json.dumps([f"game_deploy_script:ram_rejected:{filename}:{host}"])
            failure_text = f"game_deploy_script:NO_PROGRESS:ram_rejected:{filename}:{host}:{required_ram}"
            state = ""
        else:
            action_json = json.dumps(actions, sort_keys=True, ensure_ascii=False)
            failure_text = "|".join(str(item.get("tool", "unknown")) + ":" +
                                    str(item.get("message", "")) for item in failures)
            if any(str(item.get("message", "")).startswith("NO_PROGRESS:")
                   for item in failures):
                # A tool has explicitly rejected the repeated action without
                # sending it. Background game output can still change the DOM
                # every second, so it must not reset this same-action streak.
                state = ""
    return hashlib.sha256((action_json + "\n" + state + "\n" + failure_text).encode()).hexdigest()


def failure_signature_for_tool_results(actions: list[dict], visible: str,
                                       results: list[dict[str, str]]) -> str:
    """Only count a failed response when it contains no successful recovery action."""
    failures = [item for item in results if item.get("state") in ("failed", "game_error")]
    if not failures:
        return ""
    pending_deployment = any(
        item.get("tool") == "game_deploy_script" and
        item.get("state") == "game_error" and
        str(item.get("message", "")).startswith("NO_PROGRESS:") and
        "without a visible execution" in str(item.get("message", ""))
        for item in failures
    )
    # A successful model-chosen diagnostic earns a fresh recovery opportunity
    # for this specific guard. Preserve ordinary failed-action behavior.
    if pending_deployment and any(
            item.get("state") == "returned" and item.get("tool") != "game_observe"
            for item in results):
        return ""
    return failed_result_signature(actions, visible, failures)


class StartRequest(BaseModel):
    objective: str = Field(min_length=3, max_length=2000)


def get_model() -> ChatOllama:
    base = os.environ["OLLAMA_BASE_URL"].rstrip("/")
    model = os.environ["OLLAMA_MODEL"]
    timeout = float(os.getenv("OLLAMA_TIMEOUT", "180"))
    options = {"num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "16384")),
               "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
               "seed": int(os.getenv("OLLAMA_SEED", "7")),
               "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "30m")}
    options.update(ollama_think_options())
    client_type = ChatOllama
    if os.getenv("OLLAMA_METRICS_PATH"):
        client_type = MeasuredChatOllama
    return client_type(model=model, host=base, timeout=timeout, ollama_options=options)


def ollama_think_options() -> dict:
    """Return an explicit Ollama thinking override only when configured."""
    value = os.getenv("OLLAMA_THINK", "").strip().lower()
    if not value:
        return {}
    if value not in {"true", "false"}:
        raise ValueError("OLLAMA_THINK must be 'true' or 'false' when set")
    return {"think": value == "true"}


class MeasuredOllamaClient:
    """Record Ollama response counters and timings without retaining prompts or outputs."""
    FIELDS = ("model", "prompt_eval_count", "eval_count", "total_duration",
              "load_duration", "prompt_eval_duration", "eval_duration", "done_reason")

    def __init__(self, client, path: str):
        self.client = client
        self.path = Path(path)

    async def chat(self, **kwargs):
        started = time.monotonic()
        try:
            response = await self.client.chat(**kwargs)
            row = {name: getattr(response, name, None) for name in self.FIELDS}
            row["elapsed_seconds"] = round(time.monotonic() - started, 3)
            self._append(row)
            return response
        except Exception as exc:
            self._append({"model": kwargs.get("model"), "elapsed_seconds": round(time.monotonic() - started, 3),
                          "error": f"{type(exc).__name__}: {exc}"[:400]})
            raise

    def _append(self, row: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row["time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


class MeasuredChatOllama(ChatOllama):
    """Optional Ollama wrapper used only for isolated benchmark runs."""
    def get_client(self):
        return MeasuredOllamaClient(super().get_client(), os.environ["OLLAMA_METRICS_PATH"])


def get_browser_profile() -> BrowserProfile:
    domains = [d.strip() for d in os.getenv("ALLOWED_DOMAINS", "bitburner-official.github.io").split(",") if d.strip()]
    return BrowserProfile(user_data_dir=str(STATE / "profile"), headless=False, allowed_domains=domains,
                          downloads_path=str(STATE / "saves"), enable_default_extensions=False, keep_alive=True)


def archive_native_save(source: Path) -> tuple[str, int]:
    """Validate and archive a completed Bitburner-named save without reading its contents into memory."""
    stat = source.stat()
    if stat.st_size <= 0 or stat.st_size > 50_000_000:
        raise ValueError("export size outside 1 byte to 50 MB")
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup = SAVE_BACKUPS / f"native-save-{timestamp}-{digest.hexdigest()[:12]}.json.gz"
    temporary = backup.with_name(backup.name + ".partial")
    if backup.exists():
        source.unlink(missing_ok=True)
        return backup.name, stat.st_size
    try:
        shutil.copy2(source, temporary)
        # Verify the gzip CRC while bounding expanded data to avoid accepting a compressed bomb.
        expanded = 0
        with gzip.open(temporary, "rb") as stream:
            while chunk := stream.read(1024 * 1024):
                expanded += len(chunk)
                if expanded > 250_000_000:
                    raise ValueError("expanded export exceeds 250 MB")
        os.replace(temporary, backup)
        source.unlink(missing_ok=True)
        return backup.name, stat.st_size
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def visible_control_by_text(dom_state, label: str):
    matches = []
    for node in getattr(dom_state, "selector_map", {}).values():
        if not getattr(node, "is_visible", False):
            continue
        if " ".join(str(node.get_all_children_text()).split()) == label:
            matches.append(node)
    return matches[0] if len(matches) == 1 else None


async def _request_periodic_game_export_locked() -> Optional[tuple[str, int]]:
    """Export a native save through the visible game UI when the agent is idle."""
    if (shared_browser is None or os.getenv("VNC_INTERACTIVE", "0") == "1" or
            status.get("state") in ("running", "paused") or
            (runner is not None and not runner.done()) or
            (agent_run_task is not None and not agent_run_task.done())):
        return None
    page = await shared_browser.get_current_page()
    if page is None or "bitburner-official.github.io" not in await page.get_url():
        return None
    state = await shared_browser.get_browser_state_summary(include_screenshot=False)
    visible = state.dom_state.llm_representation()
    if await _modal(page, visible):
        if "offline for" not in visible.casefold() or "your scripts generated" not in visible.casefold():
            return None
        tools = Tools()
        register_game_tools(tools, action_state={})
        dismiss = tools.registry.registry.actions["game_dismiss_dialog"]
        dismissed = await dismiss.function(params=dismiss.param_model(), browser_session=shared_browser)
        if not str(dismissed).startswith("Dialog dismissed and verified absent"):
            return None
        record("backup", "Acknowledged visible offline-progress dialog before scheduled native export")
        state = await shared_browser.get_browser_state_summary(include_screenshot=False)
        visible = state.dom_state.llm_representation()
        if await _modal(page, visible):
            return None
    already_on_export_page = "Export Game" in visible and "System" in visible
    if not already_on_export_page:
        options = find_visible_tab_node(state.dom_state, "Options")
        if options is None:
            return None
        await (await page.get_element(options.backend_node_id)).click()
        state = await shared_browser.get_browser_state_summary(include_screenshot=False)
        visible = state.dom_state.llm_representation()
        system = find_visible_tab_node(state.dom_state, "System")
        if "Export Game" not in visible and system is not None:
            await (await page.get_element(system.backend_node_id)).click()
            state = await shared_browser.get_browser_state_summary(include_screenshot=False)
            visible = state.dom_state.llm_representation()
    if "Export Game" not in visible or "System" not in visible:
        return None
    export_button = visible_control_by_text(state.dom_state, "Export Game")
    if export_button is None:
        return None
    before = {p.name: p.stat().st_size for p in SAVE_DOWNLOADS.iterdir() if p.is_file()}
    await (await page.get_element(export_button.backend_node_id)).click()
    await asyncio.sleep(2)
    new_exports = [p for p in SAVE_DOWNLOADS.iterdir()
                   if p.is_file() and NATIVE_SAVE_NAME.fullmatch(p.name) and
                   (p.name not in before or p.stat().st_size != before[p.name]) and p.stat().st_size > 0]
    if not new_exports:
        raise RuntimeError("Visible Export Game click produced no nonempty native save download")
    if not already_on_export_page:
        after = await shared_browser.get_browser_state_summary(include_screenshot=False)
        terminal = find_visible_tab_node(after.dom_state, "Terminal")
        if terminal is not None:
            await (await page.get_element(terminal.backend_node_id)).click()
    return new_exports[0].name, new_exports[0].stat().st_size


async def request_periodic_game_export() -> Optional[tuple[str, int]]:
    """Serialize browser export with agent startup so both can't claim the UI."""
    async with gate:
        return await _request_periodic_game_export_locked()


async def archive_game_saves() -> None:
    """Archive only stable, Bitburner-named native exports with bounded retention."""
    retention = max(1, min(100, int(os.getenv("SAVE_BACKUP_RETENTION", "30"))))
    export_interval = max(60, min(7 * 24 * 3600,
                                  int(os.getenv("SAVE_EXPORT_INTERVAL_SECONDS", "21600"))))
    next_export = time.monotonic() + export_interval
    seen: dict[str, tuple[int, int]] = {}
    failed: dict[str, tuple[int, int]] = {}
    while True:
        try:
            for source in SAVE_DOWNLOADS.iterdir():
                if not source.is_file() or not NATIVE_SAVE_NAME.fullmatch(source.name):
                    continue
                signature = (0, 0)
                try:
                    stat = source.stat()
                    signature = (stat.st_size, stat.st_mtime_ns)
                    if stat.st_size <= 0 or stat.st_size > 50_000_000 or time.time() - stat.st_mtime < 20:
                        continue
                    if seen.get(source.name) != signature:
                        seen[source.name] = signature
                        continue
                    if failed.get(source.name) == signature:
                        continue
                    name, size = await asyncio.to_thread(archive_native_save, source)
                    record("backup", f"Archived gzip-validated native game save {name} ({size} bytes)")
                    seen.pop(source.name, None)
                    failed.pop(source.name, None)
                except Exception as exc:
                    failed[source.name] = signature
                    record("warning", f"Native game-save archive skipped {source.name}: {type(exc).__name__}")
            archives = sorted((p for p in SAVE_BACKUPS.iterdir() if p.is_file() and ARCHIVE_NAME.fullmatch(p.name)),
                              key=lambda p: p.stat().st_mtime, reverse=True)
            for old in archives[retention:]:
                old.unlink(missing_ok=True)
            if time.monotonic() >= next_export:
                try:
                    result = await request_periodic_game_export()
                    if result:
                        record("backup", f"Triggered periodic visible game save export {result[0]} ({result[1]} bytes)")
                        next_export = time.monotonic() + export_interval
                    else:
                        next_export = time.monotonic() + min(export_interval, 900)
                except Exception as exc:
                    record("warning", f"Periodic visible game save export failed: {type(exc).__name__}")
                    next_export = time.monotonic() + min(export_interval, 900)
        except Exception as exc:
            record("warning", f"Game-save backup watcher error: {type(exc).__name__}")
            log.exception("Game-save backup watcher failed")
        await asyncio.sleep(max(15, int(os.getenv("SAVE_BACKUP_SCAN_SECONDS", "30"))))


async def run_agent(objective: str) -> None:
    global agent, shared_browser, agent_run_task
    status.update(state="running", objective=objective, error="", steps=0, node=os.getenv("INFERENCE_NODE", "unconfigured"))
    record("session", f"Started: {objective}")
    profile = get_browser_profile()
    if shared_browser is None:
        shared_browser = BrowserSession(browser_profile=profile)
    # These stock actions provide arbitrary code/file access; gameplay must use the UI and Netscript.
    checkpoint_path = STATE / "checkpoints" / "latest.json"
    previous = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else None
    action_state = {}
    if previous:
        restore_deployment_guard(previous, action_state)
    rejection = checkpoint_ram_rejection(previous)
    if rejection:
        action_state["ram_rejection"] = rejection
    tools = create_game_tools(action_state)
    register_completion_guard(tools, objective, action_state)

    checkpoint_limit = int(agent_context_settings()["checkpoint_prompt_limit"])
    progress = (f"\nPrevious checkpoint (compact summary): "
                f"{json.dumps(checkpoint_prompt_summary(previous), ensure_ascii=False)[:checkpoint_limit]}" if previous else "")
    game_url = os.getenv("GAME_URL", "https://bitburner-official.github.io/")
    current_url = ""
    if shared_browser is not None:
        try:
            current_url = (await shared_browser.get_browser_state_summary(include_screenshot=False)).url
        except Exception:
            pass
    task = gameplay_task(objective, progress, current_url, game_url,
                         remote_authoring=remote_api_from_env() is not None,
                         pending_script=pending_script_run(action_state),
                         ram_diagnosis_required=bool(action_state.get("ram_rejection") and
                                                     not action_state["ram_rejection"].get("diagnosed")))
    last_activity = time.monotonic()
    prior = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {}
    accomplishments = list(prior.get("accomplishments", []))[-8:]
    errors = list(prior.get("errors", []))[-8:]
    visible = prior.get("latest_visible_state", "")
    previous_step_failed = checkpoint_last_action_failed(prior)
    subobjective = ("" if previous_step_failed else str(prior.get("subobjective", "")))
    last_output = {}
    last_actions = []
    successful_actions = 0
    previous_failure_signature = ""
    repeated_failure_count = 0
    tool_metrics = {"calls": 0, "failed": 0, "game_errors": 0}
    status["tool_metrics"] = tool_metrics

    async def on_step_start(current: Agent) -> None:
        # The inactivity clock advances only after a completed step, never merely
        # because a slow model call started.
        return None

    async def on_step_end(current: Agent) -> None:
        nonlocal last_activity, visible, last_output, last_actions, subobjective, successful_actions
        nonlocal previous_failure_signature, repeated_failure_count
        last_activity = time.monotonic()
        status["steps"] += 1
        actions = []
        output = {}
        latest = None
        try:
            latest = current.history.history[-1]
            output = latest.model_output.model_dump(exclude_none=True, mode="json")
            actions = [a.model_dump(exclude_none=True, mode="json") for a in latest.model_output.action]
        except Exception:
            pass
        last_output = output
        last_actions = actions
        subobjective = str(output.get("next_goal") or subobjective)[:700]
        visible = await visible_snapshot(shared_browser)
        tool_results = summarize_action_results(actions, list(getattr(latest, "result", []) or [])) if latest else []
        runtime_error = visible_runtime_error(visible)
        count_visible_error = False
        if runtime_error:
            # Runtime failures can appear after `run` already returned a PID.
            # Preserve that independently observed failure for recovery and the
            # next session instead of treating startup confirmation as success.
            message = f"Visible Netscript runtime error: {runtime_error[:600]}"
            count_visible_error = should_count_visible_runtime_error(message, errors, tool_results)
            if message not in errors:
                errors.append(message)
                del errors[:-8]
        visible_money = visible_money_amount(visible)
        if action_state.get("initial_visible_money") is None and visible_money is not None:
            action_state["initial_visible_money"] = visible_money
        if (action_state.get("confirmed_script_run") and
                action_state.get("money_at_script_run") is None and visible_money is not None):
            action_state["money_at_script_run"] = visible_money
        tool_metrics["calls"] += len(actions)
        tool_metrics["failed"] += sum(item["state"] == "failed" for item in tool_results)
        tool_metrics["game_errors"] += sum(item["state"] == "game_error" for item in tool_results)
        tool_metrics["game_errors"] += int(count_visible_error)
        successful_actions += sum(item["state"] == "returned" for item in tool_results)
        for item in tool_results:
            if item["state"] in ("failed", "game_error"):
                message = f"{item['tool']}: {item['message']}"
                if not errors or errors[-1] != message:
                    errors.append(message[:700])
                    del errors[:-8]
            record("tool", f"{item['tool']} {item['state']}: {item['message'][:180]}")
        failed_results = [item for item in tool_results if item["state"] in ("failed", "game_error")]
        if failed_results:
            # Framework failures such as empty/malformed structured model output
            # have no action bundle. Count them by the unchanged visible state
            # and exact failure so they receive the same bounded recovery as a
            # repeated failed UI tool call.
            repeat_signature = failure_signature_for_tool_results(actions, visible, tool_results)
            repeated_failure_count = failed_action_repeat_count(
                previous_failure_signature, repeated_failure_count, repeat_signature)
            previous_failure_signature = repeat_signature
            if repeated_failure_count >= 2:
                status["error"] = "The same failed model/tool result repeated with no visible state change; session stopped to prevent an unproductive loop."
                errors.append(status["error"])
                if (any(item.get("tool") == "game_observe" and
                        str(item.get("message", "")).startswith("NO_PROGRESS:")
                        for item in tool_results) and
                        money_progress_verified(objective, action_state, visible)):
                    status["outcome"] = "progress_verified_report_missing"
                    record("outcome", "Visible money-objective progress was verified, but the agent repeated a guarded observation before reporting completion")
                    save_runtime("active", objective=objective,
                                 session=status.get("session", 1), outcome=status["outcome"])
                current.stop()
        else:
            previous_failure_signature = ""
            repeated_failure_count = 0
        evaluation = str(output.get("evaluation_previous_goal") or "")
        if evaluation and any(word in evaluation.casefold() for word in ("failed", "failure", "error", "unsuccessful")):
            errors.append(evaluation[:700])
            del errors[:-8]
        accomplishment = evaluation or (f"Completed visible browser action: {json.dumps(actions, ensure_ascii=False)[:500]}"
                                         if actions else "")
        if accomplishment and accomplishment not in accomplishments:
            accomplishments.append(accomplishment[:700])
            del accomplishments[:-8]
        record("action", f"Step {status['steps']}: {json.dumps(actions, ensure_ascii=False)[:700]}")
        save_checkpoint({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "objective": objective, "subobjective": subobjective,
                         "accomplishments": accomplishments, "latest_visible_state": visible,
                         "scripts_and_observed_results": visible_script_evidence(visible), "errors": errors,
                         "tool_results": tool_results, "tool_metrics": dict(tool_metrics),
                         "session_outcome": status.get("outcome"),
                         "ram_rejection": action_state.get("ram_rejection"),
                         "deployment_guard": deployment_guard_checkpoint(action_state),
                         "unresolved_problems": errors[-4:], "next_intended_action": subobjective,
                         "session": status.get("session", 1), "steps": status["steps"],
                         "state": "active", "action": json.dumps(actions, ensure_ascii=False)[:1000],
                         "action_count": successful_actions})
        if status["steps"] % 4 == 0:
            shot = STATE / "screenshots" / f"{int(time.time())}.png"
            try:
                await current.browser_session.take_screenshot(path=str(shot))
                images = sorted((STATE / "screenshots").glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
                for old in images[20:]:
                    old.unlink(missing_ok=True)
            except Exception as exc:
                record("warning", f"Screenshot capture failed: {type(exc).__name__}")

    agent = Agent(task=task, llm=get_model(), browser_profile=profile, browser_session=shared_browser, tools=tools,
                  use_vision=True, use_judge=False, max_failures=int(os.getenv("MAX_FAILURES", "2")),
                  override_system_message=BITBURNER_SYSTEM_PROMPT,
                  max_actions_per_step=1, enable_planning=False, loop_detection_enabled=True,
                  loop_detection_window=8, enable_signal_handler=False,
                  # Startup owns initial game navigation; Browser Use must not
                  # synthesize an excluded `navigate` action from guide URLs.
                  directly_open_url=False,
                  max_history_items=int(agent_context_settings()["max_history_items"]),
                  message_compaction=True,
                  **inference_timeout_settings(),
                  save_conversation_path=STATE / "logs" / "conversation.json")
    try:
        agent_run_task = asyncio.create_task(agent.run(max_steps=int(os.getenv("MAX_STEPS", "16")),
                                                        on_step_start=on_step_start, on_step_end=on_step_end))
        idle_limit = max(60, int(os.getenv("IDLE_TIMEOUT", "900")))
        time_limit = max(60, int(os.getenv("MAX_SESSION_SECONDS", "3600")))
        session_started = time.monotonic()
        while not agent_run_task.done():
            if status["state"] == "paused":
                last_activity = time.monotonic()
                await asyncio.sleep(1)
                continue
            try:
                await asyncio.wait_for(asyncio.shield(agent_run_task), timeout=min(5, idle_limit))
            except asyncio.TimeoutError:
                if time.monotonic() - session_started >= time_limit:
                    agent.stop()
                    agent_run_task.cancel()
                    await asyncio.gather(agent_run_task, return_exceptions=True)
                    raise TimeoutError(f"Session exceeded {time_limit} seconds")
                if watchdog_expired(status["state"], time.monotonic() - last_activity, idle_limit):
                    agent.stop()
                    agent_run_task.cancel()
                    await asyncio.gather(agent_run_task, return_exceptions=True)
                    raise TimeoutError(f"No agent step completed for {idle_limit} seconds")
        history = await agent_run_task
        status["steps"] = len(history.history)
        record("session", f"Completed {len(history.history)} steps")
        final_result = str(history.final_result() or "")[:1200]
        checkpoint = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "objective": objective,
                      "subobjective": subobjective,
                      "accomplishments": accomplishments, "latest_visible_state": await visible_snapshot(shared_browser),
                      "scripts_and_observed_results": visible_script_evidence(await visible_snapshot(shared_browser)), "errors": errors,
                      "tool_results": summarize_action_results(
                          [last_actions[-1]] if last_actions else [],
                          list(getattr(history.history[-1], "result", []) or []) if history.history else []),
                      "tool_metrics": dict(tool_metrics),
                      "session_outcome": status.get("outcome"),
                      "accepted_done": bool(action_state.get("accepted_done")),
                      "done_report": action_state.get("done_report", ""),
                      "ram_rejection": action_state.get("ram_rejection"),
                      "deployment_guard": deployment_guard_checkpoint(action_state),
                      "unresolved_problems": errors[-4:], "next_intended_action": final_result or subobjective,
                      "session": status.get("session", 1), "steps": len(history.history),
                      "state": "active", "result": final_result,
                      "action": json.dumps(last_actions, ensure_ascii=False)[:1000],
                      "action_count": successful_actions}
        save_checkpoint(checkpoint)
        record("checkpoint", final_result or (accomplishments[-1] if accomplishments else "Session ended at step limit"))
    except asyncio.CancelledError:
        status.update(state="operator_stopped" if stop_requested else "active")
        record("session", "Cancelled by operator" if stop_requested else "Interrupted; resumable checkpoint retained")
        raise
    except Exception as exc:
        status.update(error=f"{type(exc).__name__}: {exc}")
        errors.append(status["error"][:700])
        try:
            save_checkpoint({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "objective": objective,
                             "subobjective": subobjective,
                             "accomplishments": accomplishments, "latest_visible_state": await visible_snapshot(shared_browser),
                             "scripts_and_observed_results": visible_script_evidence(await visible_snapshot(shared_browser)), "errors": errors[-8:],
                             "unresolved_problems": errors[-4:], "next_intended_action": subobjective,
                             "tool_metrics": dict(tool_metrics),
                             "ram_rejection": action_state.get("ram_rejection"),
                             "deployment_guard": deployment_guard_checkpoint(action_state),
                             "session": status.get("session", 1), "steps": status["steps"], "state": "active"})
        except Exception:
            log.exception("Could not persist failure checkpoint")
        record("error", status["error"])
    finally:
        child = agent_run_task
        if child and not child.done():
            if agent:
                agent.stop()
            child.cancel()
            await asyncio.gather(child, return_exceptions=True)
        agent_run_task = None
        if status["state"] == "running":
            status["state"] = "active"
        agent = None


async def supervise(objective: str) -> None:
    """Continue bounded sessions until progress exhaustion or an explicit terminal state."""
    global stop_requested
    objective_path = STATE / "checkpoints" / "objective.json"
    tmp = objective_path.with_name(objective_path.name + ".tmp")
    tmp.write_text(json.dumps({"objective": objective}, indent=2))
    os.replace(tmp, objective_path)
    configured = max(0, int(os.getenv("MAX_SESSIONS", "0")))
    maximum = configured or 1_000_000_000
    retry_limit = max(1, min(4, int(os.getenv("MAX_RETRIES", "2"))))
    no_progress_limit = max(2, min(20, int(os.getenv("NO_PROGRESS_SESSIONS", "5"))))
    failures = 0
    number = runtime_session_number(status.get("session"))
    runtime_path = STATE / "checkpoints" / "runtime.json"
    try:
        persisted_runtime = json.loads(runtime_path.read_text()) if runtime_path.exists() else {}
    except Exception:
        persisted_runtime = {}
    while number < maximum and not stop_requested:
        while status.get("state") == "paused" and not stop_requested:
            await asyncio.sleep(1)
        if stop_requested:
            break
        number += 1
        status.update(session=number, sessions_limit=configured or "unlimited")
        save_runtime("active", objective=objective, session=number,
                     outcome=status.get("outcome"))
        try:
            await run_agent(objective)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # Setup failures occur before Agent.run exists; persist them and send them
            # through the same bounded retry policy as runtime failures.
            status.update(error=f"{type(exc).__name__}: {exc}")
            record("error", f"Agent setup/session failed: {status['error']}")
            try:
                previous = json.loads((STATE / "checkpoints" / "latest.json").read_text())
            except Exception:
                previous = {}
            previous.update(time=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            objective=objective, session=number, state="active",
                            errors=(list(previous.get("errors", [])) + [status["error"]])[-8:],
                            unresolved_problems=[status["error"]],
                            next_intended_action=previous.get("next_intended_action") or "Retry after setup failure")
            try:
                save_checkpoint(previous)
            except Exception:
                log.exception("Could not persist setup failure checkpoint")
        if stop_requested:
            break
        if status.get("error"):
            failures += 1
            if failures >= retry_limit:
                record("supervisor", f"Stopped after {failures} consecutive failed sessions")
                status.update(state="failed")
                save_runtime("failed", error=status["error"], objective=objective,
                             outcome=status.get("outcome"))
                break
            delay = min(300, max(10, int(os.getenv("SESSION_DELAY", "60"))) * (2 ** (failures - 1)))
            await asyncio.sleep(delay)
            continue
        failures = 0
        checkpoint = STATE / "checkpoints" / "latest.json"
        data = json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
        observed = str(data.get("latest_visible_state", ""))
        action = str(data.get("action", ""))
        no_progress = stagnation_count(persisted_runtime, data)
        report = "\n".join([str(data.get("result", "")), str(data.get("next_intended_action", "")),
                            *[str(item) for item in data.get("accomplishments", [])]])
        if bitnode1_completion_confirmed(report, observed):
            status.update(state="completed")
            save_runtime("completed", objective=objective, session=number)
            record("supervisor", "Model reported and visible UI confirmed BitNode 1 completion")
            break
        if scoped_goal_completion_confirmed(objective, data):
            status.update(state="completed", outcome="objective_done")
            save_runtime("completed", objective=objective, session=number,
                         outcome="objective_done")
            record("supervisor", "Guarded model completion accepted for the bounded objective")
            break
        if no_progress >= no_progress_limit:
            status.update(state="exhausted", error=f"No observable progress across {no_progress} sessions")
            save_runtime("exhausted", objective=objective, session=number)
            record("supervisor", f"Stopped after {no_progress} sessions with no observable progress")
            break
        save_runtime("active", objective=objective, session=number,
                     no_progress_sessions=no_progress, recent_actions=data.get("recent_actions", []),
                     latest_visible_state=observed, action=action,
                     outcome=status.get("outcome"))
        persisted_runtime = {"no_progress_sessions": no_progress,
                             "recent_actions": data.get("recent_actions", []),
                             "latest_visible_state": observed, "action": action}
        await asyncio.sleep(max(10, min(600, int(os.getenv("SESSION_DELAY", "60")))))
    if stop_requested:
        status["state"] = "operator_stopped"
        save_runtime("operator_stopped")
    elif status["state"] == "active":
        status["state"] = "exhausted"
        save_runtime("exhausted", reason="Configured session limit reached")
    record("supervisor", f"Supervisor ended with state {status['state']}")


@app.get("/api/status")
async def get_status():
    checkpoint = STATE / "checkpoints" / "latest.json"
    return {**status, "events": events[-30:], "checkpoint": json.loads(checkpoint.read_text()) if checkpoint.exists() else None}


@app.get("/api/game-observation")
async def game_observation():
    """Expose only the rendered, model-visible game UI text, never game internals."""
    if shared_browser is None:
        return {"available": False, "message": "Start the player to open the game browser."}
    try:
        summary = await shared_browser.get_browser_state_summary(include_screenshot=False)
        text = summary.dom_state.llm_representation()
        current = {}
        for path, label in (("memory.current", "ram_used_bytes"), ("memory.max", "ram_limit_bytes")):
            try:
                current[label] = int(Path("/sys/fs/cgroup/" + path).read_text().strip())
            except (OSError, ValueError):
                current[label] = None
        return {"available": True, "url": summary.url, "title": summary.title,
                "visible_ui": text[:12000], "runtime": current,
                "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    except Exception as exc:
        raise HTTPException(503, f"Visible game observation unavailable: {type(exc).__name__}")


@app.get("/api/health")
async def health():
    return {"ok": True, "state": status["state"], "browser_ready": shared_browser is not None}


@app.get("/api/backups")
async def get_backups():
    archives = sorted((p for p in SAVE_BACKUPS.iterdir() if p.is_file() and ARCHIVE_NAME.fullmatch(p.name)),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    return {"count": len(archives), "retention": max(1, min(100, int(os.getenv("SAVE_BACKUP_RETENTION", "30")))),
            "backups": [{"name": p.name, "size_bytes": p.stat().st_size,
                         "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime))}
                        for p in archives]}


@app.post("/api/start")
async def start(req: StartRequest):
    global runner, stop_requested
    async with gate:
        if runner and not runner.done():
            raise HTTPException(409, "An agent session is already active")
        if agent_run_task and not agent_run_task.done():
            raise HTTPException(409, "The previous Agent.run() task is still terminating")
        stop_requested = False
        last_session = highest_recorded_session(current=status.get("session", 0))
        status.update(state="active", error="", objective=req.objective, session=last_session, steps=0, outcome=None)
        save_runtime("active", objective=req.objective, session=last_session)
        runner = asyncio.create_task(supervise(req.objective))
    return {"started": True}


@app.post("/api/pause")
async def pause():
    if status["state"] not in ("running", "active"):
        raise HTTPException(409, "No active session")
    status["state"] = "paused"
    pause_event.clear()
    if agent:
        agent.pause()
    save_runtime("paused", objective=status.get("objective", ""), session=status.get("session", 0))
    record("control", "Paused")
    return {"paused": True}


@app.post("/api/resume")
async def resume():
    global runner
    if status["state"] != "paused":
        raise HTTPException(409, "No paused session")
    if agent:
        agent.resume()
    pause_event.set()
    status["state"] = "active"
    if runner is None or runner.done():
        objective_path = STATE / "checkpoints" / "objective.json"
        if not objective_path.exists():
            raise HTTPException(409, "No saved objective to resume")
        runner = asyncio.create_task(supervise(json.loads(objective_path.read_text())["objective"]))
    save_runtime("active", objective=status.get("objective", ""), session=status.get("session", 0))
    record("control", "Resumed")
    return {"resumed": True}


@app.post("/api/stop")
async def stop():
    global stop_requested
    stop_requested = True
    status["state"] = "operator_stopped"
    save_runtime("operator_stopped", session=status.get("session", 0))
    if agent:
        agent.stop()
    child = agent_run_task
    if child and not child.done():
        try:
            await asyncio.wait_for(asyncio.shield(child), timeout=15)
        except asyncio.TimeoutError:
            child.cancel()
            await asyncio.gather(child, return_exceptions=True)
    if runner and not runner.done():
        runner.cancel()
        await asyncio.gather(runner, return_exceptions=True)
    # An explicit emergency stop must survive a later service/VM restart.
    (STATE / "checkpoints" / "objective.json").unlink(missing_ok=True)
    record("control", "Emergency stop")
    return {"stopped": True}


@app.post("/api/inference-check")
async def inference_check():
    base = os.environ["OLLAMA_BASE_URL"].rstrip("/")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(base + "/api/tags")
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            return {"endpoint": base, "model": os.getenv("OLLAMA_MODEL"), "models": models,
                    "model_available": os.getenv("OLLAMA_MODEL") in models}
        except Exception as exc:
            raise HTTPException(502, f"Inference endpoint check failed: {type(exc).__name__}")


@app.on_event("startup")
async def auto_resume():
    global runner, shared_browser, backup_worker
    # Keep the actual game visible and ready for observation even while inference is idle.
    backup_worker = asyncio.create_task(archive_game_saves())
    try:
        shared_browser = BrowserSession(browser_profile=get_browser_profile())
        await shared_browser.start()
        await shared_browser.navigate_to(os.getenv("GAME_URL", "https://bitburner-official.github.io/"))
        record("browser", "Persistent game browser ready")
    except Exception as exc:
        shared_browser = None
        record("error", f"Browser startup failed: {type(exc).__name__}: {exc}")
        log.exception("Could not start persistent game browser")
    runtime_path = STATE / "checkpoints" / "runtime.json"
    runtime = {}
    if runtime_path.exists():
        try:
            runtime = json.loads(runtime_path.read_text())
        except Exception:
            record("warning", "Could not read persisted runtime state; leaving player stopped")
            return
    persisted_state = runtime.get("state")
    if persisted_state in ("operator_stopped", "failed", "exhausted", "completed", "paused"):
        status.update(state=persisted_state, objective=runtime.get("objective", ""), error=runtime.get("error", ""),
                      session=runtime_session_number(runtime.get("session")), outcome=runtime.get("outcome"))
        record("supervisor", f"Startup preserved terminal state {persisted_state}")
        return
    objective_file = STATE / "checkpoints" / "objective.json"
    if not startup_resume_allowed(os.getenv("AUTO_RESUME", "0"), persisted_state, objective_file.exists()):
        return
    if objective_file.exists():
        try:
            objective = json.loads(objective_file.read_text())["objective"]
        except Exception:
            log.exception("Could not load saved objective; leaving player stopped")
            return
        status.update(state="active", objective=objective, session=runtime_session_number(runtime.get("session")),
                      outcome=runtime.get("outcome"))
        record("supervisor", "AUTO_RESUME=1; resuming the saved objective")
        runner = asyncio.create_task(supervise(objective))


@app.on_event("shutdown")
async def shutdown_tasks():
    if backup_worker and not backup_worker.done():
        backup_worker.cancel()
        await asyncio.gather(backup_worker, return_exceptions=True)
    if agent:
        agent.stop()
    if agent_run_task and not agent_run_task.done():
        try:
            await asyncio.wait_for(asyncio.shield(agent_run_task), timeout=10)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            agent_run_task.cancel()
            await asyncio.gather(agent_run_task, return_exceptions=True)


PAGE = r"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Bitburner AI OS</title>
<style>body{font:16px system-ui;background:#111827;color:#e5e7eb;max-width:1100px;margin:2rem auto;padding:0 1rem}section{background:#1f2937;padding:1rem;margin:1rem 0;border-radius:8px}button{padding:.6rem;margin:.3rem;background:#2563eb;color:white;border:0;border-radius:5px}textarea{width:98%;height:5rem;background:#111827;color:white}pre{white-space:pre-wrap;max-height:22rem;overflow:auto}.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}a{color:#93c5fd}</style>
<h1>Bitburner AI OS</h1><section><b id=s>Loading</b> · <span id=m></span><p>Viewer: <a href="http://localhost:6080/vnc.html?autoconnect=1&resize=scale&view_only=1" target=_blank>Read-only Chromium</a> · <button onclick="window.open('http://localhost:6080/vnc.html?autoconnect=1&resize=scale','_blank')">Open interactive viewer</button></p><textarea id=o>__DEFAULT_OBJECTIVE__</textarea><br><button onclick="post('/api/start',{objective:o.value})">Start</button><button onclick="post('/api/pause')">Pause</button><button onclick="post('/api/resume')">Resume</button><button onclick="post('/api/stop')">Emergency stop</button><button onclick="post('/api/inference-check')">Check inference</button></section>
<div class=grid><section><h2>Recent actions and errors</h2><pre id=e></pre></section><section><h2>Checkpoint</h2><pre id=c></pre></section></div><section><h2>Read-only game observation</h2><button onclick="refreshGame()">Refresh visible game stats</button><p>Values come from rendered game UI text and container resource limits; no game internals are read.</p><pre id=g>Open the player once to observe the game interface.</pre></section>
<section><h2>Verified game-save backups</h2><button onclick="refreshBackups()">Refresh backups</button><pre id=b>No game-native export archived yet.</pre></section>
<script>async function post(u,b={}){let r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});alert(await r.text());refresh()}async function refresh(){try{let x=await(await fetch('/api/status')).json();s.textContent=x.state.toUpperCase()+(x.error?' — '+x.error:'');m.textContent=x.model+' @ '+x.node;e.textContent=x.events.map(v=>v.time+' ['+v.kind+'] '+v.message).join('\n');c.textContent=JSON.stringify(x.checkpoint,null,2)||'No checkpoint yet'}catch{}}async function refreshGame(){g.textContent=JSON.stringify(await(await fetch('/api/game-observation')).json(),null,2)}async function refreshBackups(){try{let x=await(await fetch('/api/backups')).json();b.textContent=JSON.stringify(x,null,2)}catch{}}setInterval(refresh,2500);setInterval(refreshBackups,30000);refresh();refreshBackups()</script>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    objective_path = Path("/config/objective.md")
    objective = objective_path.read_text() if objective_path.exists() else "Learn Bitburner through visible game controls and documented Netscript, continuing from the last checkpoint."
    return PAGE.replace("__DEFAULT_OBJECTIVE__", html.escape(objective))
