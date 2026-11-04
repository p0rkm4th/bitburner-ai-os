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
from typing import Optional

import httpx
from browser_use import Agent, BrowserProfile, BrowserSession, ChatOllama, Tools
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

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


def runtime_session_number(value) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def bitnode1_completion_confirmed(report: str, visible: str) -> bool:
    report_lines = [line.casefold() for line in report.splitlines()]
    positive_marker = any("bitnode_1_complete" in line and
                          not any(term in line for term in ("not yet", "not verified", "incomplete", "not complete"))
                          for line in report_lines)
    ui = re.sub(r"[-_\s]+", " ", visible.casefold())
    visible_confirmation = bool(re.search(r"bitnode 1.{0,100}(completed|complete|destroyed|finished)", ui) or
                                re.search(r"(completed|complete|destroyed|finished).{0,100}bitnode 1", ui))
    return positive_marker and visible_confirmation


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


class StartRequest(BaseModel):
    objective: str = Field(min_length=3, max_length=2000)


def get_model() -> ChatOllama:
    base = os.environ["OLLAMA_BASE_URL"].rstrip("/")
    return ChatOllama(model=os.environ["OLLAMA_MODEL"], host=base, timeout=float(os.getenv("OLLAMA_TIMEOUT", "120")))


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


async def archive_game_saves() -> None:
    """Archive only stable, Bitburner-named native exports with bounded retention."""
    retention = max(1, min(100, int(os.getenv("SAVE_BACKUP_RETENTION", "30"))))
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
    tools = Tools(exclude_actions=["evaluate", "write_file", "replace_file", "read_file", "upload_file",
                                  "search", "search_page", "save_as_pdf", "run_python", "run_bash"])
    checkpoint_path = STATE / "checkpoints" / "latest.json"
    previous = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else None
    progress = f"\nPrevious checkpoint (summary only): {json.dumps(previous, ensure_ascii=False)[:3500]}" if previous else ""
    task = f"Open {os.getenv('GAME_URL', 'https://bitburner-official.github.io/')} using ordinary visible browser controls. {objective}{progress}"
    last_activity = time.monotonic()
    prior = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {}
    accomplishments = list(prior.get("accomplishments", []))[-8:]
    errors = list(prior.get("errors", []))[-8:]
    visible = prior.get("latest_visible_state", "")
    subobjective = str(prior.get("subobjective", ""))
    last_output = {}
    last_actions = []
    successful_actions = 0

    async def on_step_start(current: Agent) -> None:
        # The inactivity clock advances only after a completed step, never merely
        # because a slow model call started.
        return None

    async def on_step_end(current: Agent) -> None:
        nonlocal last_activity, visible, last_output, last_actions, subobjective, successful_actions
        last_activity = time.monotonic()
        status["steps"] += 1
        actions = []
        output = {}
        try:
            latest = current.history.history[-1]
            output = latest.model_output.model_dump(exclude_none=True, mode="json")
            actions = [a.model_dump(exclude_none=True, mode="json") for a in latest.model_output.action]
        except Exception:
            pass
        last_output = output
        last_actions = actions
        successful_actions += len(actions)
        subobjective = str(output.get("next_goal") or subobjective)[:700]
        visible = await visible_snapshot(shared_browser)
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
                  max_actions_per_step=4, enable_signal_handler=False,
                  max_history_items=12,
                  save_conversation_path=STATE / "logs" / "conversation.json")
    try:
        agent_run_task = asyncio.create_task(agent.run(max_steps=int(os.getenv("MAX_STEPS", "8")),
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
        save_runtime("active", objective=objective, session=number)
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
                save_runtime("failed", error=status["error"], objective=objective)
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
        if no_progress >= no_progress_limit:
            status.update(state="exhausted", error=f"No observable progress across {no_progress} sessions")
            save_runtime("exhausted", objective=objective, session=number)
            record("supervisor", f"Stopped after {no_progress} sessions with no observable progress")
            break
        save_runtime("active", objective=objective, session=number,
                     no_progress_sessions=no_progress, recent_actions=data.get("recent_actions", []),
                     latest_visible_state=observed, action=action)
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
        status.update(state="active", error="", objective=req.objective, session=0, steps=0)
        save_runtime("active", objective=req.objective)
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
    save_runtime("operator_stopped")
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
                      session=runtime_session_number(runtime.get("session")))
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
        status.update(state="active", objective=objective, session=runtime_session_number(runtime.get("session")))
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
